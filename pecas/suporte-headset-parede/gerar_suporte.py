"""Suporte de parede para headset (Logitech PRO X 2), estilo generative design (ossos e tendões).

Estrutura de membros ramificados (grossos nas juntas, finos no meio do vão, como ossos),
unidos com mistura suave (log-soma-exp), o que cria membranas orgânicas nas junções.
A placa de parede tem dois apoios maciços (para a fita VHB) ligados por bandas, com um
grande vazio no meio. Cada membro é conferido contra o limite de balanço da impressão.
A superfície sai por `manifold3d.Manifold.level_set`.

Sistema de coordenadas = orientação de impressão:
  X = horizontal ao longo da parede, Y = para cima (em uso), Z = saindo da parede
  (na impressão, Z é a altura: a placa fica deitada na mesa).

Uso:  uv run pecas/suporte-headset-parede/gerar_suporte.py [--versao 2] [--passo 0.6]
"""
import argparse
import math
import time
from pathlib import Path

import numpy as np
import manifold3d as m3d
import trimesh

# ---------------------------------------------------------------- parâmetros
P = dict(
    raio_arco=68.0,        # berço convexo; o arco do PRO X 2 fechado tem ~140 mm por dentro (raio ~70)
    x_trilho=29.0,         # trilhos laterais do berço em x = ±x_trilho (largura útil ~ 2*(x+r))
    y_topo_berco=31.0,     # topo do berço (x=0) em Y, relativo à placa
    z_berco_ini=38.0,      # início da área de apoio (distância da parede)
    z_berco_fim=84.0,      # fim da área plana (depois a rampa da trava)
    z_ponta=92.0,          # ponta arredondada (fim do berço)
    z_curva=50.0,          # onde o berço começa a fechar em curva elíptica até a ponta
    alt_labio=8.5,         # quanto a trava sobe acima do berço
    r_trilho=1.6,          # raio dos trilhos do berço (finos; na parede alargam)
    esp_placa=4.0,         # espessura da placa
    chanfro_base=0.5,      # chanfro da aresta na mesa
    k_mistura=2.6,         # suavidade das junções 3D (mm)
    inclinacao_max=0.84,   # tangente máxima em relação a Z (0,84 ≈ 40°)
    # berço arredondado (lâmina curva contínua com forames)
    esp_berco=3.0,         # espessura da lâmina do berço
    baixa_trilho_C=2.0,    # trilhos internos um pouco abaixo da lâmina (topo liso)
    # berço em feixe de tendões: cordões que correm da parede à ponta (assimétricos, por baixo
    # da lâmina) e fibras separadas por vazios em fuso, alinhados ao fluxo do feixe
    cordoes=(-0.56, -0.13, 0.38),   # posição dos cordões na largura do berço (-1 = borda E, +1 = D)
    r_cordao=1.4,          # raio dos cordões
    onda_cordao=1.6,       # quanto os cordões serpenteiam (mm)
    fibras=(-0.78, -0.34, 0.12, 0.69),   # fibras finas da lâmina, entre os cordões (mesma escala)
    fibra_larg=1.9,        # largura das fibras finas
    fuso_comp=(13.0, 22.0),  # comprimento dos vazios em fuso (sorteado nesta faixa)
    fuso_ponte=2.6,        # material entre dois vazios seguidos (onde as fibras se juntam)
    semente=11,            # semente do desenho (muda a distribuição dos vazios e das ondas)
    # encaixe do microfone (plugue P2 macho, Ø 3,5 mm)
    furo_p2=3.7,           # Ø do furo do plugue (sai ~0,1-0,2 menor impresso: ajuste justo)
    prof_p2=17.5,          # profundidade do furo do plugue (P2 tem ~14-15 mm; o fundo arredonda ~1,5)
    # bloco do conector do mic: 7 x 9,45 mm, uma ponta redonda concêntrica ao P2, 14,5 mm de altura
    bloco_larg=7.0,
    bloco_comp=9.45,
    bloco_alt=14.5,
    folga_bloco=0.25,      # folga por lado no bolso
    bolso_prof=7.0,        # quanto do bloco entra no bolso (o resto fica para fora)
    # o encaixe fica embutido no tronco que nasce do apoio de baixo e se bifurca
    mic_elev=22.0,         # elevação do eixo do encaixe/tronco (graus acima da horizontal, em uso)
    mic_fundo=(0.0, -36.0, 1.4),  # fundo do furo do P2 (1,4 mm de piso até a face da parede)
    r_tronco_mic=5.6,      # raio do tronco em volta do furo do P2
)
TG = P["inclinacao_max"]
DEPURAR = False


