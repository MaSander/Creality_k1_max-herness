---
name: modelagem-3d
description: Projetar uma peça 3D do zero (a partir de medidas, desenho ou foto) para imprimir na K1 Max, usando o SolidCraft via MCP — regras de projeto (folgas, paredes, overhangs, furos, chanfros), prévia para aprovação e exportação STEP/STL. Use quando o Alexandre ou o Marcelo pedirem para criar, desenhar ou modificar o projeto de uma peça, antes de preparar a impressão.
---

# Modelagem 3D para a K1 Max

O resultado desta skill é uma **peça aprovada por quem pediu**, exportada em STEP + STL. Depois, o agente `configurador-impressao-k1max` gera o `.3mf`.

## Ferramenta: SolidCraft (MCP)
CAD paramétrico, gratuito e open-source (Tangency Labs), o mesmo que o Alexandre usa. O MCP roda **local** (stdio), sem conta nem chave. Documentação lida em 19/11/2026: https://solidcraft.io/mcp/ e https://docs.solidcraft.io/guide/mcp.html.

**Instalação (uma vez por computador):**
- macOS: `brew install --cask tangency-labs/tap/solidcraft` (instala o app e o `solidcraft-cli`).
- Windows: baixe o app e o pacote de CLI em https://solidcraft.io/download/.
- Conectar ao Claude Code: `claude mcp add solidcraft -- solidcraft-cli mcp --headless --allow-path <pasta de trabalho>`. Prefira isso ao `solidcraft-cli mcp setup`, que reescreve o `~/.claude.json` inteiro.
- Mac do Marcelo: SolidCraft 0.30.1 instalado em 19/11/2026 (`/Applications/SolidCraft.app`, `/opt/homebrew/bin/solidcraft-cli`).
- Para ver a peça ao vivo enquanto modelo: abra o app com "Preferences → Assistant → Let AI agents connect" e registre `claude mcp add solidcraft-live -- solidcraft-cli mcp --connect 127.0.0.1:27878 --allow-path <pasta de trabalho>`.
  - A porta padrão do app é **27878** (confira com `lsof -nP -iTCP -sTCP:LISTEN | grep SolidCraf`). O `mcp setup --live` sugere 7878, que não funcionou no Mac do Marcelo em 20/11/2026. Não foi preciso token.
  - No modo ao vivo, o projeto aberto no app pode ter trabalho não salvo: **nunca** use `new_design` ou `open` sem perguntar.
- Skills oficiais (`solidcraft-modeling`, `-editing`, `-checking`, `-mechanisms`, `-reporting`) ficam no GitHub do projeto e podem ser copiadas para `~/.claude/skills/`.

**Ferramentas principais:** `list_commands` e `describe_command` (consulte antes de usar um comando novo, não chute argumentos), `execute`, `batch` (com rollback), `set_parameter`, `inspect_design`, `measure`, `body_topology`, `screenshot`, `export`, `save`.

Se o MCP não estiver disponível, diga isso e pergunte se pode modelar com `manifold3d` (script rodado com `uv run`) (só para peças simples, sem histórico editável).

## Fluxo
1. **Requisitos** (pergunte o que faltar, em múltipla escolha):
   - função da peça, onde fica (calor, esforço, sol), material e bico;
   - **medidas reais** das peças com que ela encaixa (paquímetro), com a tolerância desejada;
   - se der, uma foto com escala ou um desenho cotado.
2. **Parâmetros nomeados** para tudo que pode mudar (`espessura_parede`, `folga_encaixe`, `diametro_furo`…). Assim um ajuste depois da impressão de teste é só um `set_parameter`.
3. **Modelar** em passos pequenos, conferindo com `inspect_design` e `measure` (caixa delimitadora e volume) a cada feature importante.
4. **Prévia:** `screenshot` em vistas isométrica, frontal e superior. Mostre e **espere aprovação** antes de exportar.
5. **Exportar** em mm: o `.sc` (fonte editável), um STEP e um STL. Nome: `<peca>_v<N>`.
6. **Conferir a malha** com `uv run python` + trimesh: dimensões iguais às do CAD, `is_watertight`, `is_volume`, um corpo só (ou os corpos esperados).
   - O STL do SolidCraft vem com os vértices soltos por triângulo: carregue com `trimesh.load(...)` (que junta os vértices) antes de testar se está fechado. Com `process=False` ele parece aberto e com 1 corpo por triângulo.
   - Confira o volume de cada etapa no `measure` contra a sua conta (lição da peça de teste M3, 20/11/2026: chanfro, furos e porca bateram até 0,1 mm³).
7. **Passar para o configurador** com: material, bico, orientação pensada no projeto e quais medidas são críticas.

## Regras de projeto (bico 0,4; no 0,2, divida larguras por 2)
Valores de partida. Para encaixe crítico, **ofereça imprimir um corpo de prova** pequeno antes da peça inteira.

| Item | Valor |
|---|---|
| Parede mínima | 0,8 mm (2 linhas); estrutural ≥ 1,6 mm |
| Detalhe/relevo mínimo | 0,4 mm de largura; texto em relevo ou baixo-relevo ≥ 0,6 mm de altura |
| Overhang sem suporte | ≤ 45° da vertical. Acima disso, redesenhe (chanfro, divisão da peça) antes de recorrer a suporte |
| Ponte | curta; prefira < 10 mm e confirme no fatiador |
| Folga deslizante | 0,2–0,3 mm por lado |
| Folga justa / pressão | 0,1–0,15 mm por lado |
| Print-in-place | ≥ 0,3 mm; abaixo de 0,15 mm gruda (lição da casa) |
| Furo vertical | sai menor: some 0,1–0,2 mm no diâmetro (além de `xy_hole_compensation` no fatiador) |
| Furo horizontal | formato de gota (teardrop) ou topo chanfrado, para não precisar de suporte |
| Parafuso M3 passante | Ø 3,4 mm |
| Porca M3 | 5,5 mm entre faces + folga 0,1–0,2 |
| Inserto roscado | use a medida do fabricante do inserto (pergunte qual é) |

**Arestas:**
- **Aresta da base:** chanfro de 0,4–0,5 mm. Compensa o pé de elefante sem depender de `elefant_foot_compensation` (que fica 0 por causa do brim encostado).
- **Arestas viradas para baixo:** chanfro de 45°, não filete; filete vira balanço.
- **Arestas verticais e de cima:** filete à vontade.

**Resistência e orientação:**
- A peça é mais fraca entre camadas. Desenhe pensando na orientação: a carga principal deve correr **ao longo** das camadas, não separando-as.
- Base plana e larga na mesa. Se a peça não tem uma face plana, crie uma ou divida a peça.
- Peça maior que 300 × 300 × 300 (incluindo brim) → divida com encaixe (cavilha ou macho-fêmea) e pergunte onde cortar.

## O que não fazer
- Não "consertar" malha com repair automático. Se o export sair aberto, corrija no CAD.
- Não exportar sem aprovação da prévia.
- Não afirmar que uma medida "vai encaixar" sem ter a medida real da peça par.
