"""Sincroniza os perfis de usuário do Creality Print (impressora, filamento, processo) com o repositório.

Os presets do Creality Print são a fonte dos valores. Este script roda igual no Windows e no macOS e
NUNCA escreve na pasta do programa: a volta (repositório -> programa) é pelo menu
File > Import > Import Configuration, escolhendo .claude/perfis/perfis_creality.zip.

Uso (da raiz do repositório):
  uv run .claude/perfis/sincronizar_perfis.py comparar
      mostra o que difere entre o Creality Print deste computador e o repositório (sai com 1 se difere)
  uv run .claude/perfis/sincronizar_perfis.py exportar [--remover-ausentes]
      copia os presets do programa para .claude/perfis/creality-print/ e refaz o zip.
      Preset que está no repositório e não está no programa só é apagado com --remover-ausentes.
  uv run .claude/perfis/sincronizar_perfis.py tabela [--gravar]
      tabela dos perfis de filamento e de processo, com a herança resolvida pelos perfis de fábrica
      deste computador. --gravar atualiza a tabela da skill k1max-config-impressao.
  uv run .claude/perfis/sincronizar_perfis.py zip
      só refaz o zip a partir da pasta do repositório

  --dados PASTA   pasta de uma versão do Creality Print (a que contém "user" e "system"), se o
                  script não achar sozinho
"""
import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ferramentas"))
import k1comum

AQUI = Path(__file__).resolve().parent
PASTA = AQUI / "creality-print"
ZIP = AQUI / "perfis_creality.zip"
SKILL = k1comum.RAIZ / ".claude/skills/k1max-config-impressao/SKILL.md"
TIPOS = ("machine", "filament", "process")
MARCA_INI, MARCA_FIM = "<!-- tabela-perfis:inicio -->", "<!-- tabela-perfis:fim -->"

FILAMENTO = [  # (rótulo, chaves)
    ("Bico / 1ª camada (°C)", ["nozzle_temperature", "nozzle_temperature_initial_layer"]),
    ("Mesa lisa / 1ª camada (°C)", ["hot_plate_temp", "hot_plate_temp_initial_layer"]),
    ("Mesa texturizada / 1ª camada (°C)", ["textured_plate_temp", "textured_plate_temp_initial_layer"]),
    ("Flow ratio", ["filament_flow_ratio"]),
    ("Pressure advance", ["pressure_advance"]),
    ("Retração (mm) / veloc. / desretração", ["filament_retraction_length", "filament_retraction_speed",
                                             "filament_deretraction_speed"]),
    ("Fluxo máximo (mm³/s)", ["filament_max_volumetric_speed"]),
    ("Ventoinha mín. / máx. (%)", ["fan_min_speed", "fan_max_speed"]),
    ("Ventoinha lateral (%)", ["additional_cooling_fan_speed"]),
    ("Tempo mínimo de camada (s)", ["slow_down_layer_time"]),
]
PROCESSO = [
    ("Camada / 1ª camada (mm)", ["layer_height", "initial_layer_print_height"]),
    ("Largura de linha (mm)", ["line_width"]),
    ("Paredes / topo / base", ["wall_loops", "top_shell_layers", "bottom_shell_layers"]),
    ("Preenchimento", ["sparse_infill_density", "sparse_infill_pattern"]),
    ("Parede externa / interna (mm/s)", ["outer_wall_speed", "inner_wall_speed"]),
    ("Suporte", ["enable_support", "support_type", "support_style"]),
    ("Folga Z do suporte em cima / embaixo (mm)", ["support_top_z_distance", "support_bottom_z_distance"]),
    ("Brim: tipo / largura / gap", ["brim_type", "brim_width", "brim_object_gap"]),
    ("Compensação de pé de elefante", ["elefant_foot_compensation"]),
    ("Compensação XY furo / contorno", ["xy_hole_compensation", "xy_contour_compensation"]),
]


# --- onde ficam os presets -----------------------------------------------------------------
def pasta_versao(dados):
    """Pasta da versão mais nova do Creality Print que tenha presets (ou a informada)."""
    if dados:
        return Path(dados)
    base = k1comum.pasta_dados_creality()
    versoes = sorted((p for p in base.glob("*") if (p / "user").is_dir()),
                     key=lambda p: [int(x) for x in re.findall(r"\d+", p.name)], reverse=True)
    if not versoes:
        sys.exit(f"Não achei o Creality Print em {base}. Passe a pasta com --dados.")
    return versoes[0]


