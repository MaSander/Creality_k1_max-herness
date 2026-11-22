---
name: calibrar-filamento-novo
description: Assistente passo a passo para calibrar um filamento novo (marca, tipo ou cor que ainda não tem perfil) na K1 Max com o Creality Print 7. Pergunta tipo e marca, diz qual teste imprimir e com quais valores, pede o resultado de cada um, faz as contas, grava tudo em filamentos/<filamento>/ e exporta o preset para importar no Creality Print. Use sempre que o Alexandre ou o Marcelo disserem que colocaram ou compraram um filamento novo, quiserem criar ou refazer o perfil de um filamento, estiverem com problemas de impressão depois de trocar de filamento, ou quiserem retomar uma calibração que ficou pela metade, mesmo sem usar a palavra "calibrar".
---

# Calibrar filamento novo – K1 Max

Você conduz a calibração **em conversa**: um teste por vez, a pessoa imprime, conta o resultado, você calcula, registra e passa para o próximo. Por isso **rode esta skill na conversa principal**, não delegue ao agente `configurador-impressao-k1max`: um subagente não consegue esperar a pessoa imprimir e responder.

Contas, procedimentos e referências do bico 0,2 ficam em `k1max-calibracao`. Leia essa skill antes de começar. Faixas iniciais por material e o mapa de sintomas ficam em `referencias/faixas-por-material.md`.

## Registro (sempre pelo script)
Todo resultado vai para `filamentos/<slug>/` pelo `perfil_filamento.py`. Ele grava `perfil.json` (estado), gera `perfil.md` (leitura) e exporta o preset. Registrar **logo depois de cada teste** permite retomar a calibração outro dia sem perder nada.

- Mac do Marcelo: `.venv/bin/python .claude/skills/calibrar-filamento-novo/perfil_filamento.py <comando>`
- PC do Alexandre: Python completo com `-P` (veja `AGENTS.md`).

| Comando | Para quê |
|---|---|
| `listar` | ver filamentos registrados e o status de cada bico |
| `novo --tipo --marca [--linha] [--cor] --bico [--diametro] [--temp-fabricante] [--mesa-fabricante] [--nome] [--obs]` | criar o registro |
| `bico <slug> --bico 0.2` | calibrar outro bico do mesmo filamento |
| `definir <slug> --bico X --param chave=valor` | gravar valor que não veio de teste (ex.: mesa, ventoinha) |
| `registrar <slug> --bico X --teste T --faixa "..." --resultado "..." --param chave=valor [--obs]` | gravar um teste e o valor escolhido |
| `calcular flow --atual A --valor V` / `calcular torre --inicio I --passo-mm P --altura H` / `calcular passo --inicio I --fim F --altura-teste H` | contas por código, nunca de cabeça |
| `concluir <slug> --bico X` / `exportar <slug> --bico X` / `mostrar <slug>` | fechar, gerar o preset importável e mostrar o resumo |

Testes válidos: `secagem`, `temperatura`, `flow_grosso`, `flow_fino`, `pressure_advance`, `fluxo_maximo`, `retracao`, `mesa`, `validacao`, `outro`. As chaves de `--param` são as do Creality Print (`nozzle_temperature`, `filament_flow_ratio`, `pressure_advance`, `filament_max_volumetric_speed`, `filament_retraction_length`...); o script recusa chave errada.

## Passo 1: entender o filamento
1. Descubra em qual computador a sessão está (`AGENTS.md`).
2. Rode `listar`. Se o filamento já existe com status em andamento, mostre onde parou (`mostrar`) e retome do próximo teste.
3. Pergunte numa mensagem só, com múltipla escolha curta onde der:
   - **tipo** (PLA, PLA-Silk, PETG, ABS, ASA, TPU, CF...), **marca**, linha e **cor**;
   - **bico** montado (0,4 ou 0,2). A impressora não informa, então confirme;
   - **temperaturas do carretel** (bico e mesa). Peça foto da etiqueta se for mais fácil;
   - se está tendo **algum problema** agora e qual (foto ajuda).
4. Se descreveu problemas, use o mapa de sintomas da referência para dizer **qual teste vai resolver**. Se houver sinal de umidade, a secagem vem antes de tudo, porque filamento úmido estraga todos os testes seguintes.
5. Se for CF/GF ou com partículas e o bico for 0,2, pare e avise: entope.
6. Crie o registro com `novo`. Se já existir um preset com o mesmo nome (outra cor da mesma marca), use `--nome` incluindo a cor.

