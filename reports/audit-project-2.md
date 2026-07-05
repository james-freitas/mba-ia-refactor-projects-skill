# 🔍 Relatório de Auditoria Arquitetural

- **Projeto:** `ecommerce-api-legacy`
- **Stack detectada:** Node.js + Express 4.18 · SQLite in-memory (`:memory:`) via `sqlite3` 5.1 (SQL cru, callbacks; queries **parametrizadas**) · deps via `npm` (`package.json`)
- **Data:** 2026-07-04
- **Arquitetura atual:** procedural em 3 arquivos (`app.js` bootstrap, `AppManager.js` god class com DB + rotas + regra, `utils.js` config/helpers globais), sem camada de serviço nem de repositório
- **Arquitetura alvo:** MVC em camadas (Routes → Controllers → Services → Repositories → Models)

## 1. Sumário executivo

O risco dominante é **de segurança combinado com acoplamento total**: segredos de
produção hardcoded (`pk_live_...`, senha do banco, SMTP) e o **número do cartão +
chave do gateway impressos em log**, somados a um "hash" caseiro de base64 com
senha default `"123456"`. Diferente de projetos legados típicos, as queries **já
são parametrizadas** (AP-01 ausente). O defeito arquitetural é severo: a classe
`AppManager` concentra criação de schema, seed, conexão, rotas HTTP, regra de
pagamento e relatório financeiro num único arquivo, com _callback hell_ e um
relatório N+1. Esforço de remediação: **médio** — base pequena, mas exige
reestruturação completa em camadas além das correções de segurança.

## 2. Contagem por severidade

| Severidade | Qtd |
|------------|-----|
| 🔴 CRITICAL | 2 |
| 🟠 HIGH     | 3 |
| 🟡 MEDIUM   | 4 |
| 🔵 LOW      | 4 |
| **Total**  | 13 |

