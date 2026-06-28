#!/usr/bin/env python3
"""Génération de visuels pour les publications (Ideogram).

`build_visual_prompt` est pur (testable) ; `generate_image` appelle l'API Ideogram.
Clé via la variable d'environnement IDEOGRAM_API_KEY (config/.env du profil).
"""
from __future__ import annotations

from pipeline.config import BRAND_STYLE, VISUAL_ASPECT, IDEOGRAM_ENDPOINT, VISUAL_NEGATIVE


def build_visual_prompt(idea: dict) -> str:
    """Construit le prompt visuel d'une idée : concept ABSTRAIT (sans personnage)."""
    titre = (idea.get("titre") or "").strip()
    return (
        f"{BRAND_STYLE}. Illustration conceptuelle et abstraite illustrant : {titre}. "
        "PAS de personnage, pas de visage, pas de personne. "
        "Motifs tech abstraits (réseaux de nœuds, circuits, formes géométriques, icônes). "
        f"Portrait {VISUAL_ASPECT}, composition épurée, espace négatif généreux. "
        "Sans filigrane, sans texte parasite."
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
        files={"prompt": (None, prompt),
               "negative_prompt": (None, VISUAL_NEGATIVE),
               "aspect_ratio": (None, VISUAL_ASPECT),
               "rendering_speed": (None, "DEFAULT")},
        timeout=120,
    )
    resp.raise_for_status()
    url = resp.json()["data"][0]["url"]

    img = requests.get(url, timeout=120)
    img.raise_for_status()
    with open(out_path, "wb") as fh:
        fh.write(img.content)
    return out_path


def composite_photo_bottom_right(base_path: str, photo_path: str, out_path: str,
                                 size_ratio: float = 0.16, margin: int = 40) -> str:
    """Incruste `photo_path` en rond dans le coin bas-droite de `base_path`.

    size_ratio = diamètre du rond en fraction de la largeur. Retourne out_path.
    """
    from PIL import Image, ImageDraw

    base = Image.open(base_path).convert("RGBA")
    photo = Image.open(photo_path).convert("RGBA")
    width, height = base.size
    diam = int(width * size_ratio)

    # recadrage carré centré puis redimensionnement au diamètre
    pw, ph = photo.size
    side = min(pw, ph)
    left, top = (pw - side) // 2, (ph - side) // 2
    photo = photo.crop((left, top, left + side, top + side)).resize((diam, diam))

    # masque circulaire
    mask = Image.new("L", (diam, diam), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diam, diam), fill=255)

    # anneau blanc fin pour détacher du fond
    ring = Image.new("RGBA", (diam, diam), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, diam - 1, diam - 1),
                                 outline=(255, 255, 255, 255), width=max(2, diam // 36))

    pos = (width - diam - margin, height - diam - margin)
    base.paste(photo, pos, mask)
    base.alpha_composite(ring, pos)
    base.convert("RGB").save(out_path, "PNG")
    return out_path
