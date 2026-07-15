#!/usr/bin/env python3
"""Bibliothèque de clips animés réutilisables (catalogue à tags manuels).

Centralise les clips image-to-video déjà générés (fal.ai) dans `clip-library/` :
les MP4/vignettes restent locaux (git-ignorés), `index.json` est versionné. But :
retrouver et réutiliser un clip existant AVANT de repayer un appel fal.

Usage CLI : python -m pipeline.clip_library <add|ingest|search|list|show> ...
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Racine par défaut = <repo>/clip-library (pipeline/ est un cran sous la racine).
DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "clip-library"
INDEX_VERSION = 1


def _index_path(root: Path) -> Path:
    return Path(root) / "index.json"


def load_index(root: Path) -> dict:
    """Lit index.json. Retourne un squelette vide si absent (bootstrap naturel)."""
    p = _index_path(root)
    if not p.exists():
        return {"version": INDEX_VERSION, "clips": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save_index(root: Path, data: dict) -> None:
    """Écrit index.json (UTF-8, indent 2), clips triés par id pour un diff stable."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    data["clips"].sort(key=lambda c: c["id"])
    _index_path(root).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify(text: str) -> str:
    """kebab-case ASCII pour un id de clip. 'Flux Données' -> 'flux-donnees'."""
    text = text.lower()
    for a, b in (("à", "a"), ("â", "a"), ("é", "e"), ("è", "e"), ("ê", "e"),
                 ("ï", "i"), ("î", "i"), ("ô", "o"), ("ù", "u"), ("û", "u"),
                 ("ç", "c")):
        text = text.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return s or "clip"


def make_thumb(mp4_path: Path, out_jpg: Path) -> bool:
    """1er frame du clip en jpg via ffmpeg. Best-effort : échec = warning, non bloquant."""
    out_jpg = Path(out_jpg)
    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp4_path), "-frames:v", "1", "-q:v", "3",
             str(out_jpg)],
            check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.warning("Vignette non générée pour %s : %s", mp4_path, exc)
        return False


def _unique_id(base: str, existing: set[str]) -> str:
    """base si libre, sinon base-02, base-03… (anti-collision)."""
    if base not in existing:
        return base
    i = 2
    while f"{base}-{i:02d}" in existing:
        i += 1
    return f"{base}-{i:02d}"


def add_clip(root: Path, mp4_path, tags: list[str], description: str, *,
             clip_id: str | None = None, thumb: bool = True, **meta) -> dict:
    """Catalogue un clip : copie le mp4 dans clips/, génère la vignette, enregistre.

    Idempotent sur `id` : réimporter le même `clip_id` met à jour l'entrée sans
    dupliquer. Sans `clip_id`, l'id est un slug de la description (suffixe anti-collision).
    `meta` (model, cost_usd, origin_video, source_still…) est fusionné si non-None.

    Args:
        root: racine de la bibliothèque (contient clips/, thumbs/, index.json).
        mp4_path: chemin du clip source à cataloguer.
        tags: mots-clés métier (recherche par recouvrement).
        description: description humaine du clip.
        clip_id: id explicite (sinon dérivé de la description).
        thumb: générer la vignette (ffmpeg) si True.
        **meta: métadonnées optionnelles (model, cost_usd, origin_video, source_still).

    Returns:
        L'entrée de catalogue créée/mise à jour.
    """
    root = Path(root)
    (root / "clips").mkdir(parents=True, exist_ok=True)
    data = load_index(root)
    existing = {c["id"] for c in data["clips"]}

    if clip_id and clip_id in existing:
        cid = clip_id  # upsert idempotent
    else:
        base = slugify(clip_id or description or (tags[0] if tags else "clip"))
        cid = _unique_id(base, existing)

    dest = root / "clips" / f"{cid}.mp4"
    shutil.copyfile(mp4_path, dest)

    entry = {"id": cid, "file": f"clips/{cid}.mp4",
             "tags": list(tags), "description": description}
    if thumb and make_thumb(dest, root / "thumbs" / f"{cid}.jpg"):
        entry["thumb"] = f"thumbs/{cid}.jpg"
    entry.update({k: v for k, v in meta.items() if v is not None})

    data["clips"] = [c for c in data["clips"] if c["id"] != cid] + [entry]
    save_index(root, data)
    logger.info("Clip catalogué : %s (tags=%s)", cid, list(tags))
    return entry


def search(root: Path, tags: list[str] | None = None,
           text: str | None = None) -> list[dict]:
    """Clips filtrés puis classés par recouvrement de tags (décroissant).

    - `tags` : ne garde que les clips avec ≥ 1 tag commun, triés par nb de tags communs.
    - `text` : sous-chaîne (insensible à la casse) dans description ou tags.
    Les deux filtres se combinent. Sans critère : tous les clips.

    Args:
        root: racine de la bibliothèque.
        tags: tags recherchés (recouvrement).
        text: sous-chaîne à chercher dans description/tags.

    Returns:
        Liste d'entrées, classée par recouvrement de tags décroissant.
    """
    results = load_index(root)["clips"]
    if text:
        t = text.lower()
        results = [c for c in results
                   if t in c["description"].lower()
                   or any(t in tag for tag in c["tags"])]
    if tags:
        wanted = set(tags)
        results = [c for c in results if wanted & set(c["tags"])]
        results = sorted(results, key=lambda c: len(wanted & set(c["tags"])),
                         reverse=True)
    return results


def get(root: Path, clip_id: str) -> dict | None:
    """Une entrée par id, ou None."""
    return next((c for c in load_index(root)["clips"] if c["id"] == clip_id), None)


def reuse(root: Path, clip_id: str, out_path) -> str:
    """Copie le clip catalogué vers out_path. Lève KeyError si id inconnu.

    Args:
        root: racine de la bibliothèque.
        clip_id: id du clip à réutiliser.
        out_path: destination du clip copié.

    Returns:
        Le chemin de destination (str).
    """
    entry = get(root, clip_id)
    if entry is None:
        raise KeyError(f"clip inconnu : {clip_id}")
    shutil.copyfile(Path(root) / entry["file"], out_path)
    logger.info("Clip réutilisé : %s -> %s", clip_id, out_path)
    return str(out_path)
