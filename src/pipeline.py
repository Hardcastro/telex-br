"""
pipeline.py — Orquestrador (junta as 5 etapas do fluxo operacional).

Uso:
    python -m src.pipeline --demo        # roda com dados de amostra, sem rede
    python -m src.pipeline               # roda de verdade (RSS + BCB)
    python -m src.pipeline --window 24   # janela de coleta diferente de 12h

O modo --demo existe para o time testar/ajustar classificação, pontuação
e curadoria sem esperar preencher config/sources.json nem depender da
rede — é o mesmo pipeline, só troca a fonte dos itens brutos.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from .classify import classify_all, load_keywords
from .collect import RawItem, collect_all, fetch_macro_snapshot, load_sources
from .curate import curate
from .export import build_envelope, write_cycle
from .score import score_all

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = PROJECT_ROOT / "data" / "sample" / "sample_items.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("telexbr.pipeline")


def _load_sample_items() -> list[RawItem]:
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    items = []
    for entry in raw:
        items.append(
            RawItem(
                source_id=entry["source_id"],
                source_name=entry["source_name"],
                headline=entry["headline"],
                summary=entry["summary"],
                url=entry["url"],
                published_at=datetime.fromisoformat(entry["published_at"]),
                raw={"bucket": entry["bucket"]},
            )
        )
    return items


def run(demo: bool = False, window_hours: int = 12) -> dict:
    if demo:
        logger.info("modo demo: usando data/sample/sample_items.json (nenhuma chamada de rede)")
        raw_items = _load_sample_items()
        macro_snapshot: dict = {
            "selic_meta": 10.75, "ipca_mensal": 0.35, "cambio_usd": 5.31,
            "_fonte": "valores de amostra — modo --demo",
        }
    else:
        sources_cfg = load_sources()
        raw_items = collect_all(sources_cfg, window_hours=window_hours)
        macro_snapshot = fetch_macro_snapshot()

    logger.info("itens brutos coletados: %d", len(raw_items))

    keywords_cfg = load_keywords()
    classified = classify_all(raw_items, keywords_cfg)

    scored = score_all(classified)

    result = curate(scored)
    logger.info(
        "curadoria: %d/20 itens selecionados — %s",
        len(result.items),
        ", ".join(f"{k}:{v['filled']}/{v['target']}" for k, v in result.quota_status.items()),
    )

    envelope = build_envelope(result, window_hours=window_hours, macro_snapshot=macro_snapshot)
    json_path, latest_json, latest_csv = write_cycle(envelope)
    logger.info("ciclo gravado em %s", json_path)
    logger.info("apontar o Power BI para: %s (ou o .json equivalente)", latest_csv)

    return envelope


def main(argv: list[str] | None = None) -> int:
    # console do Windows por padrão não é UTF-8 — sem isso, acentos saem
    # como "?" na tela (o JSON gravado em disco já é UTF-8 de qualquer jeito).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Telex BR — pipeline de curadoria de notícias")
    parser.add_argument("--demo", action="store_true", help="usa dados de amostra, sem chamadas de rede")
    parser.add_argument("--window", type=int, default=12, help="janela de coleta em horas (padrão: 12)")
    args = parser.parse_args(argv)

    envelope = run(demo=args.demo, window_hours=args.window)

    print()
    print(f"  Ciclo {envelope['cycle_id']}")
    print(f"  {envelope['total_items']} itens · balanço {envelope['editorial_balance']}")
    if envelope["highlights"]["top_view_id"]:
        top_view = next(i for i in envelope["items"] if i["id"] == envelope["highlights"]["top_view_id"])
        print(f"  Top view:   {top_view['headline']}  ({top_view['source']})")
    if envelope["highlights"]["top_reply_id"]:
        top_reply = next(i for i in envelope["items"] if i["id"] == envelope["highlights"]["top_reply_id"])
        print(f"  Top réplica: {top_reply['headline']}  ({top_reply['source']})")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
