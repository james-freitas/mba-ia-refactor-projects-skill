from dataclasses import dataclass


@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    senha: str  # hash com salt; nunca serializado (RP-11)
    tipo: str
    criado_em: str

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            nome=row["nome"],
            email=row["email"],
            senha=row["senha"],
            tipo=row["tipo"],
            criado_em=row["criado_em"],
        )

    def to_dict(self):
        # Segurança: o hash de senha NÃO é exposto em respostas da API.
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "tipo": self.tipo,
            "criado_em": self.criado_em,
        }
