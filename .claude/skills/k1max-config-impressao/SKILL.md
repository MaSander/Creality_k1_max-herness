---
name: k1max-config-impressao
description: Perfis, regras e receitas de configuração de impressão para a Creality K1 Max do Alexandre e do Marcelo (PLA FLEXYGREEN, PETG MASTERPRINT, bicos 0,4 e 0,2). Use ao preparar, revisar ou ajustar qualquer impressão deles.
---

# Configuração de impressão – K1 Max do Alexandre e do Marcelo

## Equipamento
- **Impressora:** Creality K1 Max, fechada, mesa 300 × 300 × 300, centro da mesa em (150, 150).
- **Fatiador:** Creality Print 7.3 (base OrcaSlicer), interface em inglês, modo Expert.
- **Mesa:** `curr_bed_type = High Temp Plate` (usa `hot_plate_temp`).
- **Bicos:**
  - **0,4**: padrão, perfil de sistema `Creality K1 Max 0.4 nozzle`.
  - **0,2**: perfil de usuário `Creality K1 Max 0.2 nozzle`, importado do pacote da Creality. Herda do 0,4.
  - 0,6 e 0,8 existem como perfis de sistema, mas não são usados.
- **Modelagem:** o Alexandre projeta no Fusion 360 e no SolidCraft; o Marcelo usa o SolidCraft via MCP (skill `modelagem-3d`).
- **Computadores:** veja "Ambientes por pessoa" no `AGENTS.md` (Windows do Alexandre, Mac do Marcelo).

## Perfis de filamento e de processo (não alterar sem pedir)
**A fonte dos valores são os presets do Creality Print do Alexandre**, exportados para `.claude/perfis/creality-print/` (decisão de 22/11/2026). A tabela abaixo é gerada deles: não edite à mão. Como sincronizar: `.claude/perfis/COMO-IMPORTAR.md`.

<!-- tabela-perfis:inicio -->
_Gerado por `sincronizar_perfis.py tabela --gravar` a partir de `.claude/perfis/creality-print/`. Não edite à mão. **Negrito** = valor definido no preset; o resto vem do perfil de fábrica (lido do Creality Print deste computador, pasta `7.0`)._

**Filamentos**

| | PETG MASTERPRINT @Creality K1 Max 0.2 nozzle | PETG MASTERPRINT | PLA FLEXYGREEN @Creality K1 Max 0.2 nozzle | PLA FLEXYGREEN |
|---|---|---|---|---|
| Herda de | Generic PETG @Creality K1 Max 0.4 nozzle | Generic PETG @Creality K1 Max 0.4 nozzle | Generic PLA @Creality K1 Max 0.4 nozzle | Generic PLA @Creality K1 Max 0.4 nozzle |
| Bico / 1ª camada (°C) | **220** / **230** | **220** / **230** | **210** / **215** | **210** / **215** |
| Mesa lisa / 1ª camada (°C) | **75** / **80** | **80** / **80** | 50 / 50 | 50 / 50 |
| Mesa texturizada / 1ª camada (°C) | **75** / **75** | **80** / **75** | 50 / 50 | 50 / 50 |
| Flow ratio | **1.05** | 0.95 | **1.03** | 0.98 |
| Pressure advance | **0.2** | **0.025** | **0.2** | **0.052** |
| Retração (mm) / veloc. / desretração | **0.7** / da impressora / da impressora | **0.7** / da impressora / da impressora | **0.4** / **40** / **40** | **0.4** / **40** / **40** |
| Fluxo máximo (mm³/s) | **2.5** | **20** | **7** | **20** |
| Ventoinha mín. / máx. (%) | 40 / 90 | **30** / **50** | 100 / 100 | 100 / 100 |
| Ventoinha lateral (%) | 0 | 0 | 80 | 80 |
| Tempo mínimo de camada (s) | **8** | **8** | **0** | **0** |

**Processos**

