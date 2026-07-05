from werkzeug.security import check_password_hash, generate_password_hash

from services.errors import DomainError, NotFoundError


class UsuarioService:
    """Regras de negócio de usuários, incluindo hashing seguro de senha (RP-03)."""

    def __init__(self, repo):
        self.repo = repo

    def listar(self):
        return [u.to_dict() for u in self.repo.list()]

    def buscar(self, usuario_id):
        usuario = self.repo.get_by_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario.to_dict()

    def criar(self, nome, email, senha, tipo="cliente"):
        if not nome or not email or not senha:
            raise DomainError("Nome, email e senha são obrigatórios")
        senha_hash = generate_password_hash(senha)
        return self.repo.create(nome, email, senha_hash, tipo)

    def login(self, email, senha):
        usuario = self.repo.get_by_email(email)
        if not usuario or not check_password_hash(usuario.senha, senha):
            return None
        return {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "tipo": usuario.tipo,
        }
