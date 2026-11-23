#!/usr/bin/env python3
"""
Gera um projeto .3mf do Creality Print 7 (base OrcaSlicer) sem abrir o programa.

Como funciona
-------------
Um .3mf e um arquivo ZIP. Num projeto salvo pelo Creality Print ha:
  3D/3dmodel.model                 -> itens na mesa (posicao/rotacao = atributo "transform")
  3D/Objects/object_1.model        -> a malha (vertices e triangulos)
  Metadata/project_settings.config -> JSON com TODAS as configuracoes (impressora, filamento, processo)
  Metadata/model_settings.config   -> nome do objeto e transform de montagem
  (+ miniaturas, plate_1.json, rels)
As miniaturas (plate_1.png etc.) sao redesenhadas da malha nova: o fatiamento pela linha
de comando copia plate_1.png para o G-code, e a do MODELO mostraria outra peca na tela.

O script usa um projeto MODELO salvo pelo proprio usuario (com 1 objeto na mesa),
troca a malha, posiciona no centro da mesa, pega as configuracoes de um projeto do
usuario (para herdar os perfis e calibracoes dele) e altera so as chaves pedidas.

Uso
---
  uv run .claude/skills/creality-print-3mf/gerar_projeto_creality.py MODELO.3mf CONFIG.3mf peca.stl SAIDA.3mf NOME --config mudancas.json
  (o JSON também pode vir escrito na linha, depois do NOME; no PowerShell use sempre o arquivo)

  MODELO.3mf : projeto salvo no Creality Print com 1 objeto (so a estrutura e usada)
  CONFIG.3mf : projeto do usuario de onde vem o project_settings (perfil de filamento calibrado)
  peca.stl   : malha ja escalada e orientada (mm). Pode conter varias pecas (vira 1 objeto)
  JSON       : chaves de PROCESSO a alterar, por exemplo {"layer_height":"0.12","outer_wall_speed":"80"}

Regras importantes
------------------
- Nao altere chaves de filamento (filament_*, nozzle_temperature*, hot_plate_temp*, fan_*,
  pressure_advance, slow_down_*) se o usuario calibrou o filamento.
- Para o brim encostar na peca: "brim_object_gap":"0" E "elefant_foot_compensation":"0".
- O script registra cada chave alterada no grupo certo de different_settings_to_system
  ([0] processo, [1] filamento, [2] impressora), senao o Creality pode tratar o valor como perfil de fabrica.
"""
import argparse, io, json, re, struct, sys, zipfile
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ferramentas"))
import k1comum

# Imagens da placa que o Creality grava no .3mf. Fatiando pela linha de comando ele NAO
# redesenha: copia Metadata/plate_1.png para a miniatura do G-code (tela da impressora).
# Por isso elas sao redesenhadas aqui a partir da malha nova (senao fica a peca do MODELO).
# (pick_1.png e um mapa de cliques que o programa refaz ao abrir; fica como esta.)
PLATE_IMAGES = {"Metadata/plate_1.png": "iso", "Metadata/plate_1_small.png": "iso",
                "Metadata/plate_no_light_1.png": "iso", "Metadata/top_1.png": "top"}

def png_size(data):
    return struct.unpack(">II", data[16:24])


