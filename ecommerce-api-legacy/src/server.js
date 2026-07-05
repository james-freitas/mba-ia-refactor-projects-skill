const express = require('express');
const config = require('./config');
const logger = require('./utils/logger');

const Database = require('./db');
const initSchema = require('./db/schema');

const passwordService = require('./services/passwordService');
const UserRepository = require('./repositories/userRepository');
const CourseRepository = require('./repositories/courseRepository');
const EnrollmentRepository = require('./repositories/enrollmentRepository');
const PaymentRepository = require('./repositories/paymentRepository');
const AuditRepository = require('./repositories/auditRepository');
const ReportRepository = require('./repositories/reportRepository');

const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');
const UserService = require('./services/userService');

const checkoutController = require('./controllers/checkoutController');
const reportController = require('./controllers/reportController');
const userController = require('./controllers/userController');
const healthController = require('./controllers/healthController');

const buildRouter = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

// Entrypoint: apenas wiring (injeta dependências, registra rotas, sobe o app).
async function bootstrap() {
    const db = new Database(config.db.filename);
    await initSchema(db, passwordService);

    // Data layer
    const userRepo = new UserRepository(db);
    const courseRepo = new CourseRepository(db);
    const enrollmentRepo = new EnrollmentRepository(db);
    const paymentRepo = new PaymentRepository(db);
    const auditRepo = new AuditRepository(db);
    const reportRepo = new ReportRepository(db);

    // Business layer
    const checkoutService = new CheckoutService({
        userRepo,
        courseRepo,
        enrollmentRepo,
        paymentRepo,
        auditRepo,
        passwordService,
        gatewayKey: config.paymentGatewayKey,
    });
    const reportService = new ReportService({ reportRepo });
    const userService = new UserService({ db, userRepo, enrollmentRepo, paymentRepo });

    // Presentation layer
    const app = express();
    app.use(express.json());
    app.use(
        buildRouter({
            checkout: checkoutController(checkoutService),
            report: reportController(reportService),
            user: userController(userService),
            health: healthController(),
        })
    );
    app.use(errorHandler);

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}`);
    });
}

bootstrap().catch((err) => {
    logger.error('boot_failed', { message: err.message });
    process.exit(1);
});
