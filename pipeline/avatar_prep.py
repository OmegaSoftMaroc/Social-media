#!/usr/bin/env python3
"""Prépare un avatar HeyGen pour le template Remotion « AvatarPhases ».

Deux besoins par vidéo, couverts en une commande chacun :
- `captions` : audio de l'avatar + texte du script → sous-titres mot-à-mot EXACTS
  (forced-alignment ElevenLabs, zéro erreur de transcription), écrits en
  `<avatar>.json` à côté du mp4 — là où la composition les attend.
- `measure`  : mesure la bande utile du mp4 (HeyGen exporte en 1920×1080 avec des
  bandes blanches latérales) → valeurs `cropSource` à coller dans le props JSON.

Clé : ELEVENLABS_API_KEY (config/.env du profil hermes).

Usage :
  python -m pipeline.avatar_prep captions <avatar.mp4> <script.txt>
  python -m pipeline.avatar_prep measure <avatar.mp4>
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

ALIGN_URL = "https://api.elevenlabs.io/v1/forced-alignment"


def build_words(chars: list[str], starts: list[float], ends: list[float]) -> list[dict]:
    """Regroupe un alignement caractère → mots {text, startMs, endMs}.

    Args:
        chars: caractères alignés (espaces = séparateurs de mots).
        starts: temps de début (s) par caractère.
        ends: temps de fin (s) par caractère.

    Returns:
        Liste de mots au format captions de video-studio (startMs/endMs).
    """
    words: list[dict] = []
    cur = ""
    ws: float | None = None
    we = 0.0
    for ch, s, e in zip(chars, starts, ends):
        if ch == " ":
            if cur:
                words.append({"text": cur, "startMs": int(ws * 1000),
                              "endMs": int(we * 1000)})
                cur = ""
                ws = None
            continue
        if ws is None:
            ws = s
        cur += ch
        we = e
    if cur:
        words.append({"text": cur, "startMs": int(ws * 1000), "endMs": int(we * 1000)})
    return words


def measure_bounds(image_path: str | Path, white_threshold: int = 235,
                   step: int = 4) -> tuple[int, int]:
    """Mesure les bords gauche/droit du contenu utile (bandes blanches exclues).

    Args:
        image_path: frame extraite du mp4 avatar.
        white_threshold: niveau RGB au-dessus duquel un pixel est « blanc ».
        step: pas d'échantillonnage des colonnes.

    Returns:
        (x0, x1) : première et dernière colonne non blanche.
    """
    from PIL import Image

    im = Image.open(image_path).convert("RGB")
    w, h = im.size
    px = im.load()

    def col_white(x: int) -> bool:
        samples = range(0, h, max(1, h // 50))
        return all(all(c > white_threshold for c in px[x, y]) for y in samples)

    x0 = 0
    while x0 < w // 2 and col_white(x0):
        x0 += step
    x1 = w - 1
    while x1 > w // 2 and col_white(x1):
        x1 -= step
    return x0, x1


def extract_audio(avatar: str | Path, out_mp3: str | Path) -> Path:
    """Extrait la piste audio du mp4 (ffmpeg) pour l'alignement."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(avatar), "-vn",
         "-acodec", "libmp3lame", "-q:a", "2", str(out_mp3)],
        check=True)
    return Path(out_mp3)


def align_captions(avatar: str | Path, script_txt: str | Path,
                   api_key: str | None = None) -> Path:
    """Aligne le script sur l'audio de l'avatar → écrit `<avatar>.json`.

    Args:
        avatar: mp4 de l'avatar (avec sa voix).
        script_txt: texte EXACT lu par l'avatar.
        api_key: ELEVENLABS_API_KEY (sinon variable d'environnement).

    Returns:
        Chemin du fichier captions écrit.
    """
    import requests

    key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY manquante (config/.env du profil)")
    text = Path(script_txt).read_text(encoding="utf-8").strip()

    with tempfile.TemporaryDirectory() as tmp:
        audio = extract_audio(avatar, Path(tmp) / "audio.mp3")
        with open(audio, "rb") as fh:
            r = requests.post(ALIGN_URL, headers={"xi-api-key": key},
                              files={"file": ("audio.mp3", fh, "audio/mpeg")},
                              data={"text": text}, timeout=300)
    r.raise_for_status()
    al = r.json()
    if al.get("words"):  # réponse standard forced-alignment : mots directs
        words = [{"text": w["text"].strip(), "startMs": int(w["start"] * 1000),
                  "endMs": int(w["end"] * 1000)}
                 for w in al["words"] if w.get("text", "").strip()]
    else:  # repli : alignement caractère (format des endpoints TTS with-timestamps)
        words = build_words(al["characters"],
                            al["character_start_times_seconds"],
                            al["character_end_times_seconds"])

    out = Path(avatar).with_suffix(".json")
    out.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    logger.info("Captions écrites : %s (%d mots, fin %.1fs)", out, len(words),
                words[-1]["endMs"] / 1000 if words else 0)
    return out


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[0]

    if cmd == "captions":
        if len(argv) < 3:
            print("Usage : avatar_prep captions <avatar.mp4> <script.txt>")
            return 2
        out = align_captions(argv[1], argv[2])
        data = json.loads(out.read_text(encoding="utf-8"))
        print(f"OK {out} — {len(data)} mots, fin {data[-1]['endMs']/1000:.1f}s")
        return 0

    if cmd == "measure":
        with tempfile.TemporaryDirectory() as tmp:
            frame = Path(tmp) / "frame.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "3", "-i",
                            argv[1], "-frames:v", "1", str(frame)], check=True)
            x0, x1 = measure_bounds(frame)
        print(f'cropSource à coller dans le props JSON : '
              f'{{"x0": {x0}, "largeur": {x1 - x0}}}')
        return 0

    print(f"commande inconnue : {cmd} (captions|measure)")
    return 2


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(_main(sys.argv[1:]))
