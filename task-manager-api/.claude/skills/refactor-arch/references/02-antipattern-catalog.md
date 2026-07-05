# 02 — Catálogo de Anti-Patterns (Fase 2)

Catálogo agnóstico de stack. Cada anti-pattern tem **id**, **severidade**,
**descrição**, **sinais de detecção** (com padrões de busca por linguagem) e
**por que importa**. Na Fase 2, percorra **todos** e registre as ocorrências.

## Escala de severidade

| Nível | Critério | Ação |
|-------|----------|------|
| 🔴 CRITICAL | Exploração remota, perda/vazamento de dados, comprometimento total | Corrigir sempre, primeiro |
| 🟠 HIGH | Falha de segurança séria ou defeito arquitetural que trava evolução | Corrigir |
| 🟡 MEDIUM | Impacto de performance/manutenção relevante | Corrigir na refatoração |
| 🔵 LOW | Qualidade/legibilidade; risco baixo | Corrigir se barato |

Distribuição do catálogo: **AP-01, AP-02 → CRITICAL**; **AP-03, AP-04, AP-05 →
HIGH**; **AP-06, AP-07, AP-08, AP-09 → MEDIUM**; **AP-10, AP-11, AP-12, AP-13 →
LOW**.

---

## AP-01 — SQL Injection (query por concatenação) — 🔴 CRITICAL

**Descrição:** queries SQL montadas concatenando input do usuário, sem
parâmetros/bind.

**Sinais de detecção:**
- Python: `execute("... " + var)`, f-strings/`%`/`.format` dentro de `execute(`,
  `"WHERE id = " + str(id)`.
- Node: `db.run("... " + var)`, template strings com `${}` dentro de SQL.
- Genérico: `grep -nE "execute\(|query\(|\.run\(|\.get\(" | grep -E "\+|\$\{|%s?['\"]|f['\"]"`.
- Endpoint que executa SQL arbitrário vindo do corpo (`sql`, `query` no body).

**Por que importa:** bypass de auth, leitura/alteração/destruição do banco.

---

## AP-02 — Segredos hardcoded / dados sensíveis expostos — 🔴 CRITICAL

**Descrição:** credenciais, chaves de API, `SECRET_KEY`, senhas de SMTP/gateway
fixas no código; ou dados sensíveis retornados/logados.

**Sinais de detecção:**
- `password`, `senha`, `secret`, `api_key`, `apikey`, `token`, `pk_live`,
  `AKIA`, `-----BEGIN` atribuídos a literais.
- `grep -rniE "(secret|password|passwd|api[_-]?key|token)\s*[:=]\s*['\"]"`.
- Segredo devolvido em resposta HTTP (ex.: `secret_key` no `/health`) ou impresso
  em log (nº de cartão, chave do gateway).

**Por que importa:** vazamento de credenciais; segredo em repositório é
comprometimento permanente.

---

## AP-03 — Armazenamento inseguro de senha — 🟠 HIGH

**Descrição:** senha em texto puro, hash fraco (MD5/SHA1 sem salt) ou "crypto"
caseiro.

**Sinais de detecção:**
- `hashlib.md5`, `hashlib.sha1`, `md5(`, `sha1(`.
- Comparação direta `senha == row['senha']` / `pass === stored`.
- Funções caseiras (loops de `base64`, XOR, substring) chamadas de "hash".
- Senha default (`"123456"`, `"admin"`) no fluxo de criação.

**Por que importa:** senhas recuperáveis/quebráveis; comprometimento de contas.

---

## AP-04 — Regra de negócio / acesso a dados na camada de apresentação — 🟠 HIGH

**Descrição:** controllers/rotas contendo SQL, cálculos de negócio, envio de
e-mail/notificação. Ausência de camada de serviço/repositório.

**Sinais de detecção:**
- `import`/uso de driver de banco dentro de arquivos de rota/controller.
- Cálculos (totais, descontos, `completion_rate`, "overdue") dentro do handler.
- Efeitos colaterais (e-mail/SMS/push) disparados do controller.
- Model contendo relatórios/orquestração (não apenas representação de dados).

**Por que importa:** viola SRP e separação de camadas; código não testável e
difícil de evoluir.

---

## AP-05 — God Class / God Function (violação de SRP) — 🟠 HIGH

**Descrição:** uma classe/função que faz tudo (init de DB + rotas + regra +
pagamento), ou funções muito longas com múltiplas responsabilidades.

**Sinais de detecção:**
- Classe única referenciada em todo o app (`AppManager`, `Manager`, `Helper`,
  `Utils` genérico).
- Funções com > ~50 linhas ou > ~4 níveis de aninhamento.
- Callback hell / coordenação assíncrona manual por contadores.

**Por que importa:** baixa coesão, alto acoplamento, impossível de testar em
unidade.

---

## AP-06 — Consultas N+1 — 🟡 MEDIUM

**Descrição:** um loop que dispara uma query por item, em vez de `JOIN`/eager
loading/agregação.

