#!/usr/bin/env python3
"""Image → vidéo via fal.ai (template narration-illustree, animation « C »).

Anime un still Ideogram en clip court (~5 s) : parallax/particules/dérive de caméra
douce, SANS déformer la composition de l'illustration. Utilise la file d'attente fal
(soumission → polling → récupération de l'URL vidéo).

Clé : variable d'environnement FAL_KEY (déposée par Abdelilah, jamais en clair ici).

Usage : python -m pipeline.animate <image.png> <sortie.mp4> [--model kling|hailuo|luma|wan] [--prompt "..."]
"""
from __future__ import annotations

import base64
import logging
import mimetypes
import os
import sys
import time

import requests

logger = logging.getLogger(__name__)

# Modèles fal image-to-video (route de la file d'attente) + coût indicatif 2026.
# DÉFAUT = kling-turbo : même famille/look que le master mais ~4× moins cher.
# NE PAS utiliser kling-master pour du mouvement subtil sur illustration fixe : on
# paie le premium (0,28 $/s) sans bénéfice (retour Abdelilah 2026-07-12, 16,80 $ pour 1 vidéo).
MODELS = {
    "kling-turbo": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",  # 0,07 $/s — DÉFAUT
    "hailuo": "fal-ai/minimax/hailuo-02/standard/image-to-video",       # ~0,045 $/s
    "ltx": "fal-ai/ltx-video/image-to-video",                           # ~0,02 $/clip (le moins cher)
    "kling-master": "fal-ai/kling-video/v2/master/image-to-video",      # 0,28 $/s — CHER, éviter
    "luma": "fal-ai/luma-dream-machine/image-to-video",
    "wan": "fal-ai/wan-i2v",
}

# Prompt par défaut : mouvement subtil, la composition NE doit PAS se transformer.
DEFAULT_PROMPT = (
    "Subtle cinematic motion: gentle slow camera push-in and parallax, softly "
    "drifting particles and light, faint energy flowing along existing lines. "
    "Keep the original composition, shapes and colors stable — do NOT morph or "
    "redraw objects. Calm, premium, corporate abstract mood."
)
NEGATIVE_PROMPT = (
    "morphing, warping, distortion, extra objects appearing, text, letters, watermark, "
    "people, faces, flicker, jitter"
)

FAL_QUEUE = "https://queue.fal.run"


def _data_uri(path: str) -> str:
    """Encode l'image locale en data-URI (fal accepte image_url en data-URI)."""
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return f"data:{mime};base64,{b64}"


def _payload(model_key: str, image_uri: str, prompt: str, duration: int) -> dict:
    """Construit le corps de requête selon les conventions de chaque modèle fal."""
    body: dict = {"image_url": image_uri, "prompt": prompt}
    if model_key in ("kling-turbo", "kling-master"):
        body.update({"duration": str(duration), "negative_prompt": NEGATIVE_PROMPT,
                     "cfg_scale": 0.5})
    elif model_key == "hailuo":
        body.update({"duration": str(duration), "prompt_optimizer": True})
    elif model_key == "ltx":
        body.update({"negative_prompt": NEGATIVE_PROMPT})
    elif model_key == "luma":
        body.update({"aspect_ratio": "9:16"})
    elif model_key == "wan":
        body.update({"negative_prompt": NEGATIVE_PROMPT, "num_frames": 81})
    return body


def animate_image(image_path: str, out_path: str, *, model: str = "kling-turbo",
                  prompt: str = DEFAULT_PROMPT, duration: int = 5,
                  key: str | None = None, poll_s: float = 5.0,
                  timeout_s: float = 600.0,
                  reuse_tags: list[str] | None = None) -> str:
    """Anime `image_path` → `out_path` (mp4). Retourne out_path.

    Args:
        image_path: still source (Ideogram).
        out_path: mp4 de sortie.
        model: clé de MODELS (kling/hailuo/luma/wan).
        prompt: consigne de mouvement (défaut = mouvement subtil non déformant).
        duration: durée cible en secondes (selon capacités du modèle).
        key: FAL_KEY (sinon variable d'environnement).
        reuse_tags: si fourni, réutilise un clip taggé de la bibliothèque (aucun appel
            fal) quand un match existe ; sinon génère normalement.
    """
    # Réutilisation : si un clip taggé correspond, on le copie et on ÉVITE l'appel fal.
    if reuse_tags:
        # import différé : évite de charger clip_library quand reuse_tags n'est pas utilisé
        from pipeline import clip_library
        root = clip_library.DEFAULT_ROOT
        for candidate in clip_library.search(root, tags=reuse_tags):
            try:
                clip_library.reuse(root, candidate["id"], out_path)
            except OSError as exc:
                # clip catalogué mais binaire absent (MP4 non versionnés) → candidat suivant
                logger.warning("Clip %s introuvable sur disque (%s) : on continue.",
                               candidate["id"], exc)
                continue
            saved = candidate.get("cost_usd")
            logger.info("Clip réutilisé depuis la bibliothèque : %s (tags=%s)%s",
                        candidate["id"], candidate["tags"],
                        f" — ~{saved} $ économisés" if saved else "")
            return out_path
        logger.info("Aucun clip réutilisable pour tags=%s : génération fal.", reuse_tags)

    fal_key = key or os.environ.get("FAL_KEY", "")
    if not fal_key:
        raise RuntimeError("FAL_KEY manquante (déposer dans l'environnement / .env)")
    route = MODELS[model]
    headers = {"Authorization": f"Key {fal_key}"}

    # 1) soumission dans la file
    r = requests.post(f"{FAL_QUEUE}/{route}", headers=headers,
                      json=_payload(model, _data_uri(image_path), prompt, duration),
                      timeout=60)
    r.raise_for_status()
    sub = r.json()
    status_url = sub["status_url"]
    response_url = sub["response_url"]

    # 2) polling jusqu'à COMPLETED
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        s = requests.get(status_url, headers=headers, timeout=30).json()
        status = s.get("status")
        if status == "COMPLETED":
            break
        if status in ("FAILED", "ERROR"):
            raise RuntimeError(f"fal a échoué : {s}")
        time.sleep(poll_s)
    else:
        raise TimeoutError(f"fal : dépassement de {timeout_s:.0f}s")

    # 3) récupération du résultat + téléchargement de la vidéo
    res = requests.get(response_url, headers=headers, timeout=60).json()
    video_url = (res.get("video") or {}).get("url") if isinstance(res.get("video"), dict) \
        else res.get("video_url")
    if not video_url:
        raise RuntimeError(f"URL vidéo introuvable dans la réponse fal : {res}")
    vid = requests.get(video_url, timeout=180)
    vid.raise_for_status()
    with open(out_path, "wb") as fh:
        fh.write(vid.content)
    return out_path


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    image_path, out_path = argv[0], argv[1]
    model, prompt = "kling-turbo", DEFAULT_PROMPT
    i = 2
    while i < len(argv):
        if argv[i] == "--model":
            model = argv[i + 1]; i += 2
        elif argv[i] == "--prompt":
            prompt = argv[i + 1]; i += 2
        else:
            i += 1
    out = animate_image(image_path, out_path, model=model, prompt=prompt)
    print("OK", out, os.path.getsize(out), "octets")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
