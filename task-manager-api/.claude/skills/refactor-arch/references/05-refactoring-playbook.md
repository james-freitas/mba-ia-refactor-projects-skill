# 05 — Playbook de Refatoração (Fase 3)

Padrões de transformação concretos, cada um mapeado a um anti-pattern do
catálogo. Aplique na ordem: **segurança → separação de camadas → qualidade**.
Cada padrão tem **antes/depois**. Exemplos em Python/Flask e/ou Node/Express — a
ideia é agnóstica; traduza para a stack detectada.

Índice: RP-01 SQL parametrizado · RP-02 Config via env · RP-03 Hash seguro ·
RP-04 Extrair Repository · RP-05 Extrair Service · RP-06 Controller magro ·
RP-07 Corrigir N+1 · RP-08 Logging · RP-09 Tratamento de erro · RP-10 Substituir
API deprecated · RP-11 Remover segredo de resposta · RP-12 Extrair mapper (DRY).

---

## RP-01 — Parametrizar queries (corrige AP-01) 🔴

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```
Node:
```js
// antes: db.get(`SELECT * FROM users WHERE email = '${email}'`)
db.get("SELECT * FROM users WHERE email = ?", [email], cb);
```
Regra: **todo** valor dinâmico vira placeholder (`?`, `%s`, `:param`). Remova
endpoints que executam SQL arbitrário do corpo da requisição.

---

## RP-02 — Extrair configuração para variáveis de ambiente (corrige AP-02) 🔴

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
DB_PATH = "loja.db"
```
**Depois** (`config.py`)
```python
import os
class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]           # obrigatório, sem default inseguro
    DB_PATH    = os.environ.get("DB_PATH", "loja.db")
    DEBUG      = os.environ.get("DEBUG", "false").lower() == "true"
```
```python
app.config.from_object(Config)
```
Node:
```js
// config/index.js
module.exports = {
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
  port: Number(process.env.PORT || 3000),
};
```
Acrescente `.env` ao `.gitignore` e um `.env.example` sem valores reais.

---

## RP-03 — Hashing de senha seguro (corrige AP-03) 🟠

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()          # inseguro
```
```js
let hash = badCrypto(p || "123456");                            // caseiro + default
```
**Depois**
```python
import bcrypt
def set_password(self, pwd):
    self.password = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
def check_password(self, pwd):
    return bcrypt.checkpw(pwd.encode(), self.password.encode())
```
```js
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);   // exija senha; sem default "123456"
```

---

## RP-04 — Extrair Repository (corrige AP-04/AP-07) 🟠

Mover **todo** acesso a dados para uma classe de repositório com queries
parametrizadas.

**Antes** (dentro do controller/model, SQL cru + mapeamento repetido)
```python
def get_produto_por_id(id):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM produtos WHERE id = " + str(id))
    row = cur.fetchone()
    return {"id": row["id"], "nome": row["nome"], ...}   # mapeamento inline
```
**Depois** (`repositories/produto_repository.py`)
```python
class ProdutoRepository:
    def __init__(self, db):
        self.db = db
    def get_by_id(self, produto_id):
        row = self.db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return _row_to_produto(row) if row else None
    def list(self):
        rows = self.db.execute("SELECT * FROM produtos").fetchall()
        return [_row_to_produto(r) for r in rows]
```
O controller passa a chamar `repo.get_by_id(id)` — sem SQL.

---

## RP-05 — Extrair Service (corrige AP-04/AP-05) 🟠

Mover regra de negócio (cálculos, orquestração, efeitos) do controller/model
para um service.

**Antes** (regra + acesso a dados no "model")
```python
def criar_pedido(usuario_id, itens):
    # valida estoque, calcula total, insere pedido/itens, baixa estoque...
```
**Depois** (`services/pedido_service.py`)
```python
class PedidoService:
    def __init__(self, produto_repo, pedido_repo, notifier):
        self.produtos = produto_repo
        self.pedidos = pedido_repo
        self.notifier = notifier

    def criar(self, usuario_id, itens):
        total = 0
        for item in itens:
            produto = self.produtos.get_by_id(item["produto_id"])
            if not produto:
                raise DomainError(f"Produto {item['produto_id']} não encontrado")
            if produto.estoque < item["quantidade"]:
                raise DomainError(f"Estoque insuficiente para {produto.nome}")
            total += produto.preco * item["quantidade"]
        pedido_id = self.pedidos.create(usuario_id, itens, total)   # transação no repo
        self.notifier.pedido_criado(usuario_id, pedido_id)          # efeito injetado
        return {"pedido_id": pedido_id, "total": total}
