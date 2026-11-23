# Projetos de referência (projetos-base)

O `gerar_projeto_creality.py` precisa de dois `.3mf` salvos no Creality Print:
- **MODELO**: dá a estrutura do arquivo (qualquer projeto com 1 objeto na mesa; partes extras, como bloqueadores, são retiradas pelo script);
- **CONFIG**: dá o `project_settings.config` com a impressora, o bico, o filamento e o processo.

Um projeto por combinação serve para os dois papéis.

## Arquivos esperados

| Arquivo | Impressora (Printer) | Filamento | Processo |
|---|---|---|---|
| `base_0.4_PLA-FLEXYGREEN.3mf` | Creality K1 Max 0.4 nozzle | PLA FLEXYGREEN | 0.20mm Standard |
| `base_0.4_PETG-MASTERPRINT.3mf` | Creality K1 Max 0.4 nozzle | PETG MASTERPRINT | 0.20mm Standard |
| `base_0.2_PLA-FLEXYGREEN.3mf` | Creality K1 Max 0.2 nozzle | PLA FLEXYGREEN @…0.2 nozzle | 0.10mm Standard @…0.2 nozzle |
| `base_0.2_PETG-MASTERPRINT.3mf` | Creality K1 Max 0.2 nozzle | PETG MASTERPRINT @…0.2 nozzle | 0.10mm Standard @…0.2 nozzle |

**Status em 22/11/2026: nenhum salvo ainda.** Tem de ser salvo por quem tem os presets no Creality Print (hoje, só o PC do Alexandre; o Mac do Marcelo precisa importar o zip de `.claude/perfis/` antes).

## Enquanto isso
| Combinação | O que usar | Atenção |
|---|---|---|
| Bico 0,4 + PLA FLEXYGREEN | `.claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf` (aprovado em 20/11/2026) | O processo é de miniatura (camada 0,08): passe no JSON as chaves de processo da peça nova. O filamento vem com tempo mínimo de camada 8, e o preset atual tem 0 (o `checklist_3mf.py` avisa) |
| Bico 0,2 + PLA FLEXYGREEN | `.claude/referencias/Snowboarder_1-25_PLA_bico_0.2_v5.3mf` (nunca impresso) | Flow 1,035, fluxo máximo 5 e tempo mínimo de camada 8; o preset atual tem 1,03, 7 e 0 |
| PETG, qualquer bico | **Não há projeto.** Peça que salvem o projeto-base antes de gerar | Não monte um projeto de PETG trocando valores à mão num projeto de PLA |

## Como salvar cada um (Creality Print 7, modo Expert)
1. File → New Project.
2. Escolha **Printer**, **Filament** e **Process** da tabela, sem alterar nada (sem `*` no nome do perfil).
3. Coloque um cubo simples na mesa (botão direito na mesa → Add Primitive → Cube, ou importe qualquer STL pequeno).
4. Mesa: **High Temp Plate**.
5. File → Save Project As… com o nome da tabela, dentro desta pasta.
6. Confira: `uv run .claude/skills/creality-print-3mf/checklist_3mf.py projetos-base/<arquivo>.3mf`. O filamento tem de sair "igual ao preset do repositório".
7. Commit e PR numa branch `perfil/<assunto>`.

Ao mudar o preset de um filamento, salve de novo o projeto correspondente e anote a data aqui.

## Por que não gerar pela linha de comando
Testado em 22/11/2026 no Mac (Creality Print 7.2.2): `CrealityPrint --load-settings ... --load-filaments ... --export-3mf` gera um projeto a partir dos presets, mas ele não serve de base:
- os presets de usuário não são aceitos como estão (falta o campo `type`); só entram com a herança resolvida à mão;
- o projeto sai com `different_settings_to_system` vazio, sem as miniaturas, com `Cool Plate` e com a peça posicionada de outro jeito (o `gerar_projeto_creality.py` erraria a altura);
- o 7.2.2 grava 592 chaves, contra 661 de um projeto salvo no 7.3.
Por isso o projeto-base continua sendo salvo pelo programa.
