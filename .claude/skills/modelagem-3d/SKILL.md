---
name: modelagem-3d
description: Projetar uma peça 3D do zero (a partir de medidas, desenho ou foto) para imprimir na K1 Max — pelo SolidCraft via MCP (peça mecânica), por script com manifold3d (peça orgânica) ou acompanhando quem modela no chat do próprio SolidCraft. Traz as regras de projeto (folgas, paredes, overhangs, furos, chanfros), a prévia para aprovação, a exportação e a ficha da peça que passa o trabalho para a preparação da impressão. Use quando o Alexandre ou o Marcelo pedirem para criar, desenhar ou modificar o projeto de uma peça, antes de preparar a impressão.
---

# Modelagem 3D para a K1 Max

O resultado desta skill é uma **peça aprovada por quem pediu**, salva em `pecas/<peca>/` com a fonte editável, o STL na orientação de impressão e a **ficha da peça** (`ficha.json`). Com a ficha, o agente `configurador-impressao-k1max` gera o `.3mf`.

## Três jeitos de modelar
| Jeito | Quando | Quem modela |
|---|---|---|
| **A. SolidCraft pelo MCP** | Peça mecânica ou prismática: suporte, caixa, adaptador, encaixe, furo, rosca. É o padrão | O agente, nesta conversa |
| **B. Script com `manifold3d`** | Forma orgânica ou gerada por regra (ramificações, treliça, superfície por campo de distância), que o CAD paramétrico não faz bem | O agente, por um script em `pecas/<peca>/` |
| **C. Chat do SolidCraft** | Quem pediu quer modelar dentro do app, conversando com o assistente de lá | A pessoa, no app; esta conversa entra na conferência |

Na dúvida entre A e B, pergunte. Se o MCP não estiver disponível, diga isso antes de trocar de jeito.

## Passos comuns aos três
1. **Requisitos** (pergunte o que faltar, em múltipla escolha):
   - função da peça, onde fica (calor, esforço, sol), material e bico;
   - **medidas reais** das peças com que ela encaixa (paquímetro), com a tolerância desejada. Medida estimada entra no projeto marcada como estimativa;
   - se der, uma foto com escala ou um desenho cotado.
2. **Orientação de impressão decidida antes de desenhar.** Modele com Z para cima nessa orientação, para o STL já sair como vai para a mesa.
3. **Pasta da peça:** `pecas/<nome-da-peca>/`, em branch `peca/<nome>` (veja `.claude/rules/fluxo-git.md` e `pecas/README.md`). Arquivos com o nome `<peca>_v<N>`.
4. **Modelar** (jeito A, B ou C, abaixo).
5. **Prévia e aprovação:** mostre as vistas e **espere a aprovação** antes de exportar a versão final.
6. **Conferir a malha exportada** e **gravar a ficha** (seção "Conferência e ficha da peça").
7. **Registrar** no `README.md` da peça: origem, o que foi decidido e, depois da impressão, o resultado e as lições.

## A. SolidCraft pelo MCP
CAD paramétrico, gratuito e de código aberto. O MCP roda **local**, sem conta nem chave. Documentação: https://docs.solidcraft.io/guide/mcp.html (lida em 22/11/2026).

**Antes de modelar:**
- Chame `skill_reference {"skill": "solidcraft-modeling"}`: é a referência oficial de comandos, planos e armadilhas da versão instalada. Para um comando novo, `list_commands {"filter": ...}` e `describe_command`; não chute argumentos.
- `inspect_design` para ver o que já existe.

**Dois servidores** (as ferramentas são as mesmas):
| Servidor | O que é | Quando usar |
|---|---|---|
| `solidcraft` | Sessão sem janela, dentro do próprio servidor | Padrão: modelar sozinho, do começo ao fim |
| `solidcraft-live` | Dirige o app aberto: a pessoa vê a peça aparecer | Quando quem pediu quer acompanhar ou mexer junto |

- No `solidcraft-live`, o projeto aberto no app pode ter trabalho não salvo: **nunca** use `new_design` ou `open` sem perguntar. Se o app não estiver aberto, toda chamada responde `no SolidCraft app is listening`: peça para abrir o app ou use o `solidcraft`.
- Os dois só gravam dentro de `pecas/` (é o `--allow-path` do registro). Passe **caminho absoluto** em `save` e `export`.

**Modelar:**
- **Parâmetros nomeados** para tudo que pode mudar (`espessura_parede`, `folga_encaixe`, `diametro_furo`…). Assim um ajuste depois da impressão de teste é só um `set_parameter`.
- Passos pequenos, em `batch`, conferindo com `measure` a cada etapa: compare **volume e caixa delimitadora com a sua conta**. `ok: true` sozinho não prova nada: um corte que não muda o volume errou o alvo (lição da peça de teste M3, 20/11/2026: chanfro, furos e porca bateram até 0,1 mm³).
- **Prévia:** `screenshot` nas vistas isométrica, frontal e superior.
- **Exportar** em mm, com caminho absoluto: `save` do `.sc` (fonte editável) e `export` de um STEP e um STL.

