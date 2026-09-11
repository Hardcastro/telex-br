"""
curate.py — Camada de curadoria (etapa 04 do fluxo operacional).

Seleciona até 20 itens respeitando a cota de equilíbrio editorial
(4 direita, 4 esquerda, 4 centro, 8 técnica/neutra) e marca os
destaques de impacto (top view / top réplica) dentro do conjunto
selecionado.

Se um bucket não tiver itens suficientes — o caso normal para
direita/esquerda/centro até o time preencher config/sources.json —
o ciclo sai com menos de 20 itens e a lacuna fica registrada em
`quota_status`, em vez de o script quebrar ou inventar itens.
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


@dataclass
class CurationResult:
    items: list[ScoredItem]
    quota_status: dict[str, dict[str, int]]  # lean -> {target, filled}
    top_view_id: str | None
    top_reply_id: str | None


def item_id(scored: ScoredItem) -> str:
    """Chave estável para um item — usada como id do ciclo."""
    return f"{scored.item.source_id}:{hash(scored.item.url) & 0xFFFFFF:06x}"


def curate(scored_items: list[ScoredItem]) -> CurationResult:
    by_lean: dict[str, list[ScoredItem]] = {lean: [] for lean in QUOTA}
    for s in scored_items:
        by_lean.setdefault(s.item.source_lean, []).append(s)

    selected: list[ScoredItem] = []
    quota_status: dict[str, dict[str, int]] = {}

    for lean, target in QUOTA.items():
        pool = sorted(by_lean.get(lean, []), key=lambda s: s.view_score, reverse=True)
        chosen = pool[:target]
        selected.extend(chosen)
        quota_status[lean] = {"target": target, "filled": len(chosen)}

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
