#!/usr/bin/env python3
"""Génération de visuels pour les publications (Ideogram).

`build_visual_prompt` est pur (testable) ; `generate_image` appelle l'API Ideogram.
Clé via la variable d'environnement IDEOGRAM_API_KEY (config/.env du profil).
"""
from __future__ import annotations

from pipeline.config import BRAND_STYLE, VISUAL_ASPECT, IDEOGRAM_ENDPOINT


def build_visual_prompt(idea: dict) -> str:
    """Construit le prompt visuel d'une idée (concept + style de marque + format)."""
    titre = (idea.get("titre") or "").strip()
    return (
        f"{BRAND_STYLE}. Concept : {titre}. "
        f"Portrait {VISUAL_ASPECT}, espace dégagé en haut pour un titre court. "
        "Sans filigrane, sans logo, sans texte parasite."
    )


def generate_image(prompt: str, out_path: str, api_key: str | None = None) -> str:
    """Génère une image via Ideogram et l'enregistre dans `out_path`. Retourne le chemin.

    NB : endpoint/paramètres à confirmer contre la doc Ideogram courante lors du
    premier test réel (l'API évolue).
    """
    import os
    import requests

    key = api_key or os.environ.get("IDEOGRAM_API_KEY", "")
    if not key:
        raise RuntimeError("IDEOGRAM_API_KEY manquante")

    resp = requests.post(
        IDEOGRAM_ENDPOINT,
        headers={"Api-Key": key},
        data={"prompt": prompt, "aspect_ratio": VISUAL_ASPECT,
              "rendering_speed": "DEFAULT"},
        timeout=120,
    )
    resp.raise_for_status()
    url = resp.json()["data"][0]["url"]

    img = requests.get(url, timeout=120)
    img.raise_for_status()
    with open(out_path, "wb") as fh:
        fh.write(img.content)
    return out_path