| | 0.08mm Detalhe Miniaturas @Creality K1 Max 0.2 nozzle | 0.10mm Standard @Creality K1 Max 0.2 nozzle-1 | 0.20mm PLA FLEXY 0.07 tolerancia furo | PEÇA DELICADA M5 |
|---|---|---|---|---|
| Herda de | 0.08mm Standard @Creality K1 Max 0.4 nozzle | 0.08mm Standard @Creality K1 Max 0.4 nozzle | 0.20mm Standard @Creality K1 Max 0.4 nozzle | 0.08mm Standard @Creality K1 Max 0.4 nozzle |
| Camada / 1ª camada (mm) | 0.08 / **0.12** | **0.1** / **0.14** | 0.2 / 0.2 | **0.1** / 0.2 |
| Largura de linha (mm) | **0.22** | **0.22** | 0.42 | 0.42 |
| Paredes / topo / base | **4** / **8** / **6** | **4** / **7** / **5** | 2 / 5 / 3 | **6** / **5** / 7 |
| Preenchimento | 15% / **gyroid** | 15% / grid | 15% / grid | **100%** / grid |
| Parede externa / interna (mm/s) | **60** / **100** | **110** / **130** | 200 / 300 | **40** / **50** |
| Suporte | **1** / **tree(auto)** / **organic** | 0 / normal(auto) / default | **1** / normal(auto) / default | **1** / normal(auto) / **snug** |
| Folga Z do suporte em cima / embaixo (mm) | **0.16** / **0.16** | 0.2 / 0.2 | **0.1** / **0.1** | 0.2 / 0.2 |
| Brim: tipo / largura / gap | **outer_only** / **3** / **0** | auto_brim / 5 / 0.1 | **brim_ears** / 5 / **0** | auto_brim / 5 / 0.1 |
| Compensação de pé de elefante | **0** | 0.15 | 0.15 | 0.15 |
| Compensação XY furo / contorno | 0 / 0 | 0 / 0 | **0.07** / 0 | 0 / 0 |

<!-- tabela-perfis:fim -->

Notas:
- **Filamento que não está na tabela** (cor ou marca nova): veja `filamentos/<slug>/perfil.md`. Trocar de carretel da **mesma marca e modelo** usa o perfil que já existe, sem calibrar de novo.
- **Projeto antigo pode ter valores diferentes do preset atual** (os `.3mf` de `.claude/referencias/` têm tempo mínimo de camada 8, e o do bico 0,2 tem flow 1.035 e fluxo máximo 5). O `checklist_3mf.py` avisa. Num projeto novo, valem os do preset.
- **Folga Z do suporte no `0.08mm Detalhe Miniaturas`: pendente de decisão.** O preset está com 0,16, e a regra da casa (e o `checklist_3mf.py`) pede pelo menos 0,24 em PLA para o suporte soltar. Enquanto o Alexandre não decidir, use 0,24 nos projetos em PLA e diga isso na entrega.
- `enable_filament_dynamic_map = 0`, então `material_flow_temp_graph` não tem efeito.
- Mudar `slow_down_layer_time` (tempo mínimo de camada) numa peça pequena é uma mudança de filamento. Avise ou pergunte antes.
- **Limite de velocidade do bico 0,2:** velocidade ≤ fluxo máximo ÷ (largura × camada). Exemplo: 0,22 × 0,08 a 150 mm/s dá 2,6 mm³/s.
- O `0.10mm Standard @Creality K1 Max 0.2 nozzle-1` segue os valores da wiki da Creality para o bico 0,2 (velocidades e acelerações estão no preset).

## Regras da casa (definidas pelo Alexandre, valem para os dois)
1. Não mexer em filamento sem pedir.
2. O brim encosta na peça só com **gap 0 e compensação de pé de elefante 0**.
   - Exceção: em peças print-in-place com folga pequena no chão, a compensação evita que a 1ª camada grude. Explique a troca e deixe quem pediu decidir.
3. Perguntar sobre qualquer melhoria (espessura, folga, material) antes de aplicar.
4. Entregar o .3mf pronto, salvar na pasta de entrega de quem pediu (`C:\Users\alemg\Downloads` no PC do Alexandre, `~/Downloads` no Mac do Marcelo) e mandar o checklist.
5. PLA com a tampa aberta.
6. Não usar repair automático de malha.

## Receitas por tipo de peça

