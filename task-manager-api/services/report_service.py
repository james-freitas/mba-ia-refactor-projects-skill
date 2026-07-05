from datetime import timedelta

from services.errors import NotFoundError
from utils.time import utcnow
from utils.constants import CLOSED_STATUSES


class ReportService:
    def __init__(self, task_repo, user_repo, category_repo):
        self.tasks = task_repo
        self.users = user_repo
        self.categories = category_repo

    def summary(self):
        # Carrega tudo em poucas queries e agrega em memória — sem N+1 por usuário
        # (RP-07 corrige AP-06).
        tasks = self.tasks.list()
        users = self.users.list()
        now = utcnow()
        seven_days_ago = now - timedelta(days=7)

        status_counts = {'pending': 0, 'in_progress': 0, 'done': 0, 'cancelled': 0}
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        overdue_count = 0
        overdue_list = []
        recent_tasks = 0
        recent_done = 0
        tasks_by_user = {}

        for t in tasks:
            if t.status in status_counts:
                status_counts[t.status] += 1
            if t.priority in priority_counts:
                priority_counts[t.priority] += 1
            if t.is_overdue():
                overdue_count += 1
                overdue_list.append({
                    'id': t.id,
                    'title': t.title,
                    'due_date': str(t.due_date),
                    'days_overdue': (now - t.due_date).days,
                })
            if t.created_at and t.created_at >= seven_days_ago:
                recent_tasks += 1
            if t.status == 'done' and t.updated_at and t.updated_at >= seven_days_ago:
                recent_done += 1
            tasks_by_user.setdefault(t.user_id, []).append(t)

        user_stats = []
        for u in users:
            user_tasks = tasks_by_user.get(u.id, [])
            total = len(user_tasks)
            completed = sum(1 for t in user_tasks if t.status == 'done')
            user_stats.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': len(tasks),
                'total_users': len(users),
                'total_categories': len(self.categories.list()),
            },
            'tasks_by_status': {
                'pending': status_counts['pending'],
                'in_progress': status_counts['in_progress'],
                'done': status_counts['done'],
                'cancelled': status_counts['cancelled'],
            },
            'tasks_by_priority': {
                'critical': priority_counts[1],
                'high': priority_counts[2],
                'medium': priority_counts[3],
                'low': priority_counts[4],
                'minimal': priority_counts[5],
            },
            'overdue': {
                'count': overdue_count,
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = self.tasks.by_user(user_id)
        counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0

        for t in tasks:
            if t.status in counts:
                counts[t.status] += 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        total = len(tasks)
        done = counts['done']
        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': counts['pending'],
                'in_progress': counts['in_progress'],
                'cancelled': counts['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
            },
        }
