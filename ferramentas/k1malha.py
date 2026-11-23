"""Leitura de malhas (arquivo solto ou dentro de um .3mf) e análise de imprimibilidade na K1 Max.

Usado por analisar_malha.py e checklist_3mf.py (skill creality-print-3mf). Precisa de numpy e trimesh.
"""
from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, field

import numpy as np
import trimesh

import k1comum

TOL_CONTATO = 0.05   # mm acima do ponto mais baixo que ainda conta como apoiado na mesa
AREA_MIN_REGIAO = 1.0  # mm²: balanços menores que isto não são listados


# --- leitura -------------------------------------------------------------------------------
@dataclass
class Parte:
    nome: str
    subtipo: str            # normal_part, support_blocker, support_enforcer, modifier_part, negative_part
    malha: trimesh.Trimesh  # já em coordenadas da mesa


@dataclass
class Projeto:
    settings: dict
    partes: list[Parte] = field(default_factory=list)
    arquivos: list[str] = field(default_factory=list)

    def pecas(self):
        return [p for p in self.partes if p.subtipo == "normal_part"]


def _matriz(texto: str) -> np.ndarray:
    """transform do 3MF: 12 números (3x3 por linhas de vetores + translação) -> matriz 4x4."""
    t = np.array(texto.split(), dtype=float)
    m = np.eye(4)
    m[:3, :3] = t[:9].reshape(3, 3).T
    m[:3, 3] = t[9:]
    return m


def _atributo(tag: str, nome: str, padrao=None):
    m = re.search(rf'\b{re.escape(nome)}="([^"]*)"', tag)
    return m.group(1) if m else padrao


def _objetos(xml: str) -> dict[str, str]:
    """id -> bloco <object ...>...</object> de um arquivo .model."""
    return {_atributo(m.group(1), "id"): m.group(0)
            for m in re.finditer(r"(<object\b[^>]*>).*?</object>", xml, re.S)}


def _malha(bloco: str) -> trimesh.Trimesh | None:
    if "<vertices>" not in bloco:
        return None
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', bloco), dtype=float)
    f = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', bloco), dtype=np.int64)
    # process=False: o fatiador usa os triângulos por índice, sem fundir vértices
    return trimesh.Trimesh(v, f, process=False)


def ler_3mf(caminho: str) -> Projeto:
    """Lê um projeto do Creality Print: configurações e todas as partes, em coordenadas da mesa."""
    with zipfile.ZipFile(caminho) as z:
        nomes = z.namelist()
        ruim = z.testzip()
        if ruim:
            raise SystemExit(f"ZIP corrompido: {ruim}")
        settings = json.loads(z.read("Metadata/project_settings.config")) \
            if "Metadata/project_settings.config" in nomes else {}
        principal = z.read("3D/3dmodel.model").decode("utf-8")
        ms = z.read("Metadata/model_settings.config").decode("utf-8") \
            if "Metadata/model_settings.config" in nomes else ""
        cache = {"/3D/3dmodel.model": _objetos(principal)}

        def objetos_de(caminho_interno):
            if caminho_interno not in cache:
                cache[caminho_interno] = _objetos(z.read(caminho_interno.lstrip("/")).decode("utf-8"))
            return cache[caminho_interno]

        info_partes = {}  # id da parte -> (subtipo, nome)
        for m in re.finditer(r'<part id="(\d+)" subtype="([^"]+)">(.*?)</part>', ms, re.S):
            nome = re.search(r'key="name" value="([^"]*)"', m.group(3))
            info_partes[m.group(1)] = (m.group(2), nome.group(1) if nome else "")

        projeto = Projeto(settings=settings, arquivos=nomes)
        for item in re.finditer(r"<item\b[^>]*>", principal):
            if _atributo(item.group(0), "printable", "1") == "0":
                continue
            m_item = _matriz(_atributo(item.group(0), "transform", "1 0 0 0 1 0 0 0 1 0 0 0"))
            bloco = cache["/3D/3dmodel.model"].get(_atributo(item.group(0), "objectid"), "")
            componentes = re.findall(r"<component\b[^>]*>", bloco)
            if not componentes:  # malha direto no 3dmodel.model (3MF de outros programas)
                malha = _malha(bloco)
                if malha is not None:
                    malha.apply_transform(m_item)
                    projeto.partes.append(Parte("", "normal_part", malha))
                continue
            for comp in componentes:
                oid = _atributo(comp, "objectid")
                origem = _atributo(comp, "p:path", "/3D/3dmodel.model")
                malha = _malha(objetos_de(origem).get(oid, ""))
                if malha is None:
                    continue
                malha.apply_transform(m_item @ _matriz(_atributo(comp, "transform", "1 0 0 0 1 0 0 0 1 0 0 0")))
                subtipo, nome = info_partes.get(oid, ("normal_part", ""))
                projeto.partes.append(Parte(nome, subtipo, malha))
    return projeto


