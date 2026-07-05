# 01 — Análise de Projeto (Fase 1)

Heurísticas para detectar **linguagem, framework, banco de dados** e para
**mapear a arquitetura atual**. O objetivo é ser agnóstico: nunca assuma a
stack — derive-a das evidências abaixo.

## 1. Detecção de linguagem

Combine dois sinais: **arquivo de manifesto** (mais confiável) e **extensões
predominantes**.

| Linguagem | Manifesto | Extensões |
|-----------|-----------|-----------|
| Python | `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | `.py` |
| JavaScript / TypeScript | `package.json` (`tsconfig.json` → TS) | `.js`, `.mjs`, `.ts` |
| Java | `pom.xml`, `build.gradle` | `.java` |
| C# | `*.csproj`, `*.sln` | `.cs` |
| Go | `go.mod` | `.go` |
| Ruby | `Gemfile` | `.rb` |
| PHP | `composer.json` | `.php` |

Comando útil: contar extensões — `find . -type f -not -path '*/node_modules/*'
-not -path '*/.git/*' | sed 's/.*\.//' | sort | uniq -c | sort -rn`.

## 2. Detecção de framework

Procure os imports/dependências no manifesto **e** no código-fonte.

| Framework | Sinal no código | Sinal no manifesto |
|-----------|-----------------|--------------------|
| Flask (Py) | `from flask import`, `Flask(__name__)` | `flask` |
| FastAPI (Py) | `from fastapi import`, `APIRouter` | `fastapi`, `uvicorn` |
| Django (Py) | `django`, `urls.py`, `settings.py`, `manage.py` | `django` |
| Express (Node) | `require('express')`, `express()` | `express` |
| NestJS (Node) | `@Controller`, `@Module` | `@nestjs/core` |
| Spring (Java) | `@RestController`, `@SpringBootApplication` | `spring-boot-starter-web` |
| Rails (Ruby) | `ActionController`, `config/routes.rb` | `rails` |

Se nenhum framework web for encontrado mas houver rotas HTTP manuais, trate como
"framework: nenhum / servidor HTTP nativo".

## 3. Detecção de banco de dados / ORM

| Banco / camada | Sinais |
|----------------|--------|
| SQLite | `sqlite3`, `:memory:`, `*.db`, `sqlite:///` |
| PostgreSQL | `psycopg2`, `pg`, `postgres://`, `postgresql://` |
| MySQL | `mysql`, `mysql2`, `pymysql`, `mysql://` |
| MongoDB | `mongoose`, `pymongo`, `mongodb://` |
| ORM SQLAlchemy (Py) | `db.Model`, `SQLAlchemy(`, `.query.` | 
| ORM Sequelize (Node) | `sequelize.define`, `DataTypes` |
| ORM Prisma (Node) | `@prisma/client`, `schema.prisma` |
| **Sem ORM (SQL cru)** | `cursor.execute(`, `db.run(`, `db.get(`, `.query(` com strings SQL |

Registre também **como as queries são escritas** — parametrizadas (`?`, `%s`,
`:param`) ou por **concatenação de string** (sinal forte de SQL Injection, ver
catálogo AP-01).

## 4. Mapeamento da arquitetura atual

Classifique cada arquivo pela responsabilidade que ele **de fato** exerce — o
nome da pasta pode mentir (um `models.py` pode conter regra de negócio; um
`routes/` pode acessar o banco direto).

Responsabilidades a rastrear:

- **Entrypoint / bootstrap** — cria o app, registra rotas, sobe o servidor
  (`app.py`, `main.py`, `index.js`, `app.js`, `Application.java`).
- **Apresentação (Controllers/Routes/Views)** — recebe request, valida entrada,
  devolve response. Sinais: handlers de rota, `request`/`response`, `jsonify`,
  `res.send`.
- **Negócio (Services)** — orquestra regras. Muitas vezes **ausente** em código
  legado (a regra fica no controller ou no model).
- **Dados (Repositories/DAO)** — encapsula acesso ao banco. Sinais: `execute`,
  `commit`, `session`, queries. Se isso aparece dentro de controllers/models, é
  vazamento de camada.
- **Modelo (Entities)** — representação dos dados. Deve ser "burro"; se tem
  cálculo de relatório/orquestração, está inchado.
- **Configuração** — credenciais, portas, chaves. Devem vir de env/arquivo, não
  hardcoded.

### Saída do mapa

Monte uma tabela mental/textual assim:

```
arquivo            | papel nominal | responsabilidades reais            | vazamentos
-------------------|---------------|------------------------------------|------------------
app.py             | bootstrap     | bootstrap + rotas admin + SQL cru  | DB no entrypoint
controllers.py     | apresentação  | validação + regra + logs           | regra no controller
models.py          | dados/modelo  | acesso a dados + regra de negócio  | sem repo, sem service
database.py        | dados         | conexão + schema + seed            | singleton global
```

A partir do mapa, responda: **quais camadas existem, quais estão ausentes e
onde há vazamento**. Isso alimenta diretamente a auditoria da Fase 2.

## 5. Checklist de saída da Fase 1

- [ ] Linguagem e versão (se detectável) identificadas
- [ ] Framework web identificado (ou "nenhum")
- [ ] Banco + driver/ORM identificados, e estilo de query (parametrizada vs concatenada)
- [ ] Entrypoint localizado
- [ ] Cada arquivo classificado por responsabilidade real
- [ ] Camadas ausentes e vazamentos anotados
- [ ] Resumo impresso no formato definido no `SKILL.md`
