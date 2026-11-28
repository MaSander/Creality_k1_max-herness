# Validação do refino do harness (PRs 5, 7, 8, 9, 10, 11 e 12)

Passo a passo para conferir tudo o que entrou em 22/11/2026. Marque cada item quando passar. Se um item falhar, anote o comando, a mensagem de erro e em qual computador.

- **M** = Mac do Marcelo. **A** = PC do Alexandre (Windows, PowerShell). **M+A** = os dois.
- Todos os comandos são da **raiz do repositório**.
- No PowerShell, JSON vai sempre em **arquivo** (`--config`, `--caixas`), nunca escrito na linha.
- Regra que continua valendo: **nenhum teste inicia impressão à distância**. O arquivo vai para a lista e quem está na máquina inicia pela tela.

## O que cada PR entregou
| PR | Fase | Entrega |
|---|---|---|
| 5 | 1 | `uv run`, `ferramentas/k1comum.py`, argumentos nomeados nos scripts de `.3mf` |
| 7 | 2 | `analisar_malha.py`, `checklist_3mf.py`, correções do `gerar_projeto_creality.py` |
| 8 | 3 | Skill `modelagem-3d` com três jeitos, ficha da peça, `.mcp.json`, regras para o chat do SolidCraft |
| 9 | 4 | `sincronizar_perfis.py`, tabela de perfis gerada, zip renomeado |
| 10 | 4 | Calibração só por pedido, perguntas antes de delegar, contradições resolvidas |
| 11 | 4b | `fatiar_3mf.py --fatiador orca` (experimental) |
| 12 | 5 | Skill `registro-impressao` e `registrar_impressao.py` |

O que já foi testado no Mac está na descrição de cada PR. **No Windows nada foi rodado ainda.**

---

## 0. Preparação (M+A)
- [ ] **M+A** `git switch main` e `git pull`.
- [ ] **A** Instalar o `uv`: `winget install astral-sh.uv` (fechar e abrir o terminal depois).
- [ ] **M+A** `uv run pytest`
  - Mac com Creality Print e OrcaSlicer instalados: **38 passed**.
  - Windows: os dois testes de fatiamento são pulados quando o programa não está disponível; o esperado é **36 passed, 2 skipped** (ou 37 e 1, se o OrcaSlicer estiver instalado). Demora cerca de 30 a 60 segundos.
- [ ] **A** `git status` logo depois: não pode aparecer arquivo modificado (confere o fim de linha LF do `.gitattributes`).

## 1. Fase 1 – base portátil (PR 5)
- [ ] **A** Alterar um projeto com o JSON em arquivo. Crie `mudancas.json` com `{"wall_loops":"5"}` e rode:
  ```
  uv run .claude/skills/creality-print-3mf/alterar_config_3mf.py ".claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf" "$env:USERPROFILE\Downloads\teste_alterar.3mf" --config mudancas.json
  ```
  Esperado: `wall_loops: 4 -> 5`, a lista de chaves com `✓` (sem erro de acento) e `ok:` no fim.
- [ ] **A** Abrir `teste_alterar.3mf` no Creality Print: abre sem aviso, com 5 paredes e o perfil de processo marcado com `*`.
- [ ] **M+A** Recusa de saída igual à entrada: rodar o mesmo comando com a SAIDA igual à ENTRADA. Esperado: "A SAIDA não pode ser o mesmo arquivo da ENTRADA."
- [ ] **A** `uv run .claude/skills/calibrar-filamento-novo/perfil_filamento.py mostrar pla-flexygreen-vermelho` – imprime o perfil sem erro de codificação (tem emoji e seta).
- [ ] **A** `uv run .claude/skills/k1max-impressora/k1max_status.py status` – mostra estado e temperaturas.
- [ ] **M+A** `uv run .claude/skills/k1max-impressora/k1max_status.py ia` – mostra os quatro campos da detecção por câmera.
- [ ] **M ou A, com a impressora parada e só se quiserem ligar a IA:** `... k1max_status.py ia --ligar`. Esperado: os quatro campos em 1. **Este comando nunca foi executado.**

