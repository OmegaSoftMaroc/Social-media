#!/usr/bin/env python3
"""Connecteur YouTube — upload de Shorts via YouTube Data API v3 (OAuth).

⚠️ Le compte de service Google ne fonctionne PAS pour YouTube : OAuth utilisateur
obligatoire (comme LinkedIn). Flux : URL d'autorisation → code → refresh_token
(stocké dans config/.env, durable si l'app OAuth est en mode « production »).

Clés config/.env : YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
Publication UNIQUEMENT après validation explicite d'Abdelilah.
"""
from __future__ import annotations

import json

CONFIG_ENV = "/opt/hermes/data/profiles/social-media/config/.env"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
REDIRECT_URI = "https://localhost/callback"


def _env() -> dict:
    from dotenv import dotenv_values
    return dotenv_values(CONFIG_ENV)


def build_auth_url() -> str:
    """URL d'autorisation à ouvrir par Abdelilah (access_type=offline → refresh_token)."""
    from urllib.parse import urlencode
    c = _env()
    return AUTH_URL + "?" + urlencode({
        "client_id": c["YT_CLIENT_ID"],
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    })


def exchange_code(code: str) -> dict:
    """Échange le code contre access_token + refresh_token."""
    import requests
    c = _env()
    r = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": c["YT_CLIENT_ID"],
        "client_secret": c["YT_CLIENT_SECRET"],
        "redirect_uri": REDIRECT_URI,
    }, timeout=30)
    r.raise_for_status()
    return r.json()


def _access_token() -> str:
    """Access token frais depuis le refresh_token stocké."""
    import requests
    c = _env()
    r = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": c["YT_REFRESH_TOKEN"],
        "client_id": c["YT_CLIENT_ID"],
        "client_secret": c["YT_CLIENT_SECRET"],
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def publish_short(video_path: str, title: str, description: str,
                  tags: list[str] | None = None) -> dict:
    """Upload un Short (resumable). APRÈS validation explicite uniquement.

    Un 9:16 < 3 min est automatiquement traité en Short par YouTube.
    """
    import requests
    token = _access_token()
    meta = {
        "snippet": {"title": title[:100], "description": description,
                    "tags": tags or [], "categoryId": "28"},  # 28 = Science & Tech
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    with open(video_path, "rb") as fh:
        data = fh.read()
    # 1) initier la session resumable
    init = requests.post(
        UPLOAD_URL + "?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Length": str(len(data)),
                 "X-Upload-Content-Type": "video/mp4"},
        data=json.dumps(meta), timeout=60)
    init.raise_for_status()
    session_url = init.headers["Location"]
    # 2) envoyer le binaire
    up = requests.put(session_url, data=data, timeout=600,
                      headers={"Content-Type": "video/mp4"})
    up.raise_for_status()
    vid = up.json().get("id")
    return {"status": up.status_code, "video_id": vid,
            "url": f"https://youtube.com/shorts/{vid}"}
