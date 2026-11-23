#!/usr/bin/env python3
"""
Altera configuracoes de um projeto .3mf do Creality Print 7 SEM abrir o programa.
Mantem malhas, posicoes e objetos intactos; muda so o Metadata/project_settings.config.

Uso:
  uv run .claude/skills/creality-print-3mf/alterar_config_3mf.py ENTRADA.3mf SAIDA.3mf --config mudancas.json [--sem-altura-variavel]
  (o JSON tambem pode vir escrito na linha, depois da SAIDA: '{"wall_loops":"4"}'; no PowerShell use sempre o arquivo)

- Cada chave alterada e registrada no grupo certo de different_settings_to_system
  ([0] processo, [1] filamento, [2] impressora).
- Chaves de filamento geram AVISO (regra: so mudar com autorizacao de quem pediu).
- --sem-altura-variavel remove Metadata/layer_heights_profile.txt (necessario para suporte Organic).
"""
import argparse, json, sys, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ferramentas"))
import k1comum


def main():
    k1comum.saida_utf8()
    ap = argparse.ArgumentParser(description="Altera configuracoes de um .3mf do Creality Print 7 (malhas intactas).")
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("mudancas", nargs="?", help="JSON com as chaves a alterar")
    ap.add_argument("--config", dest="arquivo", help="arquivo .json com as chaves a alterar")
    ap.add_argument("--sem-altura-variavel", action="store_true")
    a = ap.parse_args()
    src, dst, sem_var = a.entrada, a.saida, a.sem_altura_variavel
    mudancas = k1comum.ler_json(a.mudancas, a.arquivo, None)
    if mudancas is None and not sem_var:
        ap.error("informe as mudancas (JSON na linha ou --config arquivo.json) ou --sem-altura-variavel")
    k1comum.exigir_saida_diferente(src, dst)
    with zipfile.ZipFile(src) as zin:
        s = json.loads(zin.read("Metadata/project_settings.config"))
        tem_var = "Metadata/layer_heights_profile.txt" in zin.namelist()
    k1comum.aplicar_mudancas(s, mudancas or {})
    remover = ()
    if sem_var and tem_var:
        remover = ("Metadata/layer_heights_profile.txt",)
        print("removida altura de camada variavel")
    k1comum.copiar_zip(src, dst, {"Metadata/project_settings.config":
                                  json.dumps(s, indent=4, ensure_ascii=False).encode()}, remover)

    # conferencia, com os dois zips reabertos do zero
    with zipfile.ZipFile(src) as za, zipfile.ZipFile(dst) as zc:
        for n in za.namelist():
            if n == "Metadata/project_settings.config" or n in remover:
                continue
            if za.read(n) != zc.read(n):
                raise SystemExit(f"arquivo mudou sem querer: {n}")
        c = json.loads(zc.read("Metadata/project_settings.config"))
    for k in ["printer_settings_id", "nozzle_diameter", "filament_settings_id", "nozzle_temperature",
              "hot_plate_temp", "filament_flow_ratio", "pressure_advance", "layer_height", "enable_support",
              "support_style", "brim_type", "brim_object_gap", "elefant_foot_compensation"]:
        print(f"  ✓ {k}: {c.get(k)}")
    print("ok:", dst)


if __name__ == "__main__":
    main()
