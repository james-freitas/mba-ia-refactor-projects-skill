# Desafio — Skill `refactor-arch`: Refatoração Arquitetural Automatizada

Solução do desafio de criação de Skills: uma skill para **Claude Code** que analisa, audita e refatora projetos backend legados para o padrão **MVC em camadas** (Routes → Controllers → Services → Repositories → Models), de forma agnóstica de tecnologia.

- **Ferramenta:** Claude Code (Custom Skills em `.claude/skills/refactor-arch/`)
- **Projetos-alvo:** `code-smells-project/` (Python/Flask), `ecommerce-api-legacy/` (Node.js/Express) e `task-manager-api/` (Python/Flask parcialmente organizado)
- **Relatórios de auditoria (saída da Fase 2):** [`reports/audit-project-1.md`](reports/audit-project-1.md) · [`reports/audit-project-2.md`](reports/audit-project-2.md) · [`reports/audit-project-3.md`](reports/audit-project-3.md)

---

## A) Análise Manual

Antes de construir a skill, os três projetos foram lidos manualmente. As referências de `arquivo:linha` abaixo apontam para o **código original** (commit inicial `6d1ce62`), antes da refatoração.

### Projeto 1 — `code-smells-project` (Python/Flask, API de E-commerce)

Código procedural em 4 arquivos flat (`app.py`, `controllers.py`, `models.py`, `database.py`), sem camadas.

| # | Severidade | Problema | Onde | Por que é relevante |
|---|------------|----------|------|---------------------|
| 1 | 🔴 CRITICAL | **SQL Injection** — todas as queries montadas por concatenação de string; além disso o endpoint `/admin/query` executa SQL arbitrário vindo do corpo da requisição | `models.py:28,48-50,110,140,291`; `app.py:59-78` | Qualquer usuário pode ler, alterar ou destruir o banco inteiro. É a falha de maior impacto do projeto — compromete confidencialidade, integridade e disponibilidade de uma vez. |
| 2 | 🔴 CRITICAL | **Segredo hardcoded e exposto** — `SECRET_KEY = 'minha-chave-super-secreta-123'` no código, e o `/health` devolve `secret_key` e `debug` na resposta | `app.py:7-8`; `controllers.py:285-289` | Segredo versionado vaza para qualquer pessoa com acesso ao repositório; exposto num endpoint público, permite forjar sessões/tokens assinados com a chave. |
| 3 | 🟠 HIGH | **Senha em texto puro** — gravada e comparada sem hash; seed também em claro | `models.py:110,127-128`; `database.py:76-78` | Um vazamento do banco expõe as senhas reais dos usuários (frequentemente reutilizadas em outros serviços). |
| 4 | 🟠 HIGH | **Regra de negócio e efeitos colaterais nas camadas erradas** — cálculo de total/desconto de pedido dentro do "model"; envio de e-mail/SMS/push via `print` dentro do controller | `models.py:133-169,235-273`; `controllers.py:208-210,248-250` | Viola MVC e SRP: impossível testar a regra em isolamento; qualquer mudança de negócio exige mexer em código de apresentação e de dados ao mesmo tempo. |
| 5 | 🟡 MEDIUM | **Consultas N+1** — listagem de pedidos faz uma query por item e outra por produto, dentro de loop | `models.py:171-233` | Degrada linearmente com o volume de dados; com poucos milhares de pedidos o endpoint fica inutilizável. Resolve-se com `JOIN`/agregação. |
| 6 | 🟡 MEDIUM | **Conexão global mutável** com `check_same_thread=False`, e schema/seed criados dentro do getter de conexão | `database.py:4-10` | Estado global compartilhado entre requests é fonte de race conditions e corrupção de dados; mistura responsabilidade de conexão com migração/seed. |
| 7 | 🟡 MEDIUM | **Tratamento de erro genérico com vazamento** — `except Exception as e: return jsonify({"erro": str(e)})` em quase todos os handlers | `controllers.py:10-12,21-22,60-62,...` | Devolve detalhes internos (mensagens do SQLite, paths) ao cliente e mascara bugs — tudo vira HTTP 200/500 indistinto. |
| 8 | 🔵 LOW | **Duplicação (DRY)** — o mesmo dict de produto é montado à mão em 3 lugares; `get_pedidos_usuario` ≈ `get_todos_pedidos` | `models.py:12-21,31-40,304-313,171-233` | Cada campo novo precisa ser adicionado em N lugares; é o tipo de divergência silenciosa que gera bugs de contrato. |
| 9 | 🔵 LOW | **Logging via `print()`** | `controllers.py:8,57,161,179`; `app.py:56,83-85` | Sem níveis, timestamps ou destino configurável — inviabiliza observabilidade em produção. |
| 10 | 🔵 LOW | **Magic strings** — listas de categorias/status repetidas como literais | `controllers.py:52,242`; `models.py:289-297` | Um typo numa das cópias cria comportamento inconsistente sem nenhum erro visível. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

