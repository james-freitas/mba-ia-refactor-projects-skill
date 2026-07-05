from services.errors import DomainError

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


class PedidoService:
    """Orquestra a criação de pedidos: valida estoque, calcula total, persiste e
    dispara notificações. Toda a regra que vivia no `models.py` original (AP-04)."""

    def __init__(self, pedido_repo, produto_repo, notifier):
        self.pedidos = pedido_repo
        self.produtos = produto_repo
        self.notifier = notifier

    def criar(self, usuario_id, itens):
        if not usuario_id:
            raise DomainError("Usuario ID é obrigatório")
        if not itens or len(itens) == 0:
            raise DomainError("Pedido deve ter pelo menos 1 item")

        total = 0
        itens_com_preco = []
        for item in itens:
            produto = self.produtos.get_by_id(item["produto_id"])
            if produto is None:
                raise DomainError(f"Produto {item['produto_id']} não encontrado")
            if produto.estoque < item["quantidade"]:
                raise DomainError(f"Estoque insuficiente para {produto.nome}")
            total += produto.preco * item["quantidade"]
            itens_com_preco.append(
                {
                    "produto_id": item["produto_id"],
                    "quantidade": item["quantidade"],
                    "preco_unitario": produto.preco,
                }
            )

        pedido_id = self.pedidos.create(usuario_id, itens_com_preco, total)
        self.notifier.pedido_criado(usuario_id, pedido_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_por_usuario(self, usuario_id):
        return [p.to_dict() for p in self.pedidos.list_by_user(usuario_id)]

    def listar_todos(self):
        return [p.to_dict() for p in self.pedidos.list_all()]

    def atualizar_status(self, pedido_id, novo_status):
        if novo_status not in STATUS_VALIDOS:
            raise DomainError("Status inválido")
        self.pedidos.update_status(pedido_id, novo_status)
        self.notifier.status_alterado(pedido_id, novo_status)
