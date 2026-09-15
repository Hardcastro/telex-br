"""
export.py — Camada de publicação (etapa 05 do fluxo operacional).

Grava o envelope JSON do ciclo (mesmo formato do blueprint, seção d) e
uma versão CSV plana — o CSV é o jeito mais robusto de alimentar o
Power BI free: Get Data > Web > URL bruta do arquivo no GitHub (ver
README, "Ligar ao Power BI").
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .curate import CurationResult, item_id

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cycles"

# Fuso fixo, não ".astimezone()" — o pipeline roda em máquinas com fuso
# variado (local, Render em UTC, GitHub Actions em UTC), e o cycle_id deve
# sempre refletir BRT como o resto do projeto assume (Brasil não observa
# horário de verão desde 2019, então o offset -3 é fixo).
BRT = timezone(timedelta(hours=-3))


def build_envelope(result: CurationResult, window_hours: int = 12, macro_snapshot: dict | None = None) -> dict:
    now = datetime.now(BRT)

    # result.quota_status é aninhado por tópico desde que a cota passou a
    # ser "20 por tópico" (política/macroeconomia/manchete) em vez de "20
    # pro ciclo inteiro" — ver curate.py. editorial_balance no topo do
    # envelope soma os três tópicos por lean, pra quem só quer o balanço
    # agregado (ex.: o donut do painel); topics traz o detalhe por tópico.
    balance: dict[str, int] = {}
    for topic_quota in result.quota_status.values():
        for lean, v in topic_quota.items():
            balance[lean] = balance.get(lean, 0) + v["filled"]

    topics_summary = {
        topic: {
            "editorial_balance": {lean: v["filled"] for lean, v in topic_quota.items()},
            "quota_status": topic_quota,
        }
        for topic, topic_quota in result.quota_status.items()
    }

    items_payload = []
    for s in result.items:
        iid = item_id(s)
        items_payload.append(
            {
                "id": iid,
                "headline": s.item.headline,
                "source": s.item.source_name,
                "source_lean": s.item.source_lean,
                "category": s.item.category,
                "url": s.item.url,
                "published_at": s.item.published_at,
                "coverage_cluster_size": s.coverage_cluster_size,
                "trends_interest_score": s.trends_interest_score,
                "engagement_proxy_index": s.engagement_proxy_index,
                "is_top_view": iid == result.top_view_id,
                "is_top_reply": iid == result.top_reply_id,
                "tags": s.item.tags,
            }
        )

    return {
        "cycle_id": now.isoformat(),
        "generated_at": now.isoformat(),
        "window_hours": window_hours,
        "total_items": len(items_payload),
        "macro_snapshot": macro_snapshot or {},
        "editorial_balance": balance,
        "quota_status": result.quota_status,
        "topics": topics_summary,
        "highlights": {
            "top_view_id": result.top_view_id,
            "top_reply_id": result.top_reply_id,
        },
        "items": items_payload,
    }


def write_cycle(envelope: dict, data_dir: Path = DATA_DIR) -> tuple[Path, Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    json_path = data_dir / f"cycle_{stamp}.json"
    latest_json_path = data_dir / "latest.json"
    latest_csv_path = data_dir / "latest.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(envelope, f, ensure_ascii=False, indent=2)
    with open(latest_json_path, "w", encoding="utf-8") as f:
        json.dump(envelope, f, ensure_ascii=False, indent=2)

    _write_csv(envelope, latest_csv_path)

    return json_path, latest_json_path, latest_csv_path


def _write_csv(envelope: dict, csv_path: Path) -> None:
    fieldnames = [
        "cycle_id", "id", "headline", "source", "source_lean", "category",
        "url", "published_at", "coverage_cluster_size", "trends_interest_score",
        "engagement_proxy_index", "is_top_view", "is_top_reply", "tags",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in envelope["items"]:
            row = {"cycle_id": envelope["cycle_id"], **item}
            row["tags"] = "|".join(item.get("tags", []))
            writer.writerow(row)
