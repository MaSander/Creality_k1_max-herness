# Filamentos calibrados

Uma pasta por filamento, criada e mantida pela skill `calibrar-filamento-novo` (script `perfil_filamento.py`). Não edite os arquivos à mão: use o script, que regera o `perfil.md`.

| Arquivo | O que é |
|---|---|
| `perfil.json` | Estado completo: dados do carretel, parâmetros por bico e histórico de testes |
| `perfil.md` | Mesmo conteúdo em tabela, para ler |
| `<preset> @Creality K1 Max <bico> nozzle.json` | Preset de filamento para importar no Creality Print (*File → Import → Import Configs*) |

Ver tudo o que já foi calibrado:
```
.venv/bin/python .claude/skills/calibrar-filamento-novo/perfil_filamento.py listar
```
