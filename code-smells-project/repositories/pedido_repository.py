from models.pedido import ItemPedido, Pedido


class PedidoRepository:
    """Acesso à tabela `pedidos`/`itens_pedido`. Corrige o N+1 com um único
    JOIN por lote de pedidos (RP-07) e usa agregação SQL no relatório."""

    def __init__(self, db):
        self.db = db

    def create(self, usuario_id, itens_com_preco, total):
        cur = self.db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cur.lastrowid
        for item in itens_com_preco:
            self.db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
            self.db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        self.db.commit()
        return pedido_id

    def _fetch(self, where_sql="", params=()):
        rows = self.db.execute(
            "SELECT * FROM pedidos " + where_sql, params
        ).fetchall()
        pedidos = [Pedido.from_row(r) for r in rows]
        if not pedidos:
            return []

        ids = [p.id for p in pedidos]
        placeholders = ",".join("?" for _ in ids)
        item_rows = self.db.execute(
            "SELECT i.pedido_id, i.produto_id, pr.nome AS produto_nome, "
            "       i.quantidade, i.preco_unitario "
            "FROM itens_pedido i "
            "LEFT JOIN produtos pr ON pr.id = i.produto_id "
            f"WHERE i.pedido_id IN ({placeholders})",
            ids,
        ).fetchall()

        itens_por_pedido = {}
        for row in item_rows:
            itens_por_pedido.setdefault(row["pedido_id"], []).append(
                ItemPedido.from_row(row)
            )
        for pedido in pedidos:
            pedido.itens = itens_por_pedido.get(pedido.id, [])
        return pedidos

    def list_by_user(self, usuario_id):
        return self._fetch("WHERE usuario_id = ?", (usuario_id,))

    def list_all(self):
        return self._fetch()

    def update_status(self, pedido_id, status):
        self.db.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id)
        )
        self.db.commit()

    def report_counts(self):
        return self.db.execute(
            "SELECT COUNT(*) AS total, "
            "       COALESCE(SUM(total), 0) AS faturamento, "
            "       SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes, "
            "       SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados, "
            "       SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados "
            "FROM pedidos"
        ).fetchone()
