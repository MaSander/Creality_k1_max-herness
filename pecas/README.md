# Peças

Uma pasta por peça (`pecas/<nome-da-peca>/`), sempre com um `README.md` de registro: origem e licença, configuração aprovada, resultado e lições.

## O que vai para o git
| Arquivo | Onde | Por quê |
|---|---|---|
| `README.md` (registro) | git | Texto leve; o histórico mostra o que mudou |
| Peças **nossas**: fonte (`.sc`, `.step`, script gerador) e **só a versão aprovada/atual** (`.stl` ou, de preferência, `.3mf`) | git via **LFS** (`.gitattributes`) | Projeto fonte, editável e reaproveitável |
| **Versões intermediárias** (v1, v2… de cada iteração) | `local/` (ignorada) + backup no Drive pessoal | Cada versão tem ~20 MB, e arquivo que sobe no LFS nunca libera espaço. A peça gerada por script se refaz pelo commit do script |
| Modelos de **terceiros** e projetos que contêm as malhas deles | `local/` (ignorada) | O repositório é **público**: só suba se a licença permitir redistribuir |
| G-code e logs do fatiador | não guardar (`*.gcode` ignorado) | Saem iguais de novo do `.3mf` com o `fatiar_3mf.py` |

Antes de subir um modelo baixado, **confira a licença** (no MakerWorld, ela fica no `3D/3dmodel.model`, `<metadata name="License">`). "Standard Digital File License" e licenças "NoDerivatives" ou "não redistribuir" ficam em `local/`.

## Backup das versões intermediárias (por enquanto)
- **Marcelo:** Google Drive pessoal, pasta `3D/K1-Max/pecas/<nome-da-peca>/`, com o mesmo nome de arquivo de `local/`.
- **Alexandre:** a mesma pasta do Marcelo (`3D/K1-Max/pecas/<nome-da-peca>/`), compartilhada com ele como editor e com atalho no Meu Drive dele (no PC dele, `G:\Meu Drive\3D\K1-Max\pecas\`).
- Ao trocar de versão, mova a anterior para `local/` (e para o backup) e deixe no git só a atual.

## Git LFS
- Mac: `brew install git-lfs && git lfs install` (já feito no Mac do Marcelo em 21/11/2026).
- Windows: já vem com o Git for Windows; rode `git lfs install` uma vez.
- O armazenamento LFS conta na cota da conta dona do repositório (Alexandre).
