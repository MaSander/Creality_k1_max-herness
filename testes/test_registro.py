"""Testes do registro de impressão. Rodar: uv run pytest"""
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "registrar_impressao", RAIZ / ".claude/skills/registro-impressao/registrar_impressao.py")
ri = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ri)
REFERENCIA = RAIZ / ".claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf"
TRABALHO = {"filename": "/usr/data/printer_data/gcodes/peca_bico0.4_PLA_1h20m.gcode", "starttime": 1795381648,
            "usagetime": 4830, "usagematerial": 5408.9, "printfinish": 1}


@pytest.fixture
def pecas(tmp_path, monkeypatch):
    monkeypatch.setattr(ri, "PECAS", tmp_path / "pecas")
    monkeypatch.setattr(ri, "RAIZ", tmp_path)
    monkeypatch.setattr(ri, "historico", lambda ip: [TRABALHO])
    return tmp_path / "pecas"


def rodar(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["registrar_impressao.py", *map(str, args)])
    ri.main()


def test_cria_readme_e_registra_com_dados_da_impressora_e_do_projeto(pecas, monkeypatch, capsys):
    rodar(monkeypatch, "suporte", "--resultado", "aprovada", "--quem", "Marcelo", "--data", "2026-11-22",
          "--gcode", "peca_bico0.4_PLA_1h20m.gcode", "--projeto", REFERENCIA, "--obs", "encaixou", "--licao", "L1")
    t = (pecas / "suporte" / "README.md").read_text(encoding="utf-8")
    assert t.startswith("# suporte") and "## Impressões" in t
    assert "### 22/11/2026 – aprovada (Marcelo)" in t
    assert "concluída na impressora" in t and "1h20, 5,41 m de filamento" in t
    assert "Creality K1 Max 0.4 nozzle; filamento PLA FLEXYGREEN" in t and "brim outer_only 3 mm (gap 0" in t
    assert "- **Resultado:** encaixou" in t and "  - L1" in t


def test_so_acrescenta_e_mantem_a_ordem(pecas, monkeypatch):
    (pecas / "x").mkdir(parents=True)
    (pecas / "x" / "README.md").write_text("# X\n\ntexto antigo\n\n## Impressões\n\n### 01/01/2026 – aprovada (A)\n"
                                           "- antiga\n\n## Outra seção\nfim\n", encoding="utf-8")
    rodar(monkeypatch, "x", "--resultado", "reprovada", "--quem", "B", "--data", "2026-02-02", "--sem-impressora",
          "--gcode", "a.gcode", "--obs", "descolou")
    t = (pecas / "x" / "README.md").read_text(encoding="utf-8")
    assert "texto antigo" in t and "- antiga" in t
    assert t.index("01/01/2026") < t.index("02/02/2026 – reprovada (B)") < t.index("## Outra seção")
    assert t.rstrip().endswith("fim")


def test_avisa_trabalho_fora_do_historico_e_interrompido_aprovado(pecas, monkeypatch, capsys):
    rodar(monkeypatch, "y", "--resultado", "aprovada", "--quem", "A", "--gcode", "outro.gcode")
    assert "não está no histórico" in capsys.readouterr().out
    monkeypatch.setattr(ri, "historico", lambda ip: [{**TRABALHO, "printfinish": 0}])
    rodar(monkeypatch, "y", "--resultado", "aprovada", "--quem", "A", "--gcode", "peca_bico0.4_PLA_1h20m.gcode")
    saida = capsys.readouterr().out
    assert "**interrompida**" in saida and "registra este trabalho como interrompido" in saida


def test_impressora_fora_do_ar_nao_impede_o_registro(pecas, monkeypatch, capsys):
    def sem_rede(ip):
        raise OSError("sem rota")
    monkeypatch.setattr(ri, "historico", sem_rede)
    rodar(monkeypatch, "z", "--resultado", "parcial", "--quem", "A", "--gcode", "a.gcode")
    assert "aprovada com ressalvas" in (pecas / "z" / "README.md").read_text(encoding="utf-8")
    assert "não consegui falar com a impressora" in capsys.readouterr().out


def test_recusa_nome_de_peca_com_caminho(pecas, monkeypatch):
    with pytest.raises(SystemExit):
        rodar(monkeypatch, "../fora", "--resultado", "aprovada", "--quem", "A")