**Sem o MCP**, o `solidcraft-cli` também confere um projeto: `solidcraft-cli eval <peca>.sc` (corpos, volume, parâmetros e histórico em JSON) e `solidcraft-cli snapshot --in <peca>.sc --out previa.png --view iso`.

## B. Script com `manifold3d`
- O script fica em `pecas/<peca>/` e roda com `uv run pecas/<peca>/<script>.py`. Ele é a **fonte** da peça: os parâmetros ficam no topo, com nome e comentário, e a versão é um argumento.
- Não há histórico editável nem STEP: avise quem pediu antes de escolher este jeito.
- **Prévia:** `analisar_malha.py <stl> --render previa.png` (balanço em vermelho, contato com a mesa em azul).
- O script deve **parar com erro** quando a malha sai aberta, com mais de um corpo ou em balanço além do limite. Imprimir o aviso e exportar mesmo assim não serve.
- **Lições do suporte de headset** (malha por campo de distância e `level_set`):
  - a malha de marching cubes pode sair com volume negativo: inverta as faces (`faces[:, ::-1]`) e confira `is_volume`;
  - quase-contatos menores que a grade saem "beliscados" (um vértice dividido por duas folhas) e a malha abre: engrosse o campo em cerca de 0,1 mm ou desloque a grade de extração e tente de novo;
  - união suave de alcance largo cria películas dentro dos vazios e anéis nas emendas: use união de alcance curto nessas regiões;
  - vazio só a partir de 1,6 mm de largura; abaixo disso ele fecha ou vira fresta que o fatiador ignora;
  - limite de balanço aplicado **por membro**, na hora de gerar, e não só medido no fim.

