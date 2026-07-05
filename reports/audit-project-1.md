# 🔍 Relatório de Auditoria Arquitetural

- **Projeto:** `code-smells-project`
- **Stack detectada:** Python 3.12 + Flask 3.1 · SQLite via `sqlite3` (SQL cru, queries por concatenação) · deps via `pip` (`requirements.txt`)
- **Data:** 2026-07-04
- **Arquitetura atual:** procedural em 4 arquivos flat (`app.py`, `controllers.py`, `models.py`, `database.py`), sem camada de serviço nem de repositório
- **Arquitetura alvo:** MVC em camadas (Routes → Controllers → Services → Repositories → Models)

## 1. Sumário executivo

O risco dominante é **de segurança**: SQL Injection em 100% das queries, um
endpoint de execução de SQL arbitrário e segredos hardcoded expostos publicamente
(inclusive a `SECRET_KEY` no `/health` e senhas em texto puro). Em paralelo, há
um **defeito arquitetural**: o "model" acumula acesso a dados **e** regra de
negócio, e o controller dispara efeitos colaterais (e-mail/SMS/push via `print`).
Esforço de remediação: **médio** — a base é pequena, mas exige reestruturação
completa em camadas além das correções de segurança.

## 2. Contagem por severidade

| Severidade | Qtd |
|------------|-----|
| 🔴 CRITICAL | 2 |
| 🟠 HIGH     | 2 |
| 🟡 MEDIUM   | 3 |
| 🔵 LOW      | 3 |
| **Total**  | 10 |

> AP-08 (APIs deprecated) foi verificado e **não** encontrou ocorrências neste projeto.

## 3. Achados

| # | ID | Anti-pattern | Sev | Local (arquivo:linha) | Evidência | Correção (playbook) |
|---|----|--------------|-----|-----------------------|-----------|---------------------|
| 1 | AP-01 | SQL Injection (concatenação) | 🔴 | `models.py:28,48-50,110,140,291`; `app.py:59-78` | `"... WHERE email = '" + email + "'..."`; `/admin/query` executa SQL do corpo | RP-01 Parametrizar queries; remover `/admin/query` |
| 2 | AP-02 | Segredo hardcoded e exposto | 🔴 | `app.py:7-8`; `controllers.py:285-289` | `SECRET_KEY="minha-chave-super-secreta-123"`; `/health` devolve `secret_key`/`debug` | RP-02 Config via env; RP-11 remover de respostas |
| 3 | AP-03 | Senha em texto puro | 🟠 | `models.py:110,127-128`; `database.py:76-78` | senha gravada/comparada sem hash; seed com senha em claro | RP-03 Hash com salt (werkzeug/bcrypt) |
| 4 | AP-04 | Regra de negócio + I/O na apresentação/model | 🟠 | `models.py:133-169` (`criar_pedido`), `235-273` (`relatorio_vendas`); `controllers.py:208-210,248-250` | cálculo de total/desconto no model; e-mail/SMS/push via `print` no controller | RP-04 Repository; RP-05 Service; RP-06 controller magro |
| 5 | AP-06 | Consultas N+1 | 🟡 | `models.py:171-201`, `203-233` | loop de pedidos → query por item → query por produto | RP-07 `JOIN`/agregação |
| 6 | AP-07 | Acesso a dados sem abstração | 🟡 | `database.py:4-10` | conexão global mutável + `check_same_thread=False`; schema/seed no getter | RP-04 Repository; conexão por request |
| 7 | AP-09 | Tratamento de erro genérico/vazamento | 🟡 | `controllers.py:10-12,21-22,60-62,...` | `except Exception as e: return jsonify({"erro": str(e)})` | RP-09 Exceções específicas + resposta genérica |
| 8 | AP-10 | Duplicação (DRY) | 🔵 | `models.py:12-21,31-40,304-313`; `171-233` | mesmo dict de produto montado 3×; `get_pedidos_usuario`≈`get_todos_pedidos` | RP-12 Extrair mapper; unificar funções |
| 9 | AP-11 | Logging via `print()` | 🔵 | `controllers.py:8,57,161,179,208-210`; `app.py:56,83-85` | `print("Login bem-sucedido: " + email)` | RP-08 Logging estruturado |
| 10 | AP-13 | Magic strings inline | 🔵 | `controllers.py:52,242`; `models.py:289-297` | listas de categorias/status repetidas como literais | RP-12 Constantes/enum |

## 4. Mapa da arquitetura atual

```
app.py          -> bootstrap + rotas admin (reset-db / SQL arbitrário) + seed no boot   (DB no entrypoint)
controllers.py  -> apresentação + validação de regra + efeitos (print email/sms) + logs (regra no controller)
models.py       -> acesso a dados (SQL cru) + regra de negócio (pedido, relatório)      (sem repo, sem service)
database.py     -> conexão global singleton + schema + seed                             (estado global, thread-unsafe)
```

Camadas **ausentes:** Service, Repository.
Camadas **com vazamento:** acesso a dados no `app.py` (admin) e regra de negócio no `models.py`/`controllers.py`.

## 5. Plano de remediação (proposto)

Ordem — segurança primeiro, depois estrutura, depois qualidade:

1. **Segurança (CRITICAL/HIGH):** RP-01 parametrizar todo o SQL e remover
   `/admin/query`; RP-02 mover `SECRET_KEY`/config para env; RP-11 remover
   `secret_key` do `/health` e `senha` das respostas de usuário; RP-03 hashing
   com salt.
2. **Separação de camadas (HIGH/MEDIUM):** RP-04 extrair Repositories (SQL
   parametrizado, conexão por request); RP-05 extrair Services (pedido,
   relatório, notificação); RP-06 controllers magros; RP-08 logging.
3. **Qualidade (MEDIUM/LOW):** RP-07 corrigir N+1 com `JOIN`; RP-09 tratamento
   de erro específico; RP-12 mappers/constantes eliminando duplicação.

Impacto esperado nos contratos da API: **nenhum** nos endpoints de negócio
(mesmas rotas e payloads). Mudanças intencionais de segurança: `/health` deixa
de expor `secret_key`; respostas de usuário deixam de incluir `senha`; o endpoint
`/admin/query` (SQL arbitrário) é **removido**.

## 6. Confirmação necessária

> ⚠️ A próxima fase **modifica arquivos** para reestruturar o projeto em MVC.
> Escopo escolhido: **Aplicar tudo** (todas as severidades), conforme
> solicitado na execução da skill.
