"""Composição de dependências (wiring).

Constrói services já ligados aos seus repositories, usando a conexão por
request. Mantém os controllers livres de detalhes de instanciação.
"""

from infra.db import get_db
from repositories.pedido_repository import PedidoRepository
from repositories.produto_repository import ProdutoRepository
from repositories.usuario_repository import UsuarioRepository
from services.notification_service import NotificationService
from services.pedido_service import PedidoService
from services.produto_service import ProdutoService
from services.relatorio_service import RelatorioService
from services.usuario_service import UsuarioService

_notifier = NotificationService()


def produto_service():
    return ProdutoService(ProdutoRepository(get_db()))


def usuario_service():
    return UsuarioService(UsuarioRepository(get_db()))


def pedido_service():
    db = get_db()
    return PedidoService(PedidoRepository(db), ProdutoRepository(db), _notifier)


def relatorio_service():
    return RelatorioService(PedidoRepository(get_db()))
