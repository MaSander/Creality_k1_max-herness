---
name: creality-print-3mf
description: Como ler, revisar, gerar e alterar projetos .3mf do Creality Print 7 (base OrcaSlicer) — por script, sem abrir o programa, ou passo a passo com o programa aberto (onde fica cada configuração). Use sempre que for criar, editar ou ajustar configurações de um .3mf para a K1 Max.
---

# Projetos .3mf do Creality Print 7

## Estrutura (um arquivo ZIP)
| Arquivo | Conteúdo |
|---|---|
| `3D/3dmodel.model` | itens na mesa; a posição fica em `transform` (12 números: matriz 3×3 + x y z) |
| `3D/Objects/object_N.model` | malha (`<vertex x y z>`, `<triangle v1 v2 v3>`) |
| `Metadata/project_settings.config` | JSON com **todas** as configurações (impressora + filamento + processo) |
| `Metadata/model_settings.config` | nome do objeto, `assemble_item transform` e configurações por objeto, se houver |
| `Metadata/layer_heights_profile.txt` | altura de camada variável, quando existe (incompatível com suporte Organic) |
| `Metadata/plate_*.png/json` | miniaturas e placa; o Creality aberto regenera, mas o fatiamento por linha de comando **copia** `plate_1.png` para o G-code (o `gerar_projeto_creality.py` redesenha as imagens da malha nova) |

**Posição na mesa:** a malha fica centrada em XY na origem, com o meio da altura em z = 0. O `transform` do item é `1 0 0 0 1 0 0 0 1 150 150 <meia altura>`, igual no `3dmodel.model` e no `assemble_item`.

## Chaves de controle em `project_settings.config`
- `different_settings_to_system`: lista de 3 strings separadas por `;`:
  - [0] = processo, [1] = filamento, [2] = impressora.
  - Toda chave alterada precisa estar no grupo certo, senão o Creality pode tratar como valor de fábrica.
- Identificação dos perfis:
  - `print_settings_id`, `filament_settings_id` (lista), `printer_settings_id`;
  - `inherits_group` = [processo, filamento, impressora].
- **Valores por extrusora vão em lista:** `"outer_wall_speed": ["80"]`, `"nozzle_diameter": ["0.2"]`. Respeite o tipo que já está no arquivo.
- Algumas chaves usadas com frequência:
  - **Camada:** `layer_height`, `initial_layer_print_height`.
  - **Paredes e preenchimento:** `wall_loops`, `top_shell_layers`, `bottom_shell_layers`, `sparse_infill_density`, `sparse_infill_pattern`, `wall_generator` (classic ou arachne).
  - **Larguras de linha:** `line_width`, `outer_wall_line_width`, `inner_wall_line_width`, `top_surface_line_width`, `sparse_infill_line_width`, `internal_solid_infill_line_width`, `support_line_width`, `initial_layer_line_width`.
  - **Velocidade e aceleração:** `outer_wall_speed`, `inner_wall_speed`, `sparse_infill_speed`, `internal_solid_infill_speed`, `top_surface_speed`, `support_speed`, `outer_wall_acceleration`.
  - **Suporte:**
    - `enable_support`, `support_type` (normal(auto) ou tree(auto)), `support_style` (snug, tree_slim ou organic);
    - `support_threshold_angle`, `support_top_z_distance`, `support_bottom_z_distance`;
    - `support_interface_top_layers`, `support_interface_bottom_layers`;
    - `support_object_xy_distance`, `support_xy_overrides_z`, `independent_support_layer_height`;
    - `tree_support_tip_diameter`, `tree_support_branch_diameter_organic`, `tree_support_wall_count`.
  - **Brim:** `brim_type` (outer_only ou auto_brim), `brim_width`, `brim_object_gap`, `elefant_foot_compensation`.
  - **Compensações:** `xy_hole_compensation`, `xy_contour_compensation`.
  - **Outras:** `seam_position`, `reduce_crossing_wall`.
  - **Impressora:** `nozzle_diameter`, `max_layer_height`, `min_layer_height`, `curr_bed_type`.
  - **Filamento (não mexer sem pedir):** `nozzle_temperature*`, `hot_plate_temp*`, `filament_flow_ratio`, `pressure_advance`, `filament_retraction_length`, `filament_max_volumetric_speed`, `fan_*`, `slow_down_layer_time`.

## Fluxo para gerar um projeto
1. **Modelo:** um projeto salvo no Creality com 1 objeto na mesa, usado só pela estrutura. Procure em `projetos-base/`.
2. **Configurações:** um projeto de `projetos-base/` com a impressora, o bico e o filamento certos, para herdar a calibração.
   - Se não existir projeto para aquele bico ou filamento, **peça que salvem um** (instruções em `projetos-base/README.md`). Não invente perfil.
