# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Análise Manual

Achados priorizados por impacto arquitetural e de segurança. Referências no formato `arquivo:linha`.

### 🔴 CRITICAL — Segredos hardcoded e dados sensíveis em log

- **Onde:** `src/utils.js:1-7` (`dbPass`, `paymentGatewayKey`, `smtpUser` fixos no código) e `src/AppManager.js:45` (`console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`).
- **Problema:** credenciais de produção (senha de banco, **chave `pk_live_` do gateway de pagamento**) estão versionadas no código. Além disso, o **número do cartão de crédito** e a chave do gateway são impressos no log a cada checkout.
- **Impacto:** vazamento de credenciais e violação de PCI-DSS (dados de cartão em log). Comprometimento financeiro direto.
- **Correção:** mover segredos para variáveis de ambiente/secret manager; nunca logar PAN de cartão nem chaves; mascarar dados sensíveis.

### 🟠 HIGH — Hash de senha caseiro e inseguro + senha padrão

- **Onde:** `src/utils.js:17-23` (`badCrypto`) e `src/AppManager.js:68` (`badCrypto(p || "123456")`).
- **Problema:** o "hash" concatena `base64` do texto puro num loop e trunca em 10 chars — **reversível, sem salt, sem algoritmo criptográfico**. Quando a senha não é informada, usa o default `"123456"`.
- **Impacto:** senhas trivialmente recuperáveis; contas criadas no checkout ficam com senha previsível.
- **Correção:** usar `bcrypt`/`argon2` com salt; exigir senha válida em vez de default.

### 🟠 HIGH — God Class e "callback hell" com coordenação assíncrona manual

- **Onde:** `src/AppManager.js` inteiro; em especial o relatório `financial-report` (`AppManager.js:80-129`) com contadores `coursesPending`/`enrPending`.
- **Problema:** `AppManager` acumula responsabilidades de infraestrutura (init de DB), roteamento, regra de negócio e pagamento (viola SRP). O relatório coordena queries aninhadas manualmente por contadores decrementados dentro de callbacks — **frágil a condições de corrida**, erros de DB (`err`) são ignorados em `AppManager.js:92,104,106`, e gera N+1 queries (1 por curso, 1 por matrícula, 1 por usuário, 1 por pagamento).
- **Impacto:** relatório pode responder cedo/incompleto, dados inconsistentes e performance ruim; código praticamente impossível de testar isoladamente.
- **Correção:** separar em camadas (routes → controllers → services → repositories); usar `async/await` (ou Promises) com `JOIN`/agregação SQL em vez de contadores manuais.

### 🟡 MEDIUM — Exclusão de usuário deixa registros órfãos (sem integridade referencial)

- **Onde:** `src/AppManager.js:131-137` (`DELETE /api/users/:id`).
- **Problema:** deleta o usuário mas **não remove nem trata** matrículas e pagamentos associados — o próprio texto de resposta admite: *"as matrículas e pagamentos ficaram sujos no banco"*. As tabelas não têm `FOREIGN KEY`/`ON DELETE CASCADE` (`AppManager.js:12-16`).
- **Impacto:** dados órfãos corrompem relatórios financeiros e a consistência do domínio.
- **Correção:** definir chaves estrangeiras com cascata (ou soft delete), e executar a limpeza dentro de uma transação.

### 🟡 MEDIUM — Banco em memória e cache global sem limites

- **Onde:** `src/AppManager.js:7` (`new sqlite3.Database(':memory:')`) e `src/utils.js:9,12-15` (`globalCache` / `logAndCache`).
- **Problema:** o banco `:memory:` **perde todos os dados a cada restart**, inadequado para persistência real; o `globalCache` é um objeto global que cresce indefinidamente (memory leak) e mistura estado global com utilidades.
- **Impacto:** perda de dados e vazamento de memória em execução prolongada; estado global dificulta testes.
- **Correção:** usar arquivo/servidor de banco persistente; substituir o cache global por uma abstração com expiração/limite.

### 🔵 LOW — Nomes crípticos e ausência de validação de entrada

- **Onde:** `src/AppManager.js:29-33` (`u`, `e`, `p`, `cid`, `cc`).
- **Problema:** variáveis de uma letra prejudicam legibilidade; não há validação de formato de e-mail nem sanitização — só checagem de presença (`AppManager.js:35`).
- **Impacto:** manutenção difícil e entrada inconsistente aceita pela API.
- **Correção:** nomes descritivos (`username`, `email`, `password`...) e validação de schema (ex.: `zod`/`joi`).

### 🔵 LOW — Tratamento de erro inconsistente e "magic strings"

- **Onde:** `src/AppManager.js:133` (callback do delete **ignora `err`** e sempre responde sucesso), status de pagamento derivado de `cc.startsWith("4")` (`AppManager.js:46`), strings de status (`"PAID"`, `"DENIED"`) espalhadas.
- **Problema:** erros de banco não propagados, respostas HTTP nem sempre refletem o resultado real, e regras representadas por literais mágicos.
- **Impacto:** falhas silenciosas e comportamento difícil de rastrear.
- **Correção:** tratar `err` em todos os callbacks, padronizar respostas de erro e centralizar constantes de status.
