from models.usuario import Usuario


class UsuarioRepository:
    """Único ponto de acesso à tabela `usuarios`. Queries parametrizadas (RP-01)."""

    def __init__(self, db):
        self.db = db

    def list(self):
        rows = self.db.execute("SELECT * FROM usuarios").fetchall()
        return [Usuario.from_row(r) for r in rows]

    def get_by_id(self, usuario_id):
        row = self.db.execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return Usuario.from_row(row) if row else None

    def get_by_email(self, email):
        row = self.db.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        return Usuario.from_row(row) if row else None

    def create(self, nome, email, senha_hash, tipo):
        cur = self.db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        self.db.commit()
        return cur.lastrowid
