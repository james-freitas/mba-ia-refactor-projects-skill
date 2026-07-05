from models.produto import Produto


class ProdutoRepository:
    """Único ponto de acesso à tabela `produtos`. Queries parametrizadas (RP-01)."""

    def __init__(self, db):
        self.db = db

    def list(self):
        rows = self.db.execute("SELECT * FROM produtos").fetchall()
        return [Produto.from_row(r) for r in rows]

    def get_by_id(self, produto_id):
        row = self.db.execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return Produto.from_row(row) if row else None

    def create(self, nome, descricao, preco, estoque, categoria):
        cur = self.db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        self.db.commit()
        return cur.lastrowid

    def update(self, produto_id, nome, descricao, preco, estoque, categoria):
        self.db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
            "categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        self.db.commit()

    def delete(self, produto_id):
        self.db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        self.db.commit()

    def search(self, termo, categoria, preco_min, preco_max):
        query = "SELECT * FROM produtos WHERE 1 = 1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            query += " AND preco <= ?"
            params.append(preco_max)
        rows = self.db.execute(query, params).fetchall()
        return [Produto.from_row(r) for r in rows]
