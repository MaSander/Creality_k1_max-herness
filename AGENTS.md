# AGENTS.md – Harness da Creality K1 Max

Este repositório guarda o agente e as skills que ajudam o **Alexandre** e o **Marcelo** (irmãos que dividem a mesma **Creality K1 Max**) a **projetar peças** e preparar impressões, entregando projetos `.3mf` do **Creality Print 7** prontos para fatiar.

## Idioma e estilo
- Responda sempre em **português**.
- Entregue arquivos prontos, não explicações longas. **Precisão vale mais que velocidade.**
- Se notar uma melhoria, **pergunte antes de aplicar** (múltipla escolha curta, opção recomendada primeiro).

## Estrutura
| Caminho | O que é |
|---|---|
| `.claude/agents/configurador-impressao-k1max.md` | Subagente principal: fluxo de trabalho, regras invioláveis e checklist de entrega |
| `.claude/skills/k1max-config-impressao/SKILL.md` | Equipamento, perfis de filamento calibrados e receitas por tipo de peça |
| `.claude/skills/modelagem-3d/SKILL.md` | Projetar uma peça do zero (SolidCraft via MCP): regras de projeto para a K1 Max, prévia e exportação |
| `.claude/skills/creality-print-3mf/SKILL.md` | Estrutura do `.3mf`, chaves de configuração, como gerar/revisar/alterar projetos por script e onde fica cada opção no Creality Print aberto |
| `.claude/skills/creality-print-3mf/gerar_projeto_creality.py` | Gera o `.3mf` de um **modelo novo** a partir de um projeto modelo + projeto de configuração |
| `.claude/skills/creality-print-3mf/alterar_config_3mf.py` | Altera só as configurações de um **`.3mf` existente** (malhas intactas); `--sem-altura-variavel` para suporte Organic |
| `.claude/skills/creality-print-3mf/adicionar_bloqueador_3mf.py` | Acrescenta caixas de **bloqueio ou reforço de suporte** a um objeto, em coordenadas da mesa |
| `.claude/skills/creality-print-3mf/fatiar_3mf.py` | **Fatia** um `.3mf` pela linha de comando do Creality Print (G-code com bico e filamento no nome e miniatura) |
| `.claude/skills/k1max-impressora/SKILL.md` | Conexão com a K1 Max sem root (IP 192.168.0.69): status e histórico (`k1max_status.py`) e **envio para a lista sem imprimir** (`enviar_k1max.py`) |
| `.claude/skills/k1max-calibracao/SKILL.md` | Calibração (flow, PA, fluxo volumétrico, retração) e troca de bico 0,4/0,2 |
| `.claude/skills/calibrar-filamento-novo/SKILL.md` | Assistente passo a passo para calibrar filamento novo: pergunta tipo e marca, guia cada teste, coleta os resultados e grava o perfil |
| `.claude/skills/calibrar-filamento-novo/perfil_filamento.py` | Registra testes e parâmetros em `filamentos/`, faz as contas e exporta o preset para o Creality Print |
| `.claude/perfis/K1_Max_bico_0.2_Alexandre.creality_printer` | Pacote de perfis do bico 0,2 (impressora, processos e filamentos) para importar no Creality |
| `.claude/perfis/perfis_creality_7.3.zip` e `creality-print-7.3/` | **Todos** os perfis de usuário do Creality Print 7.3 dele (bicos 0,4 e 0,2), exportados para o irmão importar. Instruções em `COMO-IMPORTAR.md`; atualize com `exportar_perfis.ps1` |
| `.claude/referencias/` | Projetos `.3mf` aprovados, usados como base (snowboarder 1:25, bico 0,4 detalhe e bico 0,2 v5) |
| `projetos-base/` | Projetos `.3mf` de referência (por bico e filamento) usados como `MODELO`/`CONFIG` na geração |
| `filamentos/` | Uma pasta por filamento calibrado: `perfil.md`, `perfil.json` e o preset `.json` para importar |
| `pecas/` | Uma pasta por peça com `README.md` de registro (config aprovada, resultado, lições); peças nossas via Git LFS, modelos de terceiros em `local/` (ignorada) |
| `pyproject.toml` e `uv.lock` | Bibliotecas Python dos scripts, com versões fixadas; tudo roda com `uv run` |
| `ferramentas/k1comum.py` | O que os scripts têm em comum nos dois sistemas (pastas, Creality Print, cópia de `.3mf`, grupos de chaves) |
| `.claude/rules/fluxo-git.md` | Fluxo de trabalho com Git: branch por assunto e PR, nada direto na `main` |

