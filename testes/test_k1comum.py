"""Testes do que os scripts têm em comum e dos scripts de .3mf. Rodar: uv run pytest"""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "ferramentas"))
import k1comum  # noqa: E402

SCRIPTS = RAIZ / ".claude/skills/creality-print-3mf"
REFERENCIA = RAIZ / ".claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf"


def rodar(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


def settings(caminho):
    with zipfile.ZipFile(caminho) as z:
        return json.loads(z.read("Metadata/project_settings.config"))


def test_grupo_das_chaves():
    assert k1comum.grupo("layer_height") == 0
    assert k1comum.grupo("nozzle_temperature") == 1
    assert k1comum.grupo("filament_flow_ratio") == 1
    assert k1comum.grupo("nozzle_diameter") == 2


def test_aplicar_mudancas_registra_no_grupo_certo():
    s = {"wall_loops": "2", "nozzle_temperature": ["210"], "different_settings_to_system": ["a", "", ""]}
    k1comum.aplicar_mudancas(s, {"wall_loops": "4", "nozzle_temperature": "215"})
    assert s["wall_loops"] == "4"
    assert s["nozzle_temperature"] == ["215"]  # escalar vira lista quando a chave é lista
    assert s["different_settings_to_system"] == ["a;wall_loops", "nozzle_temperature", ""]
    with pytest.raises(SystemExit):
        k1comum.aplicar_mudancas(s, {"chave_que_nao_existe": "1"})


def test_ler_json_de_arquivo_e_da_linha(tmp_path):
    arq = tmp_path / "m.json"
    arq.write_text('﻿{"a": "1"}', encoding="utf-8")  # com BOM, como o PowerShell grava
    assert k1comum.ler_json(None, str(arq), {}) == {"a": "1"}
    assert k1comum.ler_json('{"b": "2"}', None, {}) == {"b": "2"}
    assert k1comum.ler_json(None, None, {}) == {}
    with pytest.raises(SystemExit):
        k1comum.ler_json("{b:2}", None, {})  # o que chega quando o PowerShell come as aspas


def test_copiar_zip_troca_e_remove(tmp_path):
    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    with zipfile.ZipFile(a, "w") as z:
        z.writestr("x.txt", "1"); z.writestr("y.txt", "2"); z.writestr("z.txt", "3")
    k1comum.copiar_zip(str(a), str(b), {"x.txt": b"novo"}, remover=("z.txt",))
    with zipfile.ZipFile(b) as z:
        assert z.namelist() == ["x.txt", "y.txt"]
        assert z.read("x.txt") == b"novo" and z.read("y.txt") == b"2"
    with zipfile.ZipFile(a) as z:  # a entrada continua legível
        assert z.read("z.txt") == b"3"
    with pytest.raises(SystemExit):
        k1comum.copiar_zip(str(a), str(b), {"nao_existe.txt": b""})


def test_alterar_muda_so_o_pedido(tmp_path):
    saida, cfg = tmp_path / "s.3mf", tmp_path / "m.json"
    cfg.write_text('{"wall_loops": "4"}', encoding="utf-8")
    r = rodar("alterar_config_3mf.py", REFERENCIA, saida, "--config", cfg)
    assert r.returncode == 0, r.stderr
    antes, depois = settings(REFERENCIA), settings(saida)
    assert depois["wall_loops"] == "4"
    assert "wall_loops" in depois["different_settings_to_system"][0].split(";")
    diferentes = {k for k in antes if antes[k] != depois[k]}
    assert diferentes <= {"wall_loops", "different_settings_to_system"}
    with zipfile.ZipFile(REFERENCIA) as za, zipfile.ZipFile(saida) as zb:
        assert za.read("3D/Objects/object_1.model") == zb.read("3D/Objects/object_1.model")


def test_alterar_recusa_saida_igual_a_entrada(tmp_path):
    copia = tmp_path / "c.3mf"
    copia.write_bytes(REFERENCIA.read_bytes())
    r = rodar("alterar_config_3mf.py", copia, copia, '{"wall_loops": "4"}')
    assert r.returncode != 0
    assert copia.read_bytes() == REFERENCIA.read_bytes()


def test_bloqueador_acrescenta_parte_e_recusa_fora_da_mesa(tmp_path):
    saida = tmp_path / "b.3mf"
    r = rodar("adicionar_bloqueador_3mf.py", REFERENCIA, saida,
              '[{"nome": "Teste", "min": [145, 173, 0], "max": [162, 181, 3.6]}]')
    assert r.returncode == 0, r.stderr
    with zipfile.ZipFile(REFERENCIA) as za, zipfile.ZipFile(saida) as zb:
        antes = za.read("Metadata/model_settings.config").count(b"support_blocker")
        assert zb.read("Metadata/model_settings.config").count(b"support_blocker") == antes + 1
    r = rodar("adicionar_bloqueador_3mf.py", REFERENCIA, tmp_path / "f.3mf",
              '[{"min": [145, 173, 0], "max": [362, 181, 3.6]}]')
    assert r.returncode != 0


def test_gerar_troca_a_malha_e_centraliza(tmp_path):
    import trimesh
    stl, saida = tmp_path / "cubo.stl", tmp_path / "g.3mf"
    trimesh.creation.box((20, 30, 10)).export(stl)
    r = rodar("gerar_projeto_creality.py", REFERENCIA, REFERENCIA, stl, saida, "Cubo", '{"layer_height": "0.12"}')
    assert r.returncode == 0, r.stderr
    assert settings(saida)["layer_height"] == "0.12"
    with zipfile.ZipFile(saida) as z:
        assert b"150.0 150.0 5.000000" in z.read("3D/3dmodel.model")  # centro da mesa, metade da altura
        assert b'value="Cubo"' in z.read("Metadata/model_settings.config")