def carregar_malha(caminho: str) -> trimesh.Trimesh:
    """Malha de um arquivo solto (STL, OBJ, GLB, PLY...), com os vértices repetidos fundidos."""
    return trimesh.load(caminho, force="mesh")


def juntar(malhas) -> trimesh.Trimesh:
    malhas = list(malhas)
    return malhas[0] if len(malhas) == 1 else trimesh.util.concatenate(malhas)


# --- análise -------------------------------------------------------------------------------
def _componentes(malha, faces):
    """Grupos de faces vizinhas dentro do conjunto `faces` (índices)."""
    marcado = np.zeros(len(malha.faces), dtype=bool)
    marcado[faces] = True
    adj = malha.face_adjacency
    adj = adj[marcado[adj].all(axis=1)]
    return trimesh.graph.connected_components(adj, nodes=faces)


def analisar(malha: trimesh.Trimesh, angulo: float = 45.0, brim: float = 0.0, na_mesa: bool = False) -> dict:
    """Mede o que importa para imprimir. `angulo`: inclinação (a partir da horizontal) abaixo da qual
    a face precisa de suporte. `na_mesa`: a malha já está em coordenadas da mesa (0..300)."""
    lo, hi = malha.bounds
    n = malha.face_normals
    area = malha.area_faces
    z_face_max = malha.vertices[malha.faces][:, :, 2].max(axis=1)

    contato = (n[:, 2] < -0.99) & (z_face_max <= lo[2] + TOL_CONTATO)
    balanco = (-n[:, 2] > np.cos(np.radians(angulo))) & ~contato

    regioes = []
    idx = np.flatnonzero(balanco)
    if len(idx):
        for grupo in _componentes(malha, idx):
            a = float(area[grupo].sum())
            if a < AREA_MIN_REGIAO:
                continue
            pts = malha.triangles_center[grupo]
            regioes.append({"area_mm2": round(a, 1),
                            "centro_xy": [round(float(c), 1) for c in pts[:, :2].mean(axis=0)],
                            "z_min": round(float(pts[:, 2].min() - lo[2]), 2),
                            "z_max": round(float(pts[:, 2].max() - lo[2]), 2)})
        regioes.sort(key=lambda r: -r["area_mm2"])

    corpos = trimesh.graph.connected_components(malha.face_adjacency, nodes=np.arange(len(malha.faces)))
    z_vert = malha.vertices[:, 2]
    sem_apoio = sum(1 for c in corpos if z_vert[malha.faces[c]].min() > lo[2] + TOL_CONTATO)

    mesa = np.array(k1comum.MESA)
    if na_mesa:
        cabe = bool(lo[0] - brim >= 0 and lo[1] - brim >= 0 and lo[2] >= -TOL_CONTATO
                    and hi[0] + brim <= mesa[0] and hi[1] + brim <= mesa[1] and hi[2] <= mesa[2])
    else:
        ext = hi - lo
        cabe = bool(ext[0] + 2 * brim <= mesa[0] and ext[1] + 2 * brim <= mesa[1] and ext[2] <= mesa[2])

    return {
        "dimensoes_mm": [round(float(x), 3) for x in hi - lo],
        "minimo": [round(float(x), 3) for x in lo],
        "maximo": [round(float(x), 3) for x in hi],
        "faces": int(len(malha.faces)),
        "fechada": bool(malha.is_watertight),
        "volume_valido": bool(malha.is_volume),
        "volume_cm3": round(float(malha.volume) / 1000, 3),
        "corpos": len(corpos),
        "corpos_sem_apoio_na_mesa": int(sem_apoio),
        "area_contato_mm2": round(float(area[contato].sum()), 1),
        "angulo_suporte": angulo,
        "area_balanco_mm2": round(float(area[balanco].sum()), 1),
        "regioes_balanco": regioes,
        "brim_mm": brim,
        "cabe_na_mesa": cabe,
        "_contato": contato,
        "_balanco": balanco,
    }