Três arquivos: `src/app.js` (bootstrap), `src/AppManager.js` (god class) e `src/utils.js` (config + helpers globais). Curiosidade: aqui as queries **já eram parametrizadas** — não há SQL Injection.

| # | Severidade | Problema | Onde | Por que é relevante |
|---|------------|----------|------|---------------------|
| 1 | 🔴 CRITICAL | **Segredos de produção hardcoded** — `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_..."`, SMTP fixos no código | `utils.js:2-5` | Chave **live** de gateway de pagamento versionada = risco financeiro direto; qualquer fork/clone do repositório carrega as credenciais. |
| 2 | 🔴 CRITICAL | **Dados sensíveis em log** — `console.log` imprime o **número do cartão** e a chave do gateway a cada checkout | `AppManager.js:45` | Violação grave de PCI-DSS: logs costumam ir para sistemas de terceiros com retenção longa; o PAN do cliente fica gravado em claro. |
| 3 | 🟠 HIGH | **"Hash" caseiro + senha default** — `badCrypto` aplica base64 em loop e trunca em 10 chars; usuário sem senha recebe `"123456"`; seed com `pass='123'` | `utils.js:17-23`; `AppManager.js:18,68` | Base64 é reversível — não é hash. Somado à senha default, qualquer conta criada sem senha é trivialmente invadível. |
| 4 | 🟠 HIGH | **God Class + callback hell** — `AppManager` concentra conexão, schema, seed, todas as rotas, decisão de pagamento (`cc.startsWith("4")`) e relatório financeiro, com ~5 níveis de callbacks aninhados | `AppManager.js:4-137` | Viola SRP por completo: nada é testável em isolamento e qualquer mudança passa pelo mesmo arquivo. O callback hell esconde erros não tratados. |
| 5 | 🟡 MEDIUM | **Consultas N+1 no relatório financeiro** — `forEach(courses)` → query de enrollments → `forEach` → query de user + query de payment, coordenado por contadores manuais | `AppManager.js:83-127` | Além do custo O(N×M) de queries, a coordenação manual por contadores é frágil — uma exceção no meio deixa a resposta pendurada. |
| 6 | 🟡 MEDIUM | **Erros silenciosos / sempre sucesso** — callbacks ignoram `err`; `DELETE /users/:id` responde 200 mesmo em falha e deixa registros órfãos | `AppManager.js:57,92,104,106,131-136` | O cliente recebe sucesso para operações que falharam — corrompe a confiança no contrato da API e dificulta depuração. |
| 7 | 🟡 MEDIUM | **API deprecated/legada** — `require('sqlite3').verbose()` com API de callbacks, sem migração para driver mantido/Promises | `AppManager.js:1` | Driver em modo legado impede `async/await`, perpetua o callback hell e deixa o projeto fora do caminho de atualizações de segurança. |
| 8 | 🔵 LOW | **Código morto** — `totalRevenue` e `globalCache` exportados e nunca usados de fato | `utils.js:10,25`; `AppManager.js:2` | Estado global morto confunde o leitor e convida a reintroduzir acoplamento. |
| 9 | 🔵 LOW | **Logging via `console.log`** como observabilidade | `utils.js:13`; `app.js:13` | Mesmo racional do projeto 1 — sem níveis nem estrutura. |
| 10 | 🔵 LOW | **Nomes crípticos e magic strings** — `u`, `e`, `p`, `cid`, `cc`; status `"PAID"`/`"DENIED"` inline | `AppManager.js:29-33,47` | Custo de leitura alto num arquivo que já concentra tudo; strings de status repetidas são propensas a typo. |

