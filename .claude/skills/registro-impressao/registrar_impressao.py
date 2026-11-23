"""Registra o resultado de uma impressão em pecas/<peca>/README.md.

Acrescenta uma entrada datada na seção "Impressões" do registro da peça, com:
  - o que a impressora informa sobre o trabalho (concluída ou interrompida, duração, metros de
    filamento), buscado no histórico dela pelo nome do G-code;
  - a configuração do projeto .3mf (impressora, bico, filamento, camada, suporte, brim), lida do arquivo;
  - o resultado dito por quem imprimiu, a observação e as lições.
Só acrescenta texto: não reescreve o que já está no README. Se a peça ainda não tem README, cria um.

Uso (da raiz do repositório):
  uv run .claude/skills/registro-impressao/registrar_impressao.py <peca> --resultado aprovada|parcial|reprovada
        --quem Marcelo [--gcode "nome.gcode"] [--projeto caminho.3mf] [--obs "..."] [--licao "..."]...
        [--sem-impressora] [--ip 192.168.0.69] [--data AAAA-MM-DD]

  uv run .claude/skills/registro-impressao/registrar_impressao.py --ultimas 5
        mostra os últimos trabalhos da impressora, para achar o nome do G-code
"""
import argparse
import datetime
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "ferramentas"))
sys.path.insert(0, str(RAIZ / ".claude/skills/k1max-impressora"))
import k1comum
import k1max_status

PECAS = RAIZ / "pecas"
SECAO = "## Impressões"
ROTULO = {"aprovada": "aprovada", "parcial": "aprovada com ressalvas", "reprovada": "reprovada"}


def historico(ip):
    d = k1max_status._ws_get(ip, {"method": "get", "params": {"reqHistory": 1}}, duracao=6)
    return sorted(d.get("historyList") or [], key=lambda x: -x.get("starttime", 0))


def linha_trabalho(h):
    dur = h.get("usagetime", 0)
    quando = datetime.datetime.fromtimestamp(h["starttime"]).strftime("%d/%m/%Y %H:%M")
    fim = "concluída" if h.get("printfinish") else "**interrompida**"
    return (f"{fim} na impressora, iniciada em {quando}, {dur // 3600}h{dur % 3600 // 60:02d}, "
            f"{h.get('usagematerial', 0) / 1000:.2f} m de filamento").replace(".", ",")


def achar_trabalho(ip, gcode):
    """Trabalho mais recente do histórico com esse nome de arquivo; None se não achar ou sem rede."""
    try:
        lista = historico(ip)
    except OSError as e:
        return None, f"não consegui falar com a impressora em {ip} ({e})"
    for h in lista:
        if os.path.basename(h.get("filename", "")) == os.path.basename(gcode):
            return h, None
    return None, f"'{gcode}' não está no histórico da impressora"


def resumo_projeto(caminho):
    import k1malha
    s = k1malha.ler_3mf(caminho).settings

    def p(k):
        v = s.get(k)
        return v[0] if isinstance(v, list) and v else v
    suporte = (f"suporte {p('support_type')} / {p('support_style')}, folga Z {p('support_top_z_distance')}"
               if str(p("enable_support")) == "1" else "sem suporte")
    brim = ("sem brim" if p("brim_type") == "no_brim" else
            f"brim {p('brim_type')} {p('brim_width')} mm (gap {p('brim_object_gap')}, "
            f"pé de elefante {p('elefant_foot_compensation')})")
    return (f"{p('printer_settings_id')}; filamento {p('filament_settings_id')} "
            f"({p('nozzle_temperature')} °C, mesa {p('hot_plate_temp')} °C, flow {p('filament_flow_ratio')}, "
            f"PA {p('pressure_advance')}); processo {p('print_settings_id')}, camada {p('layer_height')} mm, "
            f"{p('wall_loops')} paredes, {p('sparse_infill_density')} {p('sparse_infill_pattern')}; {suporte}; {brim}")


