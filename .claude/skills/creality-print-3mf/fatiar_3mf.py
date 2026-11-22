"""Fatia um projeto .3mf com o Creality Print pela linha de comando (sem abrir janela).

Usa as configurações gravadas no próprio .3mf (impressora, processo, filamento, suporte, brim):
o G-code sai igual ao que o programa geraria com o mesmo projeto aberto.

Saída: <pasta>/<nome>_<filamento>_bico<d>_<tempo>.gcode, com miniatura embutida
(a imagem da placa gerada pelo fatiador), para a peça aparecer na tela da K1 Max.

Uso (Mac do Marcelo):
  .venv/bin/python .claude/skills/creality-print-3mf/fatiar_3mf.py projeto.3mf [--saida ~/Downloads]
Opções:
  --nome NOME                 nome base do arquivo (padrão: nome do .3mf)
  --placa N                   placa a fatiar (padrão 1)
  --exe CAMINHO               executável do Creality Print (padrão: procura nos lugares de costume)
  --permitir-versao-nova      aceita .3mf salvo numa versão do Creality Print mais nova que a instalada

Não envia nada para a impressora (isso é o enviar_k1max.py, que também não imprime).
"""
import argparse
import base64
import glob
import io
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

CANDIDATOS = {
    "Darwin": ["/Applications/Creality Print.app/Contents/MacOS/CrealityPrint"],
    "Windows": sorted(glob.glob(r"C:\Program Files\Creality\Creality Print*\CrealityPrint.exe"), reverse=True),
}


def achar_exe(exe):
    if exe:
        return exe
    for c in CANDIDATOS.get(platform.system(), []):
        if os.path.exists(c):
            return c
    sys.exit("Não achei o Creality Print. Passe o caminho com --exe.")


def versao_cli(exe):
    r = subprocess.run([exe, "--help"], capture_output=True, text=True, errors="ignore", timeout=60)
    m = re.search(r"Creality-(\d+(?:\.\d+)+)", r.stdout + r.stderr)
    return m.group(1) if m else "?"


def versao_3mf(caminho):
    with zipfile.ZipFile(caminho) as z:
        try:
            txt = z.read("Metadata/creality.config").decode("utf-8", "ignore")
            m = re.search(r'key="AppVersion" value="([\d.]+)"', txt)
            if m:
                return m.group(1)
        except KeyError:
            pass
        txt = z.read("3D/3dmodel.model")[:3000].decode("utf-8", "ignore")
        m = re.search(r"V(\d+(?:\.\d+)+)", txt)
        return m.group(1) if m else "?"


def tupla(v):
    return tuple(int(x) for x in v.split(".") if x.isdigit())


def bloco_miniatura(png, w, h):
    b64 = base64.b64encode(png).decode()
    linhas = [f"; thumbnail begin {w}x{h} {len(b64)}"]
    linhas += ["; " + b64[i:i + 78] for i in range(0, len(b64), 78)]
    linhas.append("; thumbnail end")
    return "\n".join(linhas) + "\n;\n"


def miniaturas(png300):
    """Bloco com 300x300 e 96x96 (o que o perfil da K1 Max pede: thumbnails = 96x96/PNG, 300x300/PNG)."""
    blocos = ""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(png300)).convert("RGBA")
        for lado in (96, 300):
            b = io.BytesIO()
            img.resize((lado, lado), Image.LANCZOS).save(b, "PNG")
            blocos += bloco_miniatura(b.getvalue(), lado, lado)
    except ImportError:
        blocos = bloco_miniatura(png300, 300, 300)
    return "\n; THUMBNAIL_BLOCK_START\n" + blocos + "; THUMBNAIL_BLOCK_END\n\n"


def ler_config_gcode(texto):
    cfg = {}
    for m in re.finditer(r"^; ([\w \[\]()]+?) = (.*)$", texto, re.M):
        cfg.setdefault(m.group(1), m.group(2).strip().strip('"'))
    return cfg


def tempo_curto(t):
    # "4h 2m 52s" -> "4h02m"; "35m 10s" -> "35m"
    h = re.search(r"(\d+)h", t)
    m = re.search(r"(\d+)m", t)
    d = re.search(r"(\d+)d", t)
    horas = (int(d.group(1)) * 24 if d else 0) + (int(h.group(1)) if h else 0)
    mins = int(m.group(1)) if m else 0
    return f"{horas}h{mins:02d}m" if horas else f"{mins}m"