### Projeto 3 — `task-manager-api` (Python/Flask, parcialmente organizado)

Já tinha pastas `models/`, `routes/`, `services/`, `utils/` — mas as camadas não seguravam responsabilidade: regra de negócio e ORM direto dentro dos blueprints.

| # | Severidade | Problema | Onde | Por que é relevante |
|---|------------|----------|------|---------------------|
| 1 | 🔴 CRITICAL | **Segredos hardcoded** — `SECRET_KEY = 'super-secret-key-123'` no entrypoint e senha de SMTP fixa no service de notificação | `app.py:13`; `services/notification_service.py:9-10` | Mesmo racional dos projetos anteriores: segredo versionado é segredo vazado. |
| 2 | 🔴 CRITICAL | **Hash de senha devolvido nas respostas** — `to_dict()` inclui `'password'`; `login` e `create_user` retornam o hash ao cliente | `models/user.py:21`; `routes/user_routes.py:85-86,209` | Expor o hash (ainda mais MD5, ver #3) equivale a entregar a senha: MD5 sem salt é quebrado por rainbow table em segundos. |
| 3 | 🟠 HIGH | **Senha em MD5 sem salt** | `models/user.py:29,32` | MD5 é criptograficamente quebrado e, sem salt, hashes iguais denunciam senhas iguais. |
| 4 | 🟠 HIGH | **Regra de negócio + ORM na apresentação / God Function** — `summary_report` com ~90 linhas fazendo contagens, agregações e montagem de payload; `Model.query`/`db.session` direto nos blueprints | `routes/report_routes.py:13-101`; `routes/task_routes.py:273-298` | A estrutura de pastas *parece* MVC mas não é — o problema clássico de projeto "parcialmente organizado". Testar um relatório exige subir o Flask inteiro. |
| 5 | 🟡 MEDIUM | **Consultas N+1** — loop com `User.query.get`/`Category.query.get` por task; `Task.query` por usuário/categoria; `len(u.tasks)` por usuário | `routes/task_routes.py:41-57`; `routes/report_routes.py:55-68,157-165`; `routes/user_routes.py:22` | Cada listagem dispara dezenas de queries; corrige-se com `JOIN`/`selectinload`/agregação. |
| 6 | 🟡 MEDIUM | **APIs deprecated** — `datetime.utcnow()` (deprecated no Python 3.12) e `Query.get()` (legado no SQLAlchemy 2.0) espalhados por models, rotas e seed | `models/*`, `routes/*`, `seed.py` | São remoções já anunciadas: o projeto quebraria em upgrades futuros. Equivalentes modernos: `datetime.now(timezone.utc)` e `db.session.get(Model, id)`. |
| 7 | 🟡 MEDIUM | **`except:` nu / erro engolido** — capturas amplas que só logam ou silenciam | `routes/task_routes.py:62,137,204`; `routes/user_routes.py:130,149`; `utils/helpers.py:46-50` | `except:` nu captura até `KeyboardInterrupt`/`SystemExit` e esconde bugs reais atrás de respostas genéricas. |
| 8 | 🔵 LOW | **Duplicação** — lógica de `overdue` repetida 5×; `task_data` montado à mão em vez de `to_dict()` | `models/task.py:50-60` + 4 rotas | A definição de "atrasada" pode divergir entre telas — bug de negócio silencioso. |
| 9 | 🔵 LOW | **Logging via `print()`** | `routes/*`, `notification_service.py`, `helpers.py` | Mesmo racional dos demais projetos. |
| 10 | 🔵 LOW | **Código morto** — `process_task_data`/`sanitize_string`/`generate_id` nunca chamados; `marshmallow` declarado e não usado; imports mortos | `utils/helpers.py:1-108`; `requirements.txt:4` | Dependência instalada sem uso amplia a superfície de ataque; helpers mortos poluem a leitura. |

---

## B) Construção da Skill

### Estrutura: SKILL.md orquestra, referências carregam o conhecimento

O [`SKILL.md`](code-smells-project/.claude/skills/refactor-arch/SKILL.md) é tratado como **prompt de orquestração**: define as 3 fases estritamente sequenciais, o formato exato dos banners de saída e os "princípios invioláveis" (confirmação antes de escrever, preservar contratos da API). Todo o conhecimento de domínio vive em 5 arquivos de referência, e cada fase começa com a instrução explícita de **ler o arquivo relevante antes de executar** ("não confie na memória"):

| Área de conhecimento exigida | Arquivo | Fase |
|---|---|---|
| Análise de projeto (detecção de stack/arquitetura) | `references/01-project-analysis.md` | 1 |
| Catálogo de anti-patterns | `references/02-antipattern-catalog.md` | 2 |
| Template de relatório | `references/03-report-template.md` | 2 |
| Guidelines de arquitetura MVC | `references/04-architecture-guidelines.md` | 3 |
| Playbook de refatoração | `references/05-refactoring-playbook.md` | 3 |

Decisões de design que valem destacar:

- **IDs estáveis e rastreáveis:** cada anti-pattern tem um ID (`AP-01`…`AP-13`) e cada transformação do playbook também (`RP-01`…`RP-12`), com o mapeamento explícito "RP-X corrige AP-Y". Isso faz o relatório da Fase 2 já sair com o plano de remediação pronto e permite ao usuário limitar escopo por severidade.
- **Gate de confirmação como regra dura:** a Fase 2 termina com um bloco "⛔ Gate obrigatório: nenhuma escrita pode ocorrer antes deste ponto", e a pergunta oferece 3 escopos (aplicar tudo / somente CRITICAL+HIGH / cancelar). Formulações mais brandas ("peça confirmação") se mostraram insuficientes nos primeiros testes.
- **Rede de segurança na Fase 3:** a skill exige branch de trabalho antes de modificar arquivos e proíbe declarar sucesso sem validar boot + endpoints ("use `✓` apenas para checagens realmente executadas").
- **Verificação de ausência:** a Fase 2 percorre **todos** os itens do catálogo e reporta explicitamente os não encontrados (ex.: "AP-01 verificado e não encontrado"), o que evita falsos positivos e prova que a checagem de APIs deprecated rodou mesmo quando não há ocorrência.

### Catálogo: 13 anti-patterns e por quê

O catálogo cobre as quatro dimensões que a análise manual revelou nos três projetos, com severidade distribuída:

- **Segurança (🔴/🟠):** AP-01 SQL Injection, AP-02 segredos hardcoded/dados sensíveis expostos, AP-03 armazenamento inseguro de senha. São os achados de maior impacto nos 3 projetos (chave live de gateway, cartão em log, MD5, SQL arbitrário) — precisam estar no topo do relatório.
- **Arquitetura (🟠):** AP-04 regra de negócio/dados na apresentação, AP-05 God Class/Function. São o cerne do desafio (refatorar para MVC) e apareceram nos 3 projetos em formas diferentes (arquivos flat, god class, blueprints gordos).
- **Dados/performance (🟡):** AP-06 consultas N+1, AP-07 dados sem abstração (sem Repository). N+1 apareceu nos 3 projetos — era obrigatório detectá-lo.
- **Qualidade/manutenção (🟡/🔵):** AP-08 **APIs deprecated** (requisito explícito do desafio — pegou `datetime.utcnow()`/`Query.get()` no projeto 3 e o driver sqlite3 por callbacks no projeto 2), AP-09 erro amplo/silencioso, AP-10 duplicação, AP-11 logging via print/console, AP-12 código morto, AP-13 magic strings/nomes crípticos.

O playbook tem **12 padrões de transformação** (RP-01…RP-12), cada um com exemplo de código antes/depois, e um roteiro de aplicação em ordem de prioridade: **segurança → separação de camadas → qualidade**.

### Como a skill ficou agnóstica de tecnologia

1. **Detecção por evidência, não por suposição:** a Fase 1 detecta linguagem/framework por manifesto (`requirements.txt`, `package.json`, …) e extensões, e classifica cada arquivo **pela responsabilidade que ele realmente exerce, não pelo nome ou pasta** — essencial para o projeto 3, cujas pastas mentiam sobre o conteúdo.
2. **Sinais de detecção conceituais com exemplos multi-linguagem:** o catálogo descreve cada anti-pattern por sinal observável ("query montada com concatenação/f-string/template literal") com exemplos em Python **e** JavaScript, em vez de regex acopladas a um framework.
3. **Guidelines por responsabilidade de camada:** o alvo MVC é definido pelo papel de cada camada (o que um controller pode e não pode fazer), deixando a materialização (blueprints Flask vs. Router Express) para a stack detectada.
4. **Playbook com equivalentes por stack:** ex. RP-03 indica `werkzeug.security`/`bcrypt` no Python e `bcrypt` no Node; RP-08 indica `logging` vs. `pino`/`winston`.
5. **Prova empírica:** a mesma skill (cópia byte a byte) rodou nos 3 projetos — duas stacks, três níveis de organização.

### Desafios encontrados

- **Falsos positivos de SQL Injection:** a primeira versão do catálogo tendia a marcar AP-01 em qualquer SQL cru. Nos projetos 2 e 3 as queries eram parametrizadas (placeholders `?` / ORM). Solução: o sinal de detecção passou a exigir evidência de concatenação, e o relatório passou a registrar a **ausência** verificada — os relatórios 2 e 3 mostram isso funcionando.
- **Garantir a pausa da Fase 2:** em execuções iniciais o agente emendava a refatoração logo após o relatório. Foi preciso transformar a confirmação em "gate" com linguagem proibitiva (⛔) e repeti-la nos princípios invioláveis do SKILL.md.
- **Preservar contratos da API durante a reestruturação:** mover regra de negócio de lugar sem mudar rota/payload exige disciplina. A solução foi dupla: instrução "reaproveite comportamento existente — não reescreva do zero" + validação obrigatória de endpoints ao final da Fase 3, com a regra de reverter a mudança se algo regredir. As únicas mudanças de contrato foram as intencionais de segurança (ex.: `/health` deixa de expor `secret_key`, respostas deixam de incluir senha/hash) — todas anunciadas no relatório da Fase 2.
- **Projeto parcialmente organizado (projeto 3):** o risco era a skill "reorganizar por reorganizar" ou, no extremo oposto, aprovar a estrutura pelas pastas. A instrução de classificar arquivos pela responsabilidade real resolveu: a Fase 1 reportou "MVC parcial — camadas não seguram responsabilidade" e a Fase 3 **completou** as camadas (repositories, services, controllers) em vez de recriar o projeto.
- **Formato de saída estável:** para que os 3 relatórios fossem comparáveis, o template da Fase 2 precisou ser bem prescritivo (seções numeradas, tabela de achados com colunas fixas). Foram necessárias ~3 iterações de ajuste nos arquivos de referência até os relatórios saírem consistentes entre stacks.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🔵 LOW | Total | Observações |
|---|---|---|---|---|---|---|
| 1 — `code-smells-project` | 2 | 2 | 3 | 3 | **10** | AP-08 (deprecated) verificado, sem ocorrências |
| 2 — `ecommerce-api-legacy` | 2 | 3 | 4 | 4 | **13** | AP-01 (SQLi) verificado, ausente (queries parametrizadas); AP-08 encontrado (driver sqlite3 callbacks) |
| 3 — `task-manager-api` | 3 | 3 | 4 | 4 | **14** | AP-01 ausente (ORM); AP-08 encontrado (`datetime.utcnow()`, `Query.get()`) |

Relatórios completos em [`reports/`](reports/). Todos os critérios de aceite foram atingidos nos 3 projetos: stack detectada corretamente, ≥ 5 findings com ≥ 1 CRITICAL/HIGH, e aplicação funcionando após a Fase 3.

### Comparação antes/depois

**Projeto 1 — `code-smells-project`** (de 4 arquivos flat para MVC completo):

```
ANTES                                    DEPOIS
├── app.py       # bootstrap + rotas     ├── app.py                # composition root
│                # admin (SQL arbitrário)├── config.py              # config via env
├── controllers.py # apresentação +      ├── routes/                # 5 blueprints (só roteamento)
│                # regra + print email   ├── controllers/           # 5 controllers magros
├── models.py    # SQL cru + regra       ├── services/              # regra de negócio + errors
│                # de negócio (~350 l.)  ├── repositories/          # SQL parametrizado
└── database.py  # conexão global +      ├── models/                # entidades
                 # schema + seed         └── infra/                 # db (conexão/request), schema, container
```

Endpoint `/admin/query` (execução de SQL arbitrário) **removido**; `/health` deixou de expor `secret_key`; senhas passaram a ser hasheadas (`werkzeug.security`).

**Projeto 2 — `ecommerce-api-legacy`** (de god class para MVC completo):

```
ANTES                                    DEPOIS
└── src/                                 └── src/
    ├── app.js        # bootstrap            ├── server.js          # composition root
    ├── AppManager.js # DB + schema +        ├── config/            # env via dotenv (.env.example)
    │                 # seed + rotas +       ├── routes/            # mapeamento de rotas
    │                 # pagamento +          ├── controllers/       # 4 controllers magros
    │                 # relatório N+1        ├── services/          # checkout, report, password (bcrypt)
    └── utils.js      # segredos prod +      ├── repositories/      # 6 repositories (API Promise)
                      # badCrypto +          ├── middlewares/       # errorHandler centralizado
                      # cache global         ├── db/                # conexão + schema
                                             └── utils/             # logger, errors, constants
```

Segredos movidos para `.env` (com `.env.example` e `.gitignore`); número de cartão e chave do gateway **removidos dos logs**; `badCrypto` substituído por `bcrypt`; relatório financeiro reescrito com `JOIN` (sem N+1); callbacks migrados para Promises.

**Projeto 3 — `task-manager-api`** (de MVC "de fachada" para MVC real):

```
ANTES                                    DEPOIS
├── app.py        # SECRET_KEY hardcoded ├── app.py                 # factory + error handler central
├── database.py                          ├── config.py               # config via env (.env.example)
├── models/       # to_dict vaza senha   ├── container.py            # wiring das camadas
├── routes/       # regra + ORM + N+1    ├── models/                 # entidades (sem vazar password)
│                 # (god function de     ├── routes/                 # só mapeamento de rotas
│                 # relatório ~90 l.)    ├── controllers/            # request/response
├── services/     # só notificação,      ├── services/               # task, user, report, category…
│                 # senha SMTP fixa      ├── repositories/           # queries (sem N+1, sem deprecated)
└── utils/helpers.py # ~80% código morto └── utils/                  # logger, constants, time
```

MD5 substituído por hash com salt; `password` removido das respostas; `datetime.utcnow()` → `datetime.now(timezone.utc)` e `Query.get()` → `db.session.get()`; N+1 resolvidos com `selectinload`/agregação; `helpers.py` morto removido.

### Checklist de validação preenchido

Validado por execução real em 2026-07-11 (logs abaixo). Os itens de Fase 1/2 têm evidência nos relatórios em `reports/`.

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ Python 3.12 | ✅ Node.js | ✅ Python 3 |
| Framework detectado corretamente | ✅ Flask 3.1 | ✅ Express 4.18 | ✅ Flask 3.0 + SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS c/ checkout | ✅ Task Manager |
| Nº de arquivos analisados condiz | ✅ 4 | ✅ 3 | ✅ estrutura completa |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados por severidade | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 10 | ✅ 13 | ✅ 14 |
| Detecção de APIs deprecated incluída | ✅ verificado (0) | ✅ 1 achado | ✅ 1 achado |
| Skill pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura de diretórios MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ `config.py` | ✅ `src/config/` + `.env` | ✅ `config.py` + `.env` |
| Models abstraem dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `routes/` | ✅ `src/routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ `services/errors.py` + handlers | ✅ `middlewares/errorHandler.js` | ✅ `errorhandler` no `app.py` |
| Entry point claro | ✅ `app.py` | ✅ `src/server.js` | ✅ `app.py` (factory) |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem | ✅ | ✅ | ✅ |

### Logs das aplicações rodando após a refatoração

Capturados em 2026-07-11, com o código refatorado deste repositório.

**Projeto 1 — `code-smells-project`:**

```
$ .venv/bin/python app.py
2026-07-11 14:44:15,506 INFO loja :: Servidor iniciado em http://localhost:5000
 * Running on http://127.0.0.1:5000

$ curl http://127.0.0.1:5000/health
{"counts":{"pedidos":1,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}

$ curl http://127.0.0.1:5000/produtos
{"dados":[{"ativo":1,"categoria":"informatica","criado_em":"2026-07-05 01:43:53",
"descricao":"Notebook potente para jogos","estoque":9,"id":1,"nome":"Notebook Gamer","preco":5999.99}, ...]}

$ curl -X POST http://127.0.0.1:5000/login -H 'Content-Type: application/json' \
       -d '{"email":"joao@email.com","senha":"123456"}'
{"dados":{"email":"joao@email.com","id":2,"nome":"João Silva","tipo":"cliente"},"mensagem":"Login OK","sucesso":true}
```

Note que o `/health` **não expõe mais `secret_key`** e o login **não devolve mais a senha** — mudanças intencionais anunciadas no relatório.

**Projeto 2 — `ecommerce-api-legacy`:**

```
$ node src/server.js
[2026-07-11T17:46:01.042Z] INFO Frankenstein LMS rodando na porta 3000

$ curl http://127.0.0.1:3000/health
{"status":"ok"}

$ curl -X POST http://127.0.0.1:3000/api/checkout -H 'Content-Type: application/json' \
       -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
{"msg":"Sucesso","enrollment_id":2}

$ curl http://127.0.0.1:3000/api/admin/financial-report
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},
 {"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]
```

O checkout processa o cartão **sem imprimir o número nem a chave do gateway no log** — antes, cada checkout vazava ambos.

**Projeto 3 — `task-manager-api`:**

```
$ .venv/bin/python app.py
 * Running on http://127.0.0.1:5000

$ curl http://127.0.0.1:5000/health
{"status": "ok", "timestamp": "2026-07-11 17:46:31.541303"}

$ curl http://127.0.0.1:5000/users
[{"active": true, "created_at": "2026-07-05 11:13:18.137466", "email": "joao@email.com",
  "id": 1, "name": "João Silva", "role": "admin", "task_count": 5}, ...]

$ curl http://127.0.0.1:5000/tasks
[{"category_id": 1, "category_name": "Backend", "id": 1, "overdue": false,
  "priority": 1, "status": "done", "title": "Adicionar autenticação real com JWT", ...}, ...]

$ curl http://127.0.0.1:5000/reports/summary
{"generated_at": "2026-07-11 17:46:51.073495", "overdue": {"count": 2, "tasks": [...]}, ...}
```

As respostas de `/users` **não incluem mais o campo `password`** (antes devolviam o hash MD5), e `task_count` agora vem de agregação (sem N+1).

### Comportamento da skill em stacks diferentes

- **Detecção de stack foi correta nos 3 casos**, incluindo detalhes úteis (SQL cru vs. parametrizado vs. ORM), o que mudou a auditoria: a skill reportou corretamente a **ausência** de SQL Injection nos projetos 2 e 3 em vez de forçar o achado.
- **A Fase 3 se adaptou ao contexto:** no projeto 1 e 2 criou as camadas do zero; no projeto 3 **completou** as camadas existentes (adicionou repositories/controllers, moveu regra dos blueprints para services) sem renomear rotas nem reorganizar o que já estava certo.
- **As transformações usaram os idiomas de cada stack:** blueprints + `werkzeug.security` + `logging` no Flask; Router + middleware de erro + `bcrypt` + Promises no Express.
- **APIs deprecated só apareceram onde existiam de fato** (projetos 2 e 3), e o relatório do projeto 1 registrou a verificação com resultado vazio — o comportamento esperado do requisito "se aplicável".

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado ([instruções](https://docs.anthropic.com/en/docs/claude-code/overview))
- **Python 3.12+** (projetos 1 e 3) e **Node.js 18+** com npm (projeto 2)

### Executar a skill em cada projeto

A skill vive em `.claude/skills/refactor-arch/` **dentro de cada projeto** (a cópia é idêntica nos três). Basta abrir o Claude Code na pasta do projeto e invocá-la:

```bash
# Projeto 1 — Python/Flask (E-commerce)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (LMS)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask (Task Manager)
cd ../task-manager-api
claude "/refactor-arch"
```

O fluxo em cada execução: a **Fase 1** imprime o resumo da stack, a **Fase 2** gera o relatório de auditoria e **pausa pedindo confirmação** (aplicar tudo / somente CRITICAL+HIGH / cancelar), e só após o "sim" a **Fase 3** refatora e valida. Salve a saída da Fase 2 em `reports/audit-project-{1,2,3}.md`.

### Validar que a refatoração funcionou

**Projeto 1:**

```bash
cd code-smells-project
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
# em outro terminal:
curl http://127.0.0.1:5000/health      # {"status":"ok", ...} sem secret_key
curl http://127.0.0.1:5000/produtos    # lista de produtos
curl -X POST http://127.0.0.1:5000/login -H 'Content-Type: application/json' \
     -d '{"email":"joao@email.com","senha":"123456"}'   # login sem devolver senha
```

**Projeto 2:**

```bash
cd ecommerce-api-legacy
npm install
cp .env.example .env
node src/server.js
# em outro terminal:
curl http://127.0.0.1:3000/health
curl -X POST http://127.0.0.1:3000/api/checkout -H 'Content-Type: application/json' \
     -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
curl http://127.0.0.1:3000/api/admin/financial-report
```

**Projeto 3:**

```bash
cd task-manager-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py     # opcional: popula dados de exemplo
.venv/bin/python app.py
# em outro terminal:
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/tasks
curl http://127.0.0.1:5000/users            # respostas sem o campo password
curl http://127.0.0.1:5000/reports/summary
```

Critérios de sucesso em qualquer projeto: a aplicação **inicia sem erros**, os **endpoints originais respondem** com os mesmos contratos, e nenhuma resposta ou log expõe segredos, senhas/hashes ou dados de cartão.
