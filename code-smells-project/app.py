import logging

from flask import Flask
from flask_cors import CORS

from config import Config
from infra import db as db_module
from infra.schema import init_db
from routes.health_routes import health_bp
from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.relatorio_routes import relatorio_bp
from routes.usuario_routes import usuario_bp


def create_app(config_object=Config):
    """Application factory — apenas wiring: config, logging, DB e blueprints."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )

    CORS(app)
    db_module.init_app(app)
    init_db(app.config["DB_PATH"])

    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(health_bp)

    return app


app = create_app()


if __name__ == "__main__":
    logging.getLogger("loja").info("Servidor iniciado em http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
