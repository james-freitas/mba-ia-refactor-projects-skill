from datetime import datetime

from models.task import Task
from services.errors import ValidationError, NotFoundError
from utils.time import utcnow
from utils.logger import get_logger
from utils.constants import (
    VALID_STATUSES,
    MIN_TITLE_LENGTH,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MAX_PRIORITY,
    DEFAULT_PRIORITY,
)

logger = get_logger(__name__)


class TaskService:
    def __init__(self, task_repo, user_repo, category_repo):
        self.tasks = task_repo
        self.users = user_repo
        self.categories = category_repo

    # --- serialização (mapper) ---
    def _serialize(self, task, include_relations=False):
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        if include_relations:
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
        return data

    def _parse_date(self, value):
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None

    # --- casos de uso ---
    def list_tasks(self):
        return [self._serialize(t, include_relations=True) for t in self.tasks.list_with_relations()]

    def get_task(self, task_id):
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return self._serialize(task)

    def create_task(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        if len(title) < MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')

        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            raise ValidationError('Status inválido')

        priority = data.get('priority', DEFAULT_PRIORITY)
        if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
            raise ValidationError('Prioridade deve ser entre 1 e 5')

        user_id = data.get('user_id')
        if user_id and not self.users.get(user_id):
            raise NotFoundError('Usuário não encontrado')

        category_id = data.get('category_id')
        if category_id and not self.categories.get(category_id):
            raise NotFoundError('Categoria não encontrada')

        task = Task()
        task.title = title
        task.description = data.get('description', '')
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        due_date = data.get('due_date')
        if due_date:
            parsed = self._parse_date(due_date)
            if not parsed:
                raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
            task.due_date = parsed

        tags = data.get('tags')
        if tags:
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        self.tasks.add(task)
        self.tasks.commit()
        logger.info('task_created id=%s', task.id)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        if not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            if len(data['title']) < MIN_TITLE_LENGTH:
                raise ValidationError('Título muito curto')
            if len(data['title']) > MAX_TITLE_LENGTH:
                raise ValidationError('Título muito longo')
            task.title = data['title']

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if data['status'] not in VALID_STATUSES:
                raise ValidationError('Status inválido')
            task.status = data['status']

        if 'priority' in data:
            if data['priority'] < MIN_PRIORITY or data['priority'] > MAX_PRIORITY:
                raise ValidationError('Prioridade deve ser entre 1 e 5')
            task.priority = data['priority']

        if 'user_id' in data:
            if data['user_id'] and not self.users.get(data['user_id']):
                raise NotFoundError('Usuário não encontrado')
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not self.categories.get(data['category_id']):
                raise NotFoundError('Categoria não encontrada')
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                parsed = self._parse_date(data['due_date'])
                if not parsed:
                    raise ValidationError('Formato de data inválido')
                task.due_date = parsed
            else:
                task.due_date = None

        if 'tags' in data:
            tags = data['tags']
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        task.updated_at = utcnow()
        self.tasks.commit()
        logger.info('task_updated id=%s', task.id)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        self.tasks.delete(task)
        self.tasks.commit()
        logger.info('task_deleted id=%s', task_id)

    def search_tasks(self, q, status, priority, user_id):
        results = self.tasks.search(q or None, status or None, priority or None, user_id or None)
        return [t.to_dict() for t in results]

    def stats(self):
        tasks = self.tasks.list()
        total = len(tasks)
        counts = {s: 0 for s in VALID_STATUSES}
        overdue = 0
        for t in tasks:
            if t.status in counts:
                counts[t.status] += 1
            if t.is_overdue():
                overdue += 1
        done = counts['done']
        return {
            'total': total,
            'pending': counts['pending'],
            'in_progress': counts['in_progress'],
            'done': done,
            'cancelled': counts['cancelled'],
            'overdue': overdue,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }
