class DomainError(Exception):
    """Violação de regra de negócio -> HTTP 400."""


class NotFoundError(Exception):
    """Recurso inexistente -> HTTP 404."""