# ---------------------------------------------------------------- curvas
def catmull(pts, n=48):
    pts = np.asarray(pts, float)
    ext = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]])
    out = []
    segs = len(pts) - 1
    for i in range(segs):
        p0, p1, p2, p3 = ext[i:i + 4]
        for t in np.linspace(0, 1, max(4, n // segs), endpoint=(i == segs - 1)):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def y_arco(x):
    R = P["raio_arco"]
    return P["y_topo_berco"] - (R - math.sqrt(R * R - x * x))


def perfil_osso(n, ra, rm, rb, pe=0.0):
    """Afinamento contínuo de ra para rb (sem caroços); 'pe' alarga só o início, onde o membro
    nasce da placa. O engrossamento nas junções vem só da fusão suave entre membros."""
    t = np.linspace(0, 1, n)
    s = t * t * (3 - 2 * t)
    return ra + (rb - ra) * s + pe * np.exp(-(t / 0.12) ** 2)


class Estrutura:
    def __init__(self):
        self.membros = []   # (nome, pts, raios)

    def add(self, nome, pts, rad, conferir=True, grupo="livre"):
        pts = np.asarray(pts, float)
        if conferir:
            d = np.diff(pts, axis=0)
            lat = np.hypot(d[:, 0], d[:, 1])
            dz = d[:, 2]
            ok = (dz > 1e-6) & (lat <= (TG + 0.03) * dz)
            if not ok.all():
                i = int(np.argmin(ok))
                raise ValueError(f"membro '{nome}' passa do limite de balanço perto de z={pts[i, 2]:.1f} "
                                 f"(tangente {lat[i] / max(dz[i], 1e-9):.2f})")
        self.membros.append((nome, pts, np.asarray(rad, float), grupo))
        return pts

    def reto(self, nome, a, b, ra, rm, rb, bow=(0, 0), n=40, pe=0.0):
        a, b = np.asarray(a, float), np.asarray(b, float)
        t = np.linspace(0, 1, n)
        for fator in (1.0, 0.6, 0.3, 0.0):       # curvatura orgânica, reduzida se passar do limite
            pts = a + (b - a) * t[:, None]
            pts[:, 0] += fator * bow[0] * np.sin(math.pi * t)
            pts[:, 1] += fator * bow[1] * np.sin(math.pi * t)
            try:
                return self.add(nome, pts, perfil_osso(n, ra, rm, rb, pe))
            except ValueError:
                if fator == 0.0:
                    raise


def ponto_em_z(pts, z):
    i = np.searchsorted(pts[:, 2], z)
    i = min(max(i, 1), len(pts) - 1)
    a, b = pts[i - 1], pts[i]
    t = (z - a[2]) / max(b[2] - a[2], 1e-9)
    return a + (b - a) * min(max(t, 0), 1)


def alcance(p, trilho, z_max, desloc_y=0.0, folga=0.95):
    """Primeiro ponto do trilho (deslocado em y) que se alcança de p sem passar do limite."""
    for z in np.arange(p[2] + 3, z_max, 0.5):
        q = ponto_em_z(trilho, z) + np.array([0, desloc_y, 0])
        lat = math.hypot(q[0] - p[0], q[1] - p[1])
        if lat <= TG * folga * (q[2] - p[2]):
            return q
    return None


def estrutura():
    """Monta a estrutura como caminhos contínuos: cada tendão nasce na placa, sobe e se funde a um
    trilho do berço, acompanhando-o até sumir dentro dele. Não há emendas no meio do vão; os
    engrossamentos aparecem só onde dois caminhos se encontram."""
    E = Estrutura()
    r = P["r_trilho"]
    zb0, zp, lab = P["z_berco_ini"], P["z_ponta"], P["alt_labio"]
    xt = P["x_trilho"]
    rng = np.random.default_rng(P["semente"])
    trilhos, raios = {}, {}
    z_pt = zp - r
    y_ponta = y_arco(0) - r - P["baixa_trilho_C"] + lab

    def trilho(nome, u, rr, real=True, onda=0.0):
        """Linha de fluxo do berço na fração u da largura: nasce no apoio de cima, corre pelo arco
        e fecha em elipse até a ponta única."""
        x = u * xt
        yc = y_arco(x) - rr - (0.0 if abs(u) > 0.999 else P["baixa_trilho_C"])
        ctrl = [(0.62 * x, yc - 4.0, 0.0), (0.72 * x, yc - 3.0, 12.0), (0.9 * x, yc - 0.8, 26.0),
                (x, yc, zb0)]
        zc = P["z_curva"]; Rz = z_pt - zc
        for th in np.radians([0, 18, 36, 54, 70, 82, 90]):
            ctrl.append((math.cos(th) * x, yc + (y_ponta - yc) * (1 - math.cos(th)), zc + Rz * math.sin(th)))
        pts = catmull(ctrl, 140)
        pts[:, 2] = np.maximum.accumulate(pts[:, 2]) + np.arange(len(pts)) * 1e-7   # z crescente
        z = pts[:, 2]
        if onda:
            fase, lam = rng.uniform(0, 2 * math.pi), rng.uniform(38, 55)
            pts[:, 0] += (onda * np.sin(2 * math.pi * z / lam + fase)
                          * np.clip((z - 8) / 14, 0, 1) * np.clip((80 - z) / 14, 0, 1))
        rad = (rr + 2.8 * np.exp(-(z / 10.0) ** 2)                       # pé alargado (epífise)
               + (r + 0.8 - rr) * np.exp(-((z - z_pt) / 5.0) ** 2))     # ponta: fusão de todos
        trilhos[nome], raios[nome] = pts, rad
        if real:
            # No fecho os trilhos correm quase na horizontal (na impressão), mas por dentro da
            # lâmina, que os sustenta; quem confere o balanço real é a análise da malha final.
            E.add(f"trilho {nome}", pts, rad, grupo="trilho", conferir=False)

    trilho("L", -1.0, r); trilho("R", 1.0, r)             # bordas (ossos)
    trilho("C", 0.0, r, real=False)                       # só referência da superfície
    E.cordoes = []
    for i, u in enumerate(P["cordoes"]):                  # cordões (tendões) assimétricos
        trilho(f"T{i + 1}", u, P["r_cordao"], onda=P["onda_cordao"])
        E.cordoes.append(f"T{i + 1}")
    E.trilhos, E.raios = trilhos, raios

    def caminho(nome, ini, alvo, r0, r1, pe=0.0):
        """Tendão contínuo: passa pelos pontos 'ini', alcança o trilho 'alvo' por baixo (dentro do
        limite de balanço) e segue junto dele, afinando até sumir dentro do trilho."""
        tr, rr = trilhos[alvo], raios[alvo]
        p = np.asarray(ini[-1], float)
        for folga in (0.97, 0.92, 0.86, 0.80, 0.74, 0.68):
            off = float(np.interp(p[2] + 25, tr[:, 2], rr)) + 1.0
            q = alcance(p, tr, zp - 4, -off, folga)
            if q is None:
                continue
            na_ponta = q[2] > z_pt - 14.0
            if na_ponta:
                # No fecho do berço o trilho vira para dentro: uma cauda passaria reto e criaria uma
                # "orelha". Aqui o tendão termina dentro do trilho, mirando o eixo dele.
                qc = alcance(p, tr, zp - 4, -0.4 * (off - 1.0), folga)
                q = qc if qc is not None else q           # se não alcança o eixo, termina logo abaixo
                pts = catmull([*ini, q], 110)
                iq = len(pts) - 1
            else:
                cauda_mm = 12.0
                q1 = ponto_em_z(tr, q[2] + cauda_mm / 2) - np.array([0, 0.45 * off, 0])
                q2 = ponto_em_z(tr, q[2] + cauda_mm)
                pts = catmull([*ini, q, q1, q2], 110)
                iq = int(np.argmin(np.linalg.norm(pts - q, axis=1)))
            d = np.diff(pts[:iq + 1], axis=0)
            incl = np.hypot(d[:, 0], d[:, 1]) / np.maximum(d[:, 2], 1e-9)
            if DEPURAR:
                print(f"  {nome}: folga {folga:.2f} -> junta em z={q[2]:.1f}, inclinação máx {incl.max():.2f} "
                      f"em z={pts[int(np.argmax(incl)), 2]:.1f}")
            if (d[:, 2] > 1e-6).all() and (incl <= TG + 0.03).all():
                break
        else:
            raise ValueError(f"tendão '{nome}' não alcança o trilho {alvo} dentro do limite de balanço")
        sc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        t = np.clip(sc / sc[iq], 0, 1); t = t * t * (3 - 2 * t)
        if na_ponta:
            r1 = min(r1, 1.4)                                 # cabe dentro do trilho
        rad = r0 + (r1 - r0) * t + pe * np.exp(-(sc / (0.12 * sc[iq])) ** 2)
        cauda = np.clip((sc - sc[iq]) / max(sc[-1] - sc[iq], 1e-6), 0, 1)
        rad = rad * (1 - cauda) + 0.5 * cauda                 # some dentro do trilho (sem calombo)
        E.add(nome, pts, rad, conferir=False)
        return pts

    # O tronco único é o próprio corpo do encaixe do mic: segue o eixo do encaixe desde a placa.
    th = math.radians(P["mic_elev"])
    a = np.array([0.0, math.sin(th), math.cos(th)])
    T = np.array(P["mic_fundo"], float) + (P["bolso_prof"] + P["prof_p2"] - BOCA) * a
    E.mic = (T, a)
    eixo = lambda z: T + (z - T[2]) / a[2] * a       # ponto do eixo na altura z
    rt = P["r_tronco_mic"]
    E.reto("tronco único (mic)", eixo(0.0), T - 6.0 * a, rt + 0.3, 0, rt - 0.2, pe=2.5)

    # Dois braços se bifurcam dos lados do tronco; cada um se divide em dois tendões (assimétricos).
    N = tuple(eixo(4.0))
    nE, nD = (-12.0, 5.0, 55.0), (11.0, 6.5, 56.0)
    caminho("tendão E→borda", [N, nE], "L", 3.0, 2.1)
    caminho("tendão E→cordão 1", [N, nE], "T1", 3.0, 1.9)
    caminho("tendão D→borda", [N, nD], "R", 3.0, 2.1)
    caminho("tendão D→cordão 3", [N, nD], "T3", 3.0, 1.9)
    # Tendões do meio, nascendo das bandas da placa (o da esquerda se divide; o da direita não).
    mE = [(-21.0, -16.0, 0.0), (-22.0, 5.0, 26.0)]
    caminho("tendão meio E→borda", mE, "L", 2.6, 2.0, pe=2.2)
    caminho("tendão meio E→cordão 1", mE, "T1", 2.6, 1.8, pe=2.2)
    caminho("tendão meio D→borda", [(22.5, -8.0, 0.0), (23.5, 9.0, 23.0)], "R", 3.0, 2.0, pe=2.2)
    return E


def smin_poly(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax_poly(a, b, k):
    return -smin_poly(-a, -b, k)


def lamina(X, Z, E):
    """Topo (ys), espessura (tb) e meia-largura (W) da lâmina do berço em cada (x, z)."""
    t = P["esp_berco"]
    C = E.trilhos["C"]; L = E.trilhos["L"]
    rL, rC = E.raios["L"], E.raios["C"]
    yC_top = np.interp(Z, C[:, 2], C[:, 1] + rC) + P["baixa_trilho_C"]
    yL_top = np.interp(Z, L[:, 2], L[:, 1] + rL)
    W = np.maximum(np.interp(Z, L[:, 2], np.abs(L[:, 0])), 1e-3)
    u = np.clip(np.abs(X) / W, 0, 1.2)
    # topo em cúpula (liso no centro) que encontra os trilhos laterais no "ombro", 0,8 mm abaixo do topo
    ys = yC_top - (yC_top - (yL_top - 0.3)) * u * u
    # espessura: fina no meio, mísulas que descem para dentro dos trilhos e reforço na convergência
    tb = (t + 1.6 * np.exp(-((np.abs(X) - W) / 3.5) ** 2)
          + sum(1.2 * np.exp(-((X - np.interp(Z, E.trilhos[n][:, 2], E.trilhos[n][:, 0])) / 3.0) ** 2)
                for n in E.cordoes)                              # mísulas finas sobre os cordões
          + 2.5 * np.exp(-Z / 12.0)                              # raiz mais grossa (momento na parede)
          + 2.5 * np.clip((Z - P["z_curva"]) / 18, 0, 1) * np.clip((P["z_ponta"] - 4 - Z) / 12, 0, 1))
    return ys, tb, W


def sdf_berco(X, Y, Z, E):
    """Lâmina do berço que nasce dos trilhos: topo definido pelos próprios trilhos (sem degrau),
    mísulas por baixo escorrendo para dentro deles e nervuras de borda totalmente arredondada."""
    ys, tb, W = lamina(X, Z, E)
    ym = ys - tb / 2
    q1 = np.abs(Y - ym) - tb / 2
    # contorno 2D da lâmina (até o eixo dos trilhos e o fim da ponta) menos os vazios
    z_fim = P["z_ponta"] - 4.0                          # a lâmina afina e termina dentro da cabeça da ponta
    sol2d = np.maximum(np.abs(X) - W, Z - z_fim)
    sol2d = np.maximum(sol2d, -vazios_fibras(X[:, 0, :], Z[:, 0, :], E)[:, None, :])
    # bordas arredondadas (raio limitado para não comer as nervuras finas)
    re = np.minimum(tb / 2 - 0.05, 0.6)
    a1 = q1 + re; a2 = sol2d + re
    return np.sqrt(np.maximum(a1, 0) ** 2 + np.maximum(a2, 0) ** 2) + np.minimum(np.maximum(a1, a2), 0) - re


def sdf_corte_vazios(X, Y, Z, E):
    """Corte final dos vazios (negativo dentro): o mesmo desenho 2D, 0,25 mm para dentro, só na
    espessura da lâmina. Remove qualquer película que as fusões deixem dentro de um vazio."""
    ys, tb, _ = lamina(X, Z, E)
    vaz = vazios_fibras(X[:, 0, :], Z[:, 0, :], E)[:, None, :] + 0.25
    return np.maximum(vaz, np.maximum(Y - (ys + 2.0), (ys - tb) - Y))


BOCA = 3.0   # boca do encaixe, em mm ao longo do eixo a partir de mic_topo


def eixos_mic(E):
    T, a = E.mic
    th = math.radians(P["mic_elev"])
    w = np.array([0.0, math.cos(th), -math.sin(th)])   # perpendicular ao eixo; -w = ponta reta do bloco
    u = np.array([1.0, 0.0, 0.0])
    return T, a, w, u


def sdf_bloco2d(p, q, folga):
    """Seção do bloco: círculo Ø bloco_larg centrado no P2 + retângulo até a ponta reta (lado -w)."""
    Rr = P["bloco_larg"] / 2 + folga
    Ls = P["bloco_comp"] - P["bloco_larg"] / 2 + folga
    circ = np.sqrt(p * p + q * q) - Rr
    ret = np.maximum(np.maximum(np.abs(q) - Rr, -p - Ls), p)
    return np.minimum(circ, ret)


def linhas_berco(E):
    """Linhas que correm da parede à ponta, da esquerda para a direita: bordas, cordões e fibras
    finas. Cada uma é (z, x, meia_largura) e limita os vazios dos dois lados."""
    if hasattr(E, "_linhas"):
        return E._linhas
    rng = np.random.default_rng(P["semente"] + 7)
    L = E.trilhos["L"]
    z = np.arange(0.0, P["z_ponta"], 0.25)
    W = np.interp(z, L[:, 2], np.abs(L[:, 0]))
    rL = np.interp(z, L[:, 2], E.raios["L"])
    linhas = [(-1.0, z, -W, rL + 0.6), (1.0, z, W, rL + 0.6)]
    for n, u in zip(E.cordoes, P["cordoes"]):
        tr = E.trilhos[n]
        linhas.append((u, z, np.interp(z, tr[:, 2], tr[:, 0]), np.interp(z, tr[:, 2], E.raios[n]) + 0.35))
    for u in P["fibras"]:
        fase, lam, amp = rng.uniform(0, 2 * math.pi), rng.uniform(30, 50), rng.uniform(0.8, 1.6)
        x = u * W + amp * np.sin(2 * math.pi * z / lam + fase) * np.clip((z - 6) / 12, 0, 1) * W / W.max()
        linhas.append((u, z, x, np.full(len(z), P["fibra_larg"] / 2)))
    linhas.sort(key=lambda l: l[0])
    E._linhas = [l[1:] for l in linhas]
    return E._linhas


def _fuso(X2, Z2, A, B, f):
    """SDF aproximado (negativo dentro) de um vazio em fuso entre as linhas A e B."""
    zc, b, cheio, torto = f
    lo = np.interp(Z2, A[0], A[1] + A[2]); hi = np.interp(Z2, B[0], B[1] - B[2])
    # corpo cheio (acompanha as duas fibras) e pontas que fecham em ângulo imprimível
    t = np.clip((Z2 - zc) / b, -1, 1)
    ponta = 0.62 * (b - np.abs(Z2 - zc)) * (1 + 0.2 * torto * t)
    meia = cheio * np.maximum(smin_poly(np.maximum(hi - lo, 0) / 2, ponta, 1.5), 0)
    # o vazio só existe onde tem pelo menos 1,6 mm de largura: sem frestas mais finas que a malha
    # (e que o bico), as pontas terminam arredondadas
    return np.maximum(np.maximum(np.abs(X2 - (lo + hi) / 2) - meia, 0.8 - meia), np.abs(Z2 - zc) - b)


def fusos(E):
    """Entre cada par de linhas vizinhas, uma corrente de vazios em fuso de comprimentos sorteados
    (sem espelhar). Onde um fuso acaba, as duas fibras se juntam por 'fuso_ponte' mm. Cada fuso é
    estreitado até as bordas ficarem dentro do limite de balanço (≤ 40° da vertical da impressão)."""
    if hasattr(E, "_fusos"):
        return E._fusos
    rng = np.random.default_rng(P["semente"] + 1)
    lin = linhas_berco(E)
    z_ini, z_fim = 7.0, P["z_ponta"] - 8.0
    px = 0.2
    aceitos = []
    for k in range(len(lin) - 1):
        A, B = lin[k], lin[k + 1]
        z0 = z_ini + rng.uniform(0, 6)
        while z0 < z_fim - 6:
            comp = rng.uniform(*P["fuso_comp"])
            z1 = min(z0 + comp, z_fim)
            zc, b = (z0 + z1) / 2, (z1 - z0) / 2
            zz = np.arange(z0, z1 + px, px)
            xx = np.arange(float(np.interp(zz, A[0], A[1]).min()) - 1, float(np.interp(zz, B[0], B[1]).max()) + 1, px)
            X2, Z2 = np.meshgrid(xx, zz, indexing="ij")
            torto = rng.uniform(-1, 1)
            for cheio in (1.0, 0.88, 0.76, 0.64, 0.52, 0.4):
                d = _fuso(X2, Z2, A, B, (zc, b, cheio, torto))
                dentro = d < 0
                if dentro.sum() * px * px < 7.0:
                    cheio = None
                    break
                # bordas esquerda/direita do vazio em cada z e sua inclinação
                cols = dentro.any(axis=0)
                esq = np.where(dentro, X2, 1e9).min(axis=0)[cols]; dirt = np.where(dentro, X2, -1e9).max(axis=0)[cols]
                if len(esq) < 8:
                    cheio = None
                    break
                sua = lambda v: np.convolve(v, np.ones(7) / 7, mode="valid")
                incl = max(np.abs(np.diff(sua(esq))).max(), np.abs(np.diff(sua(dirt))).max()) / px
                if incl <= TG + 0.03:
                    break
            else:
                cheio = None
            if cheio is not None and (dirt - esq).max() >= 2.6:
                aceitos.append((k, zc, b, cheio, torto))
                z0 = z1 + P["fuso_ponte"]
            else:
                z0 += 4.0                 # faixa estreita demais aqui: tenta de novo mais adiante
    E._fusos = aceitos
    return aceitos


def vazios_fibras(X2, Z2, E):
    """SDF 2D (x,z) dos vazios do berço, negativo dentro do vazio."""
    lin = linhas_berco(E)
    total = np.full(X2.shape, 1e9)
    for k, zc, b, cheio, torto in fusos(E):
        m = np.abs(Z2 - zc) <= b + 1.0
        if not m.any():
            continue
        cols = m.any(axis=0)
        total[:, cols] = np.minimum(total[:, cols], _fuso(X2[:, cols], Z2[:, cols], lin[k], lin[k + 1], (zc, b, cheio, torto)))
    return total


def sdf_cabeca_mic(X, Y, Z, E):
    """Boca do encaixe: o tronco redondo vai virando o contorno do conector (retângulo com a ponta
    redonda no P2) até a boca, com parede uniforme em volta do bolso."""
    T, a, w, u = eixos_mic(E)
    vx, vy, vz = X - T[0], Y - T[1], Z - T[2]
    s = vx * a[0] + vy * a[1] + vz * a[2]
    p = vx * w[0] + vy * w[1] + vz * w[2]
    q = vx * u[0] + vy * u[1] + vz * u[2]
    parede, rc = 2.0, 1.5
    rt = P["r_tronco_mic"] - 0.2
    circ = np.sqrt(p * p + q * q) - (rt - 0.6 * np.maximum(0, -13.0 - s))    # começa em cone, dentro do tronco
    conn = sdf_bloco2d(p, q, P["folga_bloco"] + parede - rc) - rc
    m = np.clip((s + 13) / 10, 0, 1); m = m * m * (3 - 2 * m)
    d2 = (1 - m) * circ + m * conn
    re = 1.2
    a1 = d2 + re; a2 = (s - BOCA) + re
    d = np.sqrt(np.maximum(a1, 0) ** 2 + np.maximum(a2, 0) ** 2) + np.minimum(np.maximum(a1, a2), 0) - re
    return np.maximum(d, -17.0 - s)


def sdf_furo_mic(X, Y, Z, E):
    T, a, w, u = eixos_mic(E)
    vx, vy, vz = X - T[0], Y - T[1], Z - T[2]
    s = vx * a[0] + vy * a[1] + vz * a[2]
    p = vx * w[0] + vy * w[1] + vz * w[2]
    q = vx * u[0] + vy * u[1] + vz * u[2]
    rad = np.sqrt(p * p + q * q)
    fundo_bolso = BOCA - P["bolso_prof"]
    fundo_p2 = fundo_bolso - P["prof_p2"]
    d1 = np.maximum(rad - P["furo_p2"] / 2, fundo_p2 - s)
    chanfro = np.clip(s - (BOCA - 0.8), 0, 0.8)
    d2 = np.maximum(sdf_bloco2d(p, q, P["folga_bloco"]) - chanfro, fundo_bolso - s)
    # Depois da boca o corte continua como um corredor (contorno do bloco + 0,8 mm): garante a
    # passagem do conector entre os dois braços da bifurcação.
    topo = s - (BOCA + 30.0)
    return np.maximum(np.minimum(d1, d2), topo)


# ---------------------------------------------------------------- placa: dois apoios + bandas
def sdf_placa(X, Y, Z):
    def elipse(cx, cy, rx, ry):
        dx, dy = (X - cx) / rx, (Y - cy) / ry
        return (np.sqrt(dx * dx + dy * dy) - 1) * min(rx, ry)

    def banda(pts2, rr):
        pts2 = catmull(pts2, 40)
        d = np.full(X.shape, 1e9, np.float32)
        for a, b in zip(pts2[:-1], pts2[1:]):
            ba = b - a; L2 = ba @ ba
            h = np.clip(((X - a[0]) * ba[0] + (Y - a[1]) * ba[1]) / L2, 0, 1)
            d = np.minimum(d, np.hypot(X - a[0] - h * ba[0], Y - a[1] - h * ba[1]) - rr)
        return d

    partes = [
        elipse(0, 27, 33, 17),                                    # apoio de cima (VHB)
        elipse(0, -44, 25, 15.5),                                 # apoio de baixo (VHB)
        banda([(-24, 16), (-25, -4), (-20, -24), (-14, -40)], 4.5),
        banda([(24, 16), (25, -4), (20, -24), (14, -40)], 4.5),
    ]
    k = 5.0
    d2d = -k * np.log(sum(np.exp(-np.clip(p, -40, 80) / k) for p in partes))
    h = P["esp_placa"]; c = P["chanfro_base"]
    d2d = d2d + np.clip(c - Z, 0, c)                 # chanfro 45° na base
    dz = np.abs(Z - h / 2 + 1.5) - (h / 2 + 1.5)       # abaixo de 0 é cortado depois
    rr = 1.5
    q = np.stack([np.maximum(d2d + rr, 0), np.maximum(dz + rr, 0)])
    return np.sqrt((q ** 2).sum(0)) + np.minimum(np.maximum(d2d + rr, dz + rr), 0) - rr


def dist_tendao(Xs, Ys, Zs, pts, rad):
    d = np.full(Xs.shape, 1e9, np.float32)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ra, rb = rad[i], rad[i + 1]
        ba = b - a
        L2 = ba @ ba
        if L2 < 1e-9:
            continue
        px, py, pz = Xs - a[0], Ys - a[1], Zs - a[2]
        h = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / L2, 0, 1)
        ex, ey, ez = px - h * ba[0], py - h * ba[1], pz - h * ba[2]
        di = np.sqrt(ex * ex + ey * ey + ez * ez) - (ra + h * (rb - ra))
        np.minimum(d, di, out=d)
    return d


def campo(passo):
    lo = np.array([-46.0, -70.0, -2.0])
    hi = np.array([46.0, 54.0, P["z_ponta"] + 4])
    xs = np.arange(lo[0], hi[0] + passo, passo)
    ys = np.arange(lo[1], hi[1] + passo, passo)
    zs = np.arange(lo[2], hi[2] + passo, passo)
    k = P["k_mistura"]
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    acc = np.exp(-np.clip(sdf_placa(X, Y, Z), -30, 60) / k).astype(np.float64)
    del X, Y, Z
    E = estrutura()
    trilhos_min = np.full(acc.shape, 1e9, np.float32)
    for _nome, pts, rad, grupo in E.membros:
        marg = rad.max() + 6 * k
        bl = pts.min(0) - marg
        bh = pts.max(0) + marg
        ix = slice(max(0, int((bl[0] - lo[0]) / passo)), min(len(xs), int((bh[0] - lo[0]) / passo) + 2))
        iy = slice(max(0, int((bl[1] - lo[1]) / passo)), min(len(ys), int((bh[1] - lo[1]) / passo) + 2))
        iz = slice(max(0, int((bl[2] - lo[2]) / passo)), min(len(zs), int((bh[2] - lo[2]) / passo) + 2))
        Xs, Ys, Zs = np.meshgrid(xs[ix], ys[iy], zs[iz], indexing="ij")
        d = dist_tendao(Xs.astype(np.float32), Ys.astype(np.float32), Zs.astype(np.float32), pts, rad)
        if grupo == "trilho":
            np.minimum(trilhos_min[ix, iy, iz], d, out=trilhos_min[ix, iy, iz])
        else:
            acc[ix, iy, iz] += np.exp(-np.clip(d, -30, 60) / k)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    D = -k * np.log(acc)                                         # placa + tendões (fusão larga)
    # O berço entra com uma união de alcance limitado: a fusão larga somava a influência de tudo
    # que passa por perto e criava películas dentro dos vazios da lâmina.
    berco = smin_poly(sdf_berco(X, Y, Z, E), trilhos_min, 1.6)
    kb = 1.5 + 1.5 * np.clip((9.0 - Z) / 4.0, 0, 1)             # filete maior só junto à placa
    D = smin_poly(D, berco, kb)
    # cabeça do mic unida ao pescoço sem "inflar" (a soma suave criava um anel/degrau na emenda)
    D = smin_poly(D, sdf_cabeca_mic(X, Y, Z, E), 1.5)
    D = D - 0.12                       # +0,12 mm em tudo: funde quase-contatos menores que a malha
    D = smax_poly(D, -sdf_corte_vazios(X, Y, Z, E), 0.4)   # vazios do berço limpos
    D = smax_poly(D, -sdf_furo_mic(X, Y, Z, E), 0.5)   # o encaixe do mic é cortado depois, na medida
    del X, Y, Z
    campo.E = E
    return xs, ys, zs, D.astype(np.float32)


def conferir_mic(tm, E):
    """Mic encaixado: plugue, bloco 7 x 9,45 x 14,5 e haste (Ø 5 mm, reta por 130 mm) não tocam a peça."""
    T, a, w, u = eixos_mic(E)
    ang = np.linspace(0, 2 * math.pi, 24, endpoint=False)
    anel = np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * w
    fundo_bolso = BOCA - P["bolso_prof"]
    fundo_p2 = fundo_bolso - P["prof_p2"]
    # contorno do bloco (sem folga), amostrado
    Rr = P["bloco_larg"] / 2; Ls = P["bloco_comp"] - Rr
    cont = [(Rr * math.cos(t), Rr * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 13)]
    cont += [(-Ls * f, Rr) for f in np.linspace(0, 1, 6)] + [(-Ls * f, -Rr) for f in np.linspace(0, 1, 6)]
    cont += [(-Ls, Rr * f) for f in np.linspace(-1, 1, 7)]
    cont = np.array([pp * w + qq * u for pp, qq in cont])
    topo_bloco = fundo_bolso + P["bloco_alt"]
    testes = [("plugue Ø3,5", np.arange(fundo_p2 + 0.4, fundo_bolso, 1.0), 1.75 * anel),
              ("bloco 7x9,45", np.arange(fundo_bolso + 0.3, topo_bloco, 1.0), cont),
              ("haste Ø5", np.arange(topo_bloco, 130, 2.0), 2.5 * anel)]
    ok = True
    for nome, ss, forma in testes:
        p = (T + ss[:, None, None] * a + forma[None]).reshape(-1, 3)
        dentro = tm.contains(p).sum()
        ok &= dentro == 0
        print(f"mic {nome}: {dentro} pontos de {len(p)} batendo na peça")
    return ok


def malha(passo):
    xs, ys, zs, D = campo(passo)
    lo = (xs[0], ys[0], zs[0])
    nx, ny, nz = D.shape
    Dl = D.tolist()  # acesso rápido em Python puro

    def f(x, y, z):
        fx = (x - lo[0]) / passo
        fy = (y - lo[1]) / passo
        fz = (z - lo[2]) / passo
        i = min(max(int(fx), 0), nx - 2); j = min(max(int(fy), 0), ny - 2); k = min(max(int(fz), 0), nz - 2)
        tx = min(max(fx - i, 0.0), 1.0); ty = min(max(fy - j, 0.0), 1.0); tz = min(max(fz - k, 0.0), 1.0)
        a0, a1 = Dl[i], Dl[i + 1]
        c00 = a0[j][k] * (1 - tz) + a0[j][k + 1] * tz
        c01 = a0[j + 1][k] * (1 - tz) + a0[j + 1][k + 1] * tz
        c10 = a1[j][k] * (1 - tz) + a1[j][k + 1] * tz
        c11 = a1[j + 1][k] * (1 - tz) + a1[j + 1][k + 1] * tz
        v = (c00 * (1 - ty) + c01 * ty) * (1 - tx) + (c10 * (1 - ty) + c11 * ty) * tx
        return -v  # manifold: positivo = dentro

    # Quase-contatos menores que a grade podem sair "beliscados" (vértice compartilhado por duas
    # folhas). Se acontecer, desloca a grade de extração e tenta de novo; o campo não muda.
    corte = m3d.Manifold.cube([200, 300, 300]).translate([-100, -150, 0])  # mantém z >= 0
    for dg in (0.37, 0.11, 0.63, 0.83, 0.23):
        g = dg * passo
        b = [xs[0] + passo + g, ys[0] + passo + g, zs[0] + passo + g, xs[-1] - passo, ys[-1] - passo, zs[-1] - passo]
        mesh = (m3d.Manifold.level_set(f, b, passo) ^ corte).to_mesh()
        tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=True)
        corpos = len(tm.split(only_watertight=False))
        print(f"extração (grade +{dg:.2f} passo): fechada={tm.is_watertight}, corpos={corpos}")
        if tm.is_watertight and tm.is_volume and corpos == 1:
            break
    return tm


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao", default="12")
    ap.add_argument("--passo", type=float, default=0.6)
    args = ap.parse_args()
    t0 = time.time()
    tm = malha(args.passo)
    conferir_mic(tm, campo.E)
    out = Path(__file__).with_name(f"suporte_headset_v{args.versao}.stl")
    tm.export(out)
    print(f"{out.name}: {len(tm.faces)} triângulos, {time.time() - t0:.0f} s")
    print("bbox", np.round(tm.bounds, 2).tolist(), "volume cm3", round(tm.volume / 1000, 2),
          "watertight", tm.is_watertight, "corpos", len(tm.split(only_watertight=False)))
