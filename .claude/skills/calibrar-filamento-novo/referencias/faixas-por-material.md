# Faixas iniciais por material – K1 Max

São pontos de partida para montar as faixas dos testes, não valores finais. **A faixa do carretel manda**: se ela for diferente daqui, use a do carretel e cubra os dois lados dela.

Valores da casa (calibrados) para comparar: veja a tabela de `k1max-config-impressao`.

## Secagem (antes de calibrar)
| Material | Temperatura | Tempo | Observação |
|---|---|---|---|
| PLA / PLA-Silk | 45–50 °C | 4–6 h | PLA novo e lacrado costuma estar ok; seque se estalar |
| PETG | 60–65 °C | 4–6 h | absorve umidade rápido; fiapo excessivo é o sinal clássico |
| ABS / ASA | 75–80 °C | 4 h | |
| TPU | 50–55 °C | 4–6 h | quase sempre precisa |
| PA / PA-CF (nylon) | 70–80 °C | 8–12 h | imprima direto da caixa secadora |
| PC | 80 °C | 6–8 h | |

Sinais de umidade: estalos no bico, bolhinhas ou superfície áspera, fiapo que não some com retração, peça quebradiça.

## Bico 0,4
| | PLA | PLA-Silk | PETG | ABS / ASA | TPU 95A |
|---|---|---|---|---|---|
| Torre de temperatura | 230 → 190 | 230 → 200 | 255 → 220 | 270 → 240 | 240 → 210 |
| Mesa (High Temp Plate) | 50–60 | 50–60 | 70–80 | 90–100 | 35–50 |
| Tampa | **aberta** | **aberta** | fechada ou entreaberta | **fechada** | aberta |
| Ventoinha | 100% | 100% | 30–60% (casa: 40–90) | 0–30% | 50–100% |
| PA (faixa do teste) | 0 → 0,10 | 0 → 0,10 | 0 → 0,10 | 0 → 0,10 | 0 → 0,10 |
| PA esperado | 0,03–0,06 | 0,03–0,06 | 0,02–0,06 | 0,02–0,05 | 0–0,05 |
| Fluxo máximo (faixa) | 10 → 30 | 5 → 20 | 8 → 22 | 10 → 25 | 1 → 6 |
| Fluxo máximo esperado | 18–24 | 8–14 | 12–18 | 15–22 | 2–4 |
| Retração (faixa) | 0,2 → 1,0 | 0,2 → 1,0 | 0,4 → 1,4 | 0,2 → 1,0 | 0 → 0,8 |

## Bico 0,2
- Use as mesmas temperaturas do 0,4 como ponto de partida (o fluxo é bem menor, então às vezes dá para descer 5 °C).
- **PA bem mais alto:** teste de 0 a 0,40. Referências Creality: Hyper PLA 0,24; CR-PETG 0,29. O PLA FLEXYGREEN da casa ficou em 0,20.
- **Fluxo máximo baixo:** teste de 1 a 8. Referências: Creality 3 (PLA) e 2,5 (PETG); o PLA FLEXYGREEN da casa passou até 5 sem falhar.
- **Nada com partículas** (CF, GF, glitter, mármore, madeira, glow): entope o 0,2.
- As camadas grudam menos entre si do que no 0,4.

## Materiais com particularidades
- **TPU:** imprima devagar (fluxo máximo baixo já limita). Retração mínima ou zero. Pule o flow fino se o grosso já ficou bom; TPU perdoa pouco a retração e muito o flow.
- **CF / GF (PLA-CF, PETG-CF, PA-CF):** abrasivos. Confirme que o bico é de aço endurecido antes de usar e nunca no 0,2.
- **ABS / ASA:** tampa fechada, câmara aquecida antes de imprimir (deixe a mesa a 100 °C por uns 10 min), ventoinha lateral desligada ou baixa. Cheiro forte: ambiente ventilado.
- **PLA-Silk:** fica mais brilhante com temperatura mais alta e velocidade mais baixa; o fluxo máximo cai bastante.

## Sintoma → teste a revisitar
| Sintoma | Causa provável | Teste |
|---|---|---|
| Muito fiapo | umidade, temperatura alta, retração | secagem → temperatura → retração |
| Estalos, bolhas, superfície áspera | umidade | secagem |
| Camadas descolando, peça frágil | temperatura baixa, ventoinha alta | temperatura (teste de quebra) |
| Paredes com vãos, linhas finas | flow baixo, velocidade acima do limite, bico entupido | flow → fluxo máximo |
| Topo com sobra, peça "gorda" | flow alto | flow |
| Cantos com bolha ou arredondados | PA baixo | pressure advance |
| Peça solta da mesa, cantos levantando | mesa suja, temperatura da mesa, Z-offset | mesa / adesão |
| Overhang caído ou enrolado | pouca ventoinha, temperatura alta | temperatura |
| "Click" na extrusora, entupimento | retração demais, temperatura baixa, fluxo acima do limite | retração → temperatura → fluxo máximo |
