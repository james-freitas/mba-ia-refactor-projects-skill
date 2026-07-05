from models.category import Category
from services.errors import ValidationError, NotFoundError
from utils.constants import DEFAULT_COLOR


class CategoryService:
    def __init__(self, category_repo, task_repo):
        self.categories = category_repo
        self.tasks = task_repo

    def list_categories(self):
        counts = self.tasks.task_counts_by_category()
        result = []
        for c in self.categories.list():
            data = c.to_dict()
            data['task_count'] = counts.get(c.id, 0)
            result.append(data)
        return result

    def create_category(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', DEFAULT_COLOR)

        self.categories.add(category)
        self.categories.commit()
        return category.to_dict()

    def update_category(self, category_id, data):
        category = self.categories.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')

        data = data or {}
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']

        self.categories.commit()
        return category.to_dict()

    def delete_category(self, category_id):
        category = self.categories.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        self.categories.delete(category)
        self.categories.commit()
