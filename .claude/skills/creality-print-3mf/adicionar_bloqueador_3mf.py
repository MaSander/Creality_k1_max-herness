#!/usr/bin/env python3
"""
Adiciona caixas de BLOQUEIO (ou REFORCO) de suporte a um objeto de um projeto .3mf do Creality Print 7,
sem abrir o programa. Estrutura copiada de um projeto real do Creality (partes extras = type="other"
no object_N.model + component no 3dmodel.model + <part subtype=...> no model_settings.config).

Uso:
  uv run .claude/skills/creality-print-3mf/adicionar_bloqueador_3mf.py ENTRADA.3mf SAIDA.3mf --caixas caixas.json \
      [--tipo support_blocker|support_enforcer] [--objeto 1]
  (o JSON tambem pode vir escrito na linha, depois da SAIDA; no PowerShell use sempre o arquivo)

  JSON das caixas: lista em coordenadas da MESA (mm, como no fatiador; mesa 0..300):
    [{"nome":"Bloqueador bico frontal","min":[145,173,0],"max":[162,181,3.6]}]

Confira depois no Creality: os itens aparecem dentro do objeto na lista; ao fatiar, nao ha suporte na caixa.
"""
import argparse, re, sys, zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ferramentas"))
import k1comum


def caixa_xml(oid, uuid, mn, mx, tipo_obj="other"):
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    vs = "".join(f'<vertex x="{a:.6f}" y="{b:.6f}" z="{c:.6f}"/>' for a, b, c in v)
    ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
    return f'<object id="{oid}" p:UUID="{uuid}" type="{tipo_obj}"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>'


def main():
    k1comum.saida_utf8()
    ap = argparse.ArgumentParser(description="Adiciona caixas de bloqueio ou reforco de suporte a um .3mf.")
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("caixas", nargs="?", help="JSON com a lista de caixas")
    ap.add_argument("--caixas", dest="arquivo", help="arquivo .json com a lista de caixas")
    ap.add_argument("--tipo", default="support_blocker", choices=["support_blocker", "support_enforcer"])
    ap.add_argument("--objeto", default="1")
    a = ap.parse_args()
    src, dst, tipo, n_obj = a.entrada, a.saida, a.tipo, a.objeto
    caixas = k1comum.ler_json(a.caixas, a.arquivo, None)
    if not caixas:
        ap.error("informe as caixas (JSON na linha ou --caixas arquivo.json)")
    k1comum.exigir_saida_diferente(src, dst)
    for c in caixas:
        fora = [i for i in range(3) if c["min"][i] < 0 or c["max"][i] > k1comum.MESA[i] or c["min"][i] >= c["max"][i]]
        if fora:
            raise SystemExit(f"caixa fora da mesa (0..300 mm) ou com min >= max: {c}")
    path = f"3D/Objects/object_{n_obj}.model"
    with zipfile.ZipFile(src) as z:
        if path not in z.namelist():
            raise SystemExit(f"o projeto nao tem {path} (confira --objeto)")
        obj = z.read(path).decode()
        m3 = z.read("3D/3dmodel.model").decode()
        ms = z.read("Metadata/model_settings.config").decode()

    achado = re.search(rf'<component p:path="/{re.escape(path)}"[^>]*/>', m3)
    if not achado:
        raise SystemExit(f"nao achei o componente de {path} no 3dmodel.model")
    comp = achado.group(0)
    comp_t = np.array(list(map(float, re.search(r'transform="([^"]+)"', comp).group(1).split())))
    wrapper = re.search(r'<object id="(\d+)"[^>]*>\s*<components>\s*' + re.escape(comp), m3).group(1)
    item_t = np.array(list(map(float, re.search(rf'<item objectid="{wrapper}"[^>]*transform="([^"]+)"', m3).group(1).split())))
    # transform 3MF: 12 numeros (3x3 por linhas de vetores + translacao). Converter mesa -> local do objeto
    def mat(t):
        M = np.eye(4); M[:3, :3] = t[:9].reshape(3, 3).T; M[:3, 3] = t[9:]; return M
    inv = np.linalg.inv(mat(item_t) @ mat(comp_t))

    ids = [int(i) for i in re.findall(r'<object id="(\d+)"', obj)] + [int(i) for i in re.findall(r'<object id="(\d+)"', m3)]
    novo = max(ids) + 1
    xml_objs, comps, parts = "", "", ""
    for k, c in enumerate(caixas):
        cantos = np.array([[x, y, zz, 1] for x in (c["min"][0], c["max"][0]) for y in (c["min"][1], c["max"][1]) for zz in (c["min"][2], c["max"][2])])
        loc = (inv @ cantos.T).T[:, :3]
        oid = novo + k
        uuid = f"{int(n_obj):04x}{k + 1:04x}-81cb-4c03-9d28-80fed5dfa1dc"
        xml_objs += caixa_xml(oid, uuid, loc.min(0), loc.max(0))
        comps += comp.replace(re.search(r'objectid="\d+"', comp).group(0), f'objectid="{oid}"').replace(
            re.search(r'p:UUID="[^"]+"', comp).group(0), f'p:UUID="{int(n_obj):04x}{k + 1:04x}-b206-40ff-9872-83e8017abed1"')
        parts += (f'\n    <part id="{oid}" subtype="{tipo}">\n      <metadata key="name" value="{c.get("nome", "Bloqueador")}"/>\n'
                  f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                  f'      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>')
    obj = obj.replace("</resources>", xml_objs + "</resources>")
    m3 = m3.replace(comp, comp + comps)
    i = ms.index(f'<object id="{wrapper}">'); j = ms.index("</object>", i)
    last_part = ms.rindex("</part>", i, j) + len("</part>")
    ms = ms[:last_part] + parts + ms[last_part:]

    k1comum.copiar_zip(src, dst, {path: obj.encode(), "3D/3dmodel.model": m3.encode(),
                                  "Metadata/model_settings.config": ms.encode()})
    print(f"ok: {len(caixas)} caixa(s) {tipo} no objeto {wrapper} -> {dst}")


if __name__ == "__main__":
    main()
