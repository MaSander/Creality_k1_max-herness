# Fluxo de trabalho com Git (decidido em 22/11/2026)

Alexandre e Marcelo mexem no mesmo repositório. Para um não atropelar o outro, **toda mudança entra por branch e PR**.

- **Repositório:** `github.com/MaSander/Creality_k1_max-herness`, transferido do Alexandre para o Marcelo em 22/11/2026. O endereço antigo redireciona, mas cada clone deve apontar para o novo: `git remote set-url origin https://github.com/MaSander/Creality_k1_max-herness`.
- **Proteção no GitHub** (ruleset "main protegida"): a `main` não aceita push direto, force push nem exclusão. O PR é obrigatório, com 0 aprovações para o autor poder mesclar. A branch é apagada sozinha no GitHub depois do merge.

## Regras
1. **Nada de commit nem push direto na `main`.** Ela só recebe PR mesclado.
2. **Uma branch por assunto**, sempre a partir da `main` atualizada:
   ```
   git switch main && git pull --ff-only
   git switch -c <tipo>/<assunto>
   ```
   | Tipo | Para quê | Exemplo |
   |---|---|---|
   | `peca/` | Peça nova ou revisão em `pecas/<nome>/` | `peca/suporte-headset` |
   | `skill/` | Skill, agente, script novo ou regra nova | `skill/calibrar-filamento` |
   | `fix/` | Correção de script ou de instrução errada | `fix/fatiar-windows` |
   | `perfil/` | `filamentos/`, perfis do Creality, `projetos-base/` | `perfil/petg-preto` |
   | `docs/` | Só texto | `docs/como-importar` |
3. **Branch curta:** abra o PR no mesmo dia ou no seguinte. Não deixe trabalho parado sem commit por dias. Assuntos diferentes vão em branches diferentes, mesmo que feitos no mesmo dia.
4. **Antes de abrir o PR**, traga a `main` de novo (`git fetch && git merge origin/main`) e resolva conflitos **na branch**, nunca na `main`.
5. **PR:** `gh pr create --base main`, com título em português, o que mudou e como foi testado.
   - Mexeu no que é dos dois (`AGENTS.md`, `.claude/agents/`, `.claude/skills/`, `.claude/rules/`)? Espere o outro revisar e aprovar.
   - Só registro próprio (`pecas/<sua-peça>/`, `filamentos/`)? O autor pode mesclar.
6. **Depois do merge:** `git switch main && git pull --ff-only && git branch -d <branch>` (apague também a branch no GitHub).
7. **Arquivos de índice** (`AGENTS.md`, `README.md`, tabelas das `SKILL.md`) são os que mais dão conflito: mude só a linha do seu assunto, dentro do PR do assunto.

## Para os agentes
- Antes da **primeira edição** de um arquivo do repositório, rode `git branch --show-current`. Se estiver na `main`, faça `git pull --ff-only` e crie a branch do assunto (regra 2) antes de editar.
- Arquivo entregue fora do repositório (por exemplo, `.3mf` em Downloads) não precisa de branch.
- Commit, push e PR só quando quem pediu a tarefa mandar. Ao terminar, ofereça: "Quer que eu faça o commit e abra o PR?".
- Nunca faça `push --force` na `main` nem mescle PR que precise da revisão do outro (regra 5).
