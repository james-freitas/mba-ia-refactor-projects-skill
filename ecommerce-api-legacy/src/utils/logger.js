// Logger estruturado e centralizado (RP-08 corrige AP-11).
// Nunca logar segredos, chaves de gateway ou dados de cartão (PAN).
function emit(level, message, meta) {
    const base = `[${new Date().toISOString()}] ${level.toUpperCase()} ${message}`;
    const line = meta ? `${base} ${JSON.stringify(meta)}` : base;
    (level === 'error' ? console.error : console.log)(line);
}

module.exports = {
    error: (message, meta) => emit('error', message, meta),
    warn: (message, meta) => emit('warn', message, meta),
    info: (message, meta) => emit('info', message, meta),
    debug: (message, meta) => emit('debug', message, meta),
};
