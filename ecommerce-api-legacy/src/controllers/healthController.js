// Health check informativo, sem vazar segredos (guideline de arquitetura).
function healthController() {
    return (req, res) => res.json({ status: 'ok' });
}

module.exports = healthController;
