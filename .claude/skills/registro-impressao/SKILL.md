---
name: registro-impressao
description: Registrar o resultado de uma impressão na K1 Max e levar as lições de volta para as skills — pergunta como ficou, grava a entrada datada no README da peça (com o que a impressora informa e a configuração do projeto) e propõe transformar a lição em regra. Use quando o Alexandre ou o Marcelo contarem como uma impressão saiu ("ficou boa", "descolou", "o suporte não saiu", "terminou"), mandarem foto do resultado ou pedirem para registrar uma impressão.
---

# Registro da impressão e retorno das lições

O fluxo de preparação termina quando o arquivo vai para a lista da impressora. Esta skill fecha o ciclo: o que aconteceu na impressão volta para o registro da peça e, quando serve para outras peças, para as skills.

Conduza **na conversa principal** (são perguntas a quem imprimiu). Não rode por conta própria logo depois de enviar um arquivo: espere a pessoa contar o resultado.

## Passo 1: o que perguntar
Pergunte só o que a pessoa ainda não disse, em múltipla escolha curta:
1. **Qual peça e qual arquivo** foi impresso. Para achar o nome do G-code:
   ```
   uv run .claude/skills/registro-impressao/registrar_impressao.py --ultimas 5
   ```
2. **Resultado:** aprovada, aprovada com ressalvas (`parcial`) ou reprovada.
3. **O que aconteceu**, nas palavras dela: encaixe, acabamento, suporte (saiu fácil?), 1ª camada, empenamento, fiapos. Em peça com medida crítica (veja a `ficha.json`), peça a medida real.
4. **Algo fora do projeto** que influenciou: filamento úmido, mesa suja, modo de velocidade da tela, bico trocado.

Não invente resultado nem medida. Se a pessoa não mediu, registre que não foi medido.

## Passo 2: registrar
```
uv run .claude/skills/registro-impressao/registrar_impressao.py <peca> --resultado aprovada --quem Marcelo --gcode "nome.gcode" --projeto caminho/do/projeto.3mf --obs "o que aconteceu" --licao "uma lição" --licao "outra"
```
- `<peca>` é o nome da pasta em `pecas/`. Se a peça ainda não tem pasta, o script cria o `README.md`; preencha depois a origem (e a licença, se o modelo é de terceiros).
- `--gcode`: o script busca esse nome no histórico da impressora e grava se a impressão foi concluída ou interrompida, a duração e os metros de filamento. Sem rede com a impressora, use `--sem-impressora`.
- `--projeto`: o `.3mf` que foi fatiado. O script grava a configuração (impressora, filamento, camada, paredes, suporte, brim). Modelo de terceiros fica em `pecas/<peca>/local/`.
- A entrada vai para a seção **Impressões** do README, no fim. O script só acrescenta: não reescreve o que já está lá.
- Se a peça foi **aprovada**, atualize à mão a seção "Configuração aprovada" do README com o resumo que o script mostrou.
- É edição do repositório: branch `peca/<nome>` antes (veja `.claude/rules/fluxo-git.md`). Registro de peça própria o autor pode mesclar.

## Passo 3: a lição vira regra?
Para cada lição, decida onde ela vale:

| A lição é sobre… | Vai para |
|---|---|
| Só esta peça (um detalhe do modelo) | Fica no README da peça |
| Como projetar (folga, parede, balanço, furo, chanfro) | `modelagem-3d`, "Regras de projeto" (e `regras-projeto-k1max.md`, se couber) |
| Como configurar (suporte, brim, velocidade, orientação, receita por tipo de peça) | `k1max-config-impressao` |
| O `.3mf`, os scripts ou o fatiador | `creality-print-3mf` |
| A impressora (envio, câmera, tela, manutenção) | `k1max-impressora` |
| O filamento (umidade, temperatura, fluxo) | `filamentos/<slug>/` e, se for valor de preset, o preset no Creality Print |

- **Pergunte antes de mudar uma skill** (múltipla escolha, opção recomendada primeiro): mostre a frase que entraria e onde.
- Uma falha só não derruba uma regra que já funcionou outras vezes: registre como exceção, com a data e a peça.
- Lição que **contradiz** uma regra existente: mostre as duas e deixe quem pediu decidir.
- Mudança em skill é assunto dos dois irmãos: vai em branch `skill/<assunto>` e PR com revisão do outro.
- **Não mexa em valor de filamento por causa de uma impressão.** Se o problema parece ser do filamento, diga isso; calibrar é só por pedido explícito.

## O que não fazer
- Não registrar como aprovada uma impressão que a impressora marca como interrompida sem confirmar (o script avisa).
- Não apagar nem reescrever entradas antigas: o histórico é o que mostra o que mudou.
- Não subir foto ou arquivo de modelo de terceiros (repositório público; veja `pecas/README.md`).
