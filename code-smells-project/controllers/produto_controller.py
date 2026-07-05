import logging

from flask import jsonify, request

from infra.container import produto_service
from services.errors import DomainError, NotFoundError

logger = logging.getLogger("loja.produtos")


def listar():
    produtos = produto_service().listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar(id):
    try:
        produto = produto_service().buscar(id)
        return jsonify({"dados": produto, "sucesso": True}), 200
    except NotFoundError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 404


def criar():
    dados = request.get_json() or {}
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            return jsonify({"erro": f"Campo '{campo}' é obrigatório"}), 400
    try:
        produto_id = produto_service().criar(
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )
    except DomainError as e:
        return jsonify({"erro": str(e)}), 400
    logger.info("produto criado id=%s", produto_id)
    return (
        jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}),
        201,
    )


def atualizar(id):
    dados = request.get_json() or {}
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            return jsonify({"erro": f"Campo '{campo}' é obrigatório"}), 400
    try:
        produto_service().atualizar(
            id,
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )
    except NotFoundError as e:
        return jsonify({"erro": str(e)}), 404
    except DomainError as e:
        return jsonify({"erro": str(e)}), 400
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(id):
    try:
        produto_service().deletar(id)
    except NotFoundError as e:
        return jsonify({"erro": str(e)}), 404
    logger.info("produto deletado id=%s", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", default=None, type=float)
    preco_max = request.args.get("preco_max", default=None, type=float)
    resultados = produto_service().buscar_produtos(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