def pasta_usuario(versao):
    """Conta (ou 'default') com mais presets; None se o programa não tem nenhum preset de usuário."""
    contas = [p for p in (versao / "user").iterdir() if p.is_dir() and (p.name.isdigit() or p.name == "default")]
    contas = sorted(contas, key=lambda p: sum(len(list((p / t).glob("*.json"))) for t in TIPOS), reverse=True)
    if not contas or not any(list((contas[0] / t).glob("*.json")) for t in TIPOS):
        return None
    return contas[0]


def ler(pasta):
    """{(tipo, arquivo.json): dict} dos presets de uma pasta com machine/, filament/ e process/."""
    presets = {}
    for tipo in TIPOS:
        for p in sorted((pasta / tipo).glob("*.json")) if (pasta / tipo).is_dir() else []:
            presets[(tipo, p.name)] = json.loads(p.read_text(encoding="utf-8-sig"))
    return presets


def diferencas(a, b):
    """Chaves com valor diferente entre dois presets: [(chave, valor em a, valor em b)]."""
    return [(k, a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def curto(v):
    v = v[0] if isinstance(v, list) and len(v) == 1 else v
    if v == "nil":
        return "da impressora"   # "nil" no preset = usa o valor do perfil da impressora
    return "(ausente)" if v is None else str(v)


def refazer_zip():
    """Zip sem pastas internas (o Creality importa assim), com data fixa: mesmo conteúdo, mesmo arquivo."""
    arquivos = sorted(p for t in TIPOS for p in (PASTA / t).glob("*.json"))
    nomes = [p.name for p in arquivos]
    repetidos = {n for n in nomes if nomes.count(n) > 1}
    if repetidos:
        sys.exit(f"Nomes repetidos entre machine/filament/process: {', '.join(sorted(repetidos))}")
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in arquivos:
            info = zipfile.ZipInfo(p.name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
    return len(arquivos)


# --- comandos ------------------------------------------------------------------------------
def comparar(a):
    versao = pasta_versao(a.dados)
    usuario = pasta_usuario(versao)
    repo = ler(PASTA)
    app = ler(usuario) if usuario else {}
    print(f"Creality Print: {usuario or str(versao) + ' (nenhum preset de usuário)'}")
    print(f"Repositório:    {PASTA}")
    difere = False
    for chave in sorted(set(repo) | set(app)):
        nome = f"{chave[0]}/{chave[1]}"
        if chave not in app:
            print(f"  só no repositório: {nome}"); difere = True
        elif chave not in repo:
            print(f"  só no programa:    {nome}"); difere = True
        else:
            d = diferencas(app[chave], repo[chave])
            if d:
                difere = True
                print(f"  diferente:         {nome}")
                for k, va, vr in d:
                    print(f"      {k}: programa {curto(va)} | repositório {curto(vr)}")
    if not difere:
        print("Iguais.")
    elif not usuario:
        print("\nEste Creality Print não tem presets de usuário: importe .claude/perfis/perfis_creality.zip "
              "(File > Import > Import Configuration).")
    else:
        print("\nPara levar o programa ao repositório: exportar. Para trazer o repositório ao programa: "
              "importe o zip pelo menu File > Import > Import Configuration.")
    return 1 if difere else 0


def exportar(a):
    versao = pasta_versao(a.dados)
    usuario = pasta_usuario(versao)
    if not usuario:
        sys.exit(f"O Creality Print deste computador ({versao}) não tem presets de usuário: nada a exportar.\n"
                 "O repositório não foi alterado.")
    app, repo = ler(usuario), ler(PASTA)
    for (tipo, nome), dados in sorted(app.items()):
        destino = PASTA / tipo / nome
        if (tipo, nome) not in repo:
            print(f"  novo:      {tipo}/{nome}")
        elif diferencas(dados, repo[(tipo, nome)]):
            print(f"  alterado:  {tipo}/{nome}")
            for k, va, vr in diferencas(dados, repo[(tipo, nome)]):
                print(f"      {k}: {curto(vr)} -> {curto(va)}")
        else:
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(usuario / tipo / nome, destino)   # só os .json: os .info têm o ID da conta
    for tipo, nome in sorted(set(repo) - set(app)):
        if a.remover_ausentes:
            (PASTA / tipo / nome).unlink()
            print(f"  removido:  {tipo}/{nome}")
        else:
            print(f"  mantido (não está no programa; --remover-ausentes apaga): {tipo}/{nome}")
    n = refazer_zip()
    print(f"Exportado de {usuario}\n{n} presets em {PASTA}\nZip: {ZIP}")
    print("Depois: uv run .claude/perfis/sincronizar_perfis.py tabela --gravar, commit e PR (branch perfil/...).")
    return 0


def resolver(tipo, preset, sistema):
    """Valores finais de um preset: sobe pela herança nos perfis de fábrica. Devolve (valores, origem)."""
    cadeia, atual, visto = [preset], preset, set()
    while atual.get("inherits") and atual["inherits"] not in visto:
        visto.add(atual["inherits"])
        p = sistema / tipo / f"{atual['inherits']}.json"
        if not p.exists():
            cadeia.append(None)
            break
        atual = json.loads(p.read_text(encoding="utf-8-sig"))
        cadeia.append(atual)
    valores, completo = {}, cadeia[-1] is not None
    for nivel in reversed([c for c in cadeia if c is not None]):
        valores.update(nivel)
    return valores, completo


def celula(valores, preset, chaves, completo):
    partes = []
    for k in chaves:
        if k in valores:
            v = curto(valores[k])
            partes.append(f"**{v}**" if k in preset else v)   # negrito = definido no preset de usuário
        else:
            partes.append("?" if not completo else "–")
    return " / ".join(partes)


def montar_tabela(a):
    versao = pasta_versao(a.dados)
    sistema = versao / "system" / "Creality"
    repo = ler(PASTA)
    linhas = [MARCA_INI,
              f"_Gerado por `sincronizar_perfis.py tabela --gravar` a partir de `.claude/perfis/creality-print/`. "
              f"Não edite à mão. **Negrito** = valor definido no preset; o resto vem do perfil de fábrica "
              f"(lido do Creality Print deste computador, pasta `{versao.name}`)._", ""]
    incompletos = []
    for titulo, tipo, campos in (("Filamentos", "filament", FILAMENTO), ("Processos", "process", PROCESSO)):
        presets = [(dados.get("name", nome), dados) for (t, nome), dados in sorted(repo.items()) if t == tipo]
        resolvidos = [(n, d, *resolver(tipo, d, sistema)) for n, d in presets]
        incompletos += [n for n, _, _, ok in resolvidos if not ok]
        linhas += [f"**{titulo}**", "", "| | " + " | ".join(n for n, *_ in resolvidos) + " |",
                   "|---|" + "---|" * len(resolvidos),
                   "| Herda de | " + " | ".join(str(d.get("inherits", "–")) for _, d, _, _ in resolvidos) + " |"]
        for rotulo, chaves in campos:
            linhas.append(f"| {rotulo} | " + " | ".join(celula(v, d, chaves, ok) for _, d, v, ok in resolvidos) + " |")
        linhas.append("")
    linhas.append(MARCA_FIM)
    return "\n".join(linhas), incompletos


def tabela(a):
    texto, incompletos = montar_tabela(a)
    if incompletos:
        print("AVISO: perfil de fábrica não encontrado neste computador para: " + ", ".join(incompletos)
              + " (valores herdados aparecem como '?')", file=sys.stderr)
    if not a.gravar:
        print(texto)
        return 0
    s = SKILL.read_text(encoding="utf-8")
    if MARCA_INI not in s or MARCA_FIM not in s:
        sys.exit(f"Não achei os marcadores da tabela em {SKILL}")
    novo = s[:s.index(MARCA_INI)] + texto + s[s.index(MARCA_FIM) + len(MARCA_FIM):]
    SKILL.write_text(novo, encoding="utf-8", newline="\n")
    print(f"Tabela atualizada em {SKILL}" if novo != s else "Tabela já estava atualizada.")
    return 0


def main():
    k1comum.saida_utf8()
    ap = argparse.ArgumentParser(description="Sincroniza os perfis do Creality Print com o repositório.")
    ap.add_argument("comando", choices=["comparar", "exportar", "tabela", "zip"])
    ap.add_argument("--dados")
    ap.add_argument("--remover-ausentes", action="store_true")
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    if a.comando == "zip":
        print(f"{refazer_zip()} presets em {ZIP}")
        return 0
    return {"comparar": comparar, "exportar": exportar, "tabela": tabela}[a.comando](a)


if __name__ == "__main__":
    sys.exit(main())
