"""Testes da sincronização de perfis do Creality Print. Rodar: uv run pytest"""
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sincronizar_perfis", RAIZ / ".claude/perfis/sincronizar_perfis.py")
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)


def gravar(pasta, tipo, nome, dados):
    (pasta / tipo).mkdir(parents=True, exist_ok=True)
    (pasta / tipo / f"{nome}.json").write_text(json.dumps(dados), encoding="utf-8")


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    """Creality Print de mentira (pasta da versão com user/ e system/) e repositório de mentira."""
    versao = tmp_path / "dados" / "7.3"
    conta = versao / "user" / "12345"
    sistema = versao / "system" / "Creality"
    gravar(sistema, "filament", "Generic PLA", {"name": "Generic PLA", "inherits": "base_pla",
                                                "nozzle_temperature": ["220"], "fan_max_speed": ["100"]})
    gravar(sistema, "filament", "base_pla", {"name": "base_pla", "filament_flow_ratio": ["0.98"],
                                             "nozzle_temperature": ["200"]})
    gravar(conta, "filament", "PLA CASA", {"name": "PLA CASA", "inherits": "Generic PLA",
                                           "nozzle_temperature": ["210"], "pressure_advance": ["0.05"]})
    (conta / "filament" / "PLA CASA.info").write_text("user_id = 12345", encoding="utf-8")
    gravar(conta, "process", "Fino", {"name": "Fino", "layer_height": "0.1"})
    (versao / "user" / "default" / "filament").mkdir(parents=True)
    repo = tmp_path / "repo" / "creality-print"
    monkeypatch.setattr(sp, "PASTA", repo)
    monkeypatch.setattr(sp, "ZIP", tmp_path / "repo" / "perfis.zip")
    return versao, conta, repo


def args(versao, **k):
    return type("A", (), {"dados": str(versao), "remover_ausentes": False, "gravar": False, **k})()


def test_exportar_copia_so_json_e_faz_zip(ambiente, capsys):
    versao, conta, repo = ambiente
    assert sp.exportar(args(versao)) == 0
    assert sorted(p.name for p in repo.rglob("*") if p.is_file()) == ["Fino.json", "PLA CASA.json"]
    with zipfile.ZipFile(sp.ZIP) as z:
        assert sorted(z.namelist()) == ["Fino.json", "PLA CASA.json"]   # sem pastas e sem o .info da conta
    assert sp.comparar(args(versao)) == 0
    assert "Iguais." in capsys.readouterr().out


def test_zip_igual_para_o_mesmo_conteudo(ambiente):
    versao, conta, repo = ambiente
    sp.exportar(args(versao))
    antes = sp.ZIP.read_bytes()
    sp.refazer_zip()
    assert sp.ZIP.read_bytes() == antes


def test_comparar_mostra_a_chave_que_mudou(ambiente, capsys):
    versao, conta, repo = ambiente
    sp.exportar(args(versao))
    gravar(conta, "filament", "PLA CASA", {"name": "PLA CASA", "inherits": "Generic PLA",
                                           "nozzle_temperature": ["215"], "pressure_advance": ["0.05"]})
    capsys.readouterr()
    assert sp.comparar(args(versao)) == 1
    assert "nozzle_temperature: programa 215 | repositório 210" in capsys.readouterr().out


def test_exportar_nao_apaga_o_repositorio_sem_pedir(ambiente):
    versao, conta, repo = ambiente
    sp.exportar(args(versao))
    (conta / "process" / "Fino.json").unlink()
    sp.exportar(args(versao))
    assert (repo / "process" / "Fino.json").exists()            # mantido
    sp.exportar(args(versao, remover_ausentes=True))
    assert not (repo / "process" / "Fino.json").exists()        # apagado só com a opção


def test_exportar_recusa_programa_sem_presets(ambiente):
    versao, conta, repo = ambiente
    sp.exportar(args(versao))
    for p in conta.rglob("*.json"):
        p.unlink()
    with pytest.raises(SystemExit):
        sp.exportar(args(versao))
    assert (repo / "filament" / "PLA CASA.json").exists()       # o repositório não foi tocado


def test_tabela_resolve_a_heranca(ambiente):
    versao, conta, repo = ambiente
    sp.exportar(args(versao))
    texto, incompletos = sp.montar_tabela(args(versao))
    assert incompletos == []
    assert "| Bico / 1ª camada (°C) | **210** / – |" in texto     # definido no preset: negrito
    assert "| Flow ratio | 0.98 |" in texto                       # herdado de dois níveis acima
    assert "| Ventoinha mín. / máx. (%) | – / 100 |" in texto
    gravar(repo, "filament", "Solto", {"name": "Solto", "inherits": "Nao Existe"})
    assert sp.montar_tabela(args(versao))[1] == ["Solto"]


def test_presets_do_repositorio_batem_com_o_zip_e_a_tabela_esta_atualizada():
    """O que está no repositório de verdade: zip igual à pasta e tabela da skill gerada dela."""
    pasta, zip_ = RAIZ / ".claude/perfis/creality-print", RAIZ / ".claude/perfis/perfis_creality.zip"
    soltos = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in pasta.rglob("*.json")}
    with zipfile.ZipFile(zip_) as z:
        assert sorted(z.namelist()) == sorted(soltos)
        assert all(json.loads(z.read(n)) == soltos[n] for n in soltos)
    skill = (RAIZ / ".claude/skills/k1max-config-impressao/SKILL.md").read_text(encoding="utf-8")
    for nome in (d["name"] for d in soltos.values() if d.get("name") and "nozzle.json" not in d["name"]):
        if (pasta / "machine" / f"{nome}.json").exists():
            continue
        assert nome in skill, f"preset {nome} não está na tabela da skill: rode tabela --gravar"
