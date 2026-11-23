"""Testes da análise de malha, do checklist e das correções do gerar. Rodar: uv run pytest"""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
import trimesh

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "ferramentas"))
import k1malha  # noqa: E402

SCRIPTS = RAIZ / ".claude/skills/creality-print-3mf"
REFERENCIA = RAIZ / ".claude/referencias/Snowboarder_1-25_PLA_bico_0.4_detalhe.3mf"


def rodar(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


@pytest.fixture(scope="module")
def projeto_cubo(tmp_path_factory):
    """Projeto gerado de um cubo 20 x 30 x 10 sobre o projeto de referência (que tem 2 bloqueadores)."""
    pasta = tmp_path_factory.mktemp("cubo")
    stl, saida = pasta / "cubo.stl", pasta / "cubo.3mf"
    trimesh.creation.box((20, 30, 10)).export(stl)
    r = rodar("gerar_projeto_creality.py", REFERENCIA, REFERENCIA, stl, saida, "Cubo", '{"enable_support": "0"}')
    assert r.returncode == 0, r.stderr
    return saida


def mesa(n=1.0):
    """Mesa em T: tampo 40 x 40 x 4 sobre um pé 10 x 10 x 20. O tampo fica em balanço."""
    pe = trimesh.creation.box((10, 10, 20)); pe.apply_translation((0, 0, 10))
    tampo = trimesh.creation.box((40, 40, 4)); tampo.apply_translation((0, 0, 22))
    return trimesh.boolean.union([pe, tampo], engine="manifold")


def test_analisar_cubo():
    a = k1malha.analisar(trimesh.creation.box((20, 30, 10)))
    assert a["dimensoes_mm"] == [20, 30, 10]
    assert a["fechada"] and a["volume_valido"] and a["corpos"] == 1
    assert a["area_contato_mm2"] == 600 and a["area_balanco_mm2"] == 0
    assert a["volume_cm3"] == 6 and k1malha.problemas(a) == []


def test_analisar_mede_balanco_e_contato():
    a = k1malha.analisar(mesa())
    assert a["area_contato_mm2"] == 100                 # só o pé encosta
    assert a["area_balanco_mm2"] == 40 * 40 - 10 * 10   # a face de baixo do tampo, menos o pé
    assert len(a["regioes_balanco"]) == 1
    assert a["regioes_balanco"][0]["z_min"] == a["regioes_balanco"][0]["z_max"] == 20


def test_analisar_reprova_aberta_grande_e_solta():
    cubo = trimesh.creation.box((20, 30, 10))
    aberta = trimesh.Trimesh(cubo.vertices, cubo.faces[:-1])
    assert any("aberta" in p for p in k1malha.problemas(k1malha.analisar(aberta)))
    grande = k1malha.analisar(trimesh.creation.box((299, 100, 10)), brim=5)
    assert any("não cabe" in p for p in k1malha.problemas(grande))
    assert k1malha.problemas(k1malha.analisar(trimesh.creation.box((299, 100, 10)))) == []
    solto = trimesh.creation.box((5, 5, 5)); solto.apply_translation((50, 0, 30))
    a = k1malha.analisar(trimesh.util.concatenate([cubo, solto]))
    assert a["corpos"] == 2 and a["corpos_sem_apoio_na_mesa"] == 1


def test_ler_3mf_separa_peca_de_bloqueador():
    p = k1malha.ler_3mf(str(REFERENCIA))
    assert [x.subtipo for x in p.partes] == ["normal_part", "support_blocker", "support_blocker"]
    lo, hi = p.pecas()[0].malha.bounds
    assert abs(lo[2]) < 1e-3                                      # apoiada na mesa
    assert np.allclose((lo[:2] + hi[:2]) / 2, (150, 150), atol=0.01)  # no centro
    assert p.settings["printer_settings_id"] == "Creality K1 Max 0.4 nozzle"


def test_gerar_limpa_partes_extras_e_grava_com_precisao(tmp_path, projeto_cubo):
    p = k1malha.ler_3mf(str(projeto_cubo))
    assert [x.subtipo for x in p.partes] == ["normal_part"]       # os 2 bloqueadores da referência saíram
    with zipfile.ZipFile(projeto_cubo) as z:
        assert b"support_blocker" not in z.read("Metadata/model_settings.config")
        assert z.read("3D/3dmodel.model").count(b"<component ") == 1
    # vértices quase coincidentes não podem se fundir ao gravar
    cubo = trimesh.creation.box((20, 30, 10))
    cubo.vertices[0] += 1e-7
    stl, saida = tmp_path / "fino.stl", tmp_path / "fino.3mf"
    cubo.export(stl)
    assert rodar("gerar_projeto_creality.py", REFERENCIA, REFERENCIA, stl, saida, "Fino").returncode == 0
    lida = k1malha.ler_3mf(str(saida)).pecas()[0].malha
    original = trimesh.load(stl, force="mesh")
    assert np.allclose(np.sort(lida.extents), np.sort(original.extents), atol=1e-6)
    assert lida.is_watertight


def test_gerar_recusa_malha_maior_que_a_mesa(tmp_path):
    stl = tmp_path / "grande.stl"
    trimesh.creation.box((310, 20, 10)).export(stl)
    r = rodar("gerar_projeto_creality.py", REFERENCIA, REFERENCIA, stl, tmp_path / "g.3mf", "Grande")
    assert r.returncode != 0 and "nao cabe" in r.stderr
    assert not (tmp_path / "g.3mf").exists()


def test_checklist_aprova_referencias_e_projeto_gerado(projeto_cubo):
    for projeto in [REFERENCIA, RAIZ / ".claude/referencias/Snowboarder_1-25_PLA_bico_0.2_v5.3mf"]:
        r = rodar("checklist_3mf.py", projeto, "--origem", projeto)
        assert r.returncode == 0, r.stdout
        assert "[FALHA]" not in r.stdout
    r = rodar("checklist_3mf.py", projeto_cubo, "--origem", REFERENCIA, "--bico", "0.4")
    assert r.returncode == 0, r.stdout
    assert "Área de contato com a mesa: 600.0 mm²" in r.stdout


@pytest.mark.parametrize("mudanca, esperado", [
    ({"brim_object_gap": "0.1"}, "Brim não encosta"),
    ({"elefant_foot_compensation": "0.15"}, "Brim não encosta"),
    ({"support_top_z_distance": "0.16"}, "Folga Z do suporte 0.16"),
    ({"nozzle_temperature": "220"}, "Filamento alterado"),
    ({"nozzle_diameter": "0.2"}, "perfil da impressora é de 0.4"),
])
def test_checklist_reprova(tmp_path, mudanca, esperado):
    cfg, saida = tmp_path / "m.json", tmp_path / "ruim.3mf"
    cfg.write_text(json.dumps(mudanca), encoding="utf-8")
    assert rodar("alterar_config_3mf.py", REFERENCIA, saida, "--config", cfg).returncode == 0
    r = rodar("checklist_3mf.py", saida, "--origem", REFERENCIA)
    assert r.returncode == 1
    assert esperado in r.stdout


def test_checklist_permitir_e_bico_montado(tmp_path):
    cfg, saida = tmp_path / "m.json", tmp_path / "t.3mf"
    cfg.write_text('{"nozzle_temperature": "220"}', encoding="utf-8")
    rodar("alterar_config_3mf.py", REFERENCIA, saida, "--config", cfg)
    assert rodar("checklist_3mf.py", saida, "--origem", REFERENCIA, "--permitir", "nozzle_temperature").returncode == 0
    r = rodar("checklist_3mf.py", REFERENCIA, "--bico", "0.2")
    assert r.returncode == 1 and "Bico montado é 0.2" in r.stdout


def test_analisar_malha_script_e_render(tmp_path, projeto_cubo):
    png = tmp_path / "v.png"
    r = rodar("analisar_malha.py", projeto_cubo, "--json", "--render", png)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["dimensoes_mm"] == [20, 30, 10] and d["cabe_na_mesa"] and d["problemas"] == []
    assert png.read_bytes()[:4] == b"\x89PNG"
    stl = tmp_path / "aberta.stl"
    cubo = trimesh.creation.box((20, 30, 10))
    trimesh.Trimesh(cubo.vertices, cubo.faces[:-1]).export(stl)
    assert rodar("analisar_malha.py", stl).returncode == 1
