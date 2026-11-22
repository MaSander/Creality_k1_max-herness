# Peças

Uma pasta por peça (`pecas/<nome-da-peca>/`), sempre com um `README.md` de registro: origem e licença, configuração aprovada, resultado e lições.

## O que vai para o git
| Arquivo | Onde | Por quê |
|---|---|---|
| `README.md` (registro) | git | Texto leve; o histórico mostra o que mudou |
| Peças **nossas** (`.sc`, `.step`, `.stl`, `.3mf`) | git via **LFS** (`.gitattributes`) | Projeto fonte, editável e reaproveitável |
| Modelos de **terceiros** e projetos que contêm as malhas deles | `local/` (ignorada) | O repositório é **público**: só suba se a licença permitir redistribuir |
| G-code e logs do fatiador | não guardar (`*.gcode` ignorado) | Saem iguais de novo do `.3mf` com o `fatiar_3mf.py` |

Antes de subir um modelo baixado, **confira a licença** (no MakerWorld, ela fica no `3D/3dmodel.model`, `<metadata name="License">`). "Standard Digital File License" e licenças "NoDerivatives" ou "não redistribuir" ficam em `local/`.

## Git LFS
- Mac: `brew install git-lfs && git lfs install` (já feito no Mac do Marcelo em 21/11/2026).
- Windows: já vem com o Git for Windows; rode `git lfs install` uma vez.
- O armazenamento LFS conta na cota da conta dona do repositório (Marcelo, desde 22/11/2026): 10 GB de armazenamento e 10 GB de download por mês no plano gratuito. Arquivo apagado **não** libera espaço no LFS.
