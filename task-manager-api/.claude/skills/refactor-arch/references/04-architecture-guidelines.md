# 04 — Guidelines de Arquitetura MVC Alvo (Fase 3)

Regras da arquitetura em camadas para a qual refatoramos. Vale para qualquer
stack; os nomes de pasta se adaptam à convenção da linguagem, mas as
**responsabilidades e a direção das dependências** são fixas.

## Direção das dependências (regra de ouro)

```
Routes  →  Controllers  →  Services  →  Repositories  →  Models
                              │
                              └──→  (Config, Notification, Auth ... como dependências injetadas)
```

- O fluxo de chamada aponta **para dentro**. Camadas externas conhecem as
  internas, **nunca** o contrário.
- Nenhuma camada "pula" outra para acessar o banco (ex.: controller não fala
  com o banco direto).

## Responsabilidades por camada

### Models / Entities
- Representam dados e relações. Mapeamento ORM ou struct/DTO.
- **Podem** ter validações triviais de si mesmos e helpers de estado
  (`is_overdue()`), serialização (`to_dict()` **sem campos sensíveis**).
- **Não podem** conter orquestração de negócio, relatórios, acesso a outras
  tabelas via queries ad-hoc, nem I/O (e-mail, HTTP).

### Repositories / DAO
- **Único lugar** que fala com o banco. Encapsulam queries (parametrizadas),
  transações e mapeamento linha→objeto.
- Expõem métodos por intenção: `get_by_id`, `list`, `create`, `update`,
  `delete`, `search(...)`.
- **Não** contêm regra de negócio nem lidam com request/response.

### Services
- Orquestram a regra de negócio: cálculos (totais, descontos, taxas,
  "overdue"), validações de domínio, coordenação entre repositories, disparo de
  efeitos (via serviços injetados, ex.: `NotificationService`).
- Retornam dados/erros de domínio — **não** conhecem HTTP (`request`/`jsonify`).
- São o alvo natural dos testes de unidade.

### Controllers
- Traduzem HTTP ↔ domínio: leem input do request, chamam **um** service, mapeiam
  o retorno para status HTTP + payload.
- Fazem validação de **forma** (campos presentes, tipos) — a validação de
  **regra** é do service.
- **Não** contêm SQL, cálculos de negócio nem efeitos colaterais diretos.

### Routes / Views
- Apenas mapeiam método+URL → função do controller. Sem lógica.
- Seguem REST: verbo HTTP correto, URLs de recurso consistentes, status
  apropriados (200/201/204/400/401/403/404/409/500).

### Config
- Toda credencial/porta/chave vem de **variáveis de ambiente** (ou arquivo de
  config não versionado), com defaults seguros para dev.
- Nenhum segredo no código nem em respostas/logs.

### Entrypoint / Bootstrap
- Só faz **wiring**: cria o app, injeta dependências, registra rotas, sobe o
  servidor. Sem regra de negócio, sem SQL, sem seed inline.

### Cross-cutting
- **Logging:** logger configurado (níveis, formato), nunca `print`/`console.log`
  para runtime; nunca logar segredo/PII.
- **Erros:** tratamento centralizado; captura específica; resposta genérica ao
  cliente + detalhe no log.
- **Segurança:** hashing forte com salt (bcrypt/argon2), sem segredos hardcoded,
  sem endpoints de SQL arbitrário.

## Estrutura de pastas alvo

Adapte à convenção da stack detectada. Exemplos:

**Python / Flask**
```
app.py                  # bootstrap (create_app, registra blueprints)
config.py               # lê env vars
models/                 # entidades
repositories/           # acesso a dados (queries parametrizadas)
services/               # regra de negócio
controllers/            # HTTP ↔ service
routes/                 # blueprints: URL → controller
utils/                  # helpers coesos (não "util" genérico)
```

**Node / Express**
```
src/
  server.js             # bootstrap
  config/index.js       # env vars
  models/               # entidades / schema
  repositories/         # acesso a dados
  services/             # regra de negócio
  controllers/          # HTTP ↔ service
  routes/               # router: URL → controller
  middlewares/          # auth, error handler, logging
```

## Definição de "pronto" (arquitetural)

- [ ] Cada arquivo tem **uma** responsabilidade (SRP)
- [ ] Nenhum SQL fora de repositories
- [ ] Nenhuma regra de negócio em controllers/models
- [ ] Controllers não conhecem o banco; services não conhecem HTTP
- [ ] Segredos em env; nenhum em código/resposta/log
- [ ] Endpoints, verbos e status seguem REST
- [ ] `/health` presente e informativo (sem vazar segredo)
- [ ] Contratos da API preservados (mesmas rotas e payloads)
