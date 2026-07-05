# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

### Setup (uma vez)

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

### Rodar

```bash
./.venv/bin/python app.py
```

A aplicação sobe em `http://localhost:5000`. No primeiro boot, o banco SQLite
(`loja.db`) é criado automaticamente e populado com produtos e usuários de
exemplo — as senhas dos usuários são gravadas com **hash + salt** (via
`werkzeug.security`).

> Se o Flask já estiver instalado no ambiente global, `python app.py` direto
> também funciona. O venv é usado aqui porque o `pip` do sistema pode ser
> *externally-managed*.

Como alternativa, você pode **ativar** o venv e usar `python` direto:

```bash
source .venv/bin/activate
python app.py
```

Nesse caso, para **sair do venv** depois de parar a aplicação (`Ctrl+C`), rode:

```bash
deactivate
```

> Isso só é necessário quando você ativa com `source`. Se usar
> `./.venv/bin/python app.py`, o venv nunca é ativado no shell e não há nada
> para desativar.

### Configuração por variáveis de ambiente

A app lê a configuração de `config.py`, que usa variáveis de ambiente (com
defaults de desenvolvimento). Nenhum segredo é hardcoded.

| Variável | Default | Descrição |
|----------|---------|-----------|
| `SECRET_KEY` | `dev-only-change-me` | Chave da aplicação (defina em produção) |
| `DB_PATH` | `loja.db` | Caminho do arquivo SQLite |
| `DEBUG` | `false` | Liga o modo debug/reloader do Flask |

Exemplo:

```bash
SECRET_KEY="troque-isto" DEBUG=true ./.venv/bin/python app.py
```

### Resetar o banco

Os endpoints administrativos (`/admin/*`) foram removidos na refatoração. Para
recriar o banco do zero, basta apagar o arquivo — ele é regenerado no próximo
boot:

```bash
rm -f loja.db
```

### Teste rápido (com a app no ar)

```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@loja.com","senha":"admin123"}'
```

### Arquitetura

O projeto foi reestruturado em camadas MVC (ver `reports/audit-project-1.md`):

```
app.py                 # application factory (wiring)
config.py              # configuração via env
infra/                 # conexão por request (db), schema/seed, wiring (container)
models/                # entidades (Produto, Usuario, Pedido)
repositories/          # acesso a dados — queries parametrizadas
services/              # regra de negócio + notificações
controllers/           # HTTP ↔ service
routes/                # blueprints: URL → controller
```

## Análise Manual

## Análise Manual

Achados priorizados por impacto arquitetural e de segurança. Referências no formato `arquivo:linha`.

### 🔴 CRITICAL — SQL Injection generalizado e endpoint de query arbitrária

- **Onde:** `models.py` (praticamente todas as funções — ex.: `models.py:28`, `models.py:48-50`, `models.py:110`, `models.py:291`) e `app.py:59-78`.
- **Problema:** todas as queries são montadas por **concatenação de strings** com input do usuário, sem parâmetros/bind. Ex.: `login_usuario` monta `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`, permitindo bypass de autenticação (`' OR '1'='1`) e injeção em qualquer rota de busca/CRUD. Pior ainda, `POST /admin/query` executa **SQL arbitrário** enviado no corpo, sem autenticação, e `POST /admin/reset-db` apaga o banco inteiro sem nenhuma proteção.
- **Impacto:** comprometimento total do banco (leitura, alteração e destruição de dados). É a falha de maior severidade do projeto.
- **Correção:** usar queries parametrizadas (`cursor.execute(sql, (params,))`) em 100% dos acessos; remover `/admin/query`; proteger rotas administrativas com autenticação/autorização.

### 🟠 HIGH — Segredos hardcoded e senhas em texto puro

- **Onde:** `app.py:7-8`, `controllers.py:285-289` (health check devolve `secret_key`, `debug` e `db_path`), `models.py:127-128` e `models.py:110` (senha gravada/comparada em claro), `models.py:83`/`99` (senha retornada nas respostas de usuário), `database.py:76-78` (usuários semente com senha em claro).
- **Problema:** `SECRET_KEY` fixa no código e **vazada em um endpoint público** (`/health`); senhas armazenadas e comparadas sem hash; o hash/senha é serializado para o cliente.
- **Impacto:** vazamento de credenciais e da chave de assinatura da aplicação; qualquer dump do banco expõe todas as senhas.
- **Correção:** mover segredos para variáveis de ambiente; aplicar hash com salt (bcrypt/argon2); nunca retornar `senha` nas serializações; remover dados sensíveis do `/health`.

### 🟡 MEDIUM — Ausência de camadas e regra de negócio no acesso a dados

- **Onde:** `models.py:133-169` (`criar_pedido`), `models.py:235-273` (`relatorio_vendas`), `controllers.py:208-210`/`248-250`.
- **Problema:** o "model" mistura **acesso a dados + regra de negócio** (cálculo de total, validação de estoque, faixas de desconto, ticket médio), enquanto notificações (e-mail/SMS/push) são simuladas com `print()` dentro do **controller**. Não existe camada de serviço nem de repositório — viola SRP e o princípio de separação de camadas.
- **Impacto:** lógica não testável isoladamente, difícil de evoluir e duplicada entre camadas.
- **Correção:** introduzir camada de repositório (acesso a dados), camada de serviço (regras de pedido/relatório) e um serviço de notificação real; controllers apenas orquestram.

### 🟡 MEDIUM — Problema N+1 na listagem de pedidos

- **Onde:** `models.py:171-201` (`get_pedidos_usuario`) e `models.py:203-233` (`get_todos_pedidos`).
- **Problema:** para cada pedido abre-se um cursor para buscar itens e, **para cada item**, mais um cursor para buscar o nome do produto. Em N pedidos com M itens são feitas ~1 + N + N·M queries.
- **Impacto:** degradação de performance e uso de conexão que cresce linearmente com o volume de dados.
- **Correção:** resolver com `JOIN` único (pedidos ⋈ itens ⋈ produtos) ou pré-carregar produtos em um `IN (...)`.

### 🔵 LOW — Duplicação de código de serialização e funções quase idênticas

- **Onde:** o dicionário de produto é remontado à mão em `models.py:12-21`, `31-40`, `304-313`; `get_pedidos_usuario` e `get_todos_pedidos` (`models.py:171-233`) são praticamente idênticas.
- **Problema:** o mesmo mapeamento row→dict aparece várias vezes (DRY violado), e duas funções diferem apenas por um `WHERE`.
- **Impacto:** manutenção propensa a erro (uma mudança de schema exige editar vários pontos).
- **Correção:** extrair funções de mapeamento (`row_to_produto`, `row_to_pedido`) e unificar as duas listagens com parâmetro opcional de filtro.

### 🔵 LOW — Logging via `print()` e vazamento de exceções ao cliente

- **Onde:** `print(...)` em `controllers.py:8,11,57,161,179,208-210,219` etc.; `except Exception as e: return jsonify({"erro": str(e)})` repetido em quase todos os controllers.
- **Problema:** uso de `print` em vez do módulo `logging` (sem níveis, sem formatação/rotação) e retorno de `str(e)` cru na resposta HTTP, expondo detalhes internos.
- **Impacto:** observabilidade fraca e possível vazamento de detalhes de implementação/stacktrace.
- **Correção:** adotar `logging` com níveis; retornar mensagens de erro genéricas ao cliente e registrar o detalhe internamente.
