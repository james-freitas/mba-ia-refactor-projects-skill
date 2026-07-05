// Erros de domínio: carregam o status HTTP apropriado, mas não conhecem Express.
// O controller/middleware os traduz para resposta (RP-09).
class DomainError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.name = 'DomainError';
        this.status = status;
    }
}

class NotFoundError extends DomainError {
    constructor(message) {
        super(message, 404);
        this.name = 'NotFoundError';
    }
}

module.exports = { DomainError, NotFoundError };
