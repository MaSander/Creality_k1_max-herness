# Tubarão articulado (Articulated Skeleton Shark)

| | |
|---|---|
| Modelo | "Articulated Skeleton Shark", de **3DPrintyi** no MakerWorld (perfil "X1C / Single Color 0.16mm layer, 3 walls, 15% infill") |
| Licença | Standard Digital File License: imprimir para uso próprio, **sem redistribuir os arquivos**. Por isso os `.3mf` ficam só em `local/` (ignorada pelo git). Se faltarem, baixe de novo no MakerWorld |
| Quem imprimiu | Marcelo, na K1 Max |
| Resultado | **Aprovado**: "ficou muito boa" (21/11/2026) |

## Arquivos (locais, fora do git)
- `local/ArticulatedSkeletonShark_BambuStudioX1C.3mf`: original do Bambu Studio.
- `local/TubaraoArticulado_PLA_bico0.4.3mf`: projeto do Creality Print aprovado. Para refazer o G-code:
  `uv run .claude/skills/creality-print-3mf/fatiar_3mf.py pecas/tubarao-articulado/local/TubaraoArticulado_PLA_bico0.4.3mf --nome TubaraoArticulado --permitir-versao-nova`
  (a flag só é necessária enquanto o Mac tiver o Creality Print 7.2 e o projeto for da 7.3).

## Peças
- `Body.stl`: esqueleto print-in-place, com 16 elos e as juntas impressas já montadas. Mede 85 × 170 × 37,8 mm.
- `Head_Easy_Press_In.stl`: cabeça encaixada por pressão depois da impressão. Mede 39 × 36 × 37 mm.

## Configuração aprovada
- **Equipamento:** K1 Max com bico 0,4, PLA FLEXYGREEN no perfil calibrado (210/215 °C, mesa 50, flow 0,98, PA 0,052) e High Temp Plate.
- **Processo:** 0.16mm Standard modificado, com camada de 0,16 e primeira camada de 0,2.
  - 3 paredes, topo 5 e base 4, 15% gyroid, costura atrás.
  - Parede externa a 80 mm/s, aceleração 2500.
- **Sem suporte**, como pede o autor: suporte soldaria as juntas.
- **Brim:**
  - Corpo sem brim: os elos ficam a 1,15 mm um do outro na 1ª camada, e o brim os grudaria.
  - Cabeça com brim de 3 mm por objeto (gap 0, compensação de pé de elefante 0), porque ela é alta e tem pouca área apoiada na mesa.
- **Escala 100%**: o autor avisa que, se diminuir, as juntas param de funcionar.
- Tempo estimado de 4 h 12 min e 41 g de filamento.

## Lições desta impressão
- **Folgas das juntas** de 0,116 a 0,15 mm (pares 4-15, 14-15, 6-7 e 7-8) ficaram como o autor fez, sem compensação XY, e funcionaram.
- **Filamento úmido** (casa muito úmida, carretel exposto por alguns dias): deu fiapo tipo teia e estalos no bico. Seque antes de imprimir, a 45–50 °C por 4–6 h, e guarde com sílica.
- **Nó no carretel** fez a extrusão parar. A engrenagem roeu o filamento e formou um calombo, e foi preciso abrir a extrusora para limpar.
  - Prenda sempre a ponta do fio no furo do carretel.
  - Se a impressão travar, use **pausar**, não "parar".
  - **Nunca recolha filamento com o bico frio**: a engrenagem patina e rói o fio ("tec, tec" com o tubo pulando).
- **Modo de velocidade rápido** na tela: não usar nesta peça. Ele passa por cima do limite de fluxo do filamento e da desaceleração para resfriamento, e as juntas justas podem colar.