3. **Gerar:** rode `gerar_projeto_creality.py` (nesta pasta) com o JSON só das chaves de processo.
4. O script cuida sozinho de três coisas:
   - cada chave alterada vai para o grupo certo de `different_settings_to_system` (processo, filamento ou impressora);
   - **MODELO com bloqueadores ou várias partes** (como o snowboarder): as partes extras são retiradas, porque eram da peça antiga;
   - a altura de camada variável do MODELO (`Metadata/layer_heights_profile.txt`) é retirada.
5. O script recusa malha maior que a mesa e grava os vértices com precisão de float32.
6. **Conferência por código:** rode o `checklist_3mf.py` (seção "Analisar e conferir por código").

Grave as chaves num arquivo `.json` (funciona igual no PowerShell e no bash) e rode da raiz do repositório:
```
uv run .claude/skills/creality-print-3mf/gerar_projeto_creality.py MODELO.3mf CONFIG.3mf peca.stl SAIDA.3mf "Nome" --config mudancas.json
```
`mudancas.json`: `{"layer_height":"0.12","wall_loops":"3","brim_object_gap":"0","elefant_foot_compensation":"0"}`

O script recusa SAIDA igual ao MODELO ou ao CONFIG e registra cada chave no grupo certo (processo, filamento ou impressora).

## Analisar e conferir por código
Dois scripts desta pasta, iguais no Windows e no macOS. Os dois saem com código 1 quando reprovam.

**`analisar_malha.py`** – antes de gerar o projeto, para qualquer malha (STL, OBJ, GLB) ou `.3mf`:
```
uv run .claude/skills/creality-print-3mf/analisar_malha.py peca.stl [--angulo 45] [--brim 5] [--render previa.png] [--json]
```
- Mostra dimensões, se está fechada, corpos (e quantos não encostam na mesa), volume, se cabe em 300 × 300 × 300 com o brim, área de contato e as regiões em balanço (mm², posição e altura).
- Reprova malha aberta, que não cabe ou sem nenhuma face apoiada na mesa.
- Analisa na orientação do arquivo. `--render` grava 4 vistas com o balanço em vermelho e o contato em azul.
- Não mede espessura de parede nem folga de print-in-place.
- `--gravar-ficha pecas/<peca>/ficha.json` (com `--peca`, `--uso`, `--material`, `--bico` e, se houver, `--critica`, `--orientacao`, `--fonte`, `--rota`, `--versao`): grava a ficha da peça, só se a malha for aprovada. O passo a passo está na skill `modelagem-3d`.

**`checklist_3mf.py`** – antes de entregar o projeto:
```
uv run .claude/skills/creality-print-3mf/checklist_3mf.py PROJETO.3mf --origem CONFIG.3mf --bico 0.4 [--permitir chave,chave] [--render previa.png]
```
- `--origem`: o projeto de onde vieram as configurações. Qualquer chave de **filamento** diferente é `[FALHA]`, a não ser as de `--permitir` (alteradas com autorização).
- `--bico`: o bico montado na impressora, confirmado com quem pediu.
- Confere impressora e bico, brim encostado (gap 0 **e** pé de elefante 0), malha fechada dentro do `.3mf`, se cabe e está centrada e apoiada na mesa, suporte (folga Z ≥ 0,24 em PLA, Organic sem altura variável, interface, distância lateral) e lista os balanços.
- Compara o filamento com o preset de `.claude/perfis/` e dá `[aviso]` se diferir (o preset pode ter sido atualizado depois do projeto).
- `--ficha pecas/<peca>/ficha.json`: a ficha gravada na modelagem (skill `modelagem-3d`). Dimensões, material ou bico diferentes dos dela são `[FALHA]`; uso, orientação e medidas críticas saem como `[info]`.
- O que o código não tem como saber sai como `[manual]`: escala contra a medida de referência, motivo da orientação e render de perto quando a malha foi alterada.

A leitura do `.3mf` e a análise ficam em `ferramentas/k1malha.py` (`ler_3mf`, `analisar`, `render`): use essas funções em vez de reescrever a conferência.

## Cuidado técnico com o zipfile do Python
`zout.writestr(item, data)` reaproveitando o `ZipInfo` do arquivo de entrada **altera o offset dele**. Ler o ZIP de entrada depois disso dá "Bad magic number for file header". O arquivo de saída fica correto. Para não ter o erro, crie um `ZipInfo` novo para cada arquivo e confira reabrindo os dois ZIPs do zero. É o que faz o `copiar_zip` de `ferramentas/k1comum.py`, usado pelos três scripts desta pasta: ao escrever um script novo que grave `.3mf`, use essa função.

