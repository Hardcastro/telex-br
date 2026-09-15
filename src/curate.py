"""
curate.py — Camada de curadoria (etapa 04 do fluxo operacional).

Seleciona até 20 itens **por tópico de conteúdo** (política, macroeconomia,
manchete — 60 no total), respeitando dentro de cada tópico a mesma cota de
equilíbrio editorial (4 direita, 4 esquerda, 4 centro, 8 técnica/neutra) que
o projeto usava para o ciclo inteiro antes. Pedido do usuário: "20 em cada
tópico" — a cota antiga já somava exatamente 20, então vira "uma cota por
tópico" em vez de "uma cota pro ciclo".

Se um bucket não tiver itens suficientes dentro de um tópico — normal para
direita/esquerda/centro em tópicos com pouca cobertura daquela fonte — esse
tópico sai com menos itens e a lacuna fica registrada em `quota_status`
(por tópico, por lean), em vez de o script quebrar ou inventar itens.
"""

from __future__ import annotations

from dataclasses import dataclass

from .score import ScoredItem

QUOTA = {
    "direita": 4,
    "esquerda": 4,
    "centro": 4,
    "tecnica_neutra": 8,
}

TOPICS = ["politica", "macroeconomia", "manchete"]

# Evita uma única fonte encher a cota sozinha com conteúdo repetitivo/
# templated (ex.: uma série "Candidatos a senador por <Estado>" — mesma
# fonte, 8 itens quase idênticos só trocando o nome do estado, que não
# ficam no mesmo cluster de cobertura por não terem título parecido o
# suficiente). Só é ultrapassado se não sobrar fonte diferente pra
# completar a cota — preferimos isso a deixar o tópico incompleto.
MAX_PER_SOURCE_PER_BUCKET = 3


@dataclass
class CurationResult:
    items: list[ScoredItem]
    quota_status: dict[str, dict[str, dict[str, int]]]  # topico -> lean -> {target, filled}
    top_view_id: str | None
    top_reply_id: str | None


def item_id(scored: ScoredItem) -> str:
    """Chave estável para um item — usada como id do ciclo."""
    return f"{scored.item.source_id}:{hash(scored.item.url) & 0xFFFFFF:06x}"


def _select_bucket(pool: list[ScoredItem], target: int, max_per_source: int) -> list[ScoredItem]:
    """Ordena por view_score e escolhe até `target` itens, respeitando o
    teto por fonte — mas prefere completar a cota a deixar vaga, então
    itens além do teto entram por último se não houver alternativa de
    outra fonte."""
    ranked = sorted(pool, key=lambda s: s.view_score, reverse=True)
    chosen: list[ScoredItem] = []
    per_source: dict[str, int] = {}
    overflow: list[ScoredItem] = []

    for s in ranked:
        if len(chosen) >= target:
            break
        src = s.item.source_id
        if per_source.get(src, 0) < max_per_source:
            chosen.append(s)
            per_source[src] = per_source.get(src, 0) + 1
        else:
            overflow.append(s)

    for s in overflow:
        if len(chosen) >= target:
            break
        chosen.append(s)

    return chosen


def _curate_topic(scored_items: list[ScoredItem]) -> tuple[list[ScoredItem], dict[str, dict[str, int]]]:
    """Aplica a cota 4·4·4·8 dentro de um único tópico já filtrado."""
    by_lean: dict[str, list[ScoredItem]] = {lean: [] for lean in QUOTA}
    for s in scored_items:
        by_lean.setdefault(s.item.source_lean, []).append(s)

    selected: list[ScoredItem] = []
    quota_status: dict[str, dict[str, int]] = {}
    for lean, target in QUOTA.items():
        chosen = _select_bucket(by_lean.get(lean, []), target, MAX_PER_SOURCE_PER_BUCKET)
        selected.extend(chosen)
        quota_status[lean] = {"target": target, "filled": len(chosen)}

    return selected, quota_status


def curate(scored_items: list[ScoredItem]) -> CurationResult:
    by_topic: dict[str, list[ScoredItem]] = {topic: [] for topic in TOPICS}
    for s in scored_items:
        by_topic.setdefault(s.item.category, []).append(s)

    selected: list[ScoredItem] = []
    quota_status: dict[str, dict[str, dict[str, int]]] = {}

    for topic in TOPICS:
        topic_items, topic_quota = _curate_topic(by_topic.get(topic, []))
        selected.extend(topic_items)
        quota_status[topic] = topic_quota

    if not selected:
        return CurationResult(items=[], quota_status=quota_status, top_view_id=None, top_reply_id=None)

    top_view = max(selected, key=lambda s: s.view_score)
    top_reply = max(selected, key=lambda s: s.engagement_proxy_index)

    # ordem de leitura final: mais recente primeiro
    selected.sort(key=lambda s: s.item.published_at, reverse=True)

    return CurationResult(
        items=selected,
        quota_status=quota_status,
        top_view_id=item_id(top_view),
        top_reply_id=item_id(top_reply),
    )
