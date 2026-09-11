"""
github_sync.py — Grava data/cycles/latest.{json,csv} de volta no repositório
GitHub via a API de Contents, chamado pelo endpoint /run-cycle (web/app.py).

Existe porque o Render free tier não tem disco persistente entre reinícios
(o serviço "dorme" depois de 15min sem uso e acorda do zero): sem isso, o
ciclo rodaria mas o resultado sumiria antes do Power BI conseguir ler.
"""

from __future__ import annotations

import base64
import logging

import requests

logger = logging.getLogger("telexbr.web.github_sync")

API_ROOT = "https://api.github.com"
HTTP_TIMEOUT = 15


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_sha(repo: str, path: str, branch: str, token: str) -> str | None:
    """Sha do arquivo atual, se existir — a API de Contents exige isso pra
    atualizar (e não pra criar) um arquivo."""
    url = f"{API_ROOT}/repos/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(token), params={"ref": branch}, timeout=HTTP_TIMEOUT)
    if resp.status_code == 200:
        return resp.json().get("sha")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return None


def push_file(repo: str, path: str, content: bytes, token: str, message: str, branch: str = "main") -> dict:
    """Cria ou atualiza um arquivo no repo. Retorna {'ok': bool, 'detail': str}
    em vez de deixar a exceção subir — uma falha de sync não deve derrubar
    a resposta HTTP inteira do /run-cycle."""
    try:
        sha = _get_sha(repo, path, branch, token)
        url = f"{API_ROOT}/repos/{repo}/contents/{path}"
        body = {
            "message": message,
            "content": base64.b64encode(content).decode("ascii"),
            "branch": branch,
        }
        if sha:
            body["sha"] = sha
        resp = requests.put(url, headers=_headers(token), json=body, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return {"ok": True, "detail": f"{path} atualizado (commit {resp.json()['commit']['sha'][:7]})"}
    except Exception as exc:  # noqa: BLE001
        logger.warning("falha ao sincronizar %s com o GitHub: %s", path, exc)
        return {"ok": False, "detail": str(exc)}
