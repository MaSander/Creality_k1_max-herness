"""Prévia (PNG com 4 vistas, renderizada por raio) e análise de balanço de um STL do suporte.

Uso: uv run pecas/suporte-headset-parede/previa.py <arquivo.stl> <saida.png> [resolucao]
"""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

tm = trimesh.load(sys.argv[1])
saida = sys.argv[2]
res = int(sys.argv[3]) if len(sys.argv) > 3 else 300

n = tm.face_normals
c = tm.triangles_center
baixo = (n[:, 2] < -np.cos(np.radians(45))) & (c[:, 2] > 0.3)
print(f"área em balanço >45°: {tm.area_faces[baixo].sum():.1f} mm² (de {tm.area:.0f} mm²)")
if baixo.any():
    print("  z dessas faces: min %.1f max %.1f" % (c[baixo, 2].min(), c[baixo, 2].max()))
    zb = c[baixo, 2]; ab = tm.area_faces[baixo]
    for z0 in range(0, 110, 10):
        s = ab[(zb >= z0) & (zb < z0 + 10)].sum()
        if s > 1: print(f"    z {z0:3d}-{z0+10:3d}: {s:6.1f} mm²")
base = (n[:, 2] < -0.999) & (c[:, 2] < 0.01)
print(f"área apoiada na mesa (fita VHB): {tm.area_faces[base].sum():.0f} mm²")

# Vistas em uso: parede = plano XY do modelo, Y para cima, Z sai da parede.
# Renderização por pontos (amostra densa da superfície + z-buffer), rápida e sem dependências.
pts, fid = trimesh.sample.sample_surface_even(tm, 1_500_000) if False else trimesh.sample.sample_surface(tm, 2_500_000)
pn = n[fid]
bal = baixo[fid]

def vista(dir_cam, up):
    d = np.asarray(dir_cam, float); d /= np.linalg.norm(d)
    u = np.asarray(up, float); u = u - d * (u @ d); u /= np.linalg.norm(u)
    r = np.cross(d, u)
    ctr = tm.bounds.mean(0); R = np.linalg.norm(tm.extents) / 2 * 1.02
    q = pts - ctr
    px = ((q @ r) / R * 0.5 + 0.5) * (res - 1)
    py = ((-(q @ u)) / R * 0.5 + 0.5) * (res - 1)
    depth = q @ d
    ix = np.clip(px.round().astype(int), 0, res - 1); iy = np.clip(py.round().astype(int), 0, res - 1)
    pix = iy * res + ix
    ordem = np.lexsort((depth, pix))           # por pixel, o mais próximo primeiro
    pix_o = pix[ordem]
    prim = np.ones(len(pix_o), bool); prim[1:] = pix_o[1:] != pix_o[:-1]
    sel = ordem[prim]
    img = np.ones((res * res, 3))
    nn = pn[sel]
    luz = -d + 0.6 * u - 0.5 * r; luz /= np.linalg.norm(luz)
    dif = np.clip(nn @ luz, 0, 1)
    spec = np.clip(nn @ (-d), 0, 1) ** 20
    base_cor = np.where(bal[sel][:, None], [0.85, 0.2, 0.15], [0.93, 0.89, 0.80])
    img[pix[sel]] = np.clip(base_cor * (0.25 + 0.75 * dif[:, None]) + 0.12 * spec[:, None], 0, 1)
    return img.reshape(res, res, 3)

Y = [0, 1, 0]
vistas = [("Isométrica", [-1, -0.6, -1.1], Y), ("Frente", [0, 0, -1], Y),
          ("Lado", [1, 0, 0], Y), ("De baixo (vermelho = balanço na impressão)", [0.7, 1, -0.6], [0, 0, 1])]
fig, axs = plt.subplots(2, 2, figsize=(12, 12), dpi=100)
for ax, (tit, d, up) in zip(axs.flat, vistas):
    ax.imshow(vista(d, up)); ax.set_title(tit); ax.axis("off")
plt.tight_layout(); plt.savefig(saida)
print("prévia:", saida)
