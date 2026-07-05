const logger = require('../utils/logger');
const { DomainError, NotFoundError } = require('../utils/errors');
const { PAYMENT_STATUS } = require('../utils/constants');

// Orquestra o fluxo de checkout: valida curso, resolve/cria usuário, cobra
// (gateway mock) e persiste matrícula/pagamento/auditoria. Não conhece HTTP.
class CheckoutService {
    constructor({
        userRepo,
        courseRepo,
        enrollmentRepo,
        paymentRepo,
        auditRepo,
        passwordService,
        gatewayKey,
    }) {
        this.userRepo = userRepo;
        this.courseRepo = courseRepo;
        this.enrollmentRepo = enrollmentRepo;
        this.paymentRepo = paymentRepo;
        this.auditRepo = auditRepo;
        this.passwordService = passwordService;
        this.gatewayKey = gatewayKey;
    }

    async checkout({ name, email, password, courseId, card }) {
        const course = await this.courseRepo.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const userId = await this._resolveUser({ name, email, password });
        const status = this._charge({ card, userId, courseId: course.id });
        if (status === PAYMENT_STATUS.DENIED) throw new DomainError('Pagamento recusado');

        const enrollmentId = await this.enrollmentRepo.create(userId, course.id);
        await this.paymentRepo.create(enrollmentId, course.price, status);
        await this.auditRepo.log(`Checkout curso ${course.id} por ${userId}`);

        return { enrollmentId };
    }

    async _resolveUser({ name, email, password }) {
        const existing = await this.userRepo.findByEmail(email);
        if (existing) return existing.id;
        // Novo usuário: exige senha e a armazena com hash (sem default "123456").
        if (!password) throw new DomainError('senha obrigatória para novo usuário');
        const pass = await this.passwordService.hash(password);
        return this.userRepo.create({ name, email, pass });
    }

    // Gateway de pagamento simulado. Não loga PAN nem a chave (RP-11 corrige AP-02).
    _charge({ card, userId, courseId }) {
        if (!this.gatewayKey) throw new DomainError('gateway de pagamento não configurado', 500);
        logger.info('checkout_payment_attempt', { userId, courseId });
        return card.startsWith('4') ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = CheckoutService;
