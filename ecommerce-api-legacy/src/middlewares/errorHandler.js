const logger = require('../utils/logger');

// Tratamento de erro centralizado (RP-09 corrige AP-09): resposta genérica ao
// cliente para 5xx, mensagem de domínio para 4xx; detalhe fica só no log.
module.exports = function errorHandler(err, req, res, next) {
    const status = err.status || 500;
    if (status >= 500) {
        logger.error('unhandled_error', { path: req.path, message: err.message });
        return res.status(status).send('Erro interno');
    }
    logger.warn('domain_error', { path: req.path, message: err.message });
    return res.status(status).send(err.message);
};
