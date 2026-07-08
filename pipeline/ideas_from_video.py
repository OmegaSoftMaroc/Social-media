#!/usr/bin/env python3
"""Extrait des idées de publication à partir de la TRANSCRIPTION d'une vidéo YouTube.

Flux : URL → transcript (Webshare) → item d'opportunité → editorial-curator → idées.
Option `--push` : dépose les idées sur la Sheet 01_Idees + notifie Telegram (flux habituel).

Usage : python -m pipeline.ideas_from_video <url|video_id> [--push]
Publication des posts : toujours séparée et sur validation explicite (inchangé).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

from pipeline.transcript import fetch_transcript

WORKSPACE = "/opt/hermes/data/profiles/social-media/workspace/editorial"
# Le curator reçoit l'item dans le prompt ; on borne le transcript pour rester raisonnable.
MAX_TRANSCRIPT_CHARS = 6000


def _oembed(video_id: str) -> tuple[str, str]:
    """Retourne (titre, chaine) via l'API oembed publique (non bloquée par IP)."""
    import requests
    try:
        r = requests.get("https://www.youtube.com/oembed",
                         params={"url": f"https://youtu.be/{video_id}", "format": "json"},
                         timeout=15)
        r.raise_for_status()
        d = r.json()
        return d.get("title", ""), d.get("author_name", "")
    except requests.RequestException:
        return "", ""


def build_item(url_or_id: str, max_chars: int = MAX_TRANSCRIPT_CHARS) -> dict:
    """Construit un item d'opportunité grounded sur le transcript de la vidéo."""
    tr = fetch_transcript(url_or_id)
    titre, chaine = _oembed(tr["video_id"])
    text = tr["text"]
    return {
        "source": "youtube",
        "video_id": tr["video_id"],
        "chaine": chaine,
        "titre": titre or tr["video_id"],
        "url": f"https://youtu.be/{tr['video_id']}",
        "langue": tr["language"],
        "resume_fr": "",  # grounding assuré par le champ transcript ci-dessous
        "transcript": text[:max_chars],
        "transcript_tronque": len(text) > max_chars,
        "detecte_le": datetime.now().isoformat(timespec="seconds"),
    }


def run(url_or_id: str, push: bool = False) -> dict:
    """Récupère le transcript, appelle le curator, retourne les propositions.

    Si `push` : dépose sur la Sheet + notifie Telegram. Retourne le dict du curator.
    """
    from pipeline.orchestrator import (call_curator, push_to_sheet,
                                       render_proposal_message, send_telegram)
    item = build_item(url_or_id)
    proposals = call_curator(WORKSPACE, [item])
    ideas = proposals.get("idees", [])
    if push and ideas:
        date = proposals.get("date") or datetime.now().strftime("%Y-%m-%d")
        proposals["_lignes_sheet"] = push_to_sheet(ideas, date)
        send_telegram(render_proposal_message(proposals))
    return proposals


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage : python -m pipeline.ideas_from_video <url|video_id> [--push]")
    from dotenv import load_dotenv
    load_dotenv("/opt/hermes/data/.env")
    load_dotenv("/opt/hermes/data/profiles/social-media/config/.env")
    push_flag = "--push" in sys.argv[2:]
    result = run(sys.argv[1], push=push_flag)
    print(json.dumps(result, ensure_ascii=False, indent=2))
