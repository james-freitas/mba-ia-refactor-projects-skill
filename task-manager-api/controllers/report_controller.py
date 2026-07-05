from flask import request, jsonify

from container import report_service, category_service


def summary_report():
    return jsonify(report_service.summary()), 200


def user_report(user_id):
    return jsonify(report_service.user_report(user_id)), 200


def get_categories():
    return jsonify(category_service.list_categories()), 200


def create_category():
    return jsonify(category_service.create_category(request.get_json())), 201


def update_category(cat_id):
    return jsonify(category_service.update_category(cat_id, request.get_json())), 200


def delete_category(cat_id):
    category_service.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
