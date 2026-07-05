import smtplib

from utils.time import utcnow
from utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    # Credenciais injetadas a partir da config/env (RP-02 corrige AP-02).
    def __init__(self, host, port, user, password):
        self.notifications = []
        self.email_host = host
        self.email_port = port
        self.email_user = user
        self.email_password = password

    def send_email(self, to, subject, body):
        if not self.email_user or not self.email_password:
            logger.warning('email_not_configured to=%s', to)
            return False
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info('email_sent to=%s', to)
            return True
        except smtplib.SMTPException:
            logger.exception('email_send_failed to=%s', to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utcnow(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
