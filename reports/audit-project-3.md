# 🔍 Relatório de Auditoria Arquitetural

- **Projeto:** `task-manager-api`
- **Stack detectada:** Python 3 + Flask 3.0 · SQLite via SQLAlchemy ORM (`Flask-SQLAlchemy` 3.1) · deps via `pip` (`requirements.txt`)
- **Data:** 2026-07-04
- **Domínio:** Task Manager — `Task`, `User`, `Category`, com relatórios de produtividade e serviço de notificação
- **Arquitetura atual:** MVC **parcial** — há pastas `models/`, `routes/`, `services/`, `utils/`, mas as camadas de Service e Repository estão incompletas; regra de negócio e acesso a dados vivem nos blueprints
- **Arquitetura alvo:** MVC em camadas (Routes → Controllers → Services → Repositories → Models)

## 1. Sumário executivo

Projeto **parcialmente organizado**: a estrutura de pastas sugere camadas, mas
elas não seguram responsabilidade — os blueprints acumulam validação, regra de
negócio (cálculo de `overdue`, `completion_rate`, agregações de relatório) e
acesso direto ao ORM, enquanto `services/` cobre apenas notificação e boa parte
de `utils/helpers.py` é código morto. O risco dominante é **duplo**: segurança
(senha em **MD5 sem salt**, `SECRET_KEY` e senha de SMTP hardcoded, hash de senha
**devolvido** nas respostas) **e** dívida arquitetural (sem Repository, N+1 em
vários endpoints, APIs deprecated como `datetime.utcnow()` e `Query.get()`).
Esforço de remediação: **médio** — a base é razoável e o ORM já protege contra
SQL Injection (AP-01 ausente); o trabalho é completar as camadas e sanear
segurança sem alterar os contratos da API.

## 2. Contagem por severidade

| Severidade | Qtd |
|------------|-----|
| 🔴 CRITICAL | 3 |
| 🟠 HIGH     | 3 |
| 🟡 MEDIUM   | 4 |
| 🔵 LOW      | 4 |
| **Total**  | 14 |

> AP-01 (SQL Injection) foi verificado e **não** encontrou ocorrências: o acesso
> é via ORM e `.like(f'%{q}%')` é parametrizado pelo SQLAlchemy (o valor é bind,
> não concatenado no SQL).

## 3. Achados

| # | ID | Anti-pattern | Sev | Local (arquivo:linha) | Evidência | Correção (playbook) |
|---|----|--------------|-----|-----------------------|-----------|---------------------|
| 1 | AP-02 | `SECRET_KEY` hardcoded | 🔴 | `app.py:13` | `app.config['SECRET_KEY'] = 'super-secret-key-123'` | RP-02 Config via env |
| 2 | AP-02 | Senha de SMTP hardcoded | 🔴 | `services/notification_service.py:9-10` | `email_user`/`email_password = 'senha123'` fixos | RP-02 Config via env |
| 3 | AP-02 | Hash de senha exposto na resposta | 🔴 | `models/user.py:21`; `routes/user_routes.py:85-86,209` | `to_dict()` inclui `'password'`; `login`/`create_user` devolvem o hash | RP-11 Remover campo sensível do `to_dict` |
| 4 | AP-03 | Senha em MD5 sem salt | 🟠 | `models/user.py:29,32` | `hashlib.md5(pwd.encode()).hexdigest()` | RP-03 `bcrypt`/`werkzeug` com salt |
| 5 | AP-04 | Regra de negócio + acesso a dados na apresentação | 🟠 | `routes/report_routes.py:13-101,104-155`; `routes/task_routes.py:273-298` | cálculo de `overdue`/`completion_rate`/agregações e `Model.query` dentro dos handlers | RP-04 Repository; RP-05 Service; RP-06 controller magro |
| 6 | AP-05 | God Function (relatório) | 🟠 | `routes/report_routes.py:13-101` | `summary_report` com ~90 linhas: contagens, N+1, montagem de payload | RP-05 Extrair `ReportService` |
| 7 | AP-06 | Consultas N+1 | 🟡 | `routes/task_routes.py:41-57`; `routes/report_routes.py:55-68,157-165`; `routes/user_routes.py:22` | loop com `User.query.get`/`Category.query.get` por task; `Task.query...` por usuário/categoria; `len(u.tasks)` por usuário | RP-07 `JOIN`/`selectinload`/agregação |
| 8 | AP-07 | Camada de dados sem abstração (sem Repository) | 🟡 | `routes/*` (todos) | `Model.query` e `db.session` chamados direto nas rotas | RP-04 Extrair Repositories |
| 9 | AP-08 | APIs deprecated | 🟡 | `models/*`, `routes/*`, `seed.py`, `helpers.py` (`datetime.utcnow`); `*.query.get(id)` em todas as rotas | `datetime.utcnow()` (deprecated 3.12); `User.query.get(id)` (SQLAlchemy 2.0 legacy) | RP-10 `datetime.now(timezone.utc)`; `db.session.get(Model, id)` |
| 10 | AP-09 | Tratamento de erro amplo/silencioso | 🟡 | `routes/task_routes.py:62,137,204`; `routes/user_routes.py:130,149`; `routes/report_routes.py:186,207,221`; `utils/helpers.py:46-50` | `except:` nu engolindo tudo; `except Exception as e` só logando | RP-09 Captura específica + resposta genérica |
| 11 | AP-10 | Duplicação (DRY) | 🔵 | `models/task.py:50-60` + `task_routes.py:30-39,71-80`, `user_routes.py:171-180`, `report_routes.py:33-43` | lógica de `overdue` repetida 5×; listas de status/role repetidas; `task_data` montado à mão em vez de `to_dict()` | RP-12 Centralizar em Service/mapper e constantes |
| 12 | AP-11 | Logging via `print()` | 🔵 | `routes/task_routes.py:149,153,219,234`; `routes/user_routes.py:83,89,147`; `notification_service.py:21,24`; `helpers.py:39-41` | `print(f"Task criada: ...")` como observabilidade | RP-08 Logging estruturado |
| 13 | AP-12 | Código morto / imports não usados | 🔵 | `app.py:7`; `task_routes.py:7`; `user_routes.py:6`; `helpers.py:1-7,25-108`; `requirements.txt:4` | `import os, sys, json, time` não usados; `process_task_data`/`sanitize_string`/`generate_id` nunca chamados; `marshmallow` declarado e não usado | RP-12 Remover símbolos mortos |
| 14 | AP-13 | Magic strings/numbers | 🔵 | `routes/task_routes.py:110,113,177,182`; `report_routes.py:129`; `user_routes.py:210` | listas `['pending',...]` inline; `priority <= 2` = "alta"; `'fake-jwt-token-'` | RP-12 Constantes/enum |

