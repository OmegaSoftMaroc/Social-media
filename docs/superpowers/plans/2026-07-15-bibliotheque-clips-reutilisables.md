# Bibliothèque de clips réutilisables — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centraliser et indexer les clips animés fal.ai déjà générés (catalogue à tags manuels) pour les retrouver, les réutiliser, et éviter de repayer fal — puis brancher la réutilisation dans `animate.py`.

**Architecture:** Un dossier `clip-library/` à la racine : les MP4/vignettes restent **locaux** (git-ignorés), seul `index.json` est **versionné**. Un module `pipeline/clip_library.py` porte toute la logique (load/save index, ingestion, recherche par recouvrement de tags, réutilisation) + une CLI. En phase 2, `animate.py` interroge la bibliothèque avant tout appel fal.

**Tech Stack:** Python 3.12, stdlib (`json`, `pathlib`, `shutil`, `subprocess`, `logging`, `argparse`, `re`), `ffmpeg` (vignettes, best-effort), `pytest`.

**Convention d'exécution des tests :** depuis la racine du dépôt, `python -m pytest pipeline/tests/<fichier> -v`.

---

## Structure des fichiers

- Créer : `pipeline/clip_library.py` — module + CLI (logique bibliothèque, < 300 lignes).
- Créer : `pipeline/tests/test_clip_library.py` — tests unitaires.
- Modifier : `.gitignore` (racine) — ignorer les binaires, versionner l'index.
- Modifier : `pipeline/animate.py` — hook `reuse_tags` (Lot 2).
- Modifier : `pipeline/tests/test_animate.py` (créé au Lot 2) — test du chemin de réutilisation.

**Signatures publiques du module (référence, à respecter dans toutes les tâches) :**

```python
DEFAULT_ROOT: Path          # <repo>/clip-library
INDEX_VERSION = 1

load_index(root) -> dict
save_index(root, data) -> None
slugify(text) -> str
add_clip(root, mp4_path, tags, description, *, clip_id=None, thumb=True, **meta) -> dict
make_thumb(mp4_path, out_jpg) -> bool
search(root, tags=None, text=None) -> list[dict]
get(root, clip_id) -> dict | None
reuse(root, clip_id, out_path) -> str
```