## Revisar um projeto salvo por ele
- Compare `project_settings.config` com a versão anterior e liste as chaves que mudaram.
- Verifique `layer_heights_profile.txt` e configurações por objeto em `model_settings.config`.
- Projetos com vários objetos: mude só o `project_settings.config` e confirme que os arquivos `3D/*` ficaram idênticos byte a byte.

## Alterar configurações SEM abrir o Creality Print
Use `alterar_config_3mf.py` (nesta pasta) para mudar processo, suporte, brim, filamento ou impressora num .3mf que já existe. O script:
- não mexe nas malhas nem nas posições;
- registra cada chave no grupo certo;
- avisa quando uma chave é de filamento;
- confere o resultado no final.

```
uv run .claude/skills/creality-print-3mf/alterar_config_3mf.py ENTRADA.3mf SAIDA.3mf --config mudancas.json
uv run .claude/skills/creality-print-3mf/alterar_config_3mf.py ENTRADA.3mf SAIDA.3mf --config mudancas.json --sem-altura-variavel
```
`mudancas.json`: `{"wall_loops":"4","outer_wall_speed":"80"}`. SAIDA tem de ser um arquivo diferente da ENTRADA.

Mudanças que se fazem com frequência (JSON):

| Objetivo | Chaves |
|---|---|
| Suporte que solta fácil | `{"enable_support":"1","support_type":"tree(auto)","support_style":"organic","support_top_z_distance":"0.24","support_bottom_z_distance":"0.24","support_interface_top_layers":"0","support_interface_bottom_layers":"0","support_object_xy_distance":"0.6","support_xy_overrides_z":"z_overrides_xy","support_threshold_angle":"40"}` + `--sem-altura-variavel` |
| Brim encostado | `{"brim_type":"outer_only","brim_width":"5","brim_object_gap":"0","elefant_foot_compensation":"0"}` |
| Peça resistente | `{"wall_loops":"4","bottom_shell_layers":"5","sparse_infill_density":"40%","sparse_infill_pattern":"gyroid"}` |
| Precisão (encaixes, print-in-place) | `{"outer_wall_speed":"80","outer_wall_acceleration":"2500","xy_hole_compensation":"0.05","xy_contour_compensation":"-0.05"}` |
| Detalhe fino (bico 0,4) | `{"layer_height":"0.12","initial_layer_print_height":"0.16","wall_generator":"arachne","outer_wall_line_width":"0.4"}` |
| Trocar para o bico 0,2 | Prefira um projeto salvo com a impressora `Creality K1 Max 0.2 nozzle`. Mudar `nozzle_diameter` à mão exige também `max_layer_height` 0.14, larguras de linha 0.22 e o filamento da versão 0,2 |

Depois de editar, quem pediu abre o .3mf no Creality e fatia. O programa respeita os valores gravados no projeto e marca o perfil com `*` (modificado). Isso é normal.

## Bloqueador e reforço de suporte

### Sem abrir o programa
Use `adicionar_bloqueador_3mf.py` (nesta pasta). As caixas são informadas em coordenadas da **mesa**, como no fatiador (0 a 300 mm).

```
uv run .claude/skills/creality-print-3mf/adicionar_bloqueador_3mf.py ENTRADA.3mf SAIDA.3mf --caixas caixas.json [--tipo support_enforcer]
```
`caixas.json`: `[{"nome":"Bloqueador bico frontal","min":[145,173,0],"max":[162,181,3.6]}]`. O script recusa caixa fora da mesa.

**Estrutura de um objeto com várias partes** (copiada do projeto real dele, `1_esteira.3mf`):
- **`3D/Objects/object_N.model`:** vários `<object>`. A peça é `type="model"`; bloqueadores, modificadores e partes negativas são `type="other"`.
- **`3D/3dmodel.model`:** o objeto da mesa tem um `<component>` para cada parte, cada um com seu `objectid` e `transform`.
- **`Metadata/model_settings.config`:** dentro de `<object id=…>`, um `<part id="<objectid>" subtype="…">` para cada parte.
  - Subtipos: `normal_part`, `support_blocker`, `support_enforcer`, `modifier_part`, `negative_part`.

**Depois de gerar:**
1. Confira com render que as caixas cobrem só a região desejada.
2. Peça para ele confirmar no Creality que os itens aparecem na lista do objeto e que, na prévia, não há suporte ali.

