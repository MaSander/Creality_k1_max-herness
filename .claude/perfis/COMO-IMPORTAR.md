# Perfis do Creality Print: sincronizar entre o programa e o repositório

Os presets de usuário do **Creality Print do Alexandre** (impressora do bico 0,2, filamentos e processos) são a **fonte dos valores**. O repositório guarda uma cópia deles, e é dela que saem a tabela da skill `k1max-config-impressao` e a conferência do `checklist_3mf.py`.

| Aqui | O que é |
|---|---|
| `creality-print/machine/`, `filament/`, `process/` | Os presets, um `.json` cada (só o que difere do perfil de fábrica) |
| `perfis_creality.zip` | Os mesmos presets num arquivo só, para importar |
| `sincronizar_perfis.py` | Compara, exporta e gera a tabela. Roda igual no Windows e no macOS e **nunca escreve na pasta do programa** |
| `K1_Max_bico_0.2_Alexandre.creality_printer` | Pacote antigo só do bico 0,2 (18/11/2026). O zip é mais completo e mais novo |

Todos os comandos são da raiz do repositório.

## Ver se o programa e o repositório estão iguais
```
uv run .claude/perfis/sincronizar_perfis.py comparar
```
Mostra, preset por preset e chave por chave, o que só existe de um lado e o que tem valor diferente.

## Mudei um preset no Creality Print (programa → repositório)
1. No Creality Print, salve a mudança **por cima do mesmo preset** (não com "salvar como").
2. `uv run .claude/perfis/sincronizar_perfis.py exportar`
   - Mostra o que é novo e o que mudou, copia para `creality-print/` e refaz o zip.
   - Preset que está no repositório e não está no programa é **mantido**. Para apagar de propósito, acrescente `--remover-ausentes`.
3. `uv run .claude/perfis/sincronizar_perfis.py tabela --gravar` (atualiza a tabela da skill `k1max-config-impressao`).
4. Commit e PR numa branch `perfil/<assunto>`.

## O repositório mudou (repositório → programa)
1. `git pull`.
2. No Creality Print, com a impressora **Creality K1 Max (0.4 nozzle)** já adicionada (todos os perfis herdam dela): feche os projetos abertos e vá em **File → Import → Import Configuration**.
3. Escolha `perfis_creality.zip` e confirme. Se perguntar se quer substituir perfis com o mesmo nome, responda **Sim**.
   - Também dá para escolher os `.json` soltos de `creality-print/`. Nesse caso, importe primeiro o da pasta `machine`.
4. Confira com `comparar`: tem de responder "Iguais.".

## Conferir no programa depois de importar
- em **Printer** aparece `Creality K1 Max 0.2 nozzle`;
- em **Filament** aparecem `PLA FLEXYGREEN` e `PETG MASTERPRINT`. Com a impressora 0,2 selecionada, aparecem as versões `@Creality K1 Max 0.2 nozzle`;
- em **Process** aparecem os processos da pasta `process/`.

## Observações
- **Mesa do bico 0,2:** o perfil `Creality K1 Max 0.2 nozzle` não fixa o tipo de mesa. Ao selecionar essa impressora, confira se a mesa está em **High Temp Plate**.
- **Projetos .3mf:** um projeto salvo já leva todas as configurações dentro. Dá para abrir e imprimir sem importar nada. Os presets servem para criar projetos novos.
- **Onde o programa guarda os presets** (só para saber; não edite lá): no Windows, `%APPDATA%\Creality\Creality Print\<versão>\user\<conta>`; no macOS, `~/Library/Application Support/Creality/Creality Print/<versão>/user/<conta>`. O script acha sozinho a versão mais nova; se não achar, passe `--dados <pasta da versão>`.
- **Tabela e perfis de fábrica:** a tabela resolve a herança com os perfis de fábrica do computador onde foi gerada. Versões diferentes do Creality Print podem ter perfis de fábrica diferentes; os valores em negrito (definidos no preset) não dependem disso.
- **Filamento calibrado pela skill `calibrar-filamento-novo`:** o preset exportado em `filamentos/<slug>/` é importado no programa pelo mesmo menu. Depois de importar, rode `exportar` para ele entrar aqui também.
- **Outra opção:** entrar no Creality Print com a mesma conta Creality sincroniza os presets pela nuvem. Use só se o dono da conta concordar em compartilhar.
- **Em 22/11/2026:** o Creality Print do Mac do Marcelo não tinha nenhum preset de usuário; o primeiro passo lá é importar o zip.
