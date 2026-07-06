#!/usr/bin/env python3
"""Publie un post DÉJÀ développé (briefs/output/<slug>/) sur LinkedIn :
variante recommandée + visuel, ou vidéo (video.mp4 + video-script.json).

⚠️ À lancer UNIQUEMENT après validation explicite d'Abdelilah — jamais automatiquement.

Usage : python -m pipeline.publish_idea <slug> [image|video]   (ex. idee1 video)
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("/opt/hermes/data/.env")

from pipeline.linkedin import publish_image_post, publish_text

PROFILE = Path("/opt/hermes/data/profiles/social-media")


def publish(slug: str, media: str = "auto") -> dict:
    """Publie l'idée `slug`. media: auto|image|video.

    - video : publie video.mp4 avec la description du script vidéo.
    - image/auto : comportement existant (variante recommandée + visuel).
    """
    outdir = PROFILE / "briefs" / "output" / slug
    video = outdir / "video.mp4"
    if media == "video" or (media == "auto" and video.exists()
                            and not (outdir / "variants.json").exists()):
        from pipeline.linkedin import publish_video_post
        script = json.loads((outdir / "video-script.json").read_text(encoding="utf-8"))
        return publish_video_post(script.get("description", script.get("titre", "")),
                                  str(video))
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
        raise SystemExit("Usage : python -m pipeline.publish_idea <slug> [image|video]")
    print(publish(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "auto"))
