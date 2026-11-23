# Corpo de prova de furos M3

- **Origem:** projeto nosso (Marcelo), modelado no SolidCraft pelo MCP em 20/11/2026 para testar a skill `modelagem-3d`.
- **Para que serve:** escolher o diâmetro do furo passante M3 e conferir o alojamento da porca no filamento em uso, antes de uma peça com parafusos.
- **Status:** modelado e conferido; **ainda não impresso**.

## Arquivos
| Arquivo | O que é |
|---|---|
| `teste_furos_m3_v1.sc` | Fonte editável do SolidCraft |
| `teste_furos_m3_v1.step`, `teste_furos_m3_v1.stl` | Exportações em mm, na orientação de impressão |
| `ficha.json` | Ficha da peça para a preparação da impressão (gravada pelo `analisar_malha.py`) |
| `previa_v1_iso.png`, `previa_v1_topo.png` | Prévias do SolidCraft |
| `analise_v1.png` | Análise da malha (contato com a mesa em azul; não há balanço) |

## Projeto
- Bloco de 40 × 20 × 8 mm, com chanfro de 0,4 mm na base.
- Três furos passantes na vertical, a 12 mm um do outro: **3,2**, **3,4** e **3,6** mm.
- Um alojamento de porca M3 em cima: 5,7 mm entre faces, 2,6 mm de profundidade.
- Parâmetros: `L`, `W`, `H`, `passo`, `porca_af`, `porca_prof`, `chanfro_base`.

## Conferência
- Volume no SolidCraft: 6122,56 mm³; no STL: 6,123 cm³.
- Malha fechada, 1 corpo, 725,4 mm² de contato com a mesa, sem balanço.

## Configuração aprovada
_A registrar depois da impressão._

## Resultado e lições
_A registrar: qual furo deixou o parafuso M3 passar justo e se a porca entrou._
