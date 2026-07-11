# 03 — Template do Relatório de Auditoria (Fase 2)

Preencha o template abaixo **na íntegra**, no formato de banner. Substitua os
`<placeholders>`. Não invente achados: cada bloco de finding precisa de
`arquivo:linha` real. Ordene os achados por severidade (CRITICAL → LOW). Ao
final, **pare e peça confirmação**.

---

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório>
Stack:   <linguagem> + <framework> · <banco> via <driver/ORM>
Files:   <n> analyzed | ~<n> lines of code

Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

Findings

[CRITICAL] <nome do anti-pattern> (AP-xx)
File: <arquivo:linha ou arquivo:linha-linha>
Description: <o que foi encontrado, com a evidência (trecho de código)>
Impact: <consequência concreta — segurança, testabilidade, manutenção>
Recommendation: <correção, referenciando o padrão do playbook (RP-xx)>

[HIGH] <nome do anti-pattern> (AP-xx)
File: <arquivo:linha>
Description: <...>
Impact: <...>
Recommendation: <...>

<... um bloco por achado, ordenados CRITICAL → HIGH → MEDIUM → LOW ...>

Current Architecture Map
<arquivo>  ->  <responsabilidades reais>  (<vazamento>)
...
Missing layers: <ex.: Service, Repository>
Leaking layers: <ex.: DB no controller e no entrypoint>

Remediation Plan (proposed)
1. Security (CRITICAL/HIGH):   <ex.: RP-01 parametrizar SQL, RP-02 env, RP-03 bcrypt>
2. Layer separation (HIGH/MED): <ex.: RP-04 Repository, RP-05 Service, RP-06 controllers magros>
3. Quality (MEDIUM/LOW):        <ex.: RP-07 N+1, RP-08 logging, RP-09 exceções, RP-10 deprecated>

API contract impact: none (mesmos endpoints, mesmos payloads).

================================
Total: <n> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)?
> A Fase 3 vai modificar arquivos. Escolha o escopo:
> - Aplicar tudo (todas as severidades)
> - Somente CRITICAL/HIGH
> - Cancelar
```

---

## Regras de preenchimento

- **Nunca** liste um achado sem localização verificável.
- Cada correção deve referenciar um padrão do playbook (`RP-xx` em
  `05-refactoring-playbook.md`), garantindo rastreabilidade entre auditoria e
  refatoração.
- Se a contagem de CRITICAL for 0, ainda assim destaque o maior risco presente.
- A pergunta final ("Phase 2 complete. Proceed...?") é **obrigatória** e é o
  ponto de parada da Fase 2.