## 4. Mapa da arquitetura atual

```
app.py                         -> bootstrap + SECRET_KEY hardcoded + create_all no import   (segredo no código)
database.py                    -> instância SQLAlchemy (ok)
models/{task,user,category}.py -> entidades ORM + helpers (is_overdue, validate_*)          (to_dict vaza password)
routes/task_routes.py          -> apresentação + validação + regra (overdue/stats) + ORM     (sem service/repo)
routes/user_routes.py          -> apresentação + auth/login + ORM                            (hash exposto)
routes/report_routes.py        -> apresentação + agregações pesadas + N+1                    (god function)
services/notification_service.py -> só notificação; senha SMTP hardcoded                     (cobertura parcial)
utils/helpers.py               -> maioria código morto (process_task_data nunca chamado)     (dead code)
```

Camadas **ausentes/incompletas:** Repository (inexistente); Service (só notificação — falta Task/User/Report/Category).
Camadas **com vazamento:** regra de negócio e acesso a dados dentro dos routes; segredo no entrypoint e no service.

## 5. Plano de remediação (proposto)

Ordem — segurança primeiro, depois estrutura, depois qualidade:

1. **Segurança (CRITICAL/HIGH):** RP-02 mover `SECRET_KEY` e credenciais de SMTP
   para env (`.env`/`.gitignore`/`.env.example`); RP-11 remover `password` do
   `to_dict()` e das respostas de `login`/`create_user`; RP-03 trocar MD5 por
   hash com salt (`werkzeug.security`/`bcrypt`).
2. **Separação de camadas (HIGH/MEDIUM):** RP-04 extrair Repositories
   (Task/User/Category) com as queries; RP-05 extrair Services (Task, User,
   Report) movendo `overdue`, `completion_rate` e agregações; RP-06 controllers
   magros; RP-08 logging estruturado.
3. **Qualidade (MEDIUM/LOW):** RP-07 corrigir N+1 (`selectinload`/`JOIN`/`GROUP BY`);
   RP-10 substituir `datetime.utcnow()` por `datetime.now(timezone.utc)` e
   `Query.get()` por `db.session.get()`; RP-09 tratamento de erro específico;
   RP-12 mappers/constantes e remoção de código morto (`helpers.py`, `marshmallow`).

Impacto esperado nos contratos da API: **nenhum** nos endpoints de negócio
(mesmas rotas e payloads). Mudança intencional de segurança: as respostas de
usuário deixam de incluir o campo `password`.

## 6. Confirmação necessária

> ⚠️ A próxima fase **modifica arquivos** para completar a estrutura em MVC.
> Escolha o escopo:
> - **Aplicar tudo** (todas as severidades)
> - **Somente CRITICAL/HIGH**
> - **Cancelar**