## Quando usar o quê
- **Projetar uma peça nova** (a partir de medidas, desenho ou foto) → skill `modelagem-3d` para modelar; depois o agente `configurador-impressao-k1max` prepara a impressão.
- **Filamento novo** (calibrar, criar perfil, problemas depois de trocar de filamento) → skill `calibrar-filamento-novo` **na conversa principal**, sem delegar: é um vai e vem de testes impressos que um subagente não consegue esperar.
- **Qualquer pedido de impressão** (STL, 3MF, GLB, STEP), revisão de `.3mf`, troca de bico ou ajuste pontual de calibração → delegue ao agente `configurador-impressao-k1max`.
- O agente lê `k1max-config-impressao` **sempre**, `creality-print-3mf` ao gerar/editar projeto e `k1max-calibracao` só para calibração.

## Regras invioláveis (resumo – detalhes no agente)
- Não alterar configurações de **filamento** sem pedir.
- Brim encostado: `brim_object_gap = 0` **e** `elefant_foot_compensation = 0`.
- Não usar reparo automático de malha (pymeshfix etc.).
- Nunca afirmar algo que não aconteceu.
- **Nunca iniciar impressão remotamente**: o arquivo vai para a lista, e quem está na máquina inicia pela tela.
- PLA: lembrar da **tampa aberta**. Trocou o bico: **autoteste e nivelamento**.
- Todo projeto entregue vai acompanhado do **checklist** do agente, verificado por código.
- Repositório **público**: não subir modelo de terceiros sem licença que permita redistribuir (veja `pecas/README.md`).
- **Git:** nada de commit direto na `main`. Antes de editar um arquivo do repositório, crie uma branch do assunto (`peca/`, `skill/`, `fix/`, `perfil/`, `docs/`) a partir da `main` atualizada, e entregue por PR. Detalhes em `.claude/rules/fluxo-git.md`.

## Ambientes por pessoa
Antes de salvar ou rodar algo, identifique **em qual computador** a sessão está (plataforma informada no ambiente da sessão e caminho do repositório). Não use o caminho de um no computador do outro.

| | Alexandre | Marcelo |
|---|---|---|
| Sistema | Windows | macOS |
| Pasta de entrega | `C:\Users\alemg\Downloads` | `~/Downloads` (`/Users/marcelosander/Downloads`) |
| Python | `uv run <script>` (igual nos dois) | `uv run <script>` (igual nos dois) |
| Creality Print | 7.x, perfis em `AppData\Roaming\Creality` (não editar direto) | instalado em `/Applications/Creality Print.app` |
| Modelagem | Fusion 360 e SolidCraft (com MCP) | SolidCraft 0.30.1 com MCP (escopo local do projeto) |

**Python: um comando só, igual no Windows e no macOS**
- Rode tudo com o [uv](https://docs.astral.sh/uv/), **da raiz do repositório**: `uv run .claude/skills/creality-print-3mf/gerar_projeto_creality.py ...`. Código solto: `uv run python -c "..."`. Testes: `uv run pytest`.
- O `uv` cria o `.venv` e instala as versões do `uv.lock` sozinho na primeira vez. Não use `python`, `python3`, `pip` nem o caminho do `.venv` direto: no Windows o `python` do PATH abre a Microsoft Store, e no Mac o `python3` é o do Homebrew, sem os pacotes.
- Instalar o `uv` (uma vez): no Windows, `winget install astral-sh.uv`; no macOS, `brew install uv`.
- Biblioteca nova: `uv add <pacote>` (atualiza `pyproject.toml` e `uv.lock`; os dois arquivos vão no commit).
- **JSON na linha de comando:** no PowerShell as aspas se perdem. Grave o JSON num arquivo e passe o arquivo (`--config`, `--caixas`); funciona em qualquer shell.
- Pasta de entrega e Creality Print: os scripts acham sozinhos (`ferramentas/k1comum.py`). Para trocar, defina `K1_ENTREGA` ou `K1_CREALITY_EXE`.

Nos dois: os perfis do Creality não são editados diretamente; entregue perfis como pacote `.creality_printer` para importar.

## Manutenção
- Skills novas: `.claude/skills/<nome>/SKILL.md` com frontmatter `name` e `description`.
- Agentes novos: `.claude/agents/<nome>.md`.
- Ao calibrar um filamento novo, registre em `filamentos/` (skill `calibrar-filamento-novo`) e atualize a tabela de perfis em `k1max-config-impressao`.
- Ao salvar um projeto de referência novo, coloque em `projetos-base/` e atualize o `README.md` de lá.
