#!/usr/bin/env python3
"""YouTube Monitor — détecte les nouvelles vidéos suivies et écrit des
opportunités dans briefs/incoming/. Résumé via OpenRouter Gemini (économique).

Adapté de la version V1 (profil) : le routage personnel/OmegaSoft est retiré
(remplacé par le classement par pilier en aval, dans editorial-curator).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
import requests

OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def is_recent(published_str: str, hours: int = 25) -> bool:
    """True si la vidéo a été publiée dans les `hours` dernières heures."""
    if not published_str:
        return False
    try:
        pub_dt = parsedate_to_datetime(published_str)
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return pub_dt > cutoff
    except (TypeError, ValueError):
        return True  # parsing impossible → inclure par sécurité


def select_new_videos(videos: list[dict], seen: dict, hours: int = 25) -> list[dict]:
    """Garde les vidéos non vues et récentes."""
    result = []
    for v in videos:
        vid = v.get("id")
        if not vid or vid in seen:
            continue
        if not is_recent(v.get("publie_le", ""), hours=hours):
            continue
        result.append(v)
    return result


def make_incoming_item(video: dict, chaine: str, resume_fr: str, detecte_le: str) -> dict:
    """Façonne un item d'opportunité pour briefs/incoming/."""
    return {
        "source": "youtube",
        "video_id": video["id"],
        "chaine": chaine,
        "titre": video["titre"],
        "url": video["url"],
        "publie_le": video["publie_le"],
        "resume_fr": resume_fr,
        "detecte_le": detecte_le,
    }


def write_incoming_item(item: dict, incoming_dir: Path) -> Path:
    """Écrit l'item dans incoming/<video_id>.json et retourne le chemin."""
    incoming_dir = Path(incoming_dir)
    incoming_dir.mkdir(parents=True, exist_ok=True)
    path = incoming_dir / f"{item['video_id']}.json"
    path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def fetch_rss(channel_id: str) -> list[dict]:
    """Récupère les vidéos via le flux RSS YouTube (appel réseau, non testé)."""
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    videos = []
    for entry in feed.entries:
        videos.append({
            "id": entry.get("yt_videoid", entry.get("id", "")),
            "titre": entry.get("title", ""),
            "url": entry.get("link", ""),
            "description": entry.get("summary", "")[:500],
            "publie_le": entry.get("published", ""),
        })
    return videos


def summarize_with_gemini(chaine: str, titre: str, description: str, api_key: str) -> str:
    """Résumé FR court via OpenRouter Gemini (appel réseau, non testé)."""
    if not api_key:
        return "⚠️ Clé OpenRouter manquante — résumé non généré"
    prompt = (
        "Tu es l'assistant éditorial de M. Abdelilah Kahaji (expert IA, consultant "
        "ERP/Odoo).\n"
        f"Nouvelle vidéo YouTube de {chaine} :\nTitre : {titre}\nDescription : {description}\n\n"
        "En 3-4 phrases en français : (1) résume le sujet, (2) indique sa pertinence pour "
        "un expert IA / dirigeant d'ESN, (3) suggère un angle de contenu. Sois concis."
    )
    resp = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": OPENROUTER_MODEL,
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 300, "temperature": 0.3},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
