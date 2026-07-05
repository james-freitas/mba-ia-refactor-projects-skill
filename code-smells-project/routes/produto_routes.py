from flask import Blueprint

from controllers import produto_controller as c

produto_bp = Blueprint("produtos", __name__)

produto_bp.add_url_rule("/produtos", "listar", c.listar, methods=["GET"])
produto_bp.add_url_rule("/produtos/busca", "buscar_produtos", c.buscar_produtos, methods=["GET"])
produto_bp.add_url_rule("/produtos/<int:id>", "buscar", c.buscar, methods=["GET"])
produto_bp.add_url_rule("/produtos", "criar", c.criar, methods=["POST"])
produto_bp.add_url_rule("/produtos/<int:id>", "atualizar", c.atualizar, methods=["PUT"])
produto_bp.add_url_rule("/produtos/<int:id>", "deletar", c.deletar, methods=["DELETE"])
