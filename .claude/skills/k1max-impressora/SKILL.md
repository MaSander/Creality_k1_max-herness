---
name: k1max-impressora
description: Ler status (temperaturas, progresso, erro) e histórico de impressões da Creality K1 Max pela rede e enviar um G-code para a lista de arquivos dela (sem imprimir), com o firmware de fábrica. Use quando o Alexandre ou o Marcelo perguntarem o que a impressora está fazendo, o que foi impresso por último, quiserem conferir algo nela antes de imprimir ou pedirem para mandar uma peça fatiada para a impressora.
---

# Conexão com a K1 Max (leitura e envio sem imprimir)

- **IP:** `192.168.0.69` (hostname `K1Max-6D54`), visto em 20/11/2026. Se não responder, peça o IP atual (tela → Configurações → Rede); o roteador pode ter mudado.
- **Firmware de fábrica** (sem root): painel web na porta 80 e WebSocket na **9999** (o mesmo que o Creality Print usa). Fluidd (4408) e Moonraker (7125) estão **fechados**.

## Script
`k1max_status.py` (só biblioteca padrão):
```
.venv/bin/python .claude/skills/k1max-impressora/k1max_status.py status
.venv/bin/python .claude/skills/k1max-impressora/k1max_status.py historico --n 10
```
No PC do Alexandre, use o Python completo com `-P` (ver AGENTS.md).

## O que dá e o que não dá para saber (testado em 20/11/2026)
| Dá | Não dá |
|---|---|
| Estado, temperaturas (bico, mesa, câmara), progresso, camada, tempo restante, erro | **Qual filamento** está carregado: K1 Max sem CFS não lê o carretel (`cfsConnect: 0`) |
| Histórico: nome do G-code, data, duração, metros de filamento, concluída ou não | **Qual bico** está montado |
| PA atual do Klipper (`pressureAdvance`) | As configurações do fatiamento: o G-code não é servido pela porta 80 (404) |

O nome do G-code costuma trazer o filamento (`..._PLA_...`), mas isso é só uma pista: **confirme filamento e bico com quem pediu**.

## Enviar para a lista de arquivos (sem imprimir) – testado em 20/11/2026
`enviar_k1max.py` faz o mesmo que o botão de enviar arquivo do Creality Print: `POST http://IP/upload/<nome>` (porta 80, campo `file`, **sem root**). O arquivo vai para `/usr/data/printer_data/gcodes/` e aparece na tela. **Não inicia a impressão**: iniciar é outro comando (WebSocket `opGcodeFile: "printprt:<caminho>"`), que o script não tem.
```
.venv/bin/python .claude/skills/k1max-impressora/enviar_k1max.py ~/Downloads/peca_bico0.4_PLA_1h20m.gcode
```
- Recusa se a impressora estiver imprimindo ou pausada (`--mesmo-imprimindo` para forçar), se já existir arquivo com o mesmo nome (`--sobrescrever`) e se o arquivo não for um G-code do Creality Print.
- Depois do envio, confere na lista da impressora se o arquivo chegou com o tamanho certo.
- O G-code vem do `fatiar_3mf.py` (skill `creality-print-3mf`), que põe **bico e filamento no nome** e embute a miniatura.

## Listar e apagar arquivos da impressora – testado em 20/11/2026
`arquivos_k1max.py` usa o mesmo comando do Creality Print (WebSocket 9999, `opGcodeFile: "deleteprt:<caminho>"`).
```
.venv/bin/python .claude/skills/k1max-impressora/arquivos_k1max.py listar
.venv/bin/python .claude/skills/k1max-impressora/arquivos_k1max.py apagar "nome exato.gcode"
```
- Apagar **só com pedido explícito** e só pelo nome exato. O script recusa o arquivo em uso na impressão e confere depois se ele sumiu da lista.

- Às vezes o 1º envio logo depois de ligar a impressora responde OK mas o arquivo não aparece na lista (21/11/2026). O script avisa; é só enviar de novo.

## Detecção por IA da câmera – testado em 21/11/2026
A K1 Max detecta falha (peça solta, "espaguete") pela câmera, mas **só com a IA ligada**: em 21/11/2026 estava tudo em 0, e uma peça descolou duas vezes sem nenhum aviso. Os campos aparecem no `k1max_status.py bruto`:

| Campo | O que é |
|---|---|
| `aiSw` | IA ligada |
| `aiDetection` | detecção de falha durante a impressão |
| `aiPausePrint` | pausa sozinha quando detecta |
| `aiFirstFloor` | confere a 1ª camada (só no início da impressão) |

Para ligar, use o mesmo comando do Creality Print (WebSocket 9999, `{"method":"set","params":{"<campo>":1}}`), **com a impressora parada**, e depois confira no `bruto` se o campo ficou em 1:
```
cd .claude/skills/k1max-impressora && ../../../.venv/bin/python -c "
from k1max_status import IP_PADRAO, _ws_get
for k in ('aiSw','aiDetection','aiPausePrint','aiFirstFloor'): _ws_get(IP_PADRAO, {'method':'set','params':{k:1}}, duracao=2)"
../../../.venv/bin/python k1max_status.py bruto | grep '"ai'
```
- Mexa nisso só com pedido. Também dá para ligar pela tela, em Configurações, na opção de detecção por IA.
- A IA não pega tudo: nas peças grandes, vale olhar as primeiras camadas mesmo assim.

## Meta do projeto (decidida pelo Marcelo em 20/11/2026)
1. Ler status e histórico. 2. Enviar o arquivo **sem imprimir**. 3. Fatiar pela linha de comando.
**Não** fazer início remoto da impressão: quem está começando precisa ir até a máquina e conferir bico, filamento, mesa vazia e tampa. Não instalar root nem Moonraker para isso.

## Regras
- **Nunca iniciar impressão**, mesmo que peçam "manda imprimir": envie para a lista e diga para iniciar na tela.
- Envie só o que foi pedido. **Não** envie comandos de temperatura, movimento ou exclusão de arquivo sem pedido explícito.
- Não afirme o filamento ou o bico com base só no histórico.
