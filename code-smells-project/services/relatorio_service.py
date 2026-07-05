class RelatorioService:
    """Relatório de vendas. Faixas de desconto e ticket médio (regra de negócio)
    ficam aqui; a agregação numérica é feita em SQL no repositório (RP-07)."""

    def __init__(self, pedido_repo):
        self.pedidos = pedido_repo

    def vendas(self):
        r = self.pedidos.report_counts()
        total_pedidos = r["total"]
        faturamento = r["faturamento"] or 0

        desconto = 0
        if faturamento > 10000:
            desconto = faturamento * 0.1
        elif faturamento > 5000:
            desconto = faturamento * 0.05
        elif faturamento > 1000:
            desconto = faturamento * 0.02

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": r["pendentes"] or 0,
            "pedidos_aprovados": r["aprovados"] or 0,
            "pedidos_cancelados": r["cancelados"] or 0,
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
