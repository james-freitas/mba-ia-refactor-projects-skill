import os

# Configuração via variáveis de ambiente (RP-02 corrige AP-02).
# Default de dev inseguro apenas para rodar localmente; em produção vem do env.
class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-change-me')

    # Notificação por e-mail — credenciais do ambiente, nunca hardcoded.
    MAIL_HOST = os.environ.get('MAIL_HOST', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USER = os.environ.get('MAIL_USER')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
