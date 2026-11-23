"""O que os scripts do harness têm em comum, igual no Windows e no macOS.

Só biblioteca padrão. Os scripts das skills importam assim:

    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ferramentas"))
    import k1comum
"""
from __future__ import annotations

import glob
import json
import os
import platform
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SISTEMA = platform.system()  # "Darwin", "Windows" ou "Linux"
MESA = (300.0, 300.0, 300.0)  # volume útil da K1 Max, em mm


def saida_utf8():
    """O console do Windows usa cp1252 e quebra com acento, seta ou emoji."""
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def pasta_entrega() -> Path:
    """Onde os arquivos prontos são entregues: K1_ENTREGA ou a pasta Downloads do usuário."""
    return Path(os.environ.get("K1_ENTREGA") or Path.home() / "Downloads")


def exe_creality(exe: str | None = None) -> str | None:
    """Executável do Creality Print: o informado, K1_CREALITY_EXE ou os lugares de costume."""
    if exe or os.environ.get("K1_CREALITY_EXE"):
        return exe or os.environ["K1_CREALITY_EXE"]
    if SISTEMA == "Darwin":
        candidatos = ["/Applications/Creality Print.app/Contents/MacOS/CrealityPrint",
                      str(Path.home() / "Applications/Creality Print.app/Contents/MacOS/CrealityPrint")]
    elif SISTEMA == "Windows":
        base = os.environ.get("ProgramFiles", r"C:\Program Files")
        candidatos = sorted(glob.glob(os.path.join(base, "Creality", "Creality Print*", "CrealityPrint.exe")),
                            reverse=True)
    else:
        candidatos = []
    return next((c for c in candidatos if os.path.exists(c)), None)


def pasta_dados_creality() -> Path:
    """Pasta de dados do Creality Print (dentro dela há uma pasta por versão: 7.0, 7.3...)."""
    if SISTEMA == "Windows":
        return Path(os.environ["APPDATA"]) / "Creality" / "Creality Print"
    if SISTEMA == "Darwin":
        return Path.home() / "Library/Application Support/Creality/Creality Print"
    return Path.home() / ".config/Creality/Creality Print"


# --- grupos de chaves do project_settings.config -------------------------------------------
# different_settings_to_system tem 3 listas: [0] processo, [1] filamento, [2] impressora.
FILAMENTO = ("filament_", "nozzle_temperature", "hot_plate", "textured_plate", "cool_plate", "eng_plate",
             "pressure_advance", "enable_pressure", "fan_", "close_fan", "slow_down", "overhang_fan",
             "additional_cooling", "support_material_interface_fan", "full_fan", "reduce_fan",
             "chamber_temperature", "material_flow", "enable_filament", "during_print", "complete_print",
             "activate_air")
IMPRESSORA = ("nozzle_diameter", "max_layer_height", "min_layer_height", "retraction_", "deretraction_",
              "z_hop", "retract_", "wipe", "curr_bed_type", "printer_", "machine_", "travel_slope")


def grupo(chave: str) -> int:
    """0 = processo, 1 = filamento, 2 = impressora."""
    if chave.startswith(FILAMENTO):
        return 1
    if chave.startswith(IMPRESSORA):
        return 2
    return 0


def aplicar_mudancas(settings: dict, mudancas: dict) -> None:
    """Altera as chaves pedidas e registra cada uma no grupo certo de different_settings_to_system."""
    diff = settings["different_settings_to_system"]
    grupos = [[k for k in diff[i].split(";") if k] for i in range(3)]
    for k, v in mudancas.items():
        if k not in settings:
            raise SystemExit(f"chave inexistente nesta versao: {k}")
        if isinstance(settings[k], list) and not isinstance(v, list):
            v = [v] * len(settings[k])
        g = grupo(k)
        if g == 1:
            print(f"AVISO: {k} e configuracao de FILAMENTO")
        print(f"{k}: {settings[k]} -> {v}")
        settings[k] = v
        if k not in grupos[g]:
            grupos[g].append(k)
    for i in range(3):
        diff[i] = ";".join(grupos[i])


# --- argumentos e arquivos -----------------------------------------------------------------
def ler_json(inline: str | None, arquivo: str | None, vazio):
    """JSON vindo de um arquivo (--config, o jeito que funciona em qualquer shell) ou escrito na linha.

    No PowerShell 5.1 as aspas de um JSON escrito na linha se perdem: prefira o arquivo.
    """
    if inline and arquivo:
        raise SystemExit("Passe o JSON na linha ou em arquivo, não os dois.")
    if arquivo:
        return json.loads(Path(arquivo).read_text(encoding="utf-8-sig"))
    if inline:
        try:
            return json.loads(inline)
        except json.JSONDecodeError as e:
            raise SystemExit(f"JSON inválido ({e}).\nRecebido: {inline}\n"
                             "No PowerShell as aspas se perdem: grave o JSON num arquivo e passe o arquivo.")
    return vazio


def exigir_saida_diferente(entrada: str, saida: str) -> None:
    """Abrir a saída para escrita apagaria a entrada antes de ela ser lida."""
    if os.path.exists(saida) and os.path.samefile(entrada, saida):
        raise SystemExit("A SAIDA não pode ser o mesmo arquivo da ENTRADA.")


def copiar_zip(origem: str, destino: str, trocar: dict[str, bytes] | None = None, remover=()) -> None:
    """Copia um .3mf (ZIP) trocando o conteúdo de alguns arquivos e deixando os outros iguais.

    Cria um ZipInfo novo por arquivo: reaproveitar o ZipInfo do zip de entrada muda o offset
    dele e a releitura da entrada depois dava "Bad magic number for file header".
    """
    trocar = dict(trocar or {})
    with zipfile.ZipFile(origem) as zin, zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zout:
        nomes = set(zin.namelist())
        faltam = set(trocar) - nomes
        if faltam:
            raise SystemExit(f"arquivo(s) ausente(s) no .3mf: {', '.join(sorted(faltam))}")
        for item in zin.infolist():
            if item.filename in remover:
                continue
            info = zipfile.ZipInfo(item.filename, item.date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            zout.writestr(info, trocar.get(item.filename, zin.read(item.filename)))
    with zipfile.ZipFile(destino) as z:
        ruim = z.testzip()
        if ruim:
            raise SystemExit(f"ZIP corrompido ao gravar: {ruim}")
