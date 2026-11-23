#!/usr/bin/env python3
"""Registro de calibração de filamento da K1 Max.

Guarda o estado de cada filamento em filamentos/<slug>/perfil.json, gera o
perfil.md legível e exporta o preset de filamento para importar no Creality Print.
Só biblioteca padrão. Rode da raiz do repositório: uv run .claude/skills/calibrar-filamento-novo/perfil_filamento.py <comando>

Uso:
  perfil_filamento.py listar
  perfil_filamento.py novo --tipo PETG --marca Voolt [--linha HS] [--cor preto] --bico 0.4 \
        [--temp-fabricante 220-250] [--mesa-fabricante 70-80] [--diametro 1.74] [--nome "PETG VOOLT PRETO"] [--obs "..."]
  perfil_filamento.py bico <slug> --bico 0.2          # adiciona outro bico a um filamento existente
  perfil_filamento.py definir <slug> --bico 0.4 --param nozzle_temperature=235 [--param ...]
  perfil_filamento.py registrar <slug> --bico 0.4 --teste flow_grosso --faixa "-20..+20" \
        --resultado "bloco +5 mais liso" [--param filament_flow_ratio=1.029] [--obs "..."]
  perfil_filamento.py concluir <slug> --bico 0.4
  perfil_filamento.py mostrar <slug>
  perfil_filamento.py exportar <slug> --bico 0.4
  perfil_filamento.py calcular flow --atual 0.98 --valor 5
  perfil_filamento.py calcular torre --inicio 0 --passo-mm 0.002 --altura 12.5
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ferramentas"))
import k1comum
PASTA = REPO / "filamentos"

# Chaves do Creality Print que a calibração preenche, com nome legível e unidade.
PARAMETROS = {
    "nozzle_temperature": ("Bico", "°C"),
    "nozzle_temperature_initial_layer": ("Bico 1ª camada", "°C"),
    "hot_plate_temp": ("Mesa (High Temp Plate)", "°C"),
    "hot_plate_temp_initial_layer": ("Mesa 1ª camada", "°C"),
    "textured_plate_temp": ("Mesa texturizada", "°C"),
    "textured_plate_temp_initial_layer": ("Mesa texturizada 1ª camada", "°C"),
    "filament_flow_ratio": ("Flow ratio", ""),
    "pressure_advance": ("Pressure advance", ""),
    "filament_max_volumetric_speed": ("Fluxo volumétrico máximo", "mm³/s"),
    "filament_retraction_length": ("Retração", "mm"),
    "filament_retraction_speed": ("Velocidade de retração", "mm/s"),
    "filament_deretraction_speed": ("Velocidade de desretração", "mm/s"),
    "fan_min_speed": ("Ventoinha mínima", "%"),
    "fan_max_speed": ("Ventoinha máxima", "%"),
    "additional_cooling_fan_speed": ("Ventoinha lateral", "%"),
    "slow_down_layer_time": ("Tempo mínimo de camada (slow_down)", "s"),
    "filament_diameter": ("Diâmetro", "mm"),
    "filament_density": ("Densidade", "g/cm³"),
    "filament_cost": ("Custo", "R$/kg"),
}

TESTES = {
    "secagem": "Secagem",
    "temperatura": "Torre de temperatura",
    "flow_grosso": "Flow – teste 1 (grosso)",
    "flow_fino": "Flow – teste 2 (fino)",
    "pressure_advance": "Pressure advance",
    "fluxo_maximo": "Fluxo volumétrico máximo",
    "retracao": "Retração",
    "mesa": "Mesa / adesão",
    "validacao": "Peça de validação",
    "outro": "Outro",
}

# Base genérica do Creality Print por tipo (todas existem como "Generic <X> @Creality K1 Max 0.4 nozzle").
TIPOS_GENERICOS = {
    "PLA", "PLA-SILK", "PLA-CF", "PETG", "PETG-CF", "PET", "PET-CF", "ABS", "ASA", "TPU",
    "PA", "PA-CF", "PA6-CF", "PAHT-CF", "PC", "PP", "PPS", "PPS-CF", "PVA", "BVOH", "HIPS",
}


def hoje() -> str:
    return dt.date.today().isoformat()


def slugify(*partes: str) -> str:
    texto = " ".join(p for p in partes if p)
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def bico_txt(bico: str) -> str:
    b = str(bico).replace(",", ".")
    if b not in {"0.2", "0.4", "0.6", "0.8"}:
        sys.exit(f"Bico inválido: {bico} (use 0.2, 0.4, 0.6 ou 0.8)")
    return b


def generico(tipo: str) -> str:
    t = tipo.upper()
    nome = "PLA-Silk" if t == "PLA-SILK" else t
    if t not in TIPOS_GENERICOS:
        print(f"Aviso: '{tipo}' não tem base genérica conhecida; usando Generic PLA. Confira o 'inherits'.",
              file=sys.stderr)
        nome = "PLA"
    return f"Generic {nome} @Creality K1 Max 0.4 nozzle"


def nome_preset(f: dict, bico: str) -> str:
    if f.get("nome_preset"):
        return f"{f['nome_preset']} @Creality K1 Max {bico} nozzle"
    base = " ".join(p for p in (f["tipo"].upper(), f["marca"].upper(), f.get("linha", "").upper()) if p)
    return f"{base} @Creality K1 Max {bico} nozzle"


def caminho(slug: str) -> Path:
    return PASTA / slug / "perfil.json"


def carregar(slug: str) -> dict:
    p = caminho(slug)
    if not p.exists():
        existentes = ", ".join(sorted(d.name for d in PASTA.glob("*/") if (d / "perfil.json").exists())) or "nenhum"
        sys.exit(f"Perfil '{slug}' não existe. Existentes: {existentes}")
    return json.loads(p.read_text(encoding="utf-8"))


def numero(valor: str):
    v = valor.strip().replace(",", ".")
    try:
        n = float(v)
    except ValueError:
        return valor.strip()
    return int(n) if n.is_integer() and "." not in v else n


def parse_params(pares: list[str] | None) -> dict:
    saida = {}
    for par in pares or []:
        if "=" not in par:
            sys.exit(f"Parâmetro sem '=': {par}")
        k, v = par.split("=", 1)
        k = k.strip()
        if k not in PARAMETROS:
            sys.exit(f"Chave desconhecida: {k}\nVálidas: {', '.join(PARAMETROS)}")
        saida[k] = numero(v)
    return saida


def bloco_bico(perfil: dict, bico: str) -> dict:
    b = perfil["bicos"].get(bico)
    if b is None:
        sys.exit(f"O perfil não tem o bico {bico}. Adicione com: perfil_filamento.py bico {perfil['slug']} --bico {bico}")
    return b


def fmt(k: str, v) -> str:
    unidade = PARAMETROS.get(k, ("", ""))[1]
    return f"{v} {unidade}".strip()


def salvar(perfil: dict) -> Path:
    perfil["atualizado_em"] = hoje()
    pasta = PASTA / perfil["slug"]
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "perfil.json").write_text(json.dumps(perfil, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (pasta / "perfil.md").write_text(render_md(perfil), encoding="utf-8", newline="\n")
    return pasta


def render_md(perfil: dict) -> str:
    f = perfil["filamento"]
    nome = " ".join(p for p in (f["tipo"].upper(), f["marca"], f.get("linha", ""), f.get("cor", "")) if p)
    linhas = [f"# {nome}", "", "> Gerado por `perfil_filamento.py`. Não edite à mão: use o script.", ""]
    info = [
        ("Tipo", f["tipo"].upper()), ("Marca", f["marca"]), ("Linha", f.get("linha")), ("Cor", f.get("cor")),
        ("Lote", f.get("lote")), ("Diâmetro medido", f.get("diametro_medido")),
        ("Temperatura do fabricante", f.get("temp_fabricante")), ("Mesa do fabricante", f.get("mesa_fabricante")),
        ("Base no Creality Print", perfil["base_generica"]), ("Criado em", perfil["criado_em"]),
        ("Atualizado em", perfil.get("atualizado_em")),
    ]
    linhas += [f"- **{k}:** {v}" for k, v in info if v not in (None, "")]
    for obs in perfil.get("notas", []):
        linhas.append(f"- **Nota:** {obs}")

    bicos = sorted(perfil["bicos"])
    linhas += ["", "## Parâmetros", "", "| Parâmetro | " + " | ".join(f"Bico {b}" for b in bicos) + " |",
               "|---|" + "---|" * len(bicos)]
    linhas.append("| Status | " + " | ".join(
        "✅ calibrado" if perfil["bicos"][b]["status"] == "calibrado" else "🟡 em andamento" for b in bicos) + " |")
    linhas.append("| Preset | " + " | ".join(f"`{perfil['bicos'][b]['preset']}`" for b in bicos) + " |")
    chaves = [k for k in PARAMETROS if any(k in perfil["bicos"][b]["parametros"] for b in bicos)]
    for k in chaves:
        valores = [fmt(k, perfil["bicos"][b]["parametros"][k]) if k in perfil["bicos"][b]["parametros"] else "–"
                   for b in bicos]
        linhas.append(f"| {PARAMETROS[k][0]} | " + " | ".join(valores) + " |")

    for b in bicos:
        testes = perfil["bicos"][b]["testes"]
        linhas += ["", f"## Histórico de testes – bico {b}", ""]
        if not testes:
            linhas.append("Nenhum teste registrado ainda.")
            continue
        linhas += ["| Data | Teste | Faixa | Resultado | Valor salvo | Observação |", "|---|---|---|---|---|---|"]
        for t in testes:
            salvo = ", ".join(f"{PARAMETROS[k][0]} = {fmt(k, v)}" for k, v in t.get("parametros", {}).items()) or "–"
            linhas.append(f"| {t['data']} | {TESTES.get(t['teste'], t['teste'])} | {t.get('faixa') or '–'} | "
                          f"{t.get('resultado') or '–'} | {salvo} | {t.get('obs') or '–'} |")
    return "\n".join(linhas) + "\n"


# ---------- comandos ----------

def cmd_listar(_):
    perfis = sorted(PASTA.glob("*/perfil.json"))
    if not perfis:
        print("Nenhum filamento registrado em filamentos/.")
        return
    for p in perfis:
        d = json.loads(p.read_text(encoding="utf-8"))
        bicos = ", ".join(f"{b} ({v['status']}, {len(v['testes'])} testes)" for b, v in sorted(d["bicos"].items()))
        print(f"{d['slug']}: {d['filamento']['tipo'].upper()} {d['filamento']['marca']} – {bicos}")


def cmd_novo(a):
    bico = bico_txt(a.bico)
    slug = slugify(a.tipo, a.marca, a.linha or "", a.cor or "")
    if caminho(slug).exists():
        sys.exit(f"Já existe filamentos/{slug}/. Use 'mostrar {slug}' para retomar ou 'bico {slug}' para outro bico.")
    f = {"tipo": a.tipo.upper(), "marca": a.marca, "linha": a.linha or "", "cor": a.cor or "",
         "lote": a.lote or "", "diametro_medido": a.diametro, "temp_fabricante": a.temp_fabricante or "",
         "mesa_fabricante": a.mesa_fabricante or "", "nome_preset": a.nome or ""}
    perfil = {"slug": slug, "filamento": f, "base_generica": generico(a.tipo), "criado_em": hoje(),
              "notas": [a.obs] if a.obs else [], "bicos": {}}
    perfil["bicos"][bico] = {"preset": nome_preset(f, bico), "status": "em_andamento", "parametros": {}, "testes": []}
    if a.diametro:
        perfil["bicos"][bico]["parametros"]["filament_diameter"] = a.diametro
    pasta = salvar(perfil)
    print(f"Criado {pasta.relative_to(REPO)}/ – preset '{perfil['bicos'][bico]['preset']}' "
          f"herdando de '{perfil['base_generica']}'")


def cmd_bico(a):
    perfil = carregar(a.slug)
    bico = bico_txt(a.bico)
    if bico in perfil["bicos"]:
        sys.exit(f"O bico {bico} já existe neste perfil.")
    perfil["bicos"][bico] = {"preset": nome_preset(perfil["filamento"], bico), "status": "em_andamento",
                             "parametros": {}, "testes": []}
    salvar(perfil)
    print(f"Bico {bico} adicionado: preset '{perfil['bicos'][bico]['preset']}'")


def cmd_definir(a):
    perfil = carregar(a.slug)
    b = bloco_bico(perfil, bico_txt(a.bico))
    novos = parse_params(a.param)
    if not novos:
        sys.exit("Nada para definir: passe --param chave=valor.")
    b["parametros"].update(novos)
    salvar(perfil)
    print("Definido: " + ", ".join(f"{k} = {v}" for k, v in novos.items()))


def cmd_registrar(a):
    perfil = carregar(a.slug)
    b = bloco_bico(perfil, bico_txt(a.bico))
    if a.teste not in TESTES:
        sys.exit(f"Teste desconhecido: {a.teste}. Válidos: {', '.join(TESTES)}")
    novos = parse_params(a.param)
    b["testes"].append({"data": hoje(), "teste": a.teste, "faixa": a.faixa or "", "resultado": a.resultado or "",
                        "parametros": novos, "obs": a.obs or ""})
    b["parametros"].update(novos)
    if b["status"] == "calibrado" and novos:
        b["status"] = "em_andamento"
    salvar(perfil)
    print(f"Registrado {TESTES[a.teste]}" + (": " + ", ".join(f"{k} = {v}" for k, v in novos.items()) if novos else ""))


def cmd_concluir(a):
    perfil = carregar(a.slug)
    bico = bico_txt(a.bico)
    b = bloco_bico(perfil, bico)
    faltando = [k for k in ("nozzle_temperature", "filament_flow_ratio", "pressure_advance",
                            "filament_max_volumetric_speed") if k not in b["parametros"]]
    if faltando and not a.forcar:
        sys.exit("Faltam parâmetros essenciais: " + ", ".join(faltando) + " (use --forcar para concluir assim mesmo)")
    b["status"] = "calibrado"
    salvar(perfil)
    print(f"Bico {bico} marcado como calibrado.")


def cmd_mostrar(a):
    print(render_md(carregar(a.slug)))


def cmd_exportar(a):
    perfil = carregar(a.slug)
    bico = bico_txt(a.bico)
    b = bloco_bico(perfil, bico)
    nome = b["preset"]
    preset = {"base_id": "GFSA04", "from": "User", "inherits": perfil["base_generica"], "is_custom_defined": "0",
              "name": nome, "filament_settings_id": [nome], "version": "25.9.29.17"}
    f = perfil["filamento"]
    preset["filament_vendor"] = [f["marca"]]
    for k, v in b["parametros"].items():
        preset[k] = [str(v)]
    if "pressure_advance" in b["parametros"]:
        preset["enable_pressure_advance"] = ["1"]
    destino = PASTA / perfil["slug"] / f"{nome}.json"
    destino.write_text(json.dumps(preset, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")
    salvar(perfil)
    print(f"Exportado: {destino}")


def cmd_calcular(a):
    if a.tipo == "flow":
        r = a.atual * (100 + a.valor) / 100
        print(f"flow = {a.atual} × (100 {a.valor:+g}) ÷ 100 = {r:.4f} → salvar {round(r, 3)}")
    elif a.tipo == "torre":
        r = a.inicio + a.altura * a.passo_mm
        print(f"valor = {a.inicio} + {a.altura} mm × {a.passo_mm}/mm = {r:.4f} → {round(r, 4)}")
    elif a.tipo == "passo":
        r = (a.fim - a.inicio) / a.altura_teste
        print(f"passo por mm = ({a.fim} − {a.inicio}) ÷ {a.altura_teste} mm = {r:.5f}")


def main():
    k1comum.saida_utf8()
    p = argparse.ArgumentParser(description="Registro de calibração de filamento (K1 Max)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("listar").set_defaults(func=cmd_listar)

    s = sub.add_parser("novo")
    s.add_argument("--tipo", required=True)
    s.add_argument("--marca", required=True)
    s.add_argument("--linha")
    s.add_argument("--cor")
    s.add_argument("--lote")
    s.add_argument("--bico", required=True)
    s.add_argument("--diametro", type=float)
    s.add_argument("--temp-fabricante")
    s.add_argument("--mesa-fabricante")
    s.add_argument("--nome", help="nome do preset antes de ' @Creality...' (padrão: TIPO MARCA LINHA)")
    s.add_argument("--obs")
    s.set_defaults(func=cmd_novo)

    s = sub.add_parser("bico")
    s.add_argument("slug")
    s.add_argument("--bico", required=True)
    s.set_defaults(func=cmd_bico)

    s = sub.add_parser("definir")
    s.add_argument("slug")
    s.add_argument("--bico", required=True)
    s.add_argument("--param", action="append")
    s.set_defaults(func=cmd_definir)

    s = sub.add_parser("registrar")
    s.add_argument("slug")
    s.add_argument("--bico", required=True)
    s.add_argument("--teste", required=True)
    s.add_argument("--faixa")
    s.add_argument("--resultado")
    s.add_argument("--param", action="append")
    s.add_argument("--obs")
    s.set_defaults(func=cmd_registrar)

    s = sub.add_parser("concluir")
    s.add_argument("slug")
    s.add_argument("--bico", required=True)
    s.add_argument("--forcar", action="store_true")
    s.set_defaults(func=cmd_concluir)

    s = sub.add_parser("mostrar")
    s.add_argument("slug")
    s.set_defaults(func=cmd_mostrar)

    s = sub.add_parser("exportar")
    s.add_argument("slug")
    s.add_argument("--bico", required=True)
    s.set_defaults(func=cmd_exportar)

    s = sub.add_parser("calcular")
    calc = s.add_subparsers(dest="tipo", required=True)
    c = calc.add_parser("flow", help="flow novo = atual × (100 + valor) ÷ 100")
    c.add_argument("--atual", type=float, required=True)
    c.add_argument("--valor", type=float, required=True)
    c = calc.add_parser("torre", help="valor = início + altura × passo por mm (PA, fluxo, retração, temperatura)")
    c.add_argument("--inicio", type=float, required=True)
    c.add_argument("--passo-mm", type=float, required=True)
    c.add_argument("--altura", type=float, required=True)
    c = calc.add_parser("passo", help="passo por mm = (fim − início) ÷ altura do teste")
    c.add_argument("--inicio", type=float, required=True)
    c.add_argument("--fim", type=float, required=True)
    c.add_argument("--altura-teste", type=float, required=True)
    s.set_defaults(func=cmd_calcular)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