## 2. Fase 2 – verificação por código (PR 7)
- [ ] **M+A** Analisar a peça de teste:
  ```
  uv run .claude/skills/creality-print-3mf/analisar_malha.py pecas/teste-furos-m3/teste_furos_m3_v1.stl --render analise.png
  ```
  Esperado: 40.00 x 20.00 x 8.00 mm, fechada, 1 corpo, contato 725.4 mm², balanço 0, "Aprovada.". Abrir `analise.png`: quatro vistas, base em azul, textos com acento.
- [ ] **M+A** Checklist de um projeto de referência:
  ```
  uv run .claude/skills/creality-print-3mf/checklist_3mf.py ".claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf" --bico 0.4
  ```
  Esperado: "Sem falhas", com um `[aviso]` de que o tempo mínimo de camada difere do preset (8 no projeto, 0 no preset).
- [ ] **M+A** Checklist reprovando: rodar o mesmo com `--bico 0.2`. Esperado: `[FALHA] Bico montado é 0.2...` e "1 falha(s)".
- [ ] **M+A** Gerar um projeto novo. Crie `m3.json` com `{"layer_height":"0.2","initial_layer_print_height":"0.2","enable_support":"0","brim_type":"no_brim"}` e rode (troque `SAIDA` pela pasta Downloads):
  ```
  uv run .claude/skills/creality-print-3mf/gerar_projeto_creality.py ".claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf" ".claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf" pecas/teste-furos-m3/teste_furos_m3_v1.stl SAIDA/teste-furos-m3.3mf teste-furos-m3 --config m3.json
  ```
  Esperado: "partes extras do MODELO retiradas: 2", miniaturas redesenhadas e `ok:`.
- [ ] **M+A** Checklist do projeto gerado, com origem e ficha:
  ```
  uv run .claude/skills/creality-print-3mf/checklist_3mf.py SAIDA/teste-furos-m3.3mf --origem ".claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf" --bico 0.4 --ficha pecas/teste-furos-m3/ficha.json
  ```
  Esperado: "Sem falhas", com "Filamento intacto", "Escala: dimensões iguais às da ficha" e sem "Partes extras".
- [ ] **M+A** Abrir `teste-furos-m3.3mf` no Creality Print: **uma peça só** (sem os bloqueadores do snowboarder), no centro da mesa, apoiada, miniatura da peça certa.
- [ ] **M** Fatiar: `uv run .claude/skills/creality-print-3mf/fatiar_3mf.py SAIDA/teste-furos-m3.3mf --permitir-versao-nova`. Esperado: cerca de 17 min e 5 g.
- [ ] **A** Fatiar o mesmo projeto pela interface (Slice plate) e comparar tempo e gramas com os do Mac.

## 3. Fase 3 – modelagem (PR 8)
- [ ] **M+A** Abrir uma sessão nova do Claude Code no repositório. Ele deve pedir para aprovar os servidores `solidcraft` e `solidcraft-live` do `.mcp.json` (no Mac, o registro local antigo continua valendo por cima; para testar o `.mcp.json`, remova o local com `claude mcp remove solidcraft` e `claude mcp remove solidcraft-live`).
- [ ] **A** Se o servidor não subir: confirmar que `solidcraft-cli` está no PATH (`solidcraft-cli --help`).
- [ ] **M+A** **Jeito A (MCP sem janela):** pedir "modele um bloco 30 x 20 x 10 com um furo passante de 5 mm, salve em pecas/teste-validacao/". Conferir que o agente:
  - chama `skill_reference` antes de modelar;
  - salva `.sc`, STEP e STL em `pecas/teste-validacao/` (e não consegue salvar fora de `pecas/`);
  - mostra a prévia e espera aprovação;
  - roda `analisar_malha.py` e grava a `ficha.json`.
