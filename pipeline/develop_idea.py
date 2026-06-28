#!/usr/bin/env python3
"""Développe l'idée N de briefs/proposals/latest.json via editorial-writer,
génère son visuel (Ideogram + photo incrustée) et sauvegarde les sorties.

Usage : python -m pipeline.develop_idea <N>
Sorties : briefs/output/ideeN/variants.json + visual.png
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from pipeline.config import BRAND_PHOTO_FILE_ID
from pipeline.google_workspace import download_file, pilier_nom
from pipeline.visuals import (
    build_visual_prompt, generate_image, composite_photo_bottom_right,
)

PROFILE = Path("/opt/hermes/data/profiles/social-media")
WORKSPACE = PROFILE / "workspace" / "editorial"


def _extract_json(text: str) -> dict:
    start = text.rfind("```json")
    if start != -1:
        body = text[start + 7:]
        end = body.find("```")
        return json.loads(body[:end if end != -1 else None])
    s, e = text.find("{"), text.rfind("}")
    return json.loads(text[s:e + 1])


def develop(n: int) -> tuple[dict, dict, str]:
    """Appelle editorial-writer sur l'idée N. Retourne (idée, variantes, slug)."""
    data = json.loads((PROFILE / "briefs/proposals/latest.json").read_text(encoding="utf-8"))
    idea = data["idees"][n - 1]
    brief = {
        "idee": idea.get("titre", ""),
        "theme": idea.get("angle") or pilier_nom(idea.get("pilier")),
        "audience": "dirigeants PME/ESN au Maroc, étudiants ENSA, managers tech",
        "plateformes": idea.get("plateformes_suggerees") or ["linkedin"],
        "confidentialite": idea.get("confidentialite", "public"),
        "ton": "professionnel, pédagogique, première personne",
        "slug": f"idee{n}",
    }
    prompt = ("Voici le brief Hermes :\n" + json.dumps(brief, ensure_ascii=False)
              + "\nProduis les variantes.")
    out = subprocess.run(
        ["claude", "-p", prompt, "--agent", "editorial-writer",
         "--permission-mode", "dontAsk", "--max-turns", "8"],
        cwd=str(WORKSPACE), capture_output=True, text=True, timeout=400,
        env={**os.environ, "HOME": "/opt/hermes"})
    return idea, _extract_json(out.stdout), brief["slug"]


def make_visual(idea: dict, out_path: str) -> str:
    """Génère le visuel (fond abstrait + photo incrustée) pour une idée."""
    photo = "/tmp/brand_photo.png"
    download_file(BRAND_PHOTO_FILE_ID, photo)
    base = "/tmp/visual_base.png"
    generate_image(build_visual_prompt(idea), base)
    return composite_photo_bottom_right(base, photo, out_path)


def main(n: int) -> int:
    from dotenv import load_dotenv
    load_dotenv("/opt/hermes/data/.env")
    load_dotenv(str(PROFILE / "config" / ".env"))
    idea, variants, slug = develop(n)
    outdir = PROFILE / "briefs" / "output" / slug
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "variants.json").write_text(
        json.dumps(variants, ensure_ascii=False, indent=2), encoding="utf-8")
    visual_path = make_visual(idea, str(outdir / "visual.png"))
    print("IDEE:", idea.get("titre"))
    print("VARIANTES:", len(variants.get("variantes", [])))
    print("VISUEL:", visual_path)
    print("OUTDIR:", outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 1))
