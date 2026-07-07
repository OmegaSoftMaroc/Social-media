#!/usr/bin/env python3
"""Connecteur Meta — publication Facebook (Page) et Instagram (Reels) via Graph API.

Prérequis : app Meta (mode dev suffit pour ses propres comptes), Page Facebook,
compte Instagram professionnel LIÉ à la Page.
Clés config/.env : META_PAGE_ID, META_PAGE_TOKEN (long-lived), META_IG_USER_ID.
NB : endpoints Graph vérifiés contre la doc au premier test réel (l'API évolue).
Publication UNIQUEMENT après validation explicite d'Abdelilah.
"""
from __future__ import annotations

import time

CONFIG_ENV = "/opt/hermes/data/profiles/social-media/config/.env"
GRAPH = "https://graph.facebook.com/v21.0"
GRAPH_VIDEO = "https://graph-video.facebook.com/v21.0"


def _env() -> dict:
    from dotenv import dotenv_values
    return dotenv_values(CONFIG_ENV)


def publish_facebook_video(video_path: str, description: str) -> dict:
    """Publie une vidéo sur la Page Facebook (upload binaire direct)."""
    import requests
    c = _env()
    page, token = c.get("META_PAGE_ID"), c.get("META_PAGE_TOKEN")
    if not page or not token:
        raise RuntimeError("META_PAGE_ID / META_PAGE_TOKEN manquant")
    with open(video_path, "rb") as fh:
        r = requests.post(f"{GRAPH_VIDEO}/{page}/videos", timeout=600,
                          data={"description": description, "access_token": token},
                          files={"source": ("video.mp4", fh, "video/mp4")})
    r.raise_for_status()
    return {"status": r.status_code, "video_id": r.json().get("id")}


def publish_facebook_photo(image_path: str, message: str) -> dict:
    """Publie une image + texte sur la Page Facebook."""
    import requests
    c = _env()
    page, token = c.get("META_PAGE_ID"), c.get("META_PAGE_TOKEN")
    if not page or not token:
        raise RuntimeError("META_PAGE_ID / META_PAGE_TOKEN manquant")
    with open(image_path, "rb") as fh:
        r = requests.post(f"{GRAPH}/{page}/photos", timeout=120,
                          data={"message": message, "access_token": token},
                          files={"source": ("visual.png", fh, "image/png")})
    r.raise_for_status()
    return {"status": r.status_code, "post_id": r.json().get("post_id") or r.json().get("id")}


def publish_instagram_reel(video_url: str, caption: str,
                           poll_s: int = 10, timeout_s: int = 600) -> dict:
    """Publie un Reel Instagram depuis une URL vidéo PUBLIQUE.

    L'API IG exige une URL accessible publiquement (pas d'upload binaire direct
    en mode simple). Astuce pipeline : passer l'URL du mp4 HeyGen (pré-signée)
    ou tout autre lien direct. Container → polling statut → publish.
    """
    import requests
    c = _env()
    ig, token = c.get("META_IG_USER_ID"), c.get("META_PAGE_TOKEN")
    if not ig or not token:
        raise RuntimeError("META_IG_USER_ID / META_PAGE_TOKEN manquant")
    r = requests.post(f"{GRAPH}/{ig}/media", timeout=60, data={
        "media_type": "REELS", "video_url": video_url,
        "caption": caption, "access_token": token})
    r.raise_for_status()
    container = r.json()["id"]
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        s = requests.get(f"{GRAPH}/{container}", timeout=30,
                         params={"fields": "status_code", "access_token": token})
        s.raise_for_status()
        code = s.json().get("status_code")
        if code == "FINISHED":
            p = requests.post(f"{GRAPH}/{ig}/media_publish", timeout=60,
                              data={"creation_id": container, "access_token": token})
            p.raise_for_status()
            return {"status": p.status_code, "media_id": p.json().get("id")}
        if code == "ERROR":
            raise RuntimeError(f"Instagram container en erreur (id={container})")
        time.sleep(poll_s)
    raise RuntimeError(f"Instagram : timeout après {timeout_s}s (container={container})")