- [ ] **M+A** **Modo ao vivo:** abrir o SolidCraft, ligar Preferences → Assistant → "Let AI agents connect" e pedir uma alteração na peça pelo `solidcraft-live`. A peça muda na tela. Se a porta não for 27878, anotar qual é.
- [ ] **M+A** **Jeito C (chat do SolidCraft):** colar `.claude/skills/modelagem-3d/regras-projeto-k1max.md` em Preferences → AI → Custom instructions. Abrir um chat novo e pedir uma peça simples. Conferir que o assistente pergunta uso, material e bico, usa parâmetros nomeados e mostra a prévia antes de exportar.
- [ ] **M+A** Depois do chat do SolidCraft: exportar para `pecas/<peca>/` e, no Claude Code do repositório, rodar `analisar_malha.py` com `--gravar-ficha`.
- [ ] **M+A** Apagar `pecas/teste-validacao/` no fim (não vai para o git).

## 4. Fase 4 – perfis e preparação (PRs 9 e 10)
### Sincronização dos perfis
- [ ] **M** No Creality Print: File → Import → Import Configuration → `.claude/perfis/perfis_creality.zip`. Conferir que aparecem a impressora `Creality K1 Max 0.2 nozzle`, os filamentos `PLA FLEXYGREEN` e `PETG MASTERPRINT` e os processos.
- [ ] **M** `uv run .claude/perfis/sincronizar_perfis.py comparar` – esperado: "Iguais.". Se listar diferenças logo depois de importar, anotar quais (pode ser o programa regravando o preset).
- [ ] **A** `uv run .claude/perfis/sincronizar_perfis.py comparar` – é o primeiro teste com presets de verdade. Esperado: "Iguais." ou a lista do que mudou no programa desde a última exportação.
- [ ] **A** `uv run .claude/perfis/sincronizar_perfis.py exportar` e depois `git status`: só devem mudar os presets que o `comparar` listou (e o zip, se algum mudou). **O CR-PETG e o Hyper PLA não podem voltar.**
- [ ] **A** `uv run .claude/perfis/sincronizar_perfis.py tabela --gravar` e `git diff .claude/skills/k1max-config-impressao/SKILL.md`. A tabela atual foi gerada com os perfis de fábrica do Creality Print 7.2.2 do Mac: conferir se algum valor **sem negrito** muda com os do 7.3.
- [ ] **A** Conferir a tabela de `k1max-config-impressao` contra o que o Creality Print mostra para cada filamento (temperaturas, flow, PA, fluxo máximo).

### Projetos-base (não foram feitos)
- [ ] **A** Salvar os quatro projetos de `projetos-base/README.md` (PLA e PETG, bicos 0,4 e 0,2), seguindo o passo a passo de lá.
- [ ] **A** Para cada um: `uv run .claude/skills/creality-print-3mf/checklist_3mf.py projetos-base/<arquivo>.3mf`. Esperado: "Filamento igual ao preset do repositório".
- [ ] **M+A** Gerar a peça de teste M3 usando `projetos-base/base_0.4_PLA-FLEXYGREEN.3mf` como MODELO e CONFIG, e rodar o checklist.

### Comportamento do agente (sessão nova do Claude Code)
- [ ] **M+A** Dizer "troquei o carretel de PLA FLEXYGREEN por outro igual". Esperado: **não** sugere calibrar.
- [ ] **M+A** Digitar `/calibrar-filamento-novo`. Esperado: a skill abre e começa pelas perguntas.
- [ ] **M+A** Pedir "prepara essa peça para imprimir" com um STL, sem dizer bico nem material. Esperado: as perguntas (bico e filamento montados, uso, material) vêm **na conversa principal**, antes de o agente configurador ser chamado, e a entrega vem com a saída do `checklist_3mf.py`.