```
O service não conhece HTTP; erros de domínio viram exceções tratadas no
controller.

---

## RP-06 — Controller magro (corrige AP-04) 🟠

**Antes**
```python
def criar_pedido():
    dados = request.get_json()
    # ...validação + regra + SQL + print de email/sms/push tudo aqui...
```
**Depois**
```python
def criar_pedido():
    dados = request.get_json() or {}
    if not dados.get("usuario_id") or not dados.get("itens"):
        return jsonify({"erro": "usuario_id e itens são obrigatórios"}), 400
    try:
        resultado = pedido_service.criar(dados["usuario_id"], dados["itens"])
        return jsonify({"dados": resultado, "sucesso": True}), 201
    except DomainError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 400
```
Controller só faz: ler request → chamar service → mapear para HTTP.

---

## RP-07 — Corrigir N+1 (corrige AP-06) 🟡

**Antes**
```python
for row in pedidos:
    itens = cur.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],)).fetchall()
    for item in itens:
        prod = cur.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()
```
**Depois** (um JOIN só)
```python
rows = self.db.execute("""
    SELECT p.id AS pedido_id, i.produto_id, pr.nome AS produto_nome,
           i.quantidade, i.preco_unitario
    FROM pedidos p
    JOIN itens_pedido i ON i.pedido_id = p.id
    JOIN produtos pr    ON pr.id = i.produto_id
""").fetchall()
```
ORM (SQLAlchemy): `Task.query.options(selectinload(Task.user), selectinload(Task.category))`.
Estatísticas: use `func.count`/`GROUP BY` em vez de contar em loop no Python.

---

## RP-08 — Logging estruturado (corrige AP-11) 🔵

**Antes**
```python
print("Login bem-sucedido: " + email)
```
**Depois**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("login_ok", extra={"email": email})   # nunca logar senha/segredo
```
Node: substituir `console.log` por um logger (ex.: `pino`/`winston`).

---

## RP-09 — Tratamento de erro específico (corrige AP-09) 🟡

**Antes**
```python
try:
    tasks = Task.query.all()
    ...
except:
    return jsonify({'error': 'Erro interno'}), 500     # engole tudo
```
**Depois**
```python
from sqlalchemy.exc import SQLAlchemyError
try:
    tasks = repo.list()
except SQLAlchemyError:
    logger.exception("falha ao listar tasks")
    return jsonify({"error": "Erro ao acessar dados"}), 500
```
Node: sempre tratar `err` no callback e não responder sucesso quando houve erro.
Nunca devolver `str(e)`/stacktrace ao cliente.

---

## RP-10 — Substituir APIs deprecated (corrige AP-08) 🟡

**Antes → Depois**
```python
datetime.utcnow()              →  datetime.now(timezone.utc)
User.query.get(user_id)        →  db.session.get(User, user_id)
@app.before_first_request      →  inicialização no factory create_app()
```
```js
new Buffer(data)               →  Buffer.from(data)
crypto.createCipher(...)       →  crypto.createCipheriv(...)
url.parse(str)                 →  new URL(str)
```
Rode a app/testes e confirme que os `DeprecationWarning` sumiram.

---

## RP-11 — Remover dados sensíveis das respostas (corrige AP-02) 🔴/🟠

**Antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, ...}
```
**Depois**
```python
def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email,
            "role": self.role, "active": self.active}   # sem password/hash
```
Também: remover `secret_key`/`debug`/segredos de endpoints como `/health`; não
logar nº de cartão nem chaves.

---

## RP-12 — Extrair mapper / eliminar duplicação (corrige AP-10/AP-13) 🔵

**Antes** (mesmo dict montado em 3 funções; funções quase idênticas)
```python
result.append({"id": row["id"], "nome": row["nome"], "preco": row["preco"], ...})
```
**Depois**
```python
def _row_to_produto(row):
    return {"id": row["id"], "nome": row["nome"], "descricao": row["descricao"],
            "preco": row["preco"], "estoque": row["estoque"],
            "categoria": row["categoria"], "ativo": row["ativo"],
            "criado_em": row["criado_em"]}
```
Centralize também "magic strings" (status, categorias) em constantes/enums e
unifique funções que só diferem por um filtro em uma única função parametrizada.

---

## Roteiro de aplicação e validação

1. Aplique RP-01→RP-03 e RP-11 (**segurança**) primeiro.
2. Depois RP-04→RP-06 (**camadas**), migrando comportamento existente sem
   reescrever contratos.
3. Por fim RP-07→RP-10 e RP-12 (**qualidade**).
4. **Valide** (obrigatório): suba a app e exercite `/health`, uma listagem, uma
   criação e o fluxo crítico (login/checkout/pedido). Compare status e payloads
   com o comportamento original. Se regredir, reverta a transformação
   responsável antes de seguir.
