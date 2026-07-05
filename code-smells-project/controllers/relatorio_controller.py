from flask import jsonify

from infra.container import relatorio_service


def vendas():
    return jsonify({"dados": relatorio_service().vendas(), "sucesso": True}), 200
