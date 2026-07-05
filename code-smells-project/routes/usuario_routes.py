from flask import Blueprint

from controllers import usuario_controller as c

usuario_bp = Blueprint("usuarios", __name__)

usuario_bp.add_url_rule("/usuarios", "listar", c.listar, methods=["GET"])
usuario_bp.add_url_rule("/usuarios/<int:id>", "buscar", c.buscar, methods=["GET"])
usuario_bp.add_url_rule("/usuarios", "criar", c.criar, methods=["POST"])
usuario_bp.add_url_rule("/login", "login", c.login, methods=["POST"])