def render_png(mesh, size, view="iso"):
    """Desenha a malha (laranja, fundo transparente) num PNG quadrado de size x size."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    m = mesh
    if len(m.faces) > 60000:                 # so para desenhar; a malha impressa nao muda
        import fast_simplification
        v, f = fast_simplification.simplify(m.vertices, m.faces, target_count=60000)
        m = trimesh.Trimesh(v, f, process=False)
    tri = m.vertices[m.faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    luz = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])
    sombra = 0.25 + 0.75 * np.clip(n @ luz, 0, 1)
    cores = np.c_[np.outer(sombra, [0.95, 0.55, 0.15]), np.ones(len(sombra))]

    fig = plt.figure(figsize=(size[0] / 100, size[1] / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=cores, edgecolor="none"))
    lo, hi = m.bounds
    c, r = (lo + hi) / 2, (hi - lo).max() / 2 * 0.85
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.axis("off")
    ax.view_init(elev=90, azim=-90) if view == "top" else ax.view_init(elev=28, azim=-60)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()


def main():
    k1comum.saida_utf8()
    ap = argparse.ArgumentParser(description="Gera um .3mf do Creality Print 7 a partir de um projeto modelo.")
    ap.add_argument("modelo", help="projeto .3mf com 1 objeto na mesa (so a estrutura e usada)")
    ap.add_argument("config", help="projeto .3mf de onde vem o project_settings")
    ap.add_argument("malha", help="STL (ou outro formato de malha) ja escalado e orientado, em mm")
    ap.add_argument("saida")
    ap.add_argument("nome", help="nome do objeto no projeto")
    ap.add_argument("mudancas", nargs="?", help="JSON com as chaves a alterar")
    ap.add_argument("--config", dest="arquivo", help="arquivo .json com as chaves a alterar")
    a = ap.parse_args()
    tmpl, settings_src, mesh_path, dst, name = a.modelo, a.config, a.malha, a.saida, a.nome
    changes = k1comum.ler_json(a.mudancas, a.arquivo, {})
    for entrada in (tmpl, settings_src):
        k1comum.exigir_saida_diferente(entrada, dst)

    # 1) malha: centraliza na origem em XY e com o meio da altura em z=0 (padrao do Creality)
    mesh = trimesh.load(mesh_path, force="mesh")
    bed_center = (k1comum.MESA[0] / 2, k1comum.MESA[1] / 2)
    half_h = mesh.extents[2] / 2
    c = mesh.bounds.mean(axis=0)
    mesh.apply_translation([-c[0], -c[1], -mesh.bounds[0][2] - half_h])

    with zipfile.ZipFile(tmpl) as zin:
        arquivos = {n: zin.read(n) for n in zin.namelist()}
    obj = arquivos["3D/Objects/object_1.model"].decode()
    head = obj[:obj.index("<vertices>")]
    tail = obj[obj.index("</triangles>") + len("</triangles>"):]
    verts = "".join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in mesh.vertices)
    tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c_}"/>' for a, b, c_ in mesh.faces)
    new_obj = head + "<vertices>" + verts + "</vertices><triangles>" + tris + "</triangles>" + tail

    # 2) configuracoes: copia do projeto do usuario e altera so o pedido
    with zipfile.ZipFile(settings_src) as z:
        settings = json.loads(z.read("Metadata/project_settings.config"))
    k1comum.aplicar_mudancas(settings, changes)

    # 3) transform do item na mesa (posicao do centro da peca)
    transform = f"1 0 0 0 1 0 0 0 1 {bed_center[0]} {bed_center[1]} {half_h:.6f}"

    trocar = {"3D/Objects/object_1.model": new_obj.encode(),
              "Metadata/project_settings.config": json.dumps(settings, indent=4, ensure_ascii=False).encode()}
    t = arquivos["3D/3dmodel.model"].decode()
    t, n = re.subn(r'(<item objectid="\d+"[^>]*?transform=")[^"]+(")', r"\g<1>" + transform + r"\2", t)
    if n != 1:
        raise SystemExit("o MODELO precisa ter exatamente 1 objeto na mesa")
    trocar["3D/3dmodel.model"] = t.encode()
    t = arquivos["Metadata/model_settings.config"].decode()
    t = re.sub(r'(assemble_item[^>]*?transform=")[^"]+(")', r"\g<1>" + transform + r"\2", t)
    t = re.sub(r'(<metadata key="name" value=")[^"]*(")', r"\g<1>" + name + r"\2", t)
    trocar["Metadata/model_settings.config"] = t.encode()
    redesenhadas = {}
    for f, vista in PLATE_IMAGES.items():
        if f in arquivos:
            redesenhadas[f] = png_size(arquivos[f])
            trocar[f] = render_png(mesh, redesenhadas[f], vista)
    k1comum.copiar_zip(tmpl, dst, trocar)

    # 4) conferencia
    with zipfile.ZipFile(dst) as z:
        for f, tam in redesenhadas.items():
            if png_size(z.read(f)) != tam:
                raise SystemExit(f"miniatura com tamanho errado: {f}")
    if "Metadata/plate_1.png" not in redesenhadas:
        print("AVISO: o MODELO nao tem Metadata/plate_1.png; o G-code pode sair sem miniatura")
    print("miniaturas redesenhadas:", ", ".join(redesenhadas) or "nenhuma")
    print("ok:", dst)


if __name__ == "__main__":
    main()
