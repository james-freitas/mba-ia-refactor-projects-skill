from flask import jsonify, request

from infra.container import pedido_service
from services.errors import DomainError


def criar():
    dados = request.get_json() or {}
    try:
        resultado = pedido_service().criar(
            dados.get("usuario_id"), dados.get("itens", [])
        )
    except DomainError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 400
    return (
        jsonify(
            {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}
        ),
        201,
    )


def listar_por_usuario(usuario_id):
    pedidos = pedido_service().listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos():
    pedidos = pedido_service().listar_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status(pedido_id):
    dados = request.get_json() or {}
    try:
        pedido_service().atualizar_status(pedido_id, dados.get("status", ""))
    except DomainError as e:
        return jsonify({"erro": str(e)}), 400
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
