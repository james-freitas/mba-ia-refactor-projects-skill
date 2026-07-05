from dataclasses import dataclass, field


@dataclass
class ItemPedido:
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: float

    @classmethod
    def from_row(cls, row):
        return cls(
            produto_id=row["produto_id"],
            produto_nome=row["produto_nome"] if row["produto_nome"] else "Desconhecido",
            quantidade=row["quantidade"],
            preco_unitario=row["preco_unitario"],
        )

    def to_dict(self):
        return {
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "quantidade": self.quantidade,
            "preco_unitario": self.preco_unitario,
        }


@dataclass
class Pedido:
    id: int
    usuario_id: int
    status: str
    total: float
    criado_em: str
    itens: list = field(default_factory=list)

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            usuario_id=row["usuario_id"],
            status=row["status"],
            total=row["total"],
            criado_em=row["criado_em"],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "status": self.status,
            "total": self.total,
            "criado_em": self.criado_em,
            "itens": [i.to_dict() for i in self.itens],
        }
