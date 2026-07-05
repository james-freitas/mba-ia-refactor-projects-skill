from flask import Blueprint

from controllers import report_controller

report_bp = Blueprint('reports', __name__)

report_bp.add_url_rule('/reports/summary', view_func=report_controller.summary_report, methods=['GET'])
report_bp.add_url_rule('/reports/user/<int:user_id>', view_func=report_controller.user_report, methods=['GET'])
report_bp.add_url_rule('/categories', view_func=report_controller.get_categories, methods=['GET'])
report_bp.add_url_rule('/categories', view_func=report_controller.create_category, methods=['POST'])
report_bp.add_url_rule('/categories/<int:cat_id>', view_func=report_controller.update_category, methods=['PUT'])
report_bp.add_url_rule('/categories/<int:cat_id>', view_func=report_controller.delete_category, methods=['DELETE'])
