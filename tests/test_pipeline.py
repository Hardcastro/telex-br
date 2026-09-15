"""
Smoke test do pipeline completo, rodando 100% sobre data/sample/sample_items.json
— nenhuma chamada de rede, então roda em CI sem depender de feeds no ar.

Cada teste passa data_dir=tmp_path pro pipeline: sem isso, run() grava em
cima de data/cycles/latest.{json,csv} de verdade a cada execução — o
arquivo que fica versionado no repo como exemplo (e que o dashboard/README
apontam) ficava sendo pisado toda vez que alguém rodava `pytest` localmente.
"""

from src.pipeline import run


def test_demo_cycle_shape(tmp_path):
    envelope = run(demo=True, data_dir=tmp_path)

    assert envelope["total_items"] > 0
    assert envelope["window_hours"] == 12
    assert set(envelope["editorial_balance"]) == {"direita", "esquerda", "centro", "tecnica_neutra"}

    # a amostra em data/sample/sample_items.json tem 4+ itens em cada
    # bucket de propósito, então a cota fecha 4·4·4·8 = 20 no modo demo.
    assert envelope["total_items"] == 20
    assert envelope["editorial_balance"] == {
        "direita": 4, "esquerda": 4, "centro": 4, "tecnica_neutra": 8,
    }
    assert (tmp_path / "latest.json").exists()


def test_highlights_point_to_real_items(tmp_path):
    envelope = run(demo=True, data_dir=tmp_path)
    ids = {item["id"] for item in envelope["items"]}

    assert envelope["highlights"]["top_view_id"] in ids
    assert envelope["highlights"]["top_reply_id"] in ids

    flagged_view = [i for i in envelope["items"] if i["is_top_view"]]
    flagged_reply = [i for i in envelope["items"] if i["is_top_reply"]]
    assert len(flagged_view) == 1
    assert len(flagged_reply) == 1


def test_every_item_has_a_category(tmp_path):
    envelope = run(demo=True, data_dir=tmp_path)
    for item in envelope["items"]:
        assert item["category"] in {"politica", "macroeconomia", "manchete"}
