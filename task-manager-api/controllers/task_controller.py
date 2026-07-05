from flask import request, jsonify

from container import task_service


# Controllers magros: leem o request, chamam o service, mapeiam para HTTP (RP-06).
# Erros de domínio sobem para o handler central (RP-09).
def list_tasks():
    return jsonify(task_service.list_tasks()), 200


def get_task(task_id):
    return jsonify(task_service.get_task(task_id)), 200


def create_task():
    return jsonify(task_service.create_task(request.get_json())), 201


def update_task(task_id):
    return jsonify(task_service.update_task(task_id, request.get_json())), 200


def delete_task(task_id):
    task_service.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    return jsonify(task_service.search_tasks(
        request.args.get('q', ''),
        request.args.get('status', ''),
        request.args.get('priority', ''),
        request.args.get('user_id', ''),
    )), 200


def task_stats():
    return jsonify(task_service.stats()), 200
