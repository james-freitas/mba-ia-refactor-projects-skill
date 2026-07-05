const express = require('express');

// Apenas mapeia método + URL → controller. Sem lógica.
function buildRouter({ checkout, report, user, health }) {
    const router = express.Router();

    router.get('/health', health);
    router.post('/api/checkout', checkout);
    router.get('/api/admin/financial-report', report);
    router.delete('/api/users/:id', user.remove);

    return router;
}

module.exports = buildRouter;
