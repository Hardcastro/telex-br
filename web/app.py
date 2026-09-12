"""
web/app.py — Gatilho HTTP do ciclo de 12h, para rodar em Render (free).

Existe porque o GitHub Actions da conta ficou bloqueado por um problema de
faturamento — isso troca só o "relógio" (quem chama o pipeline) por um
cron externo gratuito (cron-job.org) batendo num endpoint aqui. O pipeline
em si (src/) não muda uma linha.

Rotas:
  GET  /            healthcheck (é o que o Render usa pra saber se subiu)
  POST /run-cycle    roda o pipeline e sincroniza o resultado com o GitHub
                      (protegido por RUN_TOKEN — ver .env.example)

Rodar local:
    pip install -r requirements.txt -r requirements-web.txt
    RUN_TOKEN=teste FLASK_DEBUG=1 python -m web.app
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from src.pipeline import run as run_pipeline
from web.github_sync import push_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s %(message)s")
logger = logging.getLogger("telexbr.web")

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "cycles"

RUN_TOKEN = os.environ.get("RUN_TOKEN")  # obrigatório em produção — ver checagem abaixo
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")  # ex.: "Hardcastro/telex-br"

# Evita dois ciclos rodando ao mesmo tempo (ex.: um disparo manual caindo
# bem no instante do cron agendado, como aconteceu de verdade em
# 2026-09-12 00:00 BRT) — sem isso, as duas execuções competem pelo mesmo
# processo e podem gravar data/cycles/latest.json em cima uma da outra.
_run_lock = threading.Lock()


@app.get("/")
def health():
    return "Telex BR — gatilho web ativo. Use POST /run-cycle (com token) para disparar um ciclo. Painel público em /dashboard.", 200


@app.get("/dashboard")
def dashboard():
    """Página pública do painel — mesmo HTML publicado como Claude Artifact,
    servido aqui pra quem não tem/não quer usar conta na claude.ai. Lê o
    JSON do ciclo direto do GitHub no lado do cliente, não depende deste
    servidor estar acordado no momento em que alguém abre a página."""
    return send_from_directory(PROJECT_ROOT, "dashboard-live.html")


@app.route("/run-cycle", methods=["GET", "POST"])
def run_cycle():
    # autenticação simples por token compartilhado — sem isso, qualquer um
    # que descubra a URL pública consome suas horas do Render e a cota da
    # API do GitHub disparando ciclos à vontade.
    token = request.args.get("token") or request.headers.get("X-Run-Token")
    if not RUN_TOKEN:
        return jsonify(ok=False, error="RUN_TOKEN não configurado no servidor — defina a env var antes de expor este endpoint."), 500
    if token != RUN_TOKEN:
        return jsonify(ok=False, error="token inválido ou ausente"), 401

    if not _run_lock.acquire(blocking=False):
        return jsonify(ok=False, error="já tem um ciclo rodando agora — tenta de novo em alguns segundos"), 429

    try:
        demo = request.args.get("demo") == "1"
        window_hours = int(request.args.get("window", 12))
        try:
            envelope = run_pipeline(demo=demo, window_hours=window_hours)
        except Exception as exc:  # noqa: BLE001 — nunca deixar o processo do Render cair
            logger.exception("pipeline falhou")
            return jsonify(ok=False, error=f"pipeline falhou: {exc}"), 500
    finally:
        _run_lock.release()

    sync_results = {}
    if GITHUB_TOKEN and GITHUB_REPO:
        for fname, message in [
            ("latest.json", f"ciclo: {envelope['cycle_id']}"),
            ("latest.csv", f"ciclo: {envelope['cycle_id']} (csv)"),
        ]:
            fpath = DATA_DIR / fname
            if fpath.exists():
                content = fpath.read_bytes()
                sync_results[fname] = push_file(
                    repo=GITHUB_REPO,
                    path=f"data/cycles/{fname}",
                    content=content,
                    token=GITHUB_TOKEN,
                    message=message,
                )
    else:
        sync_results["_skipped"] = "GITHUB_TOKEN/GITHUB_REPO não configurados — resultado só ficou no disco efêmero do Render."

    return jsonify(
        ok=True,
        cycle_id=envelope["cycle_id"],
        total_items=envelope["total_items"],
        editorial_balance=envelope["editorial_balance"],
        github_sync=sync_results,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, threaded=True)
