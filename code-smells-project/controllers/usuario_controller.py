import logging

from flask import jsonify, request

from infra.container import usuario_service
from services.errors import DomainError, NotFoundError

logger = logging.getLogger("loja.usuarios")


def listar():
    return jsonify({"dados": usuario_service().listar(), "sucesso": True}), 200


def buscar(id):
    try:
        return jsonify({"dados": usuario_service().buscar(id), "sucesso": True}), 200
    except NotFoundError as e:
        return jsonify({"erro": str(e)}), 404


def criar():
    dados = request.get_json() or {}
    try:
        usuario_id = usuario_service().criar(
            dados.get("nome", ""),
            dados.get("email", ""),
            dados.get("senha", ""),
        )
    except DomainError as e:
        return jsonify({"erro": str(e)}), 400
    logger.info("usuario criado email=%s", dados.get("email"))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = request.get_json() or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = usuario_service().login(email, senha)
    if usuario:
        logger.info("login ok email=%s", email)
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
    logger.warning("login falhou email=%s", email)
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