def problemas(a: dict) -> list[str]:
    """O que reprova a malha para impressão."""
    p = []
    if not a["fechada"]:
        p.append("malha aberta (não é watertight)")
    elif not a["volume_valido"]:
        p.append("malha fechada mas com faces invertidas ou volume inválido")
    if not a["cabe_na_mesa"]:
        p.append(f"não cabe na mesa de 300 x 300 x 300 mm (com brim de {a['brim_mm']:g} mm)")
    if a["area_contato_mm2"] <= 0:
        p.append("nenhuma face plana apoiada na mesa (área de contato 0)")
    return p


def _vista(pontos, normais, cores, para_camera, direita, lado, centro, raio):
    """Uma vista ortográfica lado x lado, por pontos com z-buffer (o ponto mais perto da câmera ganha)."""
    para_camera = np.asarray(para_camera, float) / np.linalg.norm(para_camera)
    direita = np.asarray(direita, float) / np.linalg.norm(direita)
    cima = np.cross(para_camera, direita)
    rel = pontos - centro
    escala = (lado * 0.46) / raio
    px = np.round(lado / 2 + rel @ direita * escala).astype(np.int64)
    py = np.round(lado / 2 - rel @ cima * escala).astype(np.int64)
    prof = rel @ para_camera
    luz = 0.45 + 0.55 * np.abs(normais @ para_camera)
    cor = np.clip(cores * luz[:, None] * 255, 0, 255).astype(np.uint8)
    xs, ys, ds, cs = [], [], [], []
    for dx in (0, 1):
        for dy in (0, 1):
            xs.append(px + dx); ys.append(py + dy); ds.append(prof); cs.append(cor)
    px, py, prof, cor = np.concatenate(xs), np.concatenate(ys), np.concatenate(ds), np.concatenate(cs)
    dentro = (px >= 0) & (px < lado) & (py >= 0) & (py < lado)
    px, py, prof, cor = px[dentro], py[dentro], prof[dentro], cor[dentro]
    ordem = np.argsort(prof, kind="stable")  # do mais longe para o mais perto: o último a pintar fica
    img = np.full((lado, lado, 3), 255, dtype=np.uint8)
    img[py[ordem], px[ordem]] = cor[ordem]
    return img


def render(malha: trimesh.Trimesh, a: dict, destino: str, lado: int = 600) -> None:
    """PNG com 4 vistas: balanço em vermelho, contato com a mesa em azul."""
    from PIL import Image, ImageDraw, ImageFont

    lo, hi = malha.bounds
    centro, raio = (lo + hi) / 2, float(np.linalg.norm(hi - lo) / 2) or 1.0
    escala = (lado * 0.46) / raio
    n_pontos = int(min(1_500_000, max(200_000, 3 * malha.area * escala ** 2)))
    pontos, face = trimesh.sample.sample_surface(malha, n_pontos, seed=0)
    cores = np.tile([0.78, 0.78, 0.80], (len(face), 1))
    cores[a["_balanco"][face]] = [0.95, 0.15, 0.15]
    cores[a["_contato"][face]] = [0.15, 0.40, 0.95]
    normais = malha.face_normals[face]

    e, az = np.radians(28), np.radians(-60)
    vistas = [("isométrica", (np.cos(e) * np.cos(az), np.cos(e) * np.sin(az), np.sin(e)), (-np.sin(az), np.cos(az), 0)),
              ("frente", (0, -1, 0), (1, 0, 0)),
              ("de cima", (0, 0, 1), (1, 0, 0)),
              ("de baixo", (0, 0, -1), (-1, 0, 0))]
    topo = 44
    tela = Image.new("RGB", (2 * lado, 2 * lado + topo), "white")
    desenho = ImageDraw.Draw(tela)
    try:  # a fonte padrão do Pillow não tem acentos; a DejaVu vem com o matplotlib
        from matplotlib import font_manager
        fonte = ImageFont.truetype(font_manager.findfont("DejaVu Sans"), 17)
    except Exception:
        fonte = ImageFont.load_default()
    desenho.text((10, 10), f"vermelho: balanço abaixo de {a['angulo_suporte']:g}° ({a['area_balanco_mm2']} mm²)    "
                           f"azul: contato com a mesa ({a['area_contato_mm2']} mm²)", fill="black", font=fonte)
    for i, (titulo, para_camera, direita) in enumerate(vistas):
        x, y = (i % 2) * lado, topo + (i // 2) * lado
        tela.paste(Image.fromarray(_vista(pontos, normais, cores, para_camera, direita, lado, centro, raio)), (x, y))
        desenho.text((x + 10, y + 6), titulo, fill="black", font=fonte)
    tela.save(destino)
