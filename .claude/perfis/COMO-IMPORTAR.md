# Como importar os perfis da K1 Max em outro computador

Os perfis de filamento, bico (impressora) e processo do Alexandre ficam salvos neste repositório, exportados do Creality Print 7.3 dele.

## O que tem aqui
| Arquivo | Para quê |
|---|---|
| `perfis_creality_7.3.zip` | **Todos os perfis num arquivo só.** É o mais fácil de importar. |
| `creality-print-7.3/machine/` | Impressora com bico 0,2 (`Creality K1 Max 0.2 nozzle`) |
| `creality-print-7.3/filament/` | PLA FLEXYGREEN e PETG MASTERPRINT (bico 0,4 e versões `@… 0.2 nozzle`), CR-PETG e Hyper PLA para o bico 0,2 |
| `creality-print-7.3/process/` | 0.08mm Detalhe Miniaturas (0,2), 0.10mm Standard (0,2), 0.20mm PLA FLEXY 0.07 tolerancia furo, PEÇA DELICADA M5 |
| `K1_Max_bico_0.2_Alexandre.creality_printer` | Pacote antigo só do bico 0,2 (18/11). O zip acima é mais completo e mais novo. |

## Passo a passo (no computador que vai receber)
1. **Creality Print 7.3** instalado, com a impressora **Creality K1 Max (0.4 nozzle)** já adicionada. Todos os perfis herdam dela.
2. **Baixe o zip:** no GitHub, abra `.claude/perfis/perfis_creality_7.3.zip` e clique em **Download raw**. Se usar git, `git pull`.
3. **Feche projetos abertos** no Creality Print e vá em **File → Import → Import Configuration**.
4. **Escolha o `perfis_creality_7.3.zip`** e confirme. Se perguntar se quer substituir perfis com o mesmo nome, responda **Sim**.
   - Também dá para escolher os `.json` soltos da pasta `creality-print-7.3`. Nesse caso, importe primeiro o da pasta `machine`.
5. **Confira:**
   - em **Printer** aparece `Creality K1 Max 0.2 nozzle`;
   - em **Filament** aparecem `PLA FLEXYGREEN` e `PETG MASTERPRINT`. Com a impressora 0,2 selecionada, aparecem as versões `@Creality K1 Max 0.2 nozzle`;
   - em **Process** aparecem os perfis listados acima.

## Observações
- **Mesa do bico 0,2:** o perfil `Creality K1 Max 0.2 nozzle` não fixa o tipo de mesa. Ao selecionar essa impressora, confira se a mesa está em **High Temp Plate**.
- **Projetos .3mf:** um projeto que o Alexandre salvou já leva todas as configurações dentro. Dá para abrir e imprimir mesmo sem importar nada. Os perfis servem para criar projetos novos.
- **Outra opção:** entrar no Creality Print com a mesma conta Creality do Alexandre sincroniza os perfis pela nuvem automaticamente. Use só se ele concordar em compartilhar a conta.

## Para o Alexandre: atualizar depois de mudar um perfil
1. No PowerShell, na pasta do repositório:
   `powershell -ExecutionPolicy Bypass -File .claude\perfis\exportar_perfis.ps1`
2. Faça commit e push. O irmão baixa o zip novo e importa de novo (passos 2 a 4).
