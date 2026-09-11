"""
score.py — Camada de pontuação (etapa 03 do fluxo operacional).

Pageviews e contagens de compartilhamento reais não são públicos por
fonte no Brasil (ver blueprint, seção b) — então compomos dois índices
PROXY a partir de sinais que são abertos:

  view_score  = tamanho do cluster de cobertura (quantas fontes do
                próprio ciclo publicaram algo parecido) + Google Trends
                (opcional, precisa de `pip install pytrends`)
  reply_score = mesmo cluster + menções no Reddit (opcional, precisa de
                credenciais REDDIT_* no .env)

Os pesos abaixo são um ponto de partida documentado, não uma verdade
calibrada — ajuste depois de ver alguns ciclos reais rodando.
"""

from __future__ import annotations

import logging
import os
import unicodedata
from dataclasses import dataclass

from .classify import ClassifiedItem

logger = logging.getLogger("telexbr.score")

STOPWORDS_PT = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "em", "no", "na",
    "nos", "nas", "para", "por", "com", "sem", "sobre", "que", "e", "ou",
    "um", "uma", "uns", "umas", "ao", "aos", "à", "às", "é", "foi", "ser",
    "sua", "seu", "suas", "seus", "diz", "diz que", "apos", "após",
}

TRENDS_WEIGHT = 0.5
REDDIT_WEIGHT = 2.0
TRENDS_CANDIDATE_POOL = 15  # só consulta Trends/Reddit para os N maiores clusters


@dataclass
class ScoredItem:
    item: ClassifiedItem
    coverage_cluster_size: int
    trends_interest_score: float | None
    engagement_proxy_index: float | None  # sinal de "réplica" (reddit + cluster)
    view_score: float


def _significant_tokens(text: str) -> set[str]:
    norm = unicodedata.normalize("NFKD", text.lower())
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    tokens = {t for t in "".join(c if c.isalnum() else " " for c in norm).split() if len(t) > 3}
    return tokens - STOPWORDS_PT


def compute_clusters(items: list[ClassifiedItem], threshold: float = 0.35) -> list[int]:
    """Agrupamento ingênuo por sobreposição de palavras do título
    (Jaccard). O(n²), mas n é pequeno por ciclo (dezenas a ~100 itens),
    então roda em milissegundos. Retorna, na mesma ordem de `items`, o
    tamanho do cluster de cada item — ou seja, quantas fontes (incluindo
    a própria) publicaram algo parecido no ciclo."""
    token_sets = [_significant_tokens(it.headline) for it in items]
    n = len(items)
    cluster_of = list(range(n))  # union-find simples

    def find(x: int) -> int:
        while cluster_of[x] != x:
            cluster_of[x] = cluster_of[cluster_of[x]]
            x = cluster_of[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            cluster_of[ra] = rb

    for i in range(n):
        if not token_sets[i]:
            continue
        for j in range(i + 1, n):
            if not token_sets[j]:
                continue
            inter = token_sets[i] & token_sets[j]
            if not inter:
                continue
            union_size = len(token_sets[i] | token_sets[j])
            jaccard = len(inter) / union_size if union_size else 0
            if jaccard >= threshold:
                union(i, j)

    roots = [find(i) for i in range(n)]
    sizes: dict[int, int] = {}
    for r in roots:
        sizes[r] = sizes.get(r, 0) + 1
    return [sizes[r] for r in roots]


def _fetch_trends_score(query: str) -> float | None:
    try:
        from pytrends.request import TrendReq  # import tardio — dependência opcional
    except ImportError:
        return None
    try:
        pytrends = TrendReq(hl="pt-BR", tz=180)
        pytrends.build_payload([query[:80]], timeframe="now 1-d", geo="BR")
        df = pytrends.interest_over_time()
        if df.empty:
            return None
        return float(df[query[:80]].iloc[-1])
    except Exception as exc:  # noqa: BLE001 — Trends não-oficial, cai fácil
        logger.debug("trends indisponível para %r: %s", query, exc)
        return None


def _fetch_reddit_mentions(query: str) -> int | None:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None
    try:
        import praw  # import tardio — dependência opcional
    except ImportError:
        return None
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=os.getenv("REDDIT_USER_AGENT", "telexbr/1.0"),
        )
        results = list(reddit.subreddit("brasil").search(query[:200], limit=10, time_filter="day"))
        return sum(getattr(r, "num_comments", 0) + getattr(r, "score", 0) for r in results)
    except Exception as exc:  # noqa: BLE001
        logger.debug("reddit indisponível para %r: %s", query, exc)
        return None


def score_all(items: list[ClassifiedItem]) -> list[ScoredItem]:
    cluster_sizes = compute_clusters(items)

    # só gasta chamadas de Trends/Reddit nos N maiores clusters — o resto
    # fica só com o sinal de cluster, que já é gratuito e sempre disponível.
    order = sorted(range(len(items)), key=lambda i: cluster_sizes[i], reverse=True)
    candidate_idx = set(order[:TRENDS_CANDIDATE_POOL])

    scored: list[ScoredItem] = []
    for i, item in enumerate(items):
        cluster = cluster_sizes[i]
        trends = _fetch_trends_score(item.headline) if i in candidate_idx else None
        reddit_signal = _fetch_reddit_mentions(item.headline) if i in candidate_idx else None

        view_score = cluster + (trends or 0) * TRENDS_WEIGHT
        engagement_proxy_index = cluster + (reddit_signal or 0) * REDDIT_WEIGHT

        scored.append(
            ScoredItem(
                item=item,
                coverage_cluster_size=cluster,
                trends_interest_score=trends,
                engagement_proxy_index=round(engagement_proxy_index, 1),
                view_score=round(view_score, 1),
            )
        )
    return scored
