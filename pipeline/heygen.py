#!/usr/bin/env python3
"""Connecteur HeyGen — vidéo avatar filmé à partir d'un audio.

Fonctions pures testées (payload, parsing statut) ; réseau isolé.
Clés : HEYGEN_API_KEY + HEYGEN_AVATAR_ID (config/.env du profil).
NB : endpoints v2 vérifiés contre la doc au premier test réel (l'API évolue).
"""
from __future__ import annotations

import time

from pipeline.config import (
    HEYGEN_UPLOAD_URL, HEYGEN_GENERATE_URL, HEYGEN_STATUS_URL,
    VIDEO_FORMATS, VIDEO_POLL_S, VIDEO_TIMEOUT_S,
)


def build_video_payload(audio_asset_id: str, avatar_id: str, fmt: str) -> dict:
    """Payload /v2/video/generate : avatar filmé + audio uploadé + dimensions."""
    dimension = VIDEO_FORMATS[fmt]["dimension"]  # KeyError si format inconnu
    return {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": avatar_id,
                          "avatar_style": "normal"},
            "voice": {"type": "audio", "audio_asset_id": audio_asset_id},
        }],
        "dimension": dimension,
    }


def build_text_video_payload(script_text: str, voice_id: str, avatar_id: str,
                             fmt: str) -> dict:
    """Payload /v2/video/generate en mode voix HeyGen (TTS intégré, sans ElevenLabs)."""
    dimension = VIDEO_FORMATS[fmt]["dimension"]  # KeyError si format inconnu
    return {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": avatar_id,
                          "avatar_style": "normal"},
            "voice": {"type": "text", "voice_id": voice_id,
                      "input_text": script_text},
        }],
        "dimension": dimension,
    }


def parse_video_status(resp: dict) -> tuple[str, str | None]:
    """(statut, info) — info = video_url si completed, message si failed, sinon None."""
    data = resp.get("data") or {}
    status = data.get("status", "unknown")
    if status == "completed":
        return status, data.get("video_url")
    if status == "failed":
        err = data.get("error") or {}
        return status, str(err.get("message") or err or "échec HeyGen")
    return status, None


def _key(api_key: str | None) -> str:
    import os
    key = api_key or os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        raise RuntimeError("HEYGEN_API_KEY manquant")
    return key


def upload_audio(path: str, api_key: str | None = None) -> str:
    """Upload l'audio (asset) ; retourne l'asset_id."""
    import requests
    with open(path, "rb") as fh:
        resp = requests.post(HEYGEN_UPLOAD_URL, data=fh.read(), timeout=120,
                             headers={"x-api-key": _key(api_key),
                                      "Content-Type": "audio/mpeg"})
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def create_video(audio_asset_id: str, fmt: str, api_key: str | None = None,
                 avatar_id: str | None = None) -> str:
    """Lance la génération ; retourne le video_id."""
    import os
    import requests
    avatar = avatar_id or os.environ.get("HEYGEN_AVATAR_ID", "")
    if not avatar:
        raise RuntimeError("HEYGEN_AVATAR_ID manquant")
    resp = requests.post(HEYGEN_GENERATE_URL, timeout=60,
                         headers={"x-api-key": _key(api_key)},
                         json=build_video_payload(audio_asset_id, avatar, fmt))
    resp.raise_for_status()
    return resp.json()["data"]["video_id"]


def create_video_from_text(script_text: str, fmt: str, api_key: str | None = None,
                           avatar_id: str | None = None,
                           voice_id: str | None = None) -> str:
    """Génération en mode voix HeyGen (texte → TTS intégré). Retourne le video_id."""
    import os
    import requests
    avatar = avatar_id or os.environ.get("HEYGEN_AVATAR_ID", "")
    voice = voice_id or os.environ.get("HEYGEN_VOICE_ID", "")
    if not avatar or not voice:
        raise RuntimeError("HEYGEN_AVATAR_ID / HEYGEN_VOICE_ID manquant")
    resp = requests.post(HEYGEN_GENERATE_URL, timeout=60,
                         headers={"x-api-key": _key(api_key)},
                         json=build_text_video_payload(script_text, voice, avatar, fmt))
    resp.raise_for_status()
    return resp.json()["data"]["video_id"]


def wait_and_download(video_id: str, out_path: str, api_key: str | None = None,
                      poll_s: int = VIDEO_POLL_S,
                      timeout_s: int = VIDEO_TIMEOUT_S) -> str:
    """Polle le statut puis télécharge le mp4. Lève RuntimeError si failed/timeout."""
    import requests
    key = _key(api_key)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        resp = requests.get(HEYGEN_STATUS_URL, params={"video_id": video_id},
                            headers={"x-api-key": key}, timeout=30)
        resp.raise_for_status()
        status, info = parse_video_status(resp.json())
        if status == "completed":
            video = requests.get(info, timeout=300)
            video.raise_for_status()
            with open(out_path, "wb") as fh:
                fh.write(video.content)
            return out_path
        if status == "failed":
            raise RuntimeError(f"HeyGen a échoué : {info}")
        time.sleep(poll_s)
    raise RuntimeError(f"HeyGen : timeout après {timeout_s}s (video_id={video_id})")
