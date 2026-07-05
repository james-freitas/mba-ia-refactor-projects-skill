import logging

from flask import jsonify

from infra.db import get_db

logger = logging.getLogger("loja.health")


def health():
    try:
        db = get_db()
        produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        return (
            jsonify(
                {
                    "status": "ok",
                    "database": "connected",
                    "counts": {
                        "produtos": produtos,
                        "usuarios": usuarios,
                        "pedidos": pedidos,
                    },
                    "versao": "1.0.0",
                }
            ),
            200,
        )
    except Exception:
        # Segurança: não expõe segredos nem detalhes internos (RP-02/RP-09).
        logger.exception("health check falhou")
        return jsonify({"status": "erro", "database": "disconnected"}), 500
