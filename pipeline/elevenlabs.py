#!/usr/bin/env python3
"""Connecteur ElevenLabs — synthèse vocale avec la voix clonée d'Abdelilah.

Fonctions pures testées ; `synthesize` (réseau) reste fine et non testée.
Clés : ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID (config/.env du profil).
"""
from __future__ import annotations

from pipeline.config import ELEVENLABS_TTS_URL, ELEVENLABS_MODEL


def tts_url(voice_id: str) -> str:
    """URL TTS pour une voix donnée."""
    return ELEVENLABS_TTS_URL.format(voice_id=voice_id)


def build_tts_payload(script: str) -> dict:
    """Payload TTS : texte + modèle multilingue + réglages voix stables."""
    return {
        "text": script,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }


def synthesize(script: str, out_path: str, api_key: str | None = None,
               voice_id: str | None = None) -> str:
    """Génère le mp3 du script (réseau). Retourne out_path."""
    import os
    import requests

    key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
    voice = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "")
    if not key or not voice:
        raise RuntimeError("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID manquant")
    resp = requests.post(
        tts_url(voice),
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json=build_tts_payload(script),
        timeout=120,
    )
    resp.raise_for_status()
    with open(out_path, "wb") as fh:
        fh.write(resp.content)
    return out_path
