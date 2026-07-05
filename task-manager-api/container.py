"""Composition root: instancia repositories e services e injeta dependências."""
from config import Config
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from repositories.category_repository import CategoryRepository
from services.task_service import TaskService
from services.user_service import UserService
from services.report_service import ReportService
from services.category_service import CategoryService
from services.notification_service import NotificationService

# Data layer
task_repo = TaskRepository()
user_repo = UserRepository()
category_repo = CategoryRepository()

# Business layer
task_service = TaskService(task_repo, user_repo, category_repo)
user_service = UserService(user_repo, task_repo)
report_service = ReportService(task_repo, user_repo, category_repo)
category_service = CategoryService(category_repo, task_repo)
notification_service = NotificationService(
    Config.MAIL_HOST, Config.MAIL_PORT, Config.MAIL_USER, Config.MAIL_PASSWORD
)
