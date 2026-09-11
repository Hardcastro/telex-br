"""
classify.py — Camada de classificação (etapa 02 do fluxo operacional).

Duas classificações independentes por item:
  1. source_lean  — vem do bucket da fonte em config/sources.json
                     (direita/esquerda/centro/tecnica_neutra). Fontes de
                     manchete geral (G1, UOL, CNN Brasil...) não têm linha
                     editorial mapeada neste projeto — de propósito, ver
                     blueprint seção b — e entram como 'tecnica_neutra'
                     para fins de cota, já que não fazemos essa chamada
                     política sem validação humana.
  2. category     — política / macroeconomia / manchete, por
                     palavra-chave sobre título + resumo (config/keywords.json).
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .collect import RawItem

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

BUCKET_TO_LEAN = {
    "tecnica_neutra": "tecnica_neutra",
    "direita": "direita",
    "esquerda": "esquerda",
    "centro": "centro",
    "manchete_pool": "tecnica_neutra",
}


@dataclass
class ClassifiedItem:
    source_id: str
    source_name: str
    source_lean: str
    headline: str
    summary: str
    url: str
    published_at: str  # ISO 8601
    category: str
    tags: list[str]
    raw: RawItem


def load_keywords(config_dir: Path = CONFIG_DIR) -> dict:
    with open(config_dir / "keywords.json", encoding="utf-8") as f:
        return json.load(f)


def _normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def classify_category(text: str, keywords_cfg: dict) -> tuple[str, list[str]]:
    """Retorna (categoria, tags_encontradas). Checa política antes de
    macroeconomia; o que não bate com nenhuma vira 'manchete'."""
    norm = _normalize(text)
    for category in ("politica", "macroeconomia"):
        matched = [kw for kw in keywords_cfg.get(category, []) if kw in norm]
        if matched:
            return category, matched
    return "manchete", []


def _lean_for_bucket(bucket: str | None) -> str:
    return BUCKET_TO_LEAN.get(bucket or "", "tecnica_neutra")


def classify_item(item: RawItem, keywords_cfg: dict) -> ClassifiedItem:
    text = f"{item.headline} {item.summary}"
    category, tags = classify_category(text, keywords_cfg)
    bucket = item.raw.get("bucket") if item.raw else None

    return ClassifiedItem(
        source_id=item.source_id,
        source_name=item.source_name,
        source_lean=_lean_for_bucket(bucket),
        headline=item.headline,
        summary=item.summary,
        url=item.url,
        published_at=item.published_at.isoformat(),
        category=category,
        tags=tags,
        raw=item,
    )


def classify_all(items: list[RawItem], keywords_cfg: dict | None = None) -> list[ClassifiedItem]:
    keywords_cfg = keywords_cfg or load_keywords()
    return [classify_item(item, keywords_cfg) for item in items]
