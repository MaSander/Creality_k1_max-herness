# Suporte de parede para headset (Logitech PRO X 2)

- **Origem:** projeto nosso (Marcelo), gerado por código no estilo generative design (membros ramificados, como ossos e tendões). Fixação na parede com fita VHB.
- **Status:** em projeto. A configuração aprovada e o resultado da impressão ainda não foram registrados.

## Arquivos
| Arquivo | O que é |
|---|---|
| `gerar_suporte_v13.py` | Gera a v13 (`manifold3d`, level set): berço oval solto da parede (raio 57, para o arco do fone de 110 x 40 mm por dentro) sobre três pés separados. Uso: `uv run pecas/suporte-headset-parede/gerar_suporte_v13.py` |
| `gerar_suporte.py` | Gerador da v12 (placa de parede inteira). Uso: `uv run pecas/suporte-headset-parede/gerar_suporte.py --versao <n>` |
| `previa.py` | Renderiza as prévias PNG |
| `suporte_headset_v13.stl` | Versão atual. A ponta de trás do berço fica em balanço: imprimir com suporte |
| `local/` (fora do git) | v1 a v12 e o projeto `suporte_headset_v6.3mf`, com backup no Drive pessoal do Marcelo |
| `previa_v*.png`, `opcoes_berco_v10.png` | Prévias de cada versão |

## Configuração aprovada
_A registrar depois da impressão._

## Resultado e lições
_A registrar._