> AP-01 (SQL Injection) foi verificado e **não** encontrou ocorrências: todas as
> queries usam placeholders `?` com arrays de parâmetros.
> AP-08 (APIs deprecated) foi verificado e **encontrou** ocorrência (ver #8).

## 3. Achados

| # | ID | Anti-pattern | Sev | Local (arquivo:linha) | Evidência | Correção (playbook) |
|---|----|--------------|-----|-----------------------|-----------|---------------------|
| 1 | AP-02 | Segredos hardcoded | 🔴 | `utils.js:2-5` | `dbPass:"senha_super_secreta_prod_123"`, `paymentGatewayKey:"pk_live_1234567890abcdef"`, `smtpUser` fixos no código | RP-02 Config via env (`.env`+`.gitignore`) |
| 2 | AP-02 | Dado sensível vazado em log | 🔴 | `AppManager.js:45` | `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` — nº de cartão + chave do gateway | RP-11 Remover segredo/PAN de logs |
| 3 | AP-03 | Hash caseiro + senha default + seed em claro | 🟠 | `utils.js:17-23`; `AppManager.js:68,18` | `badCrypto` (loop de `base64`, trunca 10 chars); `badCrypto(p \|\| "123456")`; seed `pass='123'` | RP-03 `bcrypt` com salt; exigir senha |
| 4 | AP-04 | Regra de negócio + acesso a dados na apresentação | 🟠 | `AppManager.js:28-78,80-129,131-137` | handlers de rota contêm SQL, decisão de pagamento (`cc.startsWith("4")`), cálculo de receita | RP-04 Repository; RP-05 Service; RP-06 controller magro |
| 5 | AP-05 | God Class / callback hell | 🟠 | `AppManager.js:4,25,43-64` | `AppManager` faz DB+rotas+pagamento+relatório; checkout com ~5 níveis de callback aninhado | RP-05 Extrair Service; RP-04 Repository |
| 6 | AP-06 | Consultas N+1 | 🟡 | `AppManager.js:83-127` | `forEach(courses)` → query enrollments → `forEach(enr)` → query user + query payment; coordenação por contadores manuais | RP-07 `JOIN`/agregação |
| 7 | AP-07 | Acesso a dados sem abstração | 🟡 | `AppManager.js:7,10-23` | conexão criada no construtor; `CREATE TABLE`+seed dentro de `initDb`; sem Repository | RP-04 Repository; conexão dedicada |
| 8 | AP-08 | API deprecated / legada | 🟡 | `AppManager.js:1` | `require('sqlite3').verbose()` com API baseada em callbacks (sem migração para driver mantido/Promises) | RP-10 Substituir por driver mantido / API Promise |
| 9 | AP-09 | Erro silencioso / sempre sucesso | 🟡 | `AppManager.js:57,92,104,106,131-136` | callbacks ignoram `err`; `DELETE /users/:id` responde 200 mesmo em erro e deixa órfãos | RP-09 Tratar `err`; não responder sucesso em falha |
| 10 | AP-10 | Duplicação (DRY) | 🔵 | `AppManager.js:35,41,51,55,70`; `112-115` | `if (err) return res.status(500)...` repetido; montagem manual de DTO de student | RP-12 Extrair mapper; helper de erro |
| 11 | AP-11 | Logging via `console.log` | 🔵 | `utils.js:13`; `AppManager.js:45`; `app.js:13` | `console.log("[LOG] Salvando no cache...")` como observabilidade | RP-08 Logging estruturado (pino/winston) |
| 12 | AP-12 | Código morto / imports não usados | 🔵 | `utils.js:10,25`; `AppManager.js:2` | `totalRevenue` e `globalCache` exportados; `AppManager` importa `totalRevenue`/`badCrypto`… `totalRevenue` nunca usado | RP-12 Remover símbolos mortos |
| 13 | AP-13 | Magic strings / nomes crípticos | 🔵 | `AppManager.js:29-33,47` | vars `u`,`e`,`p`,`cid`,`cc`; status `"PAID"`/`"DENIED"` inline; `cc.startsWith("4")` | RP-12 Constantes/enum; nomes descritivos |

## 4. Mapa da arquitetura atual

```
app.js         -> bootstrap: cria app, instancia AppManager, sobe servidor            (aceitável)
AppManager.js  -> conexão + schema + seed + TODAS as rotas + regra de pagamento
                  + relatório financeiro N+1                                            (god class; DB+regra na apresentação)
utils.js       -> config com segredos + cache global + "hash" caseiro                  (segredos hardcoded; estado global)
```

Camadas **ausentes:** Service, Repository, Model.
Camadas **com vazamento:** acesso a dados e regra de negócio dentro dos handlers de rota (`AppManager.js`); configuração sensível e estado global em `utils.js`.

## 5. Plano de remediação (proposto)

Ordem — segurança primeiro, depois estrutura, depois qualidade:

1. **Segurança (CRITICAL/HIGH):** RP-02 mover `dbPass`/`paymentGatewayKey`/`smtpUser`
   para env (`.env` + `.gitignore` + `.env.example`); RP-11 remover nº de cartão e
   chave do gateway dos logs; RP-03 substituir `badCrypto` por `bcrypt` com salt e
   exigir senha (sem default `"123456"`); seed sem senha em claro.
2. **Separação de camadas (HIGH/MEDIUM):** RP-04 extrair Repositories (users,
   courses, enrollments, payments, audit); RP-05 extrair Services (checkout,
   relatório financeiro); RP-06 controllers magros (request → service → HTTP);
   RP-08 logging estruturado.
3. **Qualidade (MEDIUM/LOW):** RP-07 corrigir N+1 do relatório com `JOIN`/agregação;
   RP-09 tratar `err` em todos os callbacks e corrigir `DELETE` que sempre retorna
   sucesso; RP-10 substituir `sqlite3.verbose()`/callbacks pela API Promise;
   RP-12 mappers, constantes de status e remoção de código morto (`totalRevenue`).

Impacto esperado nos contratos da API: **nenhum** nos endpoints de negócio
(mesmas rotas `POST /api/checkout`, `GET /api/admin/financial-report`,
`DELETE /api/users/:id` e mesmos payloads). Mudanças intencionais de segurança: o
log deixa de expor nº de cartão/chave; senhas passam a ser hasheadas com bcrypt.

## 6. Confirmação necessária

> ⚠️ A próxima fase **modifica arquivos** para reestruturar o projeto em MVC.
> Escolha o escopo:
> - **Aplicar tudo** (todas as severidades)
> - **Somente CRITICAL/HIGH**
> - **Cancelar**
