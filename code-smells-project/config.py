import os


class Config:
    """Configuração lida de variáveis de ambiente (RP-02).

    Em produção, defina SECRET_KEY/DB_PATH no ambiente. O default de SECRET_KEY
    existe apenas para rodar em desenvolvimento e NÃO deve ser usado em produção.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
