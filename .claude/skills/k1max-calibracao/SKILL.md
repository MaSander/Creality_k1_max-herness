---
name: k1max-calibracao
description: Roteiro e contas das calibrações do Creality Print 7 na K1 Max do Alexandre (flow, pressure advance, fluxo volumétrico, retração) e procedimento de troca de bico 0,4/0,2. Use quando ele for calibrar filamento, trocar bico ou criar perfil novo.
---

# Calibração – K1 Max

> **Filamento novo:** o passo a passo guiado (perguntas, um teste por vez, registro em `filamentos/` e preset exportado) está na skill `calibrar-filamento-novo`. Esta skill guarda as contas e os procedimentos que ela usa.

## Antes de calibrar
- **Presets:** a impressora do bico em uso e o filamento **da versão daquele bico**. Por exemplo, para o bico 0,2: `PLA FLEXYGREEN @Creality K1 Max 0.2 nozzle`.
  - Nunca calibre em cima do perfil de outro bico, porque sobrescreve a calibração dele.
- **Processo:** o Standard do bico (`0.10mm Standard @Creality K1 Max 0.2 nozzle-1` ou o Standard 0,4).
  - Não use o processo Detalhe Miniaturas, porque o suporte e o brim ligados atrapalham as peças de teste.
- **Mesa:** High Temp Plate.
- **Depois de trocar o bico:** autoteste e nivelamento automático pela tela da impressora.

## Ordem recomendada
1. Fluxo (flow rate), primeiro o teste grosso e depois o fino.
2. Pressure advance.
3. Fluxo volumétrico máximo.
4. Retração (opcional, só se houver fiapos).
5. Torre de temperatura (opcional).

Depois de cada teste: clique no lápis do filamento, coloque o valor novo e **salve por cima do mesmo preset**, não com "salvar como".

## Contas

### Flow
- **Teste 1 (grosso):** flow novo = flow atual × (100 + valor) ÷ 100.
  - Exemplo: 0,98 com +10 dá 1,078.
- **Salve o resultado do teste 1 antes de rodar o teste 2.** O teste 2 é calculado sobre o flow salvo.
- **Teste 2 (fino):** flow final = flow do teste 1 × (100 + valor) ÷ 100.
  - Exemplo: 1,078 com −4 dá 1,035.
- Se ele rodou o teste 2 sem salvar o 1, o teste 2 não vale. Refaça.

### Pressure advance
- **Pattern:** escolha a linha com cantos mais nítidos; o valor está impresso ao lado.
- **Torre:** PA = início + altura do ponto bom (mm) × passo por mm.
  - Com início 0, fim 0,30 e passo 0,01, a torre tem cerca de 31 mm (30 mm de teste mais a base), e cada mm vale 0,01.
  - Exemplo: ponto bom a cerca de 20 mm dá PA 0,20.
- **Referências da Creality para o bico 0,2:** Hyper PLA 0,24; CR-PETG 0,29. Com o bico 0,4, o PA fica perto de 0,03–0,06.

### Fluxo volumétrico máximo
- Valor = início + altura × passo por mm.
  - Com início 1, fim 5 e passo 0,5, a torre tem 8 mm de teste mais a base, cerca de 10 mm.
- **Se a torre inteira saiu perfeita**, o limite real está acima do fim do teste. Salve o fim (já está comprovado) ou rode de novo com faixa maior (por exemplo, de 5 a 12).
- **Se falhou**, use cerca de 10% abaixo do ponto de falha.

### Retração
- Faixa de 0,2 a 1,0 mm. A dele no PLA é 0,4 mm, contra 0,8 mm no perfil da Creality para o bico 0,2.

## Resultados atuais
Os valores em uso ficam num lugar só: a tabela de perfis da skill `k1max-config-impressao`, gerada dos presets do Creality Print (`.claude/perfis/creality-print/`). Não repita valores aqui.

- Depois de salvar um resultado novo no preset do Creality Print, sincronize: `uv run .claude/perfis/sincronizar_perfis.py exportar` e `tabela --gravar` (passo a passo em `.claude/perfis/COMO-IMPORTAR.md`).
- O histórico dos testes de cada filamento (o que foi testado e por quê) fica em `filamentos/<slug>/`.

## Trocar de bico num projeto pronto ("readequar só o bico")
Quando ele pedir para mudar de bico "mudando o mínimo possível", altere SÓ estes três grupos:
1. **Impressora:** todas as chaves de impressora do perfil do bico novo (`printer_settings_id`, `nozzle_diameter`, `min_layer_height`/`max_layer_height`, `retraction_speed`, `deretraction_speed`, `retract_before_wipe`, `z_hop_types`, `creality_flush_time`). `different_settings_to_system[2]` fica vazio, e `inherits_group[2]` também, quando for perfil de sistema.
2. **Filamento:** a calibração daquele bico (`filament_settings_id`, `filament_flow_ratio`, `pressure_advance`, `filament_max_volumetric_speed`). O resto do filamento fica igual.
3. **Processo, só o que depende do bico:**
   - todas as larguras de linha;
   - `tree_support_tip_diameter` (0,6 no bico 0,2, 0,8 no bico 0,4);
   - `print_settings_id` apontando para um perfil compatível.
   - Camada, paredes, velocidades, suporte, brim, bloqueadores e malha **não mudam**, desde que a camada esteja dentro do limite do bico novo.

Copie os valores de um projeto do Alexandre que já use aquele bico (por exemplo, um projeto 0,4 com PLA FLEXYGREEN). Confira byte a byte que `3D/*` e `model_settings.config` ficaram idênticos.

## Depois de trocar o bico na impressora
- O essencial é **medir de novo a altura do bico**. Na K1 Max, o nivelamento automático faz isso com o sensor da mesa.
  - Marcar a opção de nivelamento ou calibração na janela de envio da impressão resolve.
  - O autoteste completo pela tela (input shaping, ventoinhas) não é necessário só por causa do bico.
- Acompanhe a 1ª camada e, se precisar, ajuste o Z-offset pela tela em passos pequenos.
- **Bico 0,2 entupido (20/11/2026):** puxadas a frio (cold pull) com PLA a cerca de 230 °C e agulha de limpeza de 0,2 mm. Evite filamento com partículas nesse bico.

## Bico 0,2: dados oficiais da Creality (wiki da K1 Series)
- **Impressora:**
  - camada mín. 0,04 / máx. 0,14;
  - retração 0,8 mm, velocidade 30/30;
  - z-hop Slope, ângulo 3, limite de deslocamento 1 mm;
  - retração antes do wipe 90%, wipe 2 mm.
- **Processo:**
  - camada 0,10, 1ª 0,14, linha 0,22, 4 paredes, topo 7, base 5, 15% grid;
  - velocidades: externa 110, interna 130, infill 120, topo 100, gap 50, 1ª camada 18;
  - aceleração 10000 / paredes 3000 / 1ª camada 2000; jerk 3.
- **Hyper PLA:** 220 °C, mesa 50, flow 0,98, PA 0,24, fluxo máximo 3, tempo mínimo de camada 12 s, ventoinha lateral 80%.
- **CR-PETG:** 250 °C, mesa 70, flow 0,98, PA 0,29, fluxo máximo 2,5, ventoinha 40–80, lateral 0%.
- **Fontes externas:**
  - Bambu: fluxo máximo de 2 mm³/s (conservador); usuários usam de 5 a 10.
  - Evitar filamentos com partículas no bico 0,2.
  - As camadas grudam menos entre si do que com o 0,4.