### Com o programa aberto
- **Caixa:** botão direito no objeto → **Add support blocker** (ou Add support enforcer) → **Box**. Ajuste a caixa com mover (M) e escalar (S).
- **Pintura:** selecione o objeto → **Support painting** (atalho L) → pincel **Block** (bloquear) ou **Enforce** (forçar) → pinte as superfícies.
- **Conferir:** fatie e olhe a prévia.

**Quando usar:**
- Embaixo de partes que levantam pouco da mesa, como os bicos da prancha e as pontas dos esquis. Ali o suporte fica baixinho (menos de 2 mm) e difícil de tirar, e a superfície imprime bem sem ele.
- Em lugares em que o suporte iria marcar uma superfície visível.

## Alterar configurações COM o Creality Print aberto (versão 7, em inglês, modo Expert)
Os nomes podem variar um pouco entre versões. Confirme com captura de tela se houver dúvida.
- **Modo Expert:** chave no topo do painel de configurações (Simple/Expert). Sem ele, várias opções ficam escondidas.
- **Painel da direita, aba Prepare:** três blocos, cada um com uma lista e um lápis para editar.
  - **Printer:** escolhe a impressora/bico. O lápis abre a configuração da impressora; o diâmetro do bico, a retração e os limites de camada ficam em **Extruder**.
  - **Filament:** o lápis abre temperaturas, flow ratio, pressure advance, ventoinha e fluxo máximo.
  - **Process:** a lista de perfis (o perfil com `*` foi modificado). Embaixo ficam as abas:
    - **Quality:** camada, largura de linha, costura (seam), compensações XY e de pé de elefante;
    - **Strength:** paredes, topo e base, preenchimento;
    - **Speed:** velocidades e acelerações;
    - **Support:** ligar, tipo e estilo (Normal, Tree Slim, Organic), ângulo e as distâncias Z e XY;
    - **Others:** brim (tipo, largura e gap), saia e sequência de impressão.
- **Salvar um perfil:** ícone de disquete ao lado da lista de Process ou Filament.
  - **Save** sobrescreve o perfil.
  - **Save as** cria um novo perfil. Na calibração, salve por cima do perfil do bico certo.
- **Configuração só para uma peça:** clique com o botão direito no objeto (ou no "+" da lista de objetos) e use Add settings para escolher a categoria. Só aquela peça muda.
- **Altura de camada variável:** ícone na barra de ferramentas do objeto. Para usar suporte Organic, abra essa ferramenta e clique em **Reset**. Isso resolve o erro "Variable layer height is not supported with Organic supports".
- **Calibração:** menu **Calibration** no topo (Flow rate, Pressure advance, Max volumetric speed, Retraction, Temperature).
- **Importar perfis ou pacotes:** File → Import → Import Configuration.
- **Salvar o projeto:** File → Save Project (Ctrl+S). Gera o .3mf com tudo dentro.

## Fatiar sem abrir o programa (linha de comando) – testado em 20/11/2026
`fatiar_3mf.py` chama o próprio Creality Print (`--slice`) e usa **as configurações gravadas no .3mf**. Ele não usa perfis soltos, então o G-code sai como o programa geraria com o mesmo projeto aberto. A comparação de 585 chaves entre o .3mf e o G-code não mostrou diferenças reais.
```
uv run .claude/skills/creality-print-3mf/fatiar_3mf.py projeto.3mf [--saida PASTA] [--nome peca]
```
- Saída: `<nome>_bico<d>_<filamento>_<tempo>.gcode`, com miniaturas 96 e 300 px embutidas. O CLI não renderiza miniatura: ele usa o `Metadata/plate_1.png` que já está no `.3mf`. Projetos do `gerar_projeto_creality.py` já trazem a imagem da peça nova; num `.3mf` editado de outro jeito, confira se a miniatura é da peça certa. O resumo mostra bico, filamento, temperaturas, camada, suporte, brim, tempo e gramas.
- **Versão:** o Mac tem o Creality Print **7.2.2**, e os projetos do Alexandre são salvos no **7.3**. O CLI recusa arquivo mais novo. O script para e avisa, e só fatia com `--permitir-versao-nova` (opções novas podem ser ignoradas). O melhor é deixar os dois computadores na mesma versão.
- **Windows: não funciona** (testado em 22/11/2026 no PC do Alexandre, Creality Print 7.3). O `CrealityPrint.exe` não tem modo linha de comando: `--help` trava, `--export-3mf` dá "GUI parameter parsing failed" e `--slice` abre a janela sem fatiar. O script para e avisa. No PC dele, o fatiamento é no programa: abra o .3mf, **Slice plate** e **Export G-code**. Sem o G-code, o tempo que você informar é estimativa; diga isso.
- Para mandar à impressora (sem imprimir): `enviar_k1max.py` da skill `k1max-impressora`.

