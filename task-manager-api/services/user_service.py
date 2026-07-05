import re

from models.user import User
from services.errors import DomainError, ValidationError, NotFoundError, ConflictError
from utils.logger import get_logger
from utils.constants import VALID_ROLES, MIN_PASSWORD_LENGTH, EMAIL_REGEX

logger = get_logger(__name__)


class UserService:
    def __init__(self, user_repo, task_repo):
        self.users = user_repo
        self.tasks = task_repo

    def list_users(self):
        result = []
        for u in self.users.list_with_tasks():
            result.append({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'active': u.active,
                'created_at': str(u.created_at),
                'task_count': len(u.tasks),
            })
        return result

    def get_user_with_tasks(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in self.tasks.by_user(user_id)]
        return data

    def create_user(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        if not re.match(EMAIL_REGEX, email):
            raise ValidationError('Email inválido')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha deve ter no mínimo 4 caracteres')
        if self.users.by_email(email):
            raise ConflictError('Email já cadastrado')
        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        self.users.add(user)
        self.users.commit()
        logger.info('user_created id=%s', user.id)
        return user.to_dict()

    def update_user(self, user_id, data):
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not re.match(EMAIL_REGEX, data['email']):
                raise ValidationError('Email inválido')
            existing = self.users.by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        self.users.commit()
        return user.to_dict()

    def delete_user(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        for t in self.tasks.by_user(user_id):
            self.tasks.delete(t)
        self.users.delete(user)
        self.users.commit()
        logger.info('user_deleted id=%s', user_id)

    def get_user_tasks(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        result = []
        for t in self.tasks.by_user(user_id):
            result.append({
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(),
            })
        return result

    def login(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = self.users.by_email(email)
        if not user or not user.check_password(password):
            raise DomainError('Credenciais inválidas', 401)
        if not user.active:
            raise DomainError('Usuário inativo', 403)

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': 'fake-jwt-token-' + str(user.id),
        }
