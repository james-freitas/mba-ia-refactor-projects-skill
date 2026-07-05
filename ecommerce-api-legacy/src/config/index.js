// Configuração via variáveis de ambiente (RP-02 corrige AP-02).
// Defaults seguros apenas para desenvolvimento; nenhum segredo real no código.
module.exports = {
    port: Number(process.env.PORT || 3000),
    // Chave do gateway de pagamento — obrigatória em produção, vem do ambiente.
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_dev_placeholder',
    db: {
        filename: process.env.DB_FILE || ':memory:',
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
    },
    smtpUser: process.env.SMTP_USER,
};
