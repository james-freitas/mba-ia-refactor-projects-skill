from sqlalchemy.orm import selectinload
from database import db
from models.task import Task


class TaskRepository:
    def get(self, task_id):
        return db.session.get(Task, task_id)

    def list(self):
        return db.session.scalars(db.select(Task)).all()

    def list_with_relations(self):
        # Eager loading evita o N+1 ao acessar user/category (RP-07 corrige AP-06).
        stmt = db.select(Task).options(selectinload(Task.user), selectinload(Task.category))
        return db.session.scalars(stmt).all()

    def by_user(self, user_id):
        return db.session.scalars(db.select(Task).filter_by(user_id=user_id)).all()

    def search(self, q=None, status=None, priority=None, user_id=None):
        stmt = db.select(Task)
        if q:
            stmt = stmt.filter(db.or_(Task.title.like(f'%{q}%'), Task.description.like(f'%{q}%')))
        if status:
            stmt = stmt.filter(Task.status == status)
        if priority:
            stmt = stmt.filter(Task.priority == int(priority))
        if user_id:
            stmt = stmt.filter(Task.user_id == int(user_id))
        return db.session.scalars(stmt).all()

    def task_counts_by_category(self):
        # Uma query agregada no lugar de um COUNT por categoria (RP-07).
        rows = db.session.execute(
            db.select(Task.category_id, db.func.count(Task.id)).group_by(Task.category_id)
        ).all()
        return {category_id: count for category_id, count in rows}

    def add(self, task):
        db.session.add(task)

    def delete(self, task):
        db.session.delete(task)

    def commit(self):
        db.session.commit()
