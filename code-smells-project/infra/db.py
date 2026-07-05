import sqlite3

from flask import current_app, g


def get_db():
    """Conexão SQLite por request (armazenada em flask.g), fechada no teardown.

    Substitui o singleton global mutável do projeto original (AP-07).
    """
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
