# 03 — Template do Relatório de Auditoria (Fase 2)

Preencha o template abaixo **na íntegra**. Substitua os `<placeholders>`. Não
invente achados: cada linha da tabela precisa de `arquivo:linha` real. Ordene os
achados por severidade (CRITICAL → LOW). Ao final, **pare e peça confirmação**.

---

```markdown
# 🔍 Relatório de Auditoria Arquitetural

- **Projeto:** <nome do diretório>
- **Stack detectada:** <linguagem> + <framework> · <banco> via <driver/ORM>
- **Data:** <YYYY-MM-DD>
- **Arquitetura atual:** <ex.: procedural em 3 arquivos, sem camada de serviço>
- **Arquitetura alvo:** MVC em camadas (Routes → Controllers → Services → Repositories → Models)

## 1. Sumário executivo

<2-4 linhas: qual o risco dominante (segurança? acoplamento?) e o esforço geral
de remediação (baixo/médio/alto).>

## 2. Contagem por severidade

| Severidade | Qtd |
|------------|-----|
| 🔴 CRITICAL | <n> |
| 🟠 HIGH     | <n> |
| 🟡 MEDIUM   | <n> |
| 🔵 LOW      | <n> |
| **Total**  | <n> |

## 3. Achados

| # | ID | Anti-pattern | Sev | Local (arquivo:linha) | Evidência | Correção (playbook) |
|---|----|--------------|-----|-----------------------|-----------|---------------------|
| 1 | AP-01 | SQL Injection | 🔴 | models.py:110 | `"... email = '" + email + "'"` | RP-01 Parametrizar queries |
| 2 | AP-02 | Segredo hardcoded | 🔴 | app.py:7 | `SECRET_KEY = "..."` | RP-02 Config via env |
| ... | | | | | | |

## 4. Mapa da arquitetura atual

```
<arquivo>  ->  <responsabilidades reais>  (<vazamento>)
...
```

Camadas **ausentes:** <ex.: Service, Repository>.
Camadas **com vazamento:** <ex.: DB no controller e no entrypoint>.

## 5. Plano de remediação (proposto)

Ordem sugerida — segurança primeiro, depois estrutura, depois qualidade:

1. **Segurança (CRITICAL/HIGH):** <ex.: RP-01 parametrizar SQL, RP-02 env,
   RP-03 bcrypt, remover endpoint de SQL arbitrário>.
2. **Separação de camadas (HIGH/MEDIUM):** <ex.: RP-04 extrair Repository,
   RP-05 extrair Service, RP-06 controllers magros>.
3. **Qualidade (MEDIUM/LOW):** <ex.: RP-07 corrigir N+1, RP-08 logging,
   RP-09 tratar exceções, RP-10 substituir APIs deprecated, RP-11 remover
   segredo de respostas, RP-12 extrair mappers>.

Impacto esperado nos contratos da API: **nenhum** (mesmos endpoints, mesmos
payloads) — a refatoração muda a estrutura interna.

## 6. Confirmação necessária

> ⚠️ A próxima fase **modifica arquivos**. Escolha o escopo:
> - **Aplicar tudo** (todas as severidades)
> - **Somente CRITICAL/HIGH**
> - **Cancelar**
```

---

## Regras de preenchimento

- **Nunca** liste um achado sem localização verificável.
- Cada correção deve referenciar um padrão do playbook (`RP-xx` em
  `05-refactoring-playbook.md`), garantindo rastreabilidade entre auditoria e
  refatoração.
- Se a contagem de CRITICAL for 0, ainda assim destaque o maior risco presente.
- A seção 6 é **obrigatória** e é o ponto de parada da Fase 2.
