from flask import Blueprint

from controllers import pedido_controller as c

pedido_bp = Blueprint("pedidos", __name__)

pedido_bp.add_url_rule("/pedidos", "criar", c.criar, methods=["POST"])
pedido_bp.add_url_rule("/pedidos", "listar_todos", c.listar_todos, methods=["GET"])
pedido_bp.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>",
    "listar_por_usuario",
    c.listar_por_usuario,
    methods=["GET"],
)
pedido_bp.add_url_rule(
    "/pedidos/<int:pedido_id>/status",
    "atualizar_status",
    c.atualizar_status,
    methods=["PUT"],
)
