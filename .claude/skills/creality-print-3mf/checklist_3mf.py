"""Roda o checklist de entrega de um projeto .3mf do Creality Print 7 (K1 Max), por código.

É o checklist do agente configurador-impressao-k1max. Cada linha sai marcada:
  [ok]      conferido e certo
  [FALHA]   conferido e errado: o projeto não deve ser entregue assim
  [aviso]   merece atenção, mas pode estar certo
  [info]    valor para citar na entrega
  [manual]  o código não tem como conferir: responda você
Sai com código 1 se houver alguma FALHA.

Uso (da raiz do repositório):
  uv run .claude/skills/creality-print-3mf/checklist_3mf.py PROJETO.3mf [--bico 0.4] [--origem CONFIG.3mf]
        [--permitir chave[,chave...]] [--ficha pecas/<peca>/ficha.json] [--render previa.png]

  --bico D        bico que está montado na impressora: falha se o projeto for de outro
  --origem X.3mf  projeto de onde vieram as configurações: falha se alguma chave de FILAMENTO mudou
  --permitir      chaves de filamento que foram alteradas com autorização (não contam como falha)
  --ficha         ficha da peça gravada na modelagem: confere escala, material e bico contra ela
  --render        grava o PNG da análise da malha (balanço em vermelho, contato em azul)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ferramentas"))
import k1comum
import k1malha

Z_MIN_PLA = 0.24          # folga Z mínima do suporte em PLA (regra da casa)
XY_SUPORTE = 0.6          # distância lateral do suporte
PRESETS = k1comum.RAIZ / ".claude" / "perfis"
CITAR = ["nozzle_temperature", "nozzle_temperature_initial_layer", "hot_plate_temp", "filament_flow_ratio",
         "pressure_advance", "filament_max_volumetric_speed", "filament_retraction_length", "slow_down_layer_time"]


class Checklist:
    def __init__(self):
        self.linhas = []

    def add(self, marca, texto):
        self.linhas.append((marca, texto))

    def conferir(self, certo, texto, erro=None):
        self.add("ok" if certo else "FALHA", texto if certo else (erro or texto))

    def falhas(self):
        return [t for m, t in self.linhas if m == "FALHA"]

    def imprimir(self):
        for marca, texto in self.linhas:
            print(f"[{marca}]".ljust(9) + texto)


def primeiro(v):
    return v[0] if isinstance(v, list) and v else v


def num(v, padrao=0.0):
    try:
        return float(str(primeiro(v)).replace("%", ""))
    except (TypeError, ValueError):
        return padrao


def preset_do_repositorio(nome):
    """Preset de filamento exportado do Creality Print (só traz o que difere do perfil de fábrica)."""
    for p in PRESETS.rglob("filament/*.json"):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if j.get("name") == nome:
            return p, j
    return None, None


def main():
    k1comum.saida_utf8()
    ap = argparse.ArgumentParser(description="Checklist de entrega de um .3mf para a K1 Max.")
    ap.add_argument("projeto")
    ap.add_argument("--bico")
    ap.add_argument("--origem")
    ap.add_argument("--permitir", default="")
    ap.add_argument("--ficha")
    ap.add_argument("--render")
    a = ap.parse_args()
    ficha = json.loads(Path(a.ficha).read_text(encoding="utf-8")) if a.ficha else None
    permitidas = {k for k in a.permitir.split(",") if k}

    proj = k1malha.ler_3mf(a.projeto)
    s = proj.settings
    c = Checklist()
    if not s:
        sys.exit("O arquivo não tem Metadata/project_settings.config: não é um projeto do Creality Print.")
    pecas = proj.pecas()
    if not pecas:
        sys.exit("O projeto não tem nenhuma peça (normal_part).")

    # --- impressora e bico
    impressora = str(s.get("printer_settings_id", ""))
    bico = str(primeiro(s.get("nozzle_diameter")))
    bico_no_nome = "0.2" if "0.2 nozzle" in impressora else "0.4" if "0.4 nozzle" in impressora else None
    c.conferir("K1 Max" in impressora, f"Impressora: {impressora}", f"Impressora não é a K1 Max: {impressora!r}")
    c.conferir(bico_no_nome in (None, bico), f"Bico do projeto: {bico} mm",
               f"nozzle_diameter = {bico}, mas o perfil da impressora é de {bico_no_nome}")
    if a.bico:
        c.conferir(num(a.bico) == num(bico), f"Bico montado ({a.bico}) igual ao do projeto",
                   f"Bico montado é {a.bico}, mas o projeto é para {bico}")
    else:
        c.add("manual", f"Confirme com quem pediu se o bico montado é o {bico}")
    if ficha:
        c.conferir(num(ficha.get("bico")) == num(bico), f"Bico igual ao da ficha da peça ({ficha.get('bico')})",
                   f"A ficha da peça pede bico {ficha.get('bico')}, mas o projeto é para {bico}")
    c.add("info", f"Processo: {s.get('print_settings_id')}   camada {s.get('layer_height')} mm   "
                  f"mesa: {s.get('curr_bed_type')}")

    # --- filamento
    fil = str(primeiro(s.get("filament_settings_id")))
    tipo = str(primeiro(s.get("filament_type")))
    c.add("info", f"Filamento: {fil} [{tipo}]   " + "   ".join(f"{k}={primeiro(s.get(k))}" for k in CITAR))
    if ficha:
        mat = str(ficha.get("material", ""))
        c.conferir(mat.upper() == tipo.upper(), f"Material igual ao da ficha da peça ({mat})",
                   f"A ficha da peça pede {mat}, mas o filamento do projeto é {tipo}")
    if a.origem:
        so = k1malha.ler_3mf(a.origem).settings
        mudou = sorted(k for k in set(s) | set(so)
                       if k1comum.grupo(k) == 1 and s.get(k) != so.get(k) and k not in permitidas)
        c.conferir(not mudou, "Filamento intacto em relação ao projeto de origem",
                   "Filamento alterado em relação à origem: " +
                   "; ".join(f"{k}: {so.get(k)} -> {s.get(k)}" for k in mudou))
    else:
        c.add("manual", "Filamento intacto: passe --origem CONFIG.3mf para conferir contra o projeto de origem")
    caminho, preset = preset_do_repositorio(fil)
    if preset is None:
        c.add("aviso", f"Preset '{fil}' não está em .claude/perfis/: valores do filamento não comparados")
    else:
        difere = [f"{k}: preset {primeiro(v)}, projeto {primeiro(s.get(k))}" for k, v in preset.items()
                  if isinstance(v, list) and k in s and k1comum.grupo(k) == 1 and k != "filament_settings_id"
                  and k not in permitidas and str(primeiro(v)) != str(primeiro(s.get(k)))
                  and num(v, None) != num(s.get(k), "x")]
        if difere:
            c.add("aviso", f"Difere do preset do repositório ({caminho.name}): " + "; ".join(difere))
        else:
            c.add("ok", f"Filamento igual ao preset do repositório ({caminho.name})")

    # --- brim
    brim_tipo = str(s.get("brim_type"))
    brim = num(s.get("brim_width")) if brim_tipo != "no_brim" else 0.0
    if brim_tipo == "no_brim":
        c.add("info", "Brim: desligado")
    else:
        gap, efc = num(s.get("brim_object_gap")), num(s.get("elefant_foot_compensation"))
        c.conferir(gap == 0 and efc == 0, f"Brim {brim_tipo} de {brim:g} mm encostado (gap 0, pé de elefante 0)",
                   f"Brim não encosta: brim_object_gap = {gap:g}, elefant_foot_compensation = {efc:g} "
                   "(os dois têm de ser 0)")

    # --- malha, mesa, contato
    malha = k1malha.juntar(p.malha for p in pecas)
    suporte = str(s.get("enable_support")) == "1"
    angulo = num(s.get("support_threshold_angle"), 45.0) or 45.0
    r = k1malha.analisar(malha, angulo, brim if brim_tipo != "auto_brim" else 0.0, na_mesa=True)
    d = r["dimensoes_mm"]
    c.conferir(r["fechada"] and r["volume_valido"],
               f"Malha no .3mf fechada: {d[0]:.2f} x {d[1]:.2f} x {d[2]:.2f} mm, {r['faces']} faces, "
               f"{r['corpos']} corpo(s)", "Malha no .3mf aberta ou com faces invertidas")
    if ficha:
        esperado = [float(x) for x in ficha["medido"]["dimensoes_mm"]]
        igual = all(abs(x - y) <= 0.05 for x, y in zip(d, esperado))
        girada = all(abs(x - y) <= 0.05 for x, y in zip(sorted(d), sorted(esperado)))
        c.conferir(igual or girada, "Escala: dimensões iguais às da ficha da peça"
                   + ("" if igual else " (orientação diferente da exportada na modelagem)"),
                   f"Escala: a ficha da peça diz {esperado[0]:g} x {esperado[1]:g} x {esperado[2]:g} mm "
                   f"e o projeto tem {d[0]:.2f} x {d[1]:.2f} x {d[2]:.2f} mm")
        c.add("info", f"Uso (ficha): {ficha.get('uso')}")
        if ficha.get("orientacao"):
            c.add("info", f"Orientação pensada no projeto (ficha): {ficha['orientacao']}")
        if ficha.get("medidas_criticas"):
            c.add("info", "Medidas críticas (ficha): " + "; ".join(ficha["medidas_criticas"]))
    else:
        c.add("manual", f"Escala: confira {d[0]:.2f} x {d[1]:.2f} x {d[2]:.2f} mm contra a medida de referência "
                        "da peça (ou passe --ficha)")
    c.conferir(r["cabe_na_mesa"], f"Cabe na mesa de 300 x 300 com o brim (x {r['minimo'][0]:.1f} a "
               f"{r['maximo'][0]:.1f}, y {r['minimo'][1]:.1f} a {r['maximo'][1]:.1f}, altura {d[2]:.1f})",
               f"Não cabe na mesa com brim de {brim:g} mm: x {r['minimo'][0]:.1f} a {r['maximo'][0]:.1f}, "
               f"y {r['minimo'][1]:.1f} a {r['maximo'][1]:.1f}, z {r['minimo'][2]:.2f} a {r['maximo'][2]:.1f}")
    centro = [(r["minimo"][i] + r["maximo"][i]) / 2 for i in (0, 1)]
    fora = max(abs(centro[0] - k1comum.MESA[0] / 2), abs(centro[1] - k1comum.MESA[1] / 2))
    c.add("ok" if fora <= 1 else "aviso", f"Centro da peça em x,y = {centro[0]:.1f}, {centro[1]:.1f}"
          + ("" if fora <= 1 else " (fora do centro da mesa)"))
    c.conferir(abs(r["minimo"][2]) <= k1malha.TOL_CONTATO, "Peça apoiada na mesa (z mínimo 0)",
               f"Peça fora da mesa em Z: ponto mais baixo em {r['minimo'][2]:.3f} mm")
    c.conferir(r["area_contato_mm2"] > 0, f"Área de contato com a mesa: {r['area_contato_mm2']} mm²",
               "Área de contato com a mesa: 0 mm² (nenhuma face plana apoiada)")
    if r["corpos_sem_apoio_na_mesa"]:
        c.add("aviso", f"{r['corpos_sem_apoio_na_mesa']} corpo(s) não encosta(m) na mesa: "
                       "confira se não há parte solta no ar")
    c.add("manual", "Orientação: informe por que esta (resistência, acabamento)")

    # --- suporte
    outras = [p for p in proj.partes if p.subtipo != "normal_part"]
    if outras:
        c.add("info", "Partes extras: " + ", ".join(f"{p.subtipo} '{p.nome}'" for p in outras))
    regioes = r["regioes_balanco"]
    resumo = (f"{r['area_balanco_mm2']} mm² abaixo de {angulo:g}° em {len(regioes)} região(ões)"
              + ("; maiores: " + "; ".join(f"{g['area_mm2']} mm² em x,y {g['centro_xy'][0]}, {g['centro_xy'][1]} "
                                           f"(altura {g['z_min']} a {g['z_max']})" for g in regioes[:4])
                 if regioes else ""))
    if suporte:
        estilo = str(s.get("support_style"))
        c.add("info", f"Suporte ligado: {s.get('support_type')} / {estilo}. Balanço: {resumo}")
        if estilo == "organic":
            c.conferir("Metadata/layer_heights_profile.txt" not in proj.arquivos,
                       "Suporte Organic sem altura de camada variável",
                       "Suporte Organic com altura de camada variável (Metadata/layer_heights_profile.txt): "
                       "rode alterar_config_3mf.py com --sem-altura-variavel")
        top = num(s.get("support_top_z_distance"))
        if tipo.upper().startswith("PLA"):
            c.conferir(top >= Z_MIN_PLA - 1e-9, f"Folga Z do suporte {top:g} mm (PLA pede pelo menos {Z_MIN_PLA})",
                       f"Folga Z do suporte {top:g} mm: em PLA tem de ser pelo menos {Z_MIN_PLA}")
        else:
            c.add("info", f"Folga Z do suporte: {top:g} mm")
        inter = num(s.get("support_interface_bottom_layers"))
        c.add("ok" if inter == 0 else "aviso",
              "Sem interface onde o suporte pousa no modelo" if inter == 0 else
              f"Interface de suporte embaixo ({inter:g} camadas): mais difícil de tirar do modelo")
        xy = num(s.get("support_object_xy_distance"))
        c.add("ok" if xy >= XY_SUPORTE - 1e-9 else "aviso", f"Distância lateral do suporte: {xy:g} mm"
              + ("" if xy >= XY_SUPORTE - 1e-9 else f" (o costume da casa é {XY_SUPORTE})"))
    else:
        c.add("aviso" if r["area_balanco_mm2"] > 0 else "ok",
              f"Suporte desligado. Balanço: {resumo}" + (" – justifique" if r["area_balanco_mm2"] > 0 else ""))
    c.add("manual", "Se a malha foi alterada: render de perto (por baixo, bordas, uniões) comparado com o original")

    # --- lembretes
    if tipo.upper().startswith("PLA"):
        c.add("info", "Lembrete: PLA imprime com a tampa da K1 Max aberta")
    c.add("info", "Lembrete: se trocou o bico, autoteste e nivelamento antes de imprimir")

    if a.render:
        k1malha.render(malha, r, a.render)
        c.add("info", f"Render: {a.render}")
    print(f"Checklist de {a.projeto}")
    c.imprimir()
    falhas = c.falhas()
    print(f"\n{len(falhas)} falha(s)." if falhas else "\nSem falhas (confira os itens [manual] e [aviso]).")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
