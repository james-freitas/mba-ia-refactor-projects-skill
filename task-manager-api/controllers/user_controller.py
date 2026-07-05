from flask import request, jsonify

from container import user_service


def list_users():
    return jsonify(user_service.list_users()), 200


def get_user(user_id):
    return jsonify(user_service.get_user_with_tasks(user_id)), 200


def create_user():
    return jsonify(user_service.create_user(request.get_json())), 201


def update_user(user_id):
    return jsonify(user_service.update_user(user_id, request.get_json())), 200


def delete_user(user_id):
    user_service.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    return jsonify(user_service.get_user_tasks(user_id)), 200


def login():
    return jsonify(user_service.login(request.get_json())), 200
