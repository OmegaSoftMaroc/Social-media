#!/usr/bin/env python3
"""Publie un post DÉJÀ développé (briefs/output/<slug>/) sur le canal choisi :
LinkedIn (défaut), YouTube (Short), Facebook (Page) ou Instagram (Reel).

⚠️ À lancer UNIQUEMENT après validation explicite d'Abdelilah — jamais automatiquement.

Usage : python -m pipeline.publish_idea <slug> [image|video] [linkedin|youtube|facebook|instagram] [fichier]
Ex.    : publish_idea cadrage-metier video youtube
         publish_idea cadrage-metier video instagram https://url-publique/video.mp4
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("/opt/hermes/data/.env")

from pipeline.linkedin import publish_image_post, publish_text

PROFILE = Path("/opt/hermes/data/profiles/social-media")


def _load_script(outdir: Path) -> dict:
    return json.loads((outdir / "video-script.json").read_text(encoding="utf-8"))


def publish(slug: str, media: str = "auto", channel: str = "linkedin",
            file: str | None = None, url: str | None = None) -> dict:
    """Publie l'idée `slug` sur `channel`. media: auto|image|video.

    `file` remplace le chemin vidéo par défaut (ex. rendu HyperFrames).
    `url` (Instagram uniquement) : URL vidéo publique exigée par l'API IG.
    """
    outdir = PROFILE / "briefs" / "output" / slug
    video = Path(file) if file else outdir / "video.mp4"
    is_video = media == "video" or (media == "auto" and video.exists()
                                    and not (outdir / "variants.json").exists())

    if channel == "youtube":
        from pipeline.youtube import publish_short
        s = _load_script(outdir)
        return publish_short(str(video), s.get("titre", slug),
                             s.get("description", ""))

    if channel == "facebook":
        from pipeline.meta import publish_facebook_video, publish_facebook_photo
        if is_video:
            s = _load_script(outdir)
            return publish_facebook_video(str(video), s.get("description", ""))
        data = json.loads((outdir / "variants.json").read_text(encoding="utf-8"))
        reco = data.get("recommandation", {}).get("id")
        variant = next((v for v in data["variantes"] if v.get("id") == reco),
                       data["variantes"][0])
        return publish_facebook_photo(str(outdir / "visual.png"), variant["contenu"])

    if channel == "instagram":
        from pipeline.meta import publish_instagram_reel
        if not url:
            raise RuntimeError("Instagram exige une URL vidéo publique (argument url)")
        s = _load_script(outdir)
        return publish_instagram_reel(url, s.get("description", ""))

    # LinkedIn (défaut) — comportement historique
    if is_video:
        from pipeline.linkedin import publish_video_post
        s = _load_script(outdir)
        return publish_video_post(s.get("description", s.get("titre", "")), str(video))
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
        raise SystemExit("Usage : python -m pipeline.publish_idea <slug> "
                         "[image|video] [linkedin|youtube|facebook|instagram] [fichier|url]")
    slug_arg = sys.argv[1]
    media_arg = sys.argv[2] if len(sys.argv) > 2 else "auto"
    channel_arg = sys.argv[3] if len(sys.argv) > 3 else "linkedin"
    extra = sys.argv[4] if len(sys.argv) > 4 else None
    kwargs = {}
    if extra and extra.startswith("http"):
        kwargs["url"] = extra
    elif extra:
        kwargs["file"] = extra
    print(publish(slug_arg, media_arg, channel_arg, **kwargs))
