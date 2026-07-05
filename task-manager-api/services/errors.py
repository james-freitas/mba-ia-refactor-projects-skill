# Erros de domínio: carregam o status HTTP, mas não conhecem Flask.
# Traduzidos para resposta pelo error handler central (RP-09 corrige AP-09).
class DomainError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


class ValidationError(DomainError):
    def __init__(self, message):
        super().__init__(message, 400)


class NotFoundError(DomainError):
    def __init__(self, message):
        super().__init__(message, 404)


class ConflictError(DomainError):
    def __init__(self, message):
        super().__init__(message, 409)
