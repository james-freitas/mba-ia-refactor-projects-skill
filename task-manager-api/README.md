# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Análise Manual

Este projeto já tem alguma separação de camadas, mas ainda concentra regra de negócio nas rotas e tem falhas de segurança. Achados priorizados por impacto. Referências no formato `arquivo:linha`.

### 🔴 CRITICAL — Autenticação frágil: MD5 sem salt, hash de senha vazado e token falso

- **Onde:** `models/user.py:27-32` (`set_password`/`check_password` com `hashlib.md5`), `models/user.py:16-25` (`to_dict` retorna `'password'`), `routes/user_routes.py:210` (`'token': 'fake-jwt-token-' + str(user.id)`), `app.py:13` e `services/notification_service.py:10` (`SECRET_KEY` e senha SMTP hardcoded).
- **Problema:** senhas são hasheadas com **MD5 sem salt** (quebrável por rainbow tables); o hash é **serializado em toda resposta** de usuário (`to_dict` inclui `password`, usado no login, create, update, reports...); o "token" de login é apenas o id concatenado, sem assinatura nem expiração — trivial de forjar. Segredos (`SECRET_KEY`, senha de e-mail) estão fixos no código.
- **Impacto:** comprometimento de autenticação e vazamento de credenciais; qualquer resposta expõe o hash das senhas.
- **Correção:** usar `bcrypt`/`argon2` com salt; remover `password` do `to_dict`; emitir JWT assinado com expiração; mover segredos para variáveis de ambiente.

### 🟠 HIGH — Regra de negócio duplicada nas rotas (lógica "overdue" copiada 4×)

- **Onde:** bloco idêntico de cálculo de atraso em `routes/task_routes.py:30-39`, `71-80`, `283-287`, `routes/user_routes.py:171-180` e `routes/report_routes.py:33-37`, `132-135`. Existe `Task.is_overdue()` em `models/task.py:50-60`, mas **não é usado**.
- **Problema:** a mesma regra de domínio está reescrita à mão em vários controllers, ignorando o método do modelo. Não há camada de serviço; as rotas acumulam validação, montagem de DTO e regra de negócio (viola SRP e o princípio de rotas "magras").
- **Impacto:** mudança de regra exige editar 5+ lugares; alto risco de divergência entre endpoints.
- **Correção:** centralizar em `Task.is_overdue()` (ou numa camada de serviço) e chamar de todos os pontos; mover montagem de DTO para o próprio modelo.

### 🟡 MEDIUM — Problema N+1 e agregações feitas em Python

- **Onde:** `routes/task_routes.py:41-57` (uma query de `User` e de `Category` por task no `get_tasks`), `routes/report_routes.py:53-68` (uma query de tasks por usuário) e contagens manuais em `routes/task_routes.py:281-287` / `report_routes.py:30-51`.
- **Problema:** listagens carregam relacionamentos em loop (N+1) e estatísticas percorrem `Task.query.all()` em Python contando em laços, em vez de usar `JOIN`/`func.count`/`GROUP BY` do SQL.
- **Impacto:** número de queries e uso de memória crescem linearmente com o volume — não escala.
- **Correção:** usar `joinedload`/`selectinload` para relacionamentos e agregações no banco (`func.count`, `group_by`).

### 🟡 MEDIUM — `except:` nu engolindo erros

- **Onde:** `routes/task_routes.py:62` (`except:` retornando "Erro interno" e escondendo qualquer falha do `get_tasks`), `236`, `routes/user_routes.py:130`, `149`, `routes/report_routes.py:186`, `207`, `221`; também `except:` em `utils/helpers.py:47,49,88`.
- **Problema:** `except:` sem tipo captura **tudo**, inclusive `KeyboardInterrupt`/`SystemExit`, mascara bugs reais e dificulta o diagnóstico; muitos nem fazem log.
- **Impacto:** falhas silenciosas; erros de programação viram "Erro interno" genérico.
- **Correção:** capturar exceções específicas (`except SQLAlchemyError`), logar com stacktrace e deixar erros inesperados propagarem.

### 🔵 LOW — Validação duplicada e código morto ignorando os utilitários existentes

- **Onde:** listas de status/prioridade repetidas inline em `routes/task_routes.py:110,177`, `242` e `routes/user_routes.py:71,120`, apesar de já existirem as constantes `VALID_STATUSES`, `VALID_ROLES`, etc. em `utils/helpers.py:110-116` e os validadores `Task.validate_status/validate_priority` (`models/task.py:38-48`). Funções como `process_task_data`, `format_date`, `validate_email`, `parse_date` em `helpers.py` **não são usadas**.
- **Problema:** "magic lists" duplicadas e utilitários/validadores criados mas ignorados (código morto).
- **Impacto:** manutenção inconsistente (adicionar um status exige editar vários pontos) e confusão sobre a fonte de verdade.
- **Correção:** consumir as constantes/validadores centralizados e remover o código morto (ou passar a usá-lo).

### 🔵 LOW — Imports não usados e serialização verbosa/inconsistente

- **Onde:** `app.py:7` (`import os, sys, json, datetime` — só `datetime` é usado), `routes/task_routes.py:7` (`json, os, sys, time`), `routes/user_routes.py:6` (`hashlib, json`); montagem manual de dict em `routes/task_routes.py:16-59` e `routes/user_routes.py:162-181` enquanto existe `Task.to_dict()`.
- **Problema:** imports de sistema não utilizados poluem os módulos e o mesmo objeto é serializado ora via `to_dict()`, ora campo a campo, gerando payloads divergentes entre endpoints.
- **Impacto:** ruído no código e respostas inconsistentes para o mesmo recurso.
- **Correção:** remover imports mortos e padronizar a serialização usando sempre `to_dict()`.
