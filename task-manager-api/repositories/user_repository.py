from sqlalchemy.orm import selectinload
from database import db
from models.user import User


class UserRepository:
    def get(self, user_id):
        return db.session.get(User, user_id)

    def list(self):
        return db.session.scalars(db.select(User)).all()

    def list_with_tasks(self):
        # Carrega as tasks junto para o task_count sem N+1 (RP-07 corrige AP-06).
        stmt = db.select(User).options(selectinload(User.tasks))
        return db.session.scalars(stmt).all()

    def by_email(self, email):
        return db.session.scalars(db.select(User).filter_by(email=email)).first()

    def add(self, user):
        db.session.add(user)

    def delete(self, user):
        db.session.delete(user)

    def commit(self):
        db.session.commit()