def montar_entrada(a, trabalho, aviso, projeto):
    data = datetime.date.fromisoformat(a.data) if a.data else datetime.date.today()
    linhas = [f"### {data.strftime('%d/%m/%Y')} – {ROTULO[a.resultado]} ({a.quem})"]
    if a.gcode:
        linhas.append(f"- **G-code:** `{os.path.basename(a.gcode)}`"
                      + (f" – {linha_trabalho(trabalho)}" if trabalho else f" – sem dados da impressora ({aviso})"
                         if aviso else ""))
    if projeto:
        linhas.append(f"- **Projeto:** `{os.path.basename(a.projeto)}` – {projeto}")
    if a.obs:
        linhas.append(f"- **Resultado:** {a.obs}")
    if a.licao:
        linhas.append("- **Lições:**")
        linhas += [f"  - {l}" for l in a.licao]
    return "\n".join(linhas) + "\n"


def readme_novo(peca):
    return (f"# {peca}\n\n- **Origem:** _a registrar (projeto nosso ou modelo de terceiros, com a licença)._\n"
            "- **Para que serve:** _a registrar._\n\n"
            "Peça nossa tem a `ficha.json` ao lado (skill `modelagem-3d`).\n")


def main():
    k1comum.saida_utf8()
    ap = argparse.ArgumentParser(description="Registra o resultado de uma impressão no README da peça.")
    ap.add_argument("peca", nargs="?")
    ap.add_argument("--resultado", choices=list(ROTULO))
    ap.add_argument("--quem")
    ap.add_argument("--gcode")
    ap.add_argument("--projeto")
    ap.add_argument("--obs")
    ap.add_argument("--licao", action="append", default=[])
    ap.add_argument("--sem-impressora", action="store_true")
    ap.add_argument("--ip", default=k1max_status.IP_PADRAO)
    ap.add_argument("--data")
    ap.add_argument("--ultimas", type=int)
    a = ap.parse_args()

    if a.ultimas:
        try:
            for h in historico(a.ip)[:a.ultimas]:
                print(f"{os.path.basename(h['filename'])}  –  {linha_trabalho(h)}")
        except OSError as e:
            sys.exit(f"Não consegui falar com a impressora em {a.ip} ({e}).")
        return
    if not (a.peca and a.resultado and a.quem):
        ap.error("informe a peça, --resultado e --quem (ou use --ultimas N)")
    if "/" in a.peca or "\\" in a.peca or a.peca.startswith("."):
        ap.error("a peça é só o nome da pasta dentro de pecas/")

    trabalho, aviso = (None, None)
    if a.gcode and not a.sem_impressora:
        trabalho, aviso = achar_trabalho(a.ip, a.gcode)
    projeto = resumo_projeto(a.projeto) if a.projeto else None
    entrada = montar_entrada(a, trabalho, aviso, projeto)

    pasta = PECAS / a.peca
    readme = pasta / "README.md"
    criado = not readme.exists()
    pasta.mkdir(parents=True, exist_ok=True)
    texto = readme_novo(a.peca) if criado else readme.read_text(encoding="utf-8")
    if SECAO not in texto:
        texto = texto.rstrip("\n") + f"\n\n{SECAO}\n"
    i = texto.index(SECAO) + len(SECAO)
    prox = texto.find("\n## ", i)                       # a entrada nova fica no fim da seção
    fim = len(texto) if prox < 0 else prox
    texto = texto[:fim].rstrip("\n") + "\n\n" + entrada + (texto[fim:] if prox >= 0 else "")
    readme.write_text(texto, encoding="utf-8", newline="\n")

    print(("Criado " if criado else "Atualizado ") + str(readme.relative_to(RAIZ)))
    print(entrada)
    if aviso:
        print(f"AVISO: {aviso}. A entrada foi gravada sem os dados da impressora.")
    if trabalho and not trabalho.get("printfinish") and a.resultado == "aprovada":
        print("AVISO: a impressora registra este trabalho como interrompido, e o resultado informado é 'aprovada'. "
              "Confira se o G-code é o certo.")


if __name__ == "__main__":
    main()