## Passo 2: preparar
Passe esta lista e espere a confirmação:
- **Secagem** conforme a referência, se precisar (registre com `registrar --teste secagem`).
- **Mesa** limpa (álcool isopropílico) e High Temp Plate selecionada.
- **Preset novo no Creality Print**, para não sobrescrever a calibração de outro filamento:
  1. Impressora do bico em uso (`Creality K1 Max 0.4 nozzle` ou `Creality K1 Max 0.2 nozzle`).
  2. Filamento genérico do tipo (`Generic PETG @Creality K1 Max 0.4 nozzle` etc.; o script mostra qual).
  3. Lápis do filamento → ajuste bico e mesa para o meio da faixa do carretel → **Salvar como** com o nome que o script mostrou.
- **Processo:** o Standard do bico, sem o Detalhe Miniaturas (o suporte e o brim atrapalham as peças de teste).
- **PLA:** tampa aberta. **ABS/ASA:** tampa fechada e câmara aquecida.
- Trocou o bico há pouco: nivelamento antes.

## Passo 3: testes, um por mensagem
Ordem: **temperatura → flow grosso → flow fino → pressure advance → fluxo máximo → retração (só se houver fiapos) → validação.** A temperatura vem primeiro porque muda o flow; o flow muda o PA; e o PA muda a retração.

Para cada teste, mande:
1. **Onde:** menu *Calibration* do Creality Print e o item.
2. **O que preencher:** faixa e passo, tirados da referência e ajustados à faixa do carretel e ao bico.
3. **O que observar** e **o que me responder** (o número impresso no bloco, a altura em mm, ou uma foto).

Depois de receber o resultado:
1. Se a resposta for ambígua ou contraditória, peça foto ou esclareça. **Nunca invente ou "complete" um resultado.**
2. Calcule com o script (`calcular`) e mostre a conta.
3. Peça para salvar o valor **por cima do preset novo** (lápis → valor → salvar, sem "salvar como").
4. Registre com `registrar` (faixa, resultado como a pessoa descreveu e valor escolhido).
5. Siga para o próximo teste.

### Detalhes de cada teste
- **Temperatura:** torre em degraus de 5 °C cobrindo a faixa do carretel. Peça para avaliar fiapos, pontes e overhangs, acabamento e **quebrar a torre com a mão**: o degrau que solta fácil está frio. Escolha a temperatura mais baixa com boa adesão entre camadas e bom acabamento. 1ª camada: +5 °C. Registre `nozzle_temperature` e `nozzle_temperature_initial_layer`.
- **Flow grosso e fino:** contas em `k1max-calibracao`. O teste fino só vale **depois** de salvar o resultado do grosso no preset; confirme isso antes de pedir o fino.
- **Pressure advance:** pattern (linha com cantos mais nítidos, valor impresso ao lado) ou torre (`calcular torre`). Faixa diferente para 0,4 e 0,2: veja a referência.
- **Fluxo máximo:** `calcular torre` na altura da falha e salve uns 10% abaixo. Se a torre inteira saiu perfeita, o limite está acima: salve o fim da faixa (já comprovado) ou repita com faixa maior.
- **Retração:** só se ainda houver fiapos depois do PA. Torre de distância (`calcular torre`); confirme com a pessoa quanto vale cada mm, porque o passo pode ser por degrau e não por mm.
- **Mesa:** só se houver problema de adesão. Registre `hot_plate_temp`/`hot_plate_temp_initial_layer` com `definir` ou `registrar --teste mesa`.
- **Validação:** uma peça conhecida da casa (por exemplo, um projeto de `projetos-base/`) com o preset novo. Registre com `--teste validacao`.

Se um item do menu não existir ou tiver outro nome na versão do Creality Print, adapte, diga o que encontrou e anote aqui depois que funcionar.

## Passo 4: fechar
1. `concluir` (o script recusa se faltar temperatura, flow, PA ou fluxo máximo) e `exportar`.
2. Mostre o resumo (`mostrar`) e peça para conferir no Creality Print se o preset tem os mesmos valores.
3. O JSON exportado em `filamentos/<slug>/` serve de backup e para o outro irmão importar (*File → Import → Import Configs*). Na primeira vez, confirme com quem importou que o preset apareceu para o bico certo; se não aparecer, anote aqui o que precisou mudar.
4. Atualize as tabelas de perfis em `k1max-config-impressao` e "Resultados atuais" em `k1max-calibracao` (regra de manutenção do `AGENTS.md`).
5. Pergunte antes de fazer commit: o repositório é compartilhado e público.

## Regras
- Não altere presets de outros filamentos; tudo acontece no preset novo.
- Um teste por mensagem, esperando o resultado. Não despeje a bateria toda de uma vez.
- Valores vêm de teste impresso ou da pessoa, nunca de suposição. Se um valor for provisório (por exemplo, retração não testada), deixe claro e registre como provisório na `--obs`.
- Nunca inicie impressão remotamente: quem está na máquina manda imprimir pelo Creality Print ou pela tela.
