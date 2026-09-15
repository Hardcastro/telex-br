"""
Smoke test do pipeline completo, rodando 100% sobre data/sample/sample_items.json
— nenhuma chamada de rede, então roda em CI sem depender de feeds no ar.

Cada teste passa data_dir=tmp_path pro pipeline: sem isso, run() grava em
cima de data/cycles/latest.{json,csv} de verdade a cada execução — o
arquivo que fica versionado no repo como exemplo (e que o dashboard/README
apontam) ficava sendo pisado toda vez que alguém rodava `pytest` localmente.

A fixture de amostra (30 itens) é pequena demais pra fechar a cota nova de
20 por tópico (política/macroeconomia/manchete × 4·4·4·8 = 60 no total) —
isso é esperado, o modo --demo só prova que o pipeline roda ponta a ponta
sem rede, não que ele atinge escala de produção. Os testes checam a
*estrutura* do resultado (todos os tópicos e leans presentes, com o target
certo), não uma contagem exata de itens.
"""

from src.curate import QUOTA, TOPICS
from src.pipeline import run


def test_demo_cycle_shape(tmp_path):
    envelope = run(demo=True, data_dir=tmp_path)

    assert envelope["total_items"] > 0
    assert envelope["window_hours"] == 12
    assert set(envelope["editorial_balance"]) == set(QUOTA)
    assert (tmp_path / "latest.json").exists()


def test_topics_have_full_quota_targets(tmp_path):
    envelope = run(demo=True, data_dir=tmp_path)

    assert set(envelope["topics"]) == set(TOPICS)
    for topic in TOPICS:
        topic_data = envelope["topics"][topic]
        assert set(topic_data["quota_status"]) == set(QUOTA)
        for lean, target in QUOTA.items():
            status = topic_data["quota_status"][lean]
            assert status["target"] == target
            # a amostra é pequena, então "filled" pode ficar abaixo do
            # target -- o que não pode acontecer é passar dele.
            assert 0 <= status["filled"] <= target
            assert topic_data["editorial_balance"][lean] == status["filled"]

    # total_items bate com a soma do que cada tópico realmente preencheu
    expected_total = sum(
        status["filled"]
        for topic_data in envelope["topics"].values()
        for status in topic_data["quota_status"].values()
    )
    assert envelope["total_items"] == expected_total


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
        assert item["category"] in set(TOPICS)
