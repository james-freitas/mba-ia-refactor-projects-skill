---
name: refactor-arch
description: >-
  Audita e refatora APIs web legadas para uma arquitetura MVC limpa (camadas
  Models, Controllers e Views/Routes, com Services e Repositories). Use quando
  o usuário pedir para "detectar code smells / anti-patterns", "gerar um
  relatório de auditoria de arquitetura", "refatorar para MVC", ou
  "reestruturar em camadas" um projeto backend. Agnóstica de stack — funciona
  em Flask, Express/Node, Django, FastAPI, Spring, Rails e similares.
---

# refactor-arch

Skill de **auditoria e refatoração arquitetural**. Transforma um backend legado
(código procedural, monolítico ou "spaghetti") em uma arquitetura **MVC em
camadas**, detectando anti-patterns, gerando um relatório de auditoria e
aplicando correções — **somente após confirmação humana**.

A skill roda em **3 fases estritamente sequenciais**. Não pule fases. Não
comece a Fase 3 (que modifica arquivos) sem a aprovação explícita pedida ao
final da Fase 2.

## Arquivos de referência

Leia o arquivo relevante **antes** de executar cada fase. Não confie na
memória — as heurísticas, catálogo e exemplos vivem nesses arquivos:

| Área | Arquivo | Usar na fase |
|------|---------|--------------|
| Detecção de stack e mapeamento de arquitetura | `references/01-project-analysis.md` | Fase 1 |
| Catálogo de anti-patterns (sinais + severidade) | `references/02-antipattern-catalog.md` | Fase 2 |
| Template do relatório de auditoria | `references/03-report-template.md` | Fase 2 |
| Guidelines da arquitetura MVC alvo | `references/04-architecture-guidelines.md` | Fase 3 |
| Playbook de refatoração (antes/depois) | `references/05-refactoring-playbook.md` | Fase 3 |

---

## Fase 1 — Análise

**Objetivo:** entender o que é o projeto antes de julgá-lo. Sem modificar nada.

1. Leia `references/01-project-analysis.md`.
2. **Detecte a stack** aplicando as heurísticas: linguagem (extensões +
   manifesto), framework, banco de dados / ORM, gerenciador de dependências.
3. **Mapeie a arquitetura atual**: localize o ponto de entrada, rotas,
   controllers, models, services, repositories e configuração. Classifique cada
   arquivo pela responsabilidade que ele realmente exerce (não pelo nome/pasta).
4. **Imprima um resumo** para o usuário exatamente neste formato de banner:

   ```
   ================================
   PHASE 1: PROJECT ANALYSIS
   ================================
   Language:      <linguagem + versão se detectável>
   Framework:     <framework + versão>
   Dependencies:  <deps relevantes além do framework>
   Domain:        <domínio do sistema (ex.: E-commerce API — produtos, pedidos, usuários)>
   Architecture:  <ex.: Monolítica — tudo em N arquivos, sem separação de camadas>
   Source files:  <N> files analyzed
   DB tables:     <tabelas/coleções encontradas>
   ================================
   ```

5. Siga direto para a Fase 2 (a análise não pausa).

---

## Fase 2 — Auditoria

**Objetivo:** cruzar o código contra o catálogo de anti-patterns, produzir um
relatório e **parar para pedir confirmação**. Ainda sem modificar nada.

1. Leia `references/02-antipattern-catalog.md` e `references/03-report-template.md`.
2. Percorra **cada anti-pattern do catálogo** e busque seus sinais de detecção
   no código (use grep/leitura). Inclua obrigatoriamente a checagem de **APIs
   deprecated** (seção AP-08 do catálogo).
3. Para cada ocorrência confirmada, registre: id do anti-pattern, severidade,
   local (`arquivo:linha`), evidência (trecho) e correção recomendada.
4. **Gere o relatório de auditoria** seguindo exatamente o template, incluindo:
   contagem por severidade, tabela de achados ordenada por severidade e o plano
   de remediação mapeado para os padrões do playbook.
5. **PARE.** Apresente o relatório e faça a pergunta de confirmação (use a
   ferramenta de pergunta ao usuário quando disponível):

   > Phase 2 complete. Proceed with refactoring (Phase 3)?
   > A Fase 3 vai **modificar arquivos** para reestruturar o projeto em MVC.
   > Posso aplicar **tudo**, apenas **CRITICAL/HIGH**, ou **cancelar**.

   **Não prossiga** para a Fase 3 sem resposta afirmativa. Se o usuário limitar
   o escopo (ex.: só CRITICAL/HIGH), respeite-o na Fase 3.

> ⛔ **Gate obrigatório:** nenhuma escrita/edição de arquivo do projeto pode
> ocorrer antes deste ponto. A Fase 2 é read-only.

---

## Fase 3 — Refatoração

**Objetivo:** reestruturar para o padrão MVC alvo e **provar que continua
funcionando**. Só entra aqui após o "sim" da Fase 2.

1. Leia `references/04-architecture-guidelines.md` (estrutura alvo) e
   `references/05-refactoring-playbook.md` (transformações concretas).
2. **Prepare a rede de segurança:** confirme que está em um branch de trabalho
   (crie um se estiver no branch principal) para que tudo seja reversível.
3. **Crie o esqueleto de camadas** conforme as guidelines (models / repositories
   / services / controllers / routes / config), respeitando a stack detectada.
4. **Aplique as transformações** do playbook, uma a uma, na ordem de prioridade:
   primeiro segurança (SQL injection, segredos, hashing), depois separação de
   camadas, depois qualidade (N+1, logging, deprecated, duplicação). Reaproveite
   comportamento existente — não reescreva do zero o que já funciona.
5. **Valide o resultado** (obrigatório — a fase não termina sem isto):
   - **Boot:** suba a aplicação e confirme que ela inicia sem erro.
   - **Endpoints:** exercite as rotas principais (ex.: `GET /health`, um `GET`
     de listagem, um `POST` de criação e o login/fluxo crítico) e confirme
     status HTTP e payloads coerentes com o comportamento original.
   - Se algo quebrar, corrija antes de declarar sucesso; se não conseguir,
     reverta a mudança que causou a regressão e reporte.
6. **Imprima o relatório final** exatamente neste formato de banner (após a
   estrutura e a validação, liste o que mudou, os anti-patterns resolvidos e os
   deixados de fora se o escopo foi limitado):

   ```
   ================================
   PHASE 3: REFACTORING COMPLETE
   ================================
   New Project Structure:
   src/
   ├── config/<...>
   ├── models/<...>
   ├── views/<...>
   ├── controllers/<...>
   ├── <demais camadas criadas>
   └── app.<ext> (composition root)

   Validation
     ✓ Application boots without errors
     ✓ All endpoints respond correctly
     ✓ <anti-patterns restantes: "Zero anti-patterns remaining" ou lista do que ficou fora do escopo>
   ================================
   ```

   Use `✓` apenas para checagens realmente executadas e aprovadas; se algo
   falhou ou não foi verificado, marque com `✗` e explique.

---

## Princípios invioláveis

- **Sequencial:** Fase 1 → 2 → 3, nunca fora de ordem.
- **Confirmação antes de escrever:** Fases 1 e 2 são read-only; a Fase 3 só
  começa com autorização explícita.
- **Agnóstica de stack:** as decisões vêm das heurísticas dos arquivos de
  referência, não de suposições sobre uma linguagem específica.
- **Preservar comportamento:** a refatoração muda a *estrutura*, não os
  contratos da API. Validar é parte da definição de "pronto".
