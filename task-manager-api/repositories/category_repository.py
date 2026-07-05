from database import db
from models.category import Category


class CategoryRepository:
    def get(self, category_id):
        return db.session.get(Category, category_id)

    def list(self):
        return db.session.scalars(db.select(Category)).all()

    def add(self, category):
        db.session.add(category)

    def delete(self, category):
        db.session.delete(category)

    def commit(self):
        db.session.commit()
