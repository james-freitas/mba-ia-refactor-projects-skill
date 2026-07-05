from services.errors import DomainError, NotFoundError

CATEGORIAS_VALIDAS = [
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
]


class ProdutoService:
    """Regras de negócio de produtos. Não conhece HTTP nem SQL."""

    def __init__(self, repo):
        self.repo = repo

    def listar(self):
        return [p.to_dict() for p in self.repo.list()]

    def buscar(self, produto_id):
        produto = self.repo.get_by_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado")
        return produto.to_dict()

    def _validar(self, nome, preco, estoque, categoria):
        if preco < 0:
            raise DomainError("Preço não pode ser negativo")
        if estoque < 0:
            raise DomainError("Estoque não pode ser negativo")
        if len(nome) < 2:
            raise DomainError("Nome muito curto")
        if len(nome) > 200:
            raise DomainError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise DomainError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    def criar(self, nome, descricao, preco, estoque, categoria):
        self._validar(nome, preco, estoque, categoria)
        return self.repo.create(nome, descricao, preco, estoque, categoria)

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        if not self.repo.get_by_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        if preco < 0:
            raise DomainError("Preço não pode ser negativo")
        if estoque < 0:
            raise DomainError("Estoque não pode ser negativo")
        self.repo.update(produto_id, nome, descricao, preco, estoque, categoria)

    def deletar(self, produto_id):
        if not self.repo.get_by_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        self.repo.delete(produto_id)

    def buscar_produtos(self, termo, categoria, preco_min, preco_max):
        produtos = self.repo.search(termo, categoria, preco_min, preco_max)
        return [p.to_dict() for p in produtos]