`root` est **toujours** un paramètre explicite (jamais un défaut figé à l'import) pour
rester testable avec `tmp_path`. La CLI et le hook passent `DEFAULT_ROOT` au moment de
l'appel.

---

# LOT 1 — Catalogue

## Task 1 : Index + slug (fondations)

**Files:**
- Create: `pipeline/clip_library.py`
- Modify: `.gitignore`
- Test: `pipeline/tests/test_clip_library.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Créer `pipeline/tests/test_clip_library.py` :

```python
from pathlib import Path

import pipeline.clip_library as cl


def test_load_index_missing_returns_empty_skeleton(tmp_path):
    data = cl.load_index(tmp_path)
    assert data == {"version": cl.INDEX_VERSION, "clips": []}


def test_save_then_load_roundtrip_sorted(tmp_path):
    cl.save_index(tmp_path, {"version": 1, "clips": [
        {"id": "zeta", "file": "clips/zeta.mp4", "tags": [], "description": "z"},
        {"id": "alpha", "file": "clips/alpha.mp4", "tags": [], "description": "a"},
    ]})
    data = cl.load_index(tmp_path)
    # persisté et trié par id
    assert [c["id"] for c in data["clips"]] == ["alpha", "zeta"]
    assert (tmp_path / "index.json").exists()


def test_slugify():
    assert cl.slugify("Flux de Données ! bleu") == "flux-de-donnees-bleu"
    assert cl.slugify("") == "clip"
```

- [ ] **Step 2 : Lancer les tests pour vérifier l'échec**

Run: `python -m pytest pipeline/tests/test_clip_library.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.clip_library'`

- [ ] **Step 3 : Écrire l'implémentation minimale**

Créer `pipeline/clip_library.py` :

```python
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
```

- [ ] **Step 4 : Lancer les tests pour vérifier le succès**

Run: `python -m pytest pipeline/tests/test_clip_library.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5 : Mettre à jour `.gitignore` (racine)**

Ajouter à la fin de `.gitignore` :

```
# Bibliothèque de clips : binaires locaux, index versionné
clip-library/clips/
clip-library/thumbs/
```

- [ ] **Step 6 : Commit**

```bash
git add pipeline/clip_library.py pipeline/tests/test_clip_library.py .gitignore
git commit -m "feat(clip-library): index load/save + slug + gitignore binaires"
```

---

## Task 2 : `add_clip` + vignette

**Files:**
- Modify: `pipeline/clip_library.py`
- Test: `pipeline/tests/test_clip_library.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Ajouter à `pipeline/tests/test_clip_library.py` :

```python
import pytest


@pytest.fixture
def fake_mp4(tmp_path):
    """Petit fichier factice tenant lieu de mp4 (on teste copie/index, pas l'encodage)."""
    src = tmp_path / "src.mp4"
    src.write_bytes(b"FAKEMP4DATA")
    return src


def test_add_clip_copies_and_registers(tmp_path, fake_mp4, monkeypatch):
    # ffmpeg indispo/simulé absent : l'entrée doit quand même être créée
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    root = tmp_path / "lib"
    entry = cl.add_clip(root, fake_mp4, ["flux-donnees", "bleu"], "Flux bleus",
                        model="kling-turbo", cost_usd=0.35)
    assert entry["id"] == "flux-bleus"
    assert (root / "clips" / "flux-bleus.mp4").read_bytes() == b"FAKEMP4DATA"
    assert entry["tags"] == ["flux-donnees", "bleu"]
    assert entry["model"] == "kling-turbo" and entry["cost_usd"] == 0.35
    assert "thumb" not in entry  # make_thumb a renvoyé False
    # présent dans l'index persisté
    assert [c["id"] for c in cl.load_index(root)["clips"]] == ["flux-bleus"]


def test_add_clip_idempotent_on_same_id(tmp_path, fake_mp4, monkeypatch):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    root = tmp_path / "lib"
    cl.add_clip(root, fake_mp4, ["a"], "desc 1", clip_id="fixe")
    cl.add_clip(root, fake_mp4, ["a", "b"], "desc 2", clip_id="fixe")
    clips = cl.load_index(root)["clips"]
    assert len(clips) == 1            # pas de doublon
    assert clips[0]["description"] == "desc 2"  # mis à jour
    assert clips[0]["tags"] == ["a", "b"]


def test_add_clip_auto_id_collision_suffix(tmp_path, fake_mp4, monkeypatch):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    root = tmp_path / "lib"
    a = cl.add_clip(root, fake_mp4, ["x"], "Même titre")
    b = cl.add_clip(root, fake_mp4, ["x"], "Même titre")
    assert a["id"] == "meme-titre"
    assert b["id"] == "meme-titre-02"  # suffixe anti-collision
    assert len(cl.load_index(root)["clips"]) == 2
```

- [ ] **Step 2 : Lancer les tests pour vérifier l'échec**

Run: `python -m pytest pipeline/tests/test_clip_library.py -k "add_clip" -v`
Expected: FAIL — `AttributeError: module 'pipeline.clip_library' has no attribute 'add_clip'`

- [ ] **Step 3 : Écrire l'implémentation minimale**

Ajouter à `pipeline/clip_library.py` :

```python
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
```

- [ ] **Step 4 : Lancer les tests pour vérifier le succès**

Run: `python -m pytest pipeline/tests/test_clip_library.py -v`
Expected: PASS (tous — 6 tests)

- [ ] **Step 5 : Commit**

```bash
git add pipeline/clip_library.py pipeline/tests/test_clip_library.py
git commit -m "feat(clip-library): add_clip idempotent + vignette ffmpeg best-effort"
```

---

## Task 3 : `search` + `get` + `reuse`

**Files:**
- Modify: `pipeline/clip_library.py`
- Test: `pipeline/tests/test_clip_library.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Ajouter à `pipeline/tests/test_clip_library.py` :

```python
def _seed(root, fake_mp4, monkeypatch):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    cl.add_clip(root, fake_mp4, ["flux-donnees", "bleu", "push-in"],
                "Flux bleus push-in", clip_id="a2")
    cl.add_clip(root, fake_mp4, ["flux-donnees"], "Flux simple", clip_id="a1")
    cl.add_clip(root, fake_mp4, ["logo", "sting"], "Logo sting", clip_id="b1")


def test_search_ranks_by_tag_overlap(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    res = cl.search(root, tags=["flux-donnees", "bleu"])
    ids = [c["id"] for c in res]
    assert ids == ["a2", "a1"]   # a2 (2 tags communs) avant a1 (1), b1 exclu


def test_search_by_text_substring(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    res = cl.search(root, text="sting")
    assert [c["id"] for c in res] == ["b1"]


def test_get(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    assert cl.get(root, "a1")["description"] == "Flux simple"
    assert cl.get(root, "inconnu") is None


def test_reuse_copies_file(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    out = tmp_path / "out.mp4"
    cl.reuse(root, "a1", out)
    assert out.read_bytes() == b"FAKEMP4DATA"


def test_reuse_unknown_raises(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    with pytest.raises(KeyError):
        cl.reuse(root, "inconnu", tmp_path / "x.mp4")
```

- [ ] **Step 2 : Lancer les tests pour vérifier l'échec**

Run: `python -m pytest pipeline/tests/test_clip_library.py -k "search or get or reuse" -v`
Expected: FAIL — `AttributeError: ... has no attribute 'search'`

- [ ] **Step 3 : Écrire l'implémentation minimale**

Ajouter à `pipeline/clip_library.py` :

```python
def search(root: Path, tags: list[str] | None = None,
           text: str | None = None) -> list[dict]:
    """Clips filtrés puis classés par recouvrement de tags (décroissant).

    - `tags` : ne garde que les clips avec ≥ 1 tag commun, triés par nb de tags communs.
    - `text` : sous-chaîne (insensible à la casse) dans description ou tags.
    Les deux filtres se combinent. Sans critère : tous les clips.
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
    """Copie le clip catalogué vers out_path. Lève KeyError si id inconnu."""
    entry = get(root, clip_id)
    if entry is None:
        raise KeyError(f"clip inconnu : {clip_id}")
    shutil.copyfile(Path(root) / entry["file"], out_path)
    logger.info("Clip réutilisé : %s -> %s", clip_id, out_path)
    return str(out_path)
```

- [ ] **Step 4 : Lancer les tests pour vérifier le succès**

Run: `python -m pytest pipeline/tests/test_clip_library.py -v`
Expected: PASS (11 tests)

- [ ] **Step 5 : Commit**

```bash
git add pipeline/clip_library.py pipeline/tests/test_clip_library.py
git commit -m "feat(clip-library): search par tags + get + reuse"
```

---

## Task 4 : CLI `add` / `ingest` / `search` / `list` / `show`

**Files:**
- Modify: `pipeline/clip_library.py`
- Test: `pipeline/tests/test_clip_library.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Ajouter à `pipeline/tests/test_clip_library.py` :

```python
def test_cli_add_then_search(tmp_path, fake_mp4, monkeypatch, capsys):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    monkeypatch.setattr(cl, "DEFAULT_ROOT", tmp_path / "lib")
    assert cl._main(["add", str(fake_mp4), "--tags", "flux-donnees,bleu",
                     "--desc", "Flux bleus"]) == 0
    capsys.readouterr()
    assert cl._main(["search", "flux"]) == 0
    out = capsys.readouterr().out
    assert "flux-bleus" in out


def test_cli_ingest_glob(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    monkeypatch.setattr(cl, "DEFAULT_ROOT", tmp_path / "lib")
    src = tmp_path / "src"
    src.mkdir()
    for name in ("a.mp4", "b.mp4"):
        (src / name).write_bytes(b"X")
    rc = cl._main(["ingest", str(src / "*.mp4"), "--tags", "abstrait-corporate"])
    assert rc == 0
    assert len(cl.load_index(tmp_path / "lib")["clips"]) == 2
```

- [ ] **Step 2 : Lancer les tests pour vérifier l'échec**

Run: `python -m pytest pipeline/tests/test_clip_library.py -k cli -v`
Expected: FAIL — `AttributeError: ... has no attribute '_main'`

- [ ] **Step 3 : Écrire l'implémentation minimale**

Ajouter à `pipeline/clip_library.py` (fin du fichier) :

```python
def _print_row(c: dict) -> None:
    print(f"{c['id']:<32} {c['file']:<40} {','.join(c['tags'])}")


def _main(argv: list[str]) -> int:
    import argparse
    import glob

    p = argparse.ArgumentParser(prog="clip_library",
                                description="Bibliothèque de clips réutilisables")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="cataloguer un clip")
    pa.add_argument("mp4")
    pa.add_argument("--tags", required=True, help="tags séparés par des virgules")
    pa.add_argument("--desc", required=True)
    pa.add_argument("--id", dest="clip_id", default=None)
    pa.add_argument("--model", default=None)
    pa.add_argument("--cost", dest="cost_usd", type=float, default=None)
    pa.add_argument("--origin", dest="origin_video", default=None)

    pi = sub.add_parser("ingest", help="importer en masse (glob) avec tags communs")
    pi.add_argument("globs", nargs="+")
    pi.add_argument("--tags", required=True)
    pi.add_argument("--desc", default="")

    ps = sub.add_parser("search", help="recherche texte (description/tags)")
    ps.add_argument("text")

    pl = sub.add_parser("list", help="lister (option filtre par tags)")
    pl.add_argument("--tags", default=None)

    psh = sub.add_parser("show", help="détail d'un clip")
    psh.add_argument("clip_id")

    args = p.parse_args(argv)
    root = DEFAULT_ROOT

    if args.cmd == "add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        entry = add_clip(root, args.mp4, tags, args.desc, clip_id=args.clip_id,
                         model=args.model, cost_usd=args.cost_usd,
                         origin_video=args.origin_video)
        print("OK", entry["id"])
        return 0

    if args.cmd == "ingest":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        files = [f for g in args.globs for f in sorted(glob.glob(g))]
        if not files:
            print("Aucun fichier ne correspond au(x) motif(s).")
            return 1
        for f in files:
            desc = args.desc or Path(f).stem
            add_clip(root, f, tags, desc)
        print(f"OK {len(files)} clip(s) catalogué(s).")
        return 0

    if args.cmd == "search":
        rows = search(root, text=args.text)
        for c in rows:
            _print_row(c)
        print(f"— {len(rows)} résultat(s)")
        return 0

    if args.cmd == "list":
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        rows = search(root, tags=tags) if tags else load_index(root)["clips"]
        for c in rows:
            _print_row(c)
        return 0

    if args.cmd == "show":
        entry = get(root, args.clip_id)
        if entry is None:
            print(f"clip inconnu : {args.clip_id}")
            return 1
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(_main(sys.argv[1:]))
```

- [ ] **Step 4 : Lancer les tests pour vérifier le succès**

Run: `python -m pytest pipeline/tests/test_clip_library.py -v`
Expected: PASS (13 tests)

- [ ] **Step 5 : Vérifier le nombre de lignes du module (< 300, charte)**

Run: `wc -l pipeline/clip_library.py`
Expected: < 300. Si dépassé, extraire la CLI dans `pipeline/clip_library_cli.py`.

- [ ] **Step 6 : Commit**

```bash
git add pipeline/clip_library.py pipeline/tests/test_clip_library.py
git commit -m "feat(clip-library): CLI add/ingest/search/list/show"
```

---

## Task 5 : Peupler le catalogue avec les clips existants

Action opérationnelle (pas de nouveau code) : ingérer les clips déjà produits pour que la
bibliothèque serve immédiatement. Les tags sont **manuels** — adapte-les au contenu réel.

**Files:**
- Modify: `clip-library/index.json` (généré, versionné)

- [ ] **Step 1 : Ingérer les clips `illus/` (mouvements abstraits corporate)**

Ces clips (`idea-1.mp4` … `idea-7.mp4`) sont des animations d'illustrations abstraites.
Cataloguer un par un avec des tags/desc spécifiques (exemple, à ajuster) :

```bash
python -m pipeline.clip_library add video-studio/public/illus/idea-3.mp4 \
  --tags "flux-donnees,abstrait-corporate,bleu,push-in" \
  --desc "Flux de données bleus convergents, push-in lent" \
  --model kling-turbo --origin ia-securite-illustree
```

Répéter pour chaque clip `illus/*.mp4` pertinent (tags propres à chacun).

- [ ] **Step 2 : Vérifier le catalogue**

Run: `python -m pipeline.clip_library list`
Expected: une ligne par clip ingéré (id · fichier · tags).

- [ ] **Step 3 : Vérifier que seuls l'index (et pas les binaires) est suivi**

Run: `git status --porcelain clip-library/`
Expected: `clip-library/index.json` apparaît ; `clips/` et `thumbs/` sont ignorés (absents).

- [ ] **Step 4 : Commit du catalogue initial**

```bash
git add clip-library/index.json
git commit -m "chore(clip-library): catalogue initial (clips illus existants)"
```

---

# LOT 2 — Hook `animate.py`

## Task 6 : Réutilisation avant appel fal (`reuse_tags`)

**Files:**
- Modify: `pipeline/animate.py` (fonction `animate_image`, en-tête du module)
- Test: `pipeline/tests/test_animate.py` (créer)

- [ ] **Step 1 : Écrire le test qui échoue**

Créer `pipeline/tests/test_animate.py` :

```python
from pathlib import Path

import pytest

import pipeline.animate as an
import pipeline.clip_library as cl


def test_reuse_tags_skips_fal(tmp_path, monkeypatch):
    # Bibliothèque avec un clip taggé
    root = tmp_path / "lib"
    src = tmp_path / "src.mp4"
    src.write_bytes(b"CLIPBYTES")
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    monkeypatch.setattr(cl, "DEFAULT_ROOT", root)
    cl.add_clip(root, src, ["flux-donnees", "bleu"], "Flux bleus",
                clip_id="ok", cost_usd=0.35)

    # Toute tentative d'appel réseau fal doit faire échouer le test
    def _boom(*a, **k):
        raise AssertionError("fal ne doit PAS être appelé quand un clip est réutilisé")
    monkeypatch.setattr(an.requests, "post", _boom)

    out = tmp_path / "out.mp4"
    # une image source bidon suffit : elle ne doit jamais être lue si réutilisation
    result = an.animate_image(tmp_path / "still.png", out,
                              reuse_tags=["flux-donnees"])
    assert Path(result) == out
    assert out.read_bytes() == b"CLIPBYTES"  # clip copié depuis la bibliothèque


def test_no_reuse_tags_still_calls_fal(tmp_path, monkeypatch):
    # Sans reuse_tags : comportement inchangé (on vérifie qu'on tente bien l'appel fal)
    monkeypatch.setenv("FAL_KEY", "k")
    called = {"post": False}

    def _fake_post(*a, **k):
        called["post"] = True
        raise RuntimeError("stop après soumission")  # on coupe court volontairement

    monkeypatch.setattr(an.requests, "post", _fake_post)
    (tmp_path / "still.png").write_bytes(b"\x89PNG\r\n")
    with pytest.raises(RuntimeError):
        an.animate_image(tmp_path / "still.png", tmp_path / "o.mp4")
    assert called["post"] is True
```

- [ ] **Step 2 : Lancer le test pour vérifier l'échec**

Run: `python -m pytest pipeline/tests/test_animate.py -v`
Expected: FAIL — `TypeError: animate_image() got an unexpected keyword argument 'reuse_tags'`

- [ ] **Step 3 : Écrire l'implémentation minimale**

Dans `pipeline/animate.py`, ajouter un logger sous les imports :

```python
import logging

logger = logging.getLogger(__name__)
```

Modifier la signature de `animate_image` pour ajouter `reuse_tags` :

```python
def animate_image(image_path: str, out_path: str, *, model: str = "kling-turbo",
                  prompt: str = DEFAULT_PROMPT, duration: int = 5,
                  key: str | None = None, poll_s: float = 5.0,
                  timeout_s: float = 600.0,
                  reuse_tags: list[str] | None = None) -> str:
```

Insérer le hook tout au début du corps de `animate_image`, **avant** la vérification
de `FAL_KEY` (docstring inchangée hormis la ligne ci-dessous à ajouter dans Args) :

```python
    # Réutilisation : si un clip taggé correspond, on le copie et on ÉVITE l'appel fal.
    if reuse_tags:
        from pipeline import clip_library
        root = clip_library.DEFAULT_ROOT
        matches = clip_library.search(root, tags=reuse_tags)
        if matches:
            best = matches[0]
            clip_library.reuse(root, best["id"], out_path)
            saved = best.get("cost_usd")
            logger.info("Clip réutilisé depuis la bibliothèque : %s (tags=%s)%s",
                        best["id"], best["tags"],
                        f" — ~{saved} $ économisés" if saved else "")
            return out_path
        logger.info("Aucun clip en bibliothèque pour tags=%s : génération fal.", reuse_tags)
```

Ajouter dans la docstring de `animate_image`, sous `key:` :

```
        reuse_tags: si fourni, réutilise un clip taggé de la bibliothèque (aucun appel
            fal) quand un match existe ; sinon génère normalement.
```

- [ ] **Step 4 : Lancer le test pour vérifier le succès**

Run: `python -m pytest pipeline/tests/test_animate.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5 : Non-régression complète**

Run: `python -m pytest pipeline/tests/ -v`
Expected: PASS (aucune régression sur les tests existants)

- [ ] **Step 6 : Commit**

```bash
git add pipeline/animate.py pipeline/tests/test_animate.py
git commit -m "feat(animate): réutilisation clip bibliothèque avant appel fal (reuse_tags)"
```

---

## Task 7 : Exposer `--reuse-tags` dans la CLI `animate`

**Files:**
- Modify: `pipeline/animate.py` (fonction `_main`)
- Test: `pipeline/tests/test_animate.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Ajouter à `pipeline/tests/test_animate.py` :

```python
def test_cli_parses_reuse_tags(tmp_path, monkeypatch):
    captured = {}

    def _fake_animate(image_path, out_path, **kwargs):
        captured.update(kwargs)
        Path(out_path).write_bytes(b"X")
        return out_path

    monkeypatch.setattr(an, "animate_image", _fake_animate)
    rc = an._main([str(tmp_path / "img.png"), str(tmp_path / "o.mp4"),
                   "--reuse-tags", "flux-donnees,bleu"])
    assert rc == 0
    assert captured["reuse_tags"] == ["flux-donnees", "bleu"]
```

- [ ] **Step 2 : Lancer le test pour vérifier l'échec**

Run: `python -m pytest pipeline/tests/test_animate.py -k reuse_tags -v`
Expected: FAIL — `reuse_tags` absent de `captured` (KeyError).

- [ ] **Step 3 : Écrire l'implémentation minimale**

Dans `pipeline/animate.py`, modifier la boucle de parsing de `_main` pour reconnaître
`--reuse-tags` et le passer à `animate_image`. Remplacer le corps de `_main` par :

```python
def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    image_path, out_path = argv[0], argv[1]
    model, prompt, reuse_tags = "kling-turbo", DEFAULT_PROMPT, None
    i = 2
    while i < len(argv):
        if argv[i] == "--model":
            model = argv[i + 1]; i += 2
        elif argv[i] == "--prompt":
            prompt = argv[i + 1]; i += 2
        elif argv[i] == "--reuse-tags":
            reuse_tags = [t.strip() for t in argv[i + 1].split(",") if t.strip()]
            i += 2
        else:
            i += 1
    out = animate_image(image_path, out_path, model=model, prompt=prompt,
                        reuse_tags=reuse_tags)
    print("OK", out, os.path.getsize(out), "octets")
    return 0
```

- [ ] **Step 4 : Lancer les tests pour vérifier le succès**

Run: `python -m pytest pipeline/tests/test_animate.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5 : Mettre à jour le docstring d'usage du module**

Dans l'en-tête de `pipeline/animate.py`, compléter la ligne `Usage` :

```
Usage : python -m pipeline.animate <image.png> <sortie.mp4> [--model kling|hailuo|luma|wan] [--prompt "..."] [--reuse-tags a,b,c]
```

- [ ] **Step 6 : Non-régression complète**

Run: `python -m pytest pipeline/tests/ -v`
Expected: PASS (suite complète)

- [ ] **Step 7 : Commit**

```bash
git add pipeline/animate.py pipeline/tests/test_animate.py
git commit -m "feat(animate): flag CLI --reuse-tags"
```

---

## Vérification finale (Lot 1 + Lot 2)

- [ ] Suite complète verte : `python -m pytest pipeline/tests/ -v`
- [ ] `wc -l pipeline/clip_library.py` < 300 (charte).
- [ ] `git status` : `clip-library/clips/` et `thumbs/` ignorés ; `index.json` versionné.
- [ ] Essai bout-en-bout : `python -m pipeline.animate <still.png> /tmp/o.mp4 --reuse-tags flux-donnees` réutilise un clip catalogué sans appel fal (log « Clip réutilisé »).
