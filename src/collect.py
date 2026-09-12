"""
collect.py — Camada de coleta (etapa 01 do fluxo operacional).

Lê RSS das fontes ativas em config/sources.json e busca indicadores
macroeconômicos oficiais (BCB, IBGE). Cada fonte falha isoladamente —
um feed fora do ar não derruba o ciclo inteiro.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import feedparser
import requests

logger = logging.getLogger("telexbr.collect")

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
HTTP_TIMEOUT = 10  # segundos
USER_AGENT = "TelexBR/1.0 (+monitoramento de noticias BR; contato: configure em .env)"

# Códigos de série do SGS (Sistema Gerenciador de Séries Temporais) do Banco
# Central — conferir em https://www3.bcb.gov.br/sgspub se algum parar de bater.
BCB_SERIES = {
    "selic_meta": 432,   # Meta Selic definida pelo Copom (% a.a.)
    "ipca_mensal": 433,  # IPCA - variação mensal (%)
    "cambio_usd": 1,     # Taxa de câmbio livre - dólar americano (venda) - diário
}


@dataclass
class RawItem:
    """Um item de notícia bruto, antes de classificação/pontuação."""

    source_id: str
    source_name: str
    headline: str
    summary: str
    url: str
    published_at: datetime
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def load_sources(config_dir: Path = CONFIG_DIR) -> dict:
    import json

    with open(config_dir / "sources.json", encoding="utf-8") as f:
        return json.load(f)


def _active_feed_sources(sources_cfg: dict) -> list[dict]:
    """Achata todos os buckets (tecnica_neutra, direita, esquerda, centro,
    manchete_pool) num único conjunto de fontes com status 'active' e RSS
    configurado."""
    buckets = ["tecnica_neutra", "direita", "esquerda", "centro", "manchete_pool"]
    out = []
    for bucket in buckets:
        for src in sources_cfg.get(bucket, []):
            if src.get("status") == "active" and src.get("rss"):
                entry = dict(src)
                entry["_bucket"] = bucket
                out.append(entry)
    return out


def fetch_rss(source: dict, window_hours: int = 12) -> list[RawItem]:
    """Busca um feed RSS e retorna só os itens publicados dentro da janela."""
    items: list[RawItem] = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    try:
        parsed = feedparser.parse(source["rss"], agent=USER_AGENT)
        if parsed.bozo and not parsed.entries:
            logger.warning("feed com erro e sem entradas: %s (%s)", source["name"], parsed.bozo_exception)
            return items

        for entry in parsed.entries:
            published = _entry_datetime(entry)
            if published is None or published < cutoff:
                continue
            items.append(
                RawItem(
                    source_id=source["id"],
                    source_name=source["name"],
                    headline=entry.get("title", "").strip(),
                    summary=entry.get("summary", entry.get("description", "")).strip(),
                    url=entry.get("link", ""),
                    published_at=published,
                    raw={"bucket": source.get("_bucket")},
                )
            )
    except Exception as exc:  # noqa: BLE001 — coleta não pode derrubar o ciclo
        logger.warning("falha ao coletar %s: %s", source.get("name", "?"), exc)

    return items


def _entry_datetime(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def collect_all(sources_cfg: dict, window_hours: int = 12, max_workers: int = 10) -> list[RawItem]:
    """Coleta todas as fontes ativas em paralelo (I/O-bound — cada feed é
    uma requisição HTTP independente). Sequencial era razoável com ~13
    fontes (~20-25s); com 23 fontes ativas passou de 39s no ciclo real,
    perto do limite de timeout de cron externos (cron-job.org) — por
    isso o pool de threads em vez de um loop simples."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_items: list[RawItem] = []
    sources = _active_feed_sources(sources_cfg)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_source = {pool.submit(fetch_rss, s, window_hours): s for s in sources}
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                items = future.result()
            except Exception as exc:  # noqa: BLE001 — uma fonte não pode derrubar o ciclo
                logger.warning("falha ao coletar %s: %s", source["name"], exc)
                items = []
            logger.info("coletado: %-28s %d itens", source["name"], len(items))
            all_items.extend(items)

    pending = [
        s["id"]
        for bucket in ("direita", "esquerda", "centro")
        for s in sources_cfg.get(bucket, [])
        if s.get("status") == "pending_review"
    ]
    if pending:
        logger.warning(
            "%d slot(s) de fonte aguardando classificação em config/sources.json "
            "(direita/esquerda/centro) — a cota 4·4·4·8 não fecha até isso ser preenchido: %s",
            len(pending),
            ", ".join(pending),
        )
    return all_items


def fetch_macro_snapshot() -> dict[str, float | None]:
    """Busca os indicadores macro mais recentes no BCB. Cada série falha
    isoladamente; retorna None para o que não conseguir buscar."""
    snapshot: dict[str, float | None] = {}
    for label, code in BCB_SERIES.items():
        snapshot[label] = _fetch_bcb_series_latest(code)
    return snapshot


def _fetch_bcb_series_latest(series_code: int) -> float | None:
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados/ultimos/1?formato=json"
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[-1]["valor"].replace(",", "."))
    except Exception as exc:  # noqa: BLE001
        logger.warning("falha ao buscar série BCB %s: %s", series_code, exc)
    return None


def fetch_ibge_indicator(table_code: str, variable_code: str) -> float | None:
    """Placeholder honesto: a API SIDRA do IBGE exige código de tabela e
    variável exatos por indicador (PIB, desemprego, etc.), e não vamos
    inventar esses códigos aqui sem confirmar contra
    https://sidra.ibge.gov.br/ — preencha table_code/variable_code no
    .env (IBGE_PIB_TABLE, IBGE_DESEMPREGO_TABLE) depois de checar a
    tabela certa e esta função passa a funcionar como as do BCB."""
    if not table_code or not variable_code:
        logger.info("indicador IBGE não configurado (table_code/variable_code vazios) — pulando")
        return None
    url = f"https://apisidra.ibge.gov.br/values/t/{table_code}/n1/all/v/{variable_code}/p/last%201"
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        rows = resp.json()
        if len(rows) > 1:
            return float(rows[-1]["V"].replace(",", "."))
    except Exception as exc:  # noqa: BLE001
        logger.warning("falha ao buscar indicador IBGE (tabela %s): %s", table_code, exc)
    return None