### Fatiar com o OrcaSlicer (`--fatiador orca`) – experimental, testado em 22/11/2026
O Creality Print é derivado do OrcaSlicer, e o OrcaSlicer tem linha de comando nos dois sistemas. Serve de saída para o Windows, onde o Creality Print não fatia por script. **O padrão continua sendo o Creality Print**; só use o OrcaSlicer quando pedirem ou quando não houver outro jeito, e diga que é experimental.
```
uv run .claude/skills/creality-print-3mf/fatiar_3mf.py projeto.3mf --fatiador orca
```
- Instalar: macOS, `brew install --cask orcaslicer`; Windows, o instalador de https://github.com/OrcaSlicer/OrcaSlicer/releases. Se o script não achar o programa, passe `--exe` ou defina `K1_ORCA_EXE`.
- O arquivo sai com `_orca` no nome, e o resumo avisa que é experimental.
- **O que foi comparado no Mac** (OrcaSlicer 2.5.2 contra Creality Print 7.2.2, mesmos `.3mf` salvos no 7.3):
  - o OrcaSlicer abre o projeto do Creality Print direto, sem conversão;
  - G-code de início, temperaturas, pressure advance e número de camadas: **iguais**;
  - peça sem suporte (corpo de prova M3): filamento 5,05 g contra 5,06 g; tempo estimado 19 min contra 17 min;
  - **peça com suporte Organic (snowboarder): a peça sai quase igual (paredes a menos de 1% de diferença, preenchimento a menos de 3%), mas o suporte sai com 62% mais material** (20,2 g contra 17,6 g no total; 4 h 41 contra 4 h 03). O suporte que "solta fácil" foi acertado no Creality Print: no OrcaSlicer ele é outro;
  - cerca de 100 opções que só existem no Creality Print são ignoradas (ventoinhas especiais, temperatura por fluxo, `creality_flush_time` e outras);
  - o OrcaSlicer acrescenta `MINIMUM_CRUISE_RATIO` ao comando `SET_VELOCITY_LIMIT`. Não foi testado se o firmware de fábrica da K1 Max aceita.
- **Falta para confiar:** imprimir uma peça sem suporte e uma com suporte fatiadas pelo OrcaSlicer e comparar com as do Creality Print. **Nenhum G-code do OrcaSlicer foi impresso até agora.** No Windows o `--fatiador orca` não foi testado.
- Não mude os perfis para o OrcaSlicer: os presets continuam sendo os do Creality Print (`.claude/perfis/`).

## Pacotes de perfil (.creality_printer)
- Também é um ZIP:
  - `bundle_structure.json` com `printer_config`, `filament_config`, `process_config` e `printer_preset_name`;
  - pastas `printer/`, `filament/` e `process/` com JSONs do tipo `"from": "User"` e `"inherits": "<perfil de sistema>"`.
- **Filamento de usuário:** herde de `Generic PLA @Creality K1 Max 0.4 nozzle` (ou PETG) e mude só o necessário. A impressora 0,2 herda da 0,4, então fica compatível.
- **Atenção:** o pacote da Creality vem com `curr_bed_type = Cool Plate`. Troque para `High Temp Plate`.
- **Importar:** File → Import → Import Configuration.

## Acesso aos arquivos por computador

Nos dois: Python com `uv run`, da raiz do repositório (veja "Ambientes por pessoa" no `AGENTS.md`).

### Mac do Marcelo
- Pasta de entrega: `~/Downloads`.
- Creality Print em `/Applications/Creality Print.app`; os perfis de usuário também não são editados direto: entregue pacote para importar.

### PC do Alexandre (Windows)
- Pasta conectada: `C:\Users\alemg\Downloads`. Use stage e commit pela ponte com o computador.
- A pasta `AppData\Roaming\Creality` (perfis) não está liberada. Entregue perfis como pacote para importar.

### Nos dois computadores: gravar a malha no .3mf
- Escreva as coordenadas com precisão de float32 (`{:.9g}`). Com 5 a 7 casas fixas, vértices quase coincidentes se fundem e a malha abre (esquiador, 20/11/2026). O `gerar_projeto_creality.py` grava assim.
- Para conferir, releia com `process=False`: o fatiador usa os triângulos por índice. É o que o `k1malha.ler_3mf` faz.
- Para reduzir a malha, use `manifold3d` (`simplify`, `set_tolerance(1e-4)`). O `fast_simplification` abriu buracos.
