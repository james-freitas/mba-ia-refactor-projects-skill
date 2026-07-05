from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from database import db
from services.errors import DomainError
from utils.time import utcnow
from utils.logger import get_logger

logger = get_logger(__name__)


def create_app(config_object=Config):
    """Bootstrap: cria o app, injeta config, registra blueprints e handlers."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app)
    db.init_app(app)

    from routes.task_routes import task_bp
    from routes.user_routes import user_bp
    from routes.report_routes import report_bp

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(utcnow())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    # Tratamento de erro centralizado (RP-09 corrige AP-09).
    @app.errorhandler(DomainError)
    def handle_domain_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        db.session.rollback()
        logger.exception('unexpected_error')
        return jsonify({'error': 'Erro interno'}), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