### Miniaturas e bonecos (maquete 1:25 da esteira de esqui)
- **Escala:** pela altura do corpo. Pessoa agachada: cerca de 1,50 m, o que dá **60 mm** em 1:25. Nunca pela maior dimensão (bastões abertos enganam).
- **Bico 0,2** com o processo Detalhe Miniaturas, ou bico 0,4 com camada 0,12, 3 paredes e linha externa 0,4.
- **Suporte Organic**, configurado para soltar fácil:
  - `support_top_z_distance` e `support_bottom_z_distance` = **0,24 mm**: 2 camadas de 0,12 ou 3 camadas de 0,08. Nunca menos que 0,24 em PLA, mesmo com o bico 0,2 (0,16 é apertado demais);
  - `support_interface_top_layers` = 0 e `support_interface_bottom_layers` = 0. A interface inferior solda nos galhos que pousam no próprio boneco;
  - `support_object_xy_distance` 0,6 e `support_xy_overrides_z` = z_overrides_xy;
  - `support_threshold_angle` 40;
  - ponta do galho 0,6–0,8 e galho Organic de 2.
- **Erro anterior:** Tree Slim com XY 0,35, interface inferior 2 e 2 paredes nos galhos colou tanto que ele teve que cortar os suportes.
- **Organic não funciona com altura de camada variável.** Se o projeto tiver `Metadata/layer_heights_profile.txt`, remova o arquivo ou use Tree Slim.
- **Partes finas:**
  - esquis e prancha com cerca de 0,7 mm ficam frágeis; ofereça dobrar para cerca de 1,5 mm, crescendo só por baixo;
  - bastões finos (cerca de 0,5 mm): remova e faça furos de Ø1,0 × 5 mm nas mãos para arame.
- **Base:** aplaine ou preencha a curvatura (camber) da prancha para aumentar o contato com a mesa (de 150 para cerca de 670 mm²).
- **Bloqueador de suporte** embaixo dos bicos da prancha e das pontas dos esquis. Sem ele, saem suportes baixinhos (0,3 a 2 mm), difíceis de tirar, e os bicos sobem devagar (10 a 20°), então imprimem bem sem apoio.
- **Antes de entregar:** estime onde vai ter suporte (faces com inclinação abaixo do limite de 40°, agrupadas por região) e diga onde ele fica. No snowboarder, o bloco maior ficou embaixo do quadril agachado, com cerca de 170 mm².
- **Na hora de tirar o suporte:** espere esfriar totalmente, comece pelos galhos de fora, gire em vez de puxar e use alicate de bico fino ou pinça no bloco maior.
- **Projetos de referência:**
  - ✅ **`Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf`: impresso em 20/11/2026 e aprovado ("ficou perfeito").** É o ponto de partida para os próximos bonecos com bico 0,4. A receita está na tabela abaixo.
  - `Snowboarder_1-25_PLA_bico_0.2_v5.3mf`: a mesma peça para o bico 0,2 (Detalhe Miniaturas, PLA 0,2 calibrado). Ainda não foi impresso, porque o bico 0,2 entupiu.

#### Receita aprovada: miniatura com bico 0,4 (snowboarder, 20/11/2026)
| Grupo | Valores |
|---|---|
| Impressora | `Creality K1 Max 0.4 nozzle` de fábrica (camada 0,08–0,3, retração 40 mm/s, z-hop Auto Lift), mesa High Temp Plate |
| Filamento | PLA FLEXYGREEN com a calibração do 0,4: 210/215 °C, mesa 50, flow 0.98, PA 0.052, retração 0.4, fluxo máximo 20, **slow_down 8** |
| Camada | **0,08**, 1ª camada 0,12 (`print_settings_id` = 0.08mm Standard @Creality K1 Max 0.4 nozzle, modificado) |
| Linhas | parede externa **0,40**; geral, topo e sólido 0,42; interna e esparsa 0,45; suporte 0,42; 1ª camada 0,5 |
| Paredes e preenchimento | 4 paredes, topo 8, base 6, Arachne, gyroid 15% |
| Velocidade | externa 60, interna 100, infill 120, sólido 120, topo 80, 1ª camada 18, suporte 100, interface 60 |
| Aceleração e jerk | 3000 nas paredes, 2000 na 1ª camada e no topo, aceleração para desaceleração 75%, jerk 3 em tudo (veio do perfil do 0,2 e deu certo no 0,4) |
| Suporte | tree(auto) Organic, limite de 40°, Z topo e base **0,24**, sem interface, XY 0,6 com z_overrides_xy, ponta 0,8, galho 2, independent off |
| Bloqueadores | caixas embaixo dos bicos da prancha (até 3,6 mm de altura) |
| Brim | só por fora, 3 mm, gap 0, compensação de pé de elefante 0 |
| Costura | atrás (back), reduce_crossing_wall ligado |
| Malha | 60 mm de boneco (1:25), prancha engrossada pelo método da varredura (1,5–1,8 mm), base plana de 668 mm² |

