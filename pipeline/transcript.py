#!/usr/bin/env python3
"""Connecteur transcript — récupère la transcription d'une vidéo YouTube.

Contexte : l'IP datacenter du VPS est bloquée par YouTube pour les endpoints de
transcription (`RequestBlocked` / bot-gate). On passe donc par un proxy résidentiel
**Webshare**, solution officiellement recommandée par `youtube-transcript-api`.

Clés config/.env : WEBSHARE_PROXY_USERNAME, WEBSHARE_PROXY_PASSWORD.
Sans ces clés, l'appel se fait en direct (échouera sur un VPS bloqué, OK en local).
"""
from __future__ import annotations

import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

CONFIG_ENV = "/opt/hermes/data/profiles/social-media/config/.env"

# Ordre de préférence des langues (chaînes suivies surtout EN, quelques FR).
DEFAULT_LANGS = ("en", "en-US", "en-GB", "fr", "es", "ar")

# id vidéo = 11 caractères base64-url (lettres, chiffres, - et _)
_ID_RE = re.compile(r"[0-9A-Za-z_-]{11}")


def _env() -> dict:
    from dotenv import dotenv_values
    return dotenv_values(CONFIG_ENV)


def extract_video_id(url_or_id: str) -> str:
    """Extrait l'identifiant vidéo depuis une URL YouTube ou un id brut.

    Gère youtu.be/<id>, watch?v=<id>, /shorts/<id> et l'id nu (11 caractères).

    Args:
        url_or_id: URL YouTube complète ou identifiant vidéo.

    Returns:
        L'identifiant vidéo à 11 caractères.

    Raises:
        ValueError: si aucun identifiant valide n'est trouvé.
    """
    value = (url_or_id or "").strip()
    # id nu
    if _ID_RE.fullmatch(value):
        return value
    # patterns d'URL usuels
    for pattern in (r"youtu\.be/([0-9A-Za-z_-]{11})",
                    r"[?&]v=([0-9A-Za-z_-]{11})",
                    r"/shorts/([0-9A-Za-z_-]{11})",
                    r"/embed/([0-9A-Za-z_-]{11})"):
        m = re.search(pattern, value)
        if m:
            return m.group(1)
    raise ValueError(f"Identifiant vidéo YouTube introuvable dans : {url_or_id!r}")


def _webshare_config(env: dict) -> WebshareProxyConfig | None:
    """Construit la config proxy Webshare si les credentials sont présents, sinon None."""
    user = env.get("WEBSHARE_PROXY_USERNAME")
    pwd = env.get("WEBSHARE_PROXY_PASSWORD")
    if user and pwd:
        return WebshareProxyConfig(proxy_username=user, proxy_password=pwd)
    return None


def fetch_transcript(url_or_id: str, languages=DEFAULT_LANGS,
                     env: dict | None = None) -> dict:
    """Récupère la transcription d'une vidéo YouTube via le proxy Webshare.

    Args:
        url_or_id: URL YouTube ou identifiant vidéo.
        languages: ordre de préférence des langues.
        env: dictionnaire d'environnement (défaut : config/.env). Utile pour les tests.

    Returns:
        dict `{video_id, language, text, segments}` où `segments` est une liste de
        `{start, text}` et `text` la transcription complète assemblée.

    Raises:
        ValueError: identifiant introuvable.
        Exception: erreurs de la librairie (RequestBlocked, TranscriptsDisabled…).
    """
    video_id = extract_video_id(url_or_id)
    env = _env() if env is None else env
    proxy = _webshare_config(env)
    api = YouTubeTranscriptApi(proxy_config=proxy) if proxy else YouTubeTranscriptApi()
    fetched = api.fetch(video_id, languages=list(languages))

    segments = []
    for snippet in fetched:
        text = snippet.text.replace("\n", " ").strip()
        segments.append({"start": round(float(snippet.start), 2), "text": text})
    full_text = " ".join(seg["text"] for seg in segments if seg["text"])

    return {
        "video_id": video_id,
        "language": getattr(fetched, "language_code", None),
        "text": full_text,
        "segments": segments,
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage : python -m pipeline.transcript <url|video_id>")
    res = fetch_transcript(sys.argv[1])
    print(f"[{res['language']}] {res['video_id']} — {len(res['text'].split())} mots")
    print(json.dumps(res, ensure_ascii=False)[:2000])