def main():
    # o console do Windows usa cp1252: sem isto os acentos saem quebrados
    for f in (sys.stdout, sys.stderr):
        f.reconfigure(encoding="utf-8", errors="replace")
    ap =argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--saida", default=os.path.expanduser("~/Downloads"))
    ap.add_argument("--nome")
    ap.add_argument("--placa", type=int, default=1)
    ap.add_argument("--exe")
    ap.add_argument("--permitir-versao-nova", action="store_true")
    a = ap.parse_args()

    projeto = os.path.abspath(a.projeto)
    if platform.system() == "Windows" and not a.exe:
        # Testado em 22/11/2026 no PC do Alexandre (Creality Print 7.3): o CrealityPrint.exe do
        # Windows não tem modo linha de comando. "--help" trava, "--export-3mf" dá
        # "GUI parameter parsing failed" e "--slice" abre a janela do programa sem fatiar.
        sys.exit("No Windows o Creality Print 7.3 não fatia pela linha de comando (abre a janela).\n"
                 "Fatie no programa: abra o .3mf, Slice plate e Export G-code.\n"
                 "Para tentar outro executável mesmo assim, passe --exe.")
    exe = achar_exe(a.exe)
    v_cli, v_arq = versao_cli(exe), versao_3mf(projeto)
    versao_nova = tupla(v_arq)[:3] > tupla(v_cli)[:3]
    if versao_nova and not a.permitir_versao_nova:
        sys.exit(f"O .3mf foi salvo no Creality Print {v_arq} e o instalado aqui é {v_cli}.\n"
                 "Atualize o Creality Print ou rode de novo com --permitir-versao-nova "
                 "(opções que só existem na versão nova podem ser ignoradas).")

    tmp = tempfile.mkdtemp(prefix="fatiar_")
    try:
        cmd = [exe, "--slice", str(a.placa), "--outputdir", tmp, "--export-3mf", "fatiado.gcode.3mf"]
        if versao_nova:
            cmd.insert(1, "--allow-newer-file=1")
        cmd.append(projeto)
        r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", timeout=3600)
        gcode_tmp = os.path.join(tmp, f"plate_{a.placa}.gcode")
        if r.returncode != 0 or not os.path.exists(gcode_tmp):
            erros = [l for l in (r.stdout + r.stderr).splitlines() if "[trace]" not in l]
            sys.exit(f"Fatiamento falhou (código {r.returncode}).\n" + "\n".join(erros[-15:]))

        texto = open(gcode_tmp, encoding="utf-8", errors="ignore").read()
        cfg = ler_config_gcode(texto)

        # Miniatura: a imagem da placa que o fatiador grava no .gcode.3mf
        tem_mini = "thumbnail begin" in texto[:200000]
        if not tem_mini:
            with zipfile.ZipFile(os.path.join(tmp, "fatiado.gcode.3mf")) as z:
                try:
                    png = z.read(f"Metadata/plate_{a.placa}.png")
                except KeyError:
                    png = None
            if png:
                fim_cab = texto.find("; HEADER_BLOCK_END")
                fim_cab = texto.find("\n", fim_cab) + 1 if fim_cab >= 0 else 0
                texto = texto[:fim_cab] + miniaturas(png) + texto[fim_cab:]
                tem_mini = True

        bico = cfg.get("nozzle_diameter", "?").split(",")[0]
        fil_tipo = cfg.get("filament_type", "?").split(";")[0]
        tempo = cfg.get("estimated printing time (normal mode)", "?")
        nome = a.nome or re.sub(r"(\.gcode)?\.3mf$", "", os.path.basename(projeto))
        nome = re.sub(r'[\\/:*?"\'<>| ]+', "_", nome)
        if f"bico_{bico}" not in nome and f"bico{bico}" not in nome:
            nome += f"_bico{bico}"
        if fil_tipo not in nome:
            nome += f"_{fil_tipo}"
        destino = os.path.join(os.path.expanduser(a.saida), f"{nome}_{tempo_curto(tempo)}.gcode")
        with open(destino, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"G-code: {destino}")
    print(f"Creality Print {v_cli} (projeto salvo na {v_arq})" + ("  ATENÇÃO: versão do projeto mais nova" if versao_nova else ""))
    print(f"Impressora/bico: {cfg.get('printer_settings_id')}  (nozzle_diameter {bico})")
    print(f"Filamento: {cfg.get('filament_settings_id')}  [{fil_tipo}]  bico {cfg.get('nozzle_temperature')} °C, "
          f"mesa {cfg.get('hot_plate_temp')} °C")
    print(f"Processo: {cfg.get('print_settings_id')}  camada {cfg.get('layer_height')} mm")
    print(f"Suporte: {'sim' if cfg.get('enable_support') == '1' else 'não'} ({cfg.get('support_type')})  "
          f"Brim: {cfg.get('brim_type')} gap {cfg.get('brim_object_gap')}  "
          f"elefant_foot {cfg.get('elefant_foot_compensation')}")
    print(f"Tempo estimado: {tempo}   Filamento: {cfg.get('filament used [g]', '?')} g   "
          f"Camadas: {cfg.get('total layers count', '?')}")
    print(f"Miniatura na tela: {'sim' if tem_mini else 'não'}")


if __name__ == "__main__":
    main()