**Sinais de detecção:**
- `for ... : execute(...)` / `.forEach(... db.get(...))`.
- ORM: acessar relação dentro de loop sem `joinedload`/`selectinload`/`include`.
- Contagens/estatísticas feitas percorrendo `.all()` em memória em vez de
  `COUNT`/`GROUP BY`.

**Por que importa:** número de queries cresce linearmente; não escala.

---

## AP-07 — Camada de dados sem abstração (sem Repository/DAO) — 🟡 MEDIUM

**Descrição:** acesso a dados espalhado, conexão global/singleton, schema e seed
misturados com a conexão, duplicação de mapeamento row→dict.

**Sinais de detecção:**
- Conexão global mutável (`db_connection = None` + `global`).
- `check_same_thread=False`, conexão única compartilhada entre threads.
- Mesmo mapeamento de linha repetido em várias funções.
- `CREATE TABLE`/seed dentro da função de obter conexão.

**Por que importa:** dificulta troca de banco, testes e transações; risco de
concorrência.

---

## AP-08 — Uso de APIs deprecated / obsoletas — 🟡 MEDIUM

**Descrição:** uso de APIs marcadas como deprecated, removidas ou desencorajadas
pela linguagem/framework/ORM. **Checagem obrigatória na Fase 2.**

**Sinais de detecção (exemplos por stack — não exaustivo):**

Python:
- `datetime.utcnow()` / `datetime.utcfromtimestamp()` — deprecated no 3.12; usar
  `datetime.now(timezone.utc)`.
- `Model.query.get(id)` (SQLAlchemy 1.x legacy) — usar `db.session.get(Model, id)`.
- Flask `@app.before_first_request` — removido no Flask 2.3+.
- Módulos `imp`, `cgi`, `asyncore`; `collections.Mapping` (mudou p/ `collections.abc`).

Node/JavaScript:
- `new Buffer(...)` — usar `Buffer.from`/`Buffer.alloc`.
- `crypto.createCipher` / `createDecipher` — usar `createCipheriv`.
- `url.parse()` (legacy) — usar `new URL()`.
- `require('sqlite3').verbose()` sem migração para driver mantido; callbacks
  antigos onde há API baseada em Promise.

Genérico:
- Warnings de "DeprecationWarning" no boot/testes.
- Chamadas marcadas `@deprecated` na doc da dependência instalada.

**Por que importa:** quebra em upgrades futuros; perde correções de segurança.

---

## AP-09 — Tratamento de erro amplo / silencioso — 🟡 MEDIUM

**Descrição:** `except:`/`catch(e){}` que engole tudo, esconde bugs, ignora o
erro ou vaza detalhes internos ao cliente.

**Sinais de detecção:**
- Python: `except:` sem tipo, `except Exception` que só retorna genérico.
- Node: callback que ignora `err` e responde sucesso; `catch {}` vazio.
- Retornar `str(e)`/stacktrace cru no corpo da resposta HTTP.

**Por que importa:** captura `KeyboardInterrupt`/`SystemExit`, mascara defeitos,
vaza implementação.

---

## AP-10 — Duplicação de código (DRY violado) — 🔵 LOW

**Descrição:** blocos idênticos repetidos (serialização, validação, regra).

**Sinais de detecção:** funções quase idênticas que diferem por um filtro;
mesmo dict/DTO montado à mão em vários pontos; listas de validação ("magic
lists") repetidas.

**Por que importa:** manutenção propensa a divergência.

---

## AP-11 — Logging via print/console — 🔵 LOW

**Descrição:** `print(...)` / `console.log(...)` como observabilidade.

**Sinais de detecção:** `grep -nE "print\(|console\.log\("` em código de
runtime.

**Por que importa:** sem níveis, sem formatação/rotação; ruído e risco de logar
dado sensível.

---

## AP-12 — Código morto / imports não usados — 🔵 LOW

**Descrição:** imports de sistema não usados (`os, sys, json, time`), funções/
constantes criadas e nunca chamadas.

**Sinais de detecção:** linters (`pyflakes`, `eslint no-unused-vars`); símbolos
definidos sem referência.

**Por que importa:** ruído, confusão sobre a fonte de verdade.

---

## AP-13 — Magic strings/numbers e nomes crípticos — 🔵 LOW

**Descrição:** literais de status/regra espalhados; variáveis de uma letra.

**Sinais de detecção:** strings de status repetidas (`"PAID"`, `"pending"`);
`u`, `e`, `p`, `cc`; números mágicos em regras.

**Por que importa:** legibilidade e consistência.

---

## Checklist de saída da Fase 2

- [ ] Todos os 13 anti-patterns verificados no código
- [ ] AP-08 (deprecated) explicitamente checado
- [ ] Cada ocorrência com `arquivo:linha`, evidência e severidade
- [ ] Contagem por severidade calculada
- [ ] Relatório gerado a partir do template (`03-report-template.md`)
- [ ] Confirmação pedida ao usuário **antes** de qualquer escrita
