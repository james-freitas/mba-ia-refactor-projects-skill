import logging

logger = logging.getLogger("loja.notifications")


class NotificationService:
    """Efeitos colaterais (e-mail/SMS/push) isolados da camada de apresentação.

    No projeto original isto era feito com `print` dentro do controller (AP-04).
    Aqui vira uma dependência injetada, facilmente substituível por um provedor
    real. Por ora, apenas registra via logging (RP-08).
    """

    def pedido_criado(self, usuario_id, pedido_id):
        logger.info(
            "pedido %s criado para usuario %s (email/sms/push enfileirados)",
            pedido_id,
            usuario_id,
        )

    def status_alterado(self, pedido_id, status):
        if status == "aprovado":
            logger.info("pedido %s aprovado — preparar envio", pedido_id)
        elif status == "cancelado":
            logger.info("pedido %s cancelado — devolver estoque", pedido_id)
