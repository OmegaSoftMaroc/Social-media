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
