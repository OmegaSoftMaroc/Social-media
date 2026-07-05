#!/usr/bin/env python3
"""Publie un post DÉJÀ développé (briefs/output/<slug>/) sur LinkedIn :
variante recommandée + visuel.

⚠️ À lancer UNIQUEMENT après validation explicite d'Abdelilah — jamais automatiquement.

Usage : python -m pipeline.publish_idea <slug>   (ex. idee1)
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("/opt/hermes/data/.env")

from pipeline.linkedin import publish_image_post, publish_text

PROFILE = Path("/opt/hermes/data/profiles/social-media")


def publish(slug: str) -> dict:
    """Publie la variante recommandée de l'idée `slug` (+ visuel s'il existe)."""
    outdir = PROFILE / "briefs" / "output" / slug
    data = json.loads((outdir / "variants.json").read_text(encoding="utf-8"))
    reco = data.get("recommandation", {}).get("id")
    variant = next((v for v in data["variantes"] if v.get("id") == reco),
                   data["variantes"][0])
    text = variant["contenu"]
    visual = outdir / "visual.png"
    if visual.exists():
        return publish_image_post(text, str(visual))
    return publish_text(text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage : python -m pipeline.publish_idea <slug>")
    print(publish(sys.argv[1]))