### Peças funcionais (dobradiças, suportes, gavetas)
- 4 paredes, base 5, infill 40% gyroid.
- Parede externa 80 mm/s com aceleração 2500, para precisão.
- **Print-in-place:** meça as folgas por camada (seções em Z).
  - Abaixo de 0,15 mm tende a grudar com bico 0,4. Exceção já vista: o tubarão articulado (modelo de terceiros, testado pelo autor) funcionou com 0,116 a 0,15 mm, a 100% e sem compensação XY. Em modelo assim, não mude escala nem folgas.
  - Aumento mínimo: `xy_contour_compensation` −0,05 e `xy_hole_compensation` +0,05, o que soma +0,1 mm na folga.
- **Peça perto do calor da câmara:** PLA amolece a 55–60 °C. Sugira PETG, mas respeite a escolha dele.
- **Alojamento de porca M3:** 5,5 mm entre faces. A compensação de furo ajuda.

### Peças que levam muito esforço (garras de morsa, ferramentas)
- **Exemplo:** garras macias de 50 mm para prender as bengalas (tubos da suspensão KYB) na morsa, em PETG.
- **Orientação:** o aperto deve ficar **no plano das camadas**, nunca empurrando para separá-las. O canal do tubo fica na vertical, e a força da morsa atravessa cada camada. Assim não precisa de suporte.
- **Configuração:**
  - 8 paredes (cerca de 3,6 mm), topo e base com 6 camadas, 60% gyroid;
  - camada 0,2, Arachne;
  - parede externa 100 mm/s, interna 150;
  - brim de 5 mm encostado.
- **Temperatura:** PETG mais quente (cerca de 240 °C) e com menos ventoinha (30 a 50%) cola melhor as camadas, mas foge da calibração dele (220/230 °C, ventoinha 40 a 90%). **Pergunte sempre** antes de usar.
- Um arquivo assim chegou com o filamento já alterado. A decisão sobre manter ou voltar à calibração dele ficou pendente.

### Peças de encaixe e furos
- Furos verticais saem menores no PLA. Use `xy_hole_compensation` de 0,05 a 0,1.
- Tolerância de furo: ele já usou um perfil "0.20mm PLA FLEXY 0.07 tolerancia furo".

## Orientação
- Teste orientações com `analisar_malha.py` (skill `creality-print-3mf`), comparando a área de contato e a área em balanço de cada uma.
- Peças altas e finas: brim de 3 a 5 mm e aceleração mais baixa.
- Verifique se não há partes "flutuando" (ilhas sem apoio). Já aconteceu de uma aleta da tampa da ventoinha ficar solta no ar.

## Lições de malha (GLB do Tripo e outros)
- GLB é Y-up: gire 90° em X. Pode usar `KHR_mesh_quantization` (o trimesh lê).
- Reduza para cerca de 200–250 mil faces com `fast_simplification`.
- Corrija a orientação das faces com `trimesh.repair.fix_winding`/`fix_inversion` antes de booleanas e de medir espessura (manifold dá `NotManifold`).
- Malha gerada por marching cubes sai com volume negativo: inverta com `faces[:, ::-1]`.
- **Engrossar uma parte fina (prancha, esquis):** NÃO desloque vértices pelas normais. Isso deixou bordas serrilhadas, "triângulos" embaixo e defeitos na união com a bota (erro de 17/11/2026).
  - **Método correto:**
    1. Recorte a região da prancha com um prisma do contorno visto de cima. Na parte plana, use z até cerca de 0,9, abaixo das botas; nas pontas, até cerca de 3,5.
    2. Some (union, manifold3d) cópias dessa região deslocadas para baixo em passos de 0,15 mm, até a espessura extra.
    3. Corte plano embaixo (`trim_by_plane`) 0,3 mm acima do ponto mais baixo, para a base ficar plana.
  - O resultado mantém as superfícies originais, fica fechado e com base plana.
- **Depois de mudar a malha:** confira fechada, `is_volume`, dimensões e área de contato, E **renderize de perto** (por baixo, borda lateral, união com a bota) comparando com o original. A conferência numérica sozinha não pega defeito visual.
