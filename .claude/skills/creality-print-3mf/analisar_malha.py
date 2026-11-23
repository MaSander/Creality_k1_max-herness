"""Analisa uma malha para impressão na K1 Max: arquivo solto (STL, OBJ, GLB...) ou projeto .3mf.

Mede dimensões, se está fechada, corpos, volume, área de contato com a mesa e área em balanço
(faces que precisam de suporte), e confere se cabe na mesa de 300 x 300 x 300 mm.
Sai com código 1 quando a malha é reprovada (aberta, não cabe ou sem apoio na mesa).

Uso (da raiz do repositório):
  uv run .claude/skills/creality-print-3mf/analisar_malha.py peca.stl [--angulo 45] [--brim 5]
        [--render previa.png] [--json]

  --angulo N   inclinação, a partir da horizontal, abaixo da qual a face precisa de suporte (padrão 45)
  --brim MM    largura do brim a somar em volta da peça ao conferir se cabe (padrão 0)
  --render     grava um PNG com 4 vistas: balanço em vermelho, contato com a mesa em azul
  --json       imprime o resultado em JSON (para outro script ler)

A malha é analisada na orientação em que está no arquivo (Z para cima). Num .3mf, as partes de
peça são analisadas juntas, na posição da mesa; bloqueadores e modificadores ficam de fora.
Não mede espessura de parede.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ferramentas"))
import k1comum
import k1malha


def main():
    k1comum.saida_utf8()
    ap = argparse.ArgumentParser(description="Analisa uma malha para impressão na K1 Max.")
    ap.add_argument("arquivo")
    ap.add_argument("--angulo", type=float, default=45.0)
    ap.add_argument("--brim", type=float, default=0.0)
    ap.add_argument("--render")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    na_mesa = a.arquivo.lower().endswith(".3mf")
    if na_mesa:
        pecas = k1malha.ler_3mf(a.arquivo).pecas()
        if not pecas:
            sys.exit("O .3mf não tem nenhuma peça (normal_part).")
        malha = k1malha.juntar(p.malha for p in pecas)
    else:
        malha = k1malha.carregar_malha(a.arquivo)
    r = k1malha.analisar(malha, a.angulo, a.brim, na_mesa)
    falhas = k1malha.problemas(r)
    if a.render:
        k1malha.render(malha, r, a.render)

    if a.json:
        print(json.dumps({**{k: v for k, v in r.items() if not k.startswith("_")}, "problemas": falhas},
                         ensure_ascii=False, indent=1))
    else:
        d = r["dimensoes_mm"]
        print(f"Arquivo: {a.arquivo}")
        print(f"Dimensões: {d[0]:.2f} x {d[1]:.2f} x {d[2]:.2f} mm   ({r['faces']} faces)")
        print(f"Fechada: {'sim' if r['fechada'] else 'NÃO'}   Volume válido: {'sim' if r['volume_valido'] else 'NÃO'}"
              f"   Volume: {r['volume_cm3']} cm³")
        print(f"Corpos: {r['corpos']}" + (f"   ATENÇÃO: {r['corpos_sem_apoio_na_mesa']} não encosta(m) na mesa "
                                          "(confira se não está solto no ar)" if r["corpos_sem_apoio_na_mesa"] else ""))
        print(f"Cabe na mesa (brim {a.brim:g} mm): {'sim' if r['cabe_na_mesa'] else 'NÃO'}")
        print(f"Área de contato com a mesa: {r['area_contato_mm2']} mm²")
        print(f"Balanço abaixo de {a.angulo:g}°: {r['area_balanco_mm2']} mm² em {len(r['regioes_balanco'])} região(ões)")
        for reg in r["regioes_balanco"][:8]:
            print(f"  {reg['area_mm2']:>8} mm²  em x,y = {reg['centro_xy'][0]}, {reg['centro_xy'][1]}"
                  f"   altura {reg['z_min']} a {reg['z_max']} mm")
        if len(r["regioes_balanco"]) > 8:
            print(f"  ... e mais {len(r['regioes_balanco']) - 8} menores")
        if a.render:
            print(f"Render: {a.render}")
        for f in falhas:
            print(f"REPROVADA: {f}")
        if not falhas:
            print("Aprovada.")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
