from flask import Blueprint

from controllers import relatorio_controller as c

relatorio_bp = Blueprint("relatorios", __name__)

relatorio_bp.add_url_rule("/relatorios/vendas", "vendas", c.vendas, methods=["GET"])