## C. Chat do SolidCraft (a pessoa modela no app)
O painel de chat do SolidCraft conversa com o Claude Code da própria pessoa, mas numa **pasta vazia e sem acesso a arquivos**: ele não lê este repositório, nem o `AGENTS.md`, nem as skills (documentação: https://docs.solidcraft.io/guide/agent-chat.html, lida em 22/11/2026). O que ele aceita é um texto fixo de instruções.

1. **Uma vez por computador:** no SolidCraft, Preferences → AI → **Custom instructions**, cole o conteúdo de `regras-projeto-k1max.md` (nesta pasta). O limite é de 4000 caracteres e o arquivo tem cerca de 3100. Vale a partir do próximo chat.
   - Se mudar as regras de projeto desta skill, atualize também esse arquivo e avise para colar de novo.
2. **A pessoa modela no chat do app** e, no fim, salva o `.sc` e exporta STEP e STL em `pecas/<peca>/`.
3. **De volta ao Claude Code do repositório:** confira a malha e grave a ficha, como nos outros dois jeitos. As respostas da ficha (uso, material, bico, medidas críticas) vêm de quem modelou.
4. Para ajustar a peça daqui sem fechar o app, use o `solidcraft-live`.

## Conferência e ficha da peça
Da raiz do repositório, igual no Windows e no macOS:
```
uv run .claude/skills/creality-print-3mf/analisar_malha.py pecas/<peca>/<peca>_v1.stl --render pecas/<peca>/analise_v1.png
```
- Tem de sair **Aprovada**: fechada, cabe na mesa, apoiada. Confira as dimensões contra o CAD e olhe o render.
- Malha aberta se corrige no CAD ou no script, nunca com reparo automático.
- O script não mede espessura de parede nem folgas: confira essas no CAD (`measure`, `body_topology`).

Depois da aprovação de quem pediu, grave a ficha:
```
uv run .claude/skills/creality-print-3mf/analisar_malha.py pecas/<peca>/<peca>_v1.stl --gravar-ficha pecas/<peca>/ficha.json --peca <peca> --versao 1 --rota solidcraft --fonte <peca>_v1.sc --uso "para que serve e onde fica" --material PLA --bico 0.4 --orientacao "como exportada, face maior na mesa" --critica "furo passante M3 = 3,4 mm"
```
- `--rota`: `solidcraft` (jeitos A e C), `script` (B) ou `terceiros` (modelo baixado).
- `--critica` pode repetir: são as medidas que precisam sair certas (encaixes, furos, folgas).
- A ficha guarda também o que foi medido (dimensões, volume, contato, balanço). O `checklist_3mf.py --ficha` usa isso para conferir escala, material e bico do projeto.

**Passar para a preparação:** chame o agente `configurador-impressao-k1max` informando o caminho da ficha. O que não couber na ficha (por exemplo, "os elos não podem levar brim") vai no pedido.

## Instalação e registro do MCP
- **Instalar o SolidCraft** (uma vez por computador): macOS, `brew install --cask tangency-labs/tap/solidcraft`; Windows, o instalador de https://solidcraft.io/download/. Os dois põem o `solidcraft-cli` no PATH.
  - Windows com instalador antigo: se o terminal não achar `solidcraft-cli`, ele fica em `C:\Program Files\SolidCraft\solidcraft-cli.exe`; reinstale ou acrescente essa pasta ao PATH.
- **Registro:** o `.mcp.json` na raiz do repositório já declara os dois servidores, iguais nos dois sistemas. Na primeira vez, o Claude Code pede para aprovar os servidores do projeto.
  - Não use `solidcraft-cli mcp setup`: ele reescreve o `~/.claude.json` inteiro.
  - Quem já tinha registrado `solidcraft` e `solidcraft-live` à mão continua valendo: o registro local tem prioridade sobre o `.mcp.json`.
- **Modo ao vivo:** no app, ligue Preferences → Assistant → "Let AI agents connect". A porta padrão é **27878**; se estiver ocupada, o app usa a seguinte e grava o número em `control/current.port`, na pasta de dados dele. Nesse caso, ajuste a porta no registro local. (O `mcp setup --live` sugere 7878, que não funcionou no Mac do Marcelo em 20/11/2026.)
- Estado em 22/11/2026: Mac do Marcelo com SolidCraft 0.30.1 e os dois servidores funcionando. **No PC do Alexandre o `.mcp.json` ainda não foi testado.**

## Regras de projeto (bico 0,4; no 0,2, divida larguras por 2)
Valores de partida. Para encaixe crítico, **ofereça imprimir um corpo de prova** pequeno antes da peça inteira (exemplo: `pecas/teste-furos-m3/`).

| Item | Valor |
|---|---|
| Parede mínima | 0,8 mm (2 linhas); estrutural ≥ 1,6 mm |
| Detalhe/relevo mínimo | 0,4 mm de largura; texto em relevo ou baixo-relevo ≥ 0,6 mm de altura |
| Vazio ou fresta | ≥ 1,6 mm de largura |
| Overhang sem suporte | ≤ 45° da vertical. Acima disso, redesenhe (chanfro, divisão da peça) antes de recorrer a suporte |
| Ponte | curta; prefira < 10 mm e confirme no fatiador |
| Folga deslizante | 0,2–0,3 mm por lado |
| Folga justa / pressão | 0,1–0,15 mm por lado |
| Print-in-place (projeto nosso) | ≥ 0,3 mm |
| Furo vertical | sai menor: some 0,1–0,2 mm no diâmetro (além de `xy_hole_compensation` no fatiador) |
| Furo horizontal | formato de gota (teardrop) ou topo chanfrado, para não precisar de suporte |
| Parafuso M3 passante | Ø 3,4 mm |
| Porca M3 | 5,5 mm entre faces + folga 0,1–0,2 |
| Inserto roscado | use a medida do fabricante do inserto (pergunte qual é) |

**Print-in-place:**
- Em projeto nosso, comece com 0,3 mm de folga. Abaixo de 0,15 mm a tendência é grudar.
- Modelo de terceiros já testado pelo autor pode ter menos: o tubarão articulado funcionou com folgas de 0,116 a 0,15 mm, a 100% e sem compensação XY. Nesse caso **não mude a escala** nem as folgas.
- Partes a menos de cerca de 1,5 mm uma da outra na 1ª camada grudam com brim: anote isso no pedido para o configurador (no tubarão, os elos a 1,15 mm ficaram sem brim).

**Arestas:**
- **Aresta da base:** chanfro de 0,4–0,5 mm. Compensa o pé de elefante sem depender de `elefant_foot_compensation` (que fica 0 por causa do brim encostado).
- **Arestas viradas para baixo:** chanfro de 45°, não filete; filete vira balanço.
- **Arestas verticais e de cima:** filete à vontade.

**Resistência e orientação:**
- A peça é mais fraca entre camadas. Desenhe pensando na orientação: a carga principal deve correr **ao longo** das camadas, não separando-as.
- Base plana e larga na mesa. Se a peça não tem uma face plana, crie uma ou divida a peça.
- Peça alta com pouca área apoiada pede brim: anote no pedido para o configurador.
- Peça maior que 300 × 300 × 300 (incluindo brim) → divida com encaixe (cavilha ou macho-fêmea) e pergunte onde cortar.

## O que não fazer
- Não "consertar" malha com repair automático. Se o export sair aberto, corrija no CAD ou no script.
- Não exportar a versão final sem aprovação da prévia.
- Não afirmar que uma medida "vai encaixar" sem ter a medida real da peça par.
- Não gravar a ficha de uma malha reprovada (o script recusa).