## 5. Fase 4b – OrcaSlicer (PR 11)
O que existe hoje é só comparação de G-code. **Nada fatiado pelo OrcaSlicer foi impresso.**
- [ ] **M** Fatiar a peça M3 pelos dois:
  ```
  uv run .claude/skills/creality-print-3mf/fatiar_3mf.py SAIDA/teste-furos-m3.3mf --permitir-versao-nova
  uv run .claude/skills/creality-print-3mf/fatiar_3mf.py SAIDA/teste-furos-m3.3mf --fatiador orca
  ```
- [ ] **M** Enviar os dois para a lista: `uv run .claude/skills/k1max-impressora/enviar_k1max.py <arquivo.gcode>`. Conferir se o `enviar_k1max.py` aceita o arquivo `_orca` e se a miniatura aparece na tela.
- [ ] **Na impressora** Imprimir o do Creality Print e depois o `_orca`, com o mesmo filamento. No `_orca`, olhar a tela no início: **não pode dar erro de comando** (o OrcaSlicer acrescenta `MINIMUM_CRUISE_RATIO` ao `SET_VELOCITY_LIMIT`).
- [ ] **Na impressora** Comparar as duas peças: primeira camada, paredes, os três furos (3,2 / 3,4 / 3,6) e o alojamento da porca.
- [ ] **Na impressora** Repetir com uma peça **com suporte**. No OrcaSlicer o suporte sai com 62% mais material: conferir se ainda solta fácil.
- [ ] **A** Instalar o OrcaSlicer e rodar `--fatiador orca`. Se o script não achar o programa, passar `--exe "caminho\orca-slicer.exe"` e anotar o caminho certo.
- [ ] **M+A** Decidir: o OrcaSlicer vira o fatiador por script do Windows, ou o Windows continua fatiando pela interface?

## 6. Fase 5 – registro da impressão (PR 12)
- [ ] **M+A** `uv run .claude/skills/registro-impressao/registrar_impressao.py --ultimas 5` – lista os últimos trabalhos da impressora.
- [ ] **M+A** Numa sessão nova do Claude Code, contar o resultado da impressão do item 5 ("imprimi o teste de furos M3, o furo de 3,4 ficou justo"). Esperado: a skill `registro-impressao` pergunta o que falta, cria a branch `peca/teste-furos-m3` e grava a entrada em `pecas/teste-furos-m3/README.md`, com os dados da impressora e do projeto.
- [ ] **M+A** Conferir que ela **pergunta** antes de levar a lição para uma skill (por exemplo, o diâmetro de furo M3 em `modelagem-3d`).

## 7. Decisões pendentes (Alexandre)
- [ ] **Folga Z do suporte no `0.08mm Detalhe Miniaturas`:** o preset está com 0,16; a regra e o `checklist_3mf.py` pedem pelo menos 0,24 em PLA. Qual vale? Se for 0,16, o limite do checklist muda; se for 0,24, o preset muda e é reexportado.
- [ ] **Troca de bico:** a regra passou de "autoteste e nivelamento" para "nivelamento automático obrigatório, autoteste completo opcional". Confirma ou reverte?
- [ ] **PETG MASTERPRINT no bico 0,2:** o preset tem flow 1,05 e PA 0,2 (a skill antiga dizia 0,95 e 0,025, "ainda não calibrado"). Os valores do preset são os calibrados?

## 8. Teste de ponta a ponta com uma peça de verdade
Depois dos itens acima, fazer uma peça real passar pelo fluxo inteiro, numa sessão nova:
- [ ] Pedir a peça (com medidas) → modelagem → prévia aprovada → `ficha.json`.
- [ ] Preparação pelo agente configurador a partir da ficha → `.3mf` com o checklist sem falhas.
- [ ] Fatiar e enviar para a lista (sem iniciar) → iniciar na tela.
- [ ] Contar o resultado → registro no README da peça → lição, se houver.

## Quando terminar
- Itens que falharam viram issue ou PR `fix/<assunto>`.
- Com tudo marcado, este arquivo pode ser apagado (o histórico do git guarda).
