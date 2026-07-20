# Phase 2 — Tranche 1 : Pipeline YouTube → curation → draft validé — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Détecter automatiquement les nouvelles vidéos YouTube suivies, en proposer 3-5 idées de publication classées par pilier sur Telegram, et produire un draft validé prêt à copier-coller.

**Architecture:** Approche hybride avec file. Un script `youtube_monitor.py` (cron, résumé Gemini économique) écrit les opportunités dans `briefs/incoming/`. Un `orchestrator.py` appelle l'agent Claude Code `editorial-curator` pour produire 3-5 idées (`briefs/proposals/latest.json`), les envoie sur Telegram via `hermes send`, puis archive les items traités. Le choix d'une idée est résolu par `editorial-writer` (réutilisé, V1) via une règle ajoutée au `SOUL.md`.

**Tech Stack:** Python 3.12 (requests, feedparser, python-dotenv, pytest), agents Claude Code (markdown + JSON), Hermes gateway (Telegram + cron), OpenRouter Gemini Flash (résumé).

---

## Conventions de test
- Tous les tests tournent depuis `pipeline/` avec le venv `pipeline/.venv`.
- **Aucun appel réseau réel dans les tests** : RSS et appels LLM sont injectés/mockés. Les fonctions pures (filtrage, dédup, formatage, I/O fichier) sont testées ; les appels externes sont des fonctions fines isolées.
- Données runtime écrites dans un `tmp_path` pytest, jamais dans le vrai profil.

---

### Task 1 : Définir les 5 piliers (source de vérité)

**Files:**
- Create: `Hermes social media/philosophy/pillars.md`

- [ ] **Step 1 : Écrire le fichier des piliers**

Créer `Hermes social media/philosophy/pillars.md` avec exactement ce contenu :

```markdown
# Piliers de marque — Abdelilah Kahaji
Version : 1.0

> Source de vérité partagée par `editorial-curator` (classement/équilibrage) et `editorial-writer` (ton).
> La pondération s'applique **dans la durée**, pas à chaque run.

| # | Pilier | Poids | Exemples / mots-clés |
|---|--------|-------|----------------------|
| 1 | IA appliquée | 35% | Claude Code, agents IA, GPT, Gemini, automatisation, MCP, n8n |
| 2 | Transformation numérique industrielle | 25% | ERP, digitalisation, industrie, pêche, PME |
| 3 | Coulisses OmegaSoft (sans confidentiel) | 20% | « automatisé un déploiement qui prenait 2h » |
| 4 | Enseignement | 10% | séances ENSA |
| 5 | Vision | 10% | « pourquoi les PME marocaines doivent adopter les agents IA » |

## Règles d'usage
- Chaque idée proposée est rattachée à **un** pilier (le plus pertinent).
- L'équilibrage vise la pondération ci-dessus sur ~2 semaines glissantes, en s'appuyant sur l'historique `decisions.jsonl`.
- Pilier 3 : jamais de nom de client, de chiffre d'affaires ni de détail interne (niveau `prudent`).
```

- [ ] **Step 2 : Vérifier le rendu**

Run: `sed -n '1,8p' "Hermes social media/philosophy/pillars.md"`
Expected: l'en-tête et le début du tableau s'affichent.

- [ ] **Step 3 : Commit**

```bash
git add "Hermes social media/philosophy/pillars.md"
git commit -m "feat(social-media): pillars.md — 5 piliers de marque (source de vérité)"
```

---

### Task 2 : Scaffold du pipeline + venv + pytest

**Files:**
- Create: `pipeline/requirements.txt`
- Create: `pipeline/__init__.py`
- Create: `pipeline/tests/__init__.py`
- Create: `pipeline/tests/conftest.py`
- Create: `pipeline/.gitignore`

- [ ] **Step 1 : Déclarer les dépendances**

Create `pipeline/requirements.txt`:

```
requests>=2.31
feedparser>=6.0
python-dotenv>=1.0
pytest>=8.0
```

- [ ] **Step 2 : Créer les packages**

Create `pipeline/__init__.py` (vide) et `pipeline/tests/__init__.py` (vide).

- [ ] **Step 3 : Ignorer le venv et les artefacts**

Create `pipeline/.gitignore`:

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 4 : conftest commun**

Create `pipeline/tests/conftest.py`:

```python
import json
from pathlib import Path
import pytest


@pytest.fixture
def briefs_dir(tmp_path: Path) -> Path:
    """Arborescence briefs/ isolée pour les tests."""
    for sub in ("incoming", "processed", "proposals"):
        (tmp_path / sub).mkdir(parents=True)
    return tmp_path


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
```

- [ ] **Step 5 : Créer le venv et installer**

Run:
```bash
cd pipeline && python3 -m venv .venv && ./.venv/bin/pip install -q -r requirements.txt && ./.venv/bin/pytest --version
```
Expected: affiche la version de pytest (ex. `pytest 8.x`).

- [ ] **Step 6 : Commit**

```bash
git add pipeline/requirements.txt pipeline/__init__.py pipeline/tests/__init__.py pipeline/tests/conftest.py pipeline/.gitignore
git commit -m "chore(pipeline): scaffold venv + pytest"
```

---

### Task 3 : youtube_monitor — fonctions pures (TDD)

**Files:**
- Create: `pipeline/youtube_monitor.py`
- Test: `pipeline/tests/test_youtube_monitor.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Create `pipeline/tests/test_youtube_monitor.py`:

```python
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

from pipeline.youtube_monitor import (
    is_recent,
    select_new_videos,
    make_incoming_item,
    write_incoming_item,
)


def _rfc822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def test_is_recent_true_for_now():
    now = datetime.now(timezone.utc)
    assert is_recent(_rfc822(now), hours=25) is True


def test_is_recent_false_for_old():
    old = datetime.now(timezone.utc) - timedelta(hours=48)
    assert is_recent(_rfc822(old), hours=25) is False


def test_select_new_videos_filters_seen_and_old():
    now = datetime.now(timezone.utc)
    videos = [
        {"id": "v1", "titre": "A", "url": "u1", "description": "d", "publie_le": _rfc822(now)},
        {"id": "v2", "titre": "B", "url": "u2", "description": "d", "publie_le": _rfc822(now)},
        {"id": "v3", "titre": "C", "url": "u3", "description": "d",
         "publie_le": _rfc822(now - timedelta(hours=48))},
    ]
    seen = {"v1": {}}
    result = select_new_videos(videos, seen, hours=25)
    ids = [v["id"] for v in result]
    assert ids == ["v2"]  # v1 déjà vu, v3 trop ancien


def test_make_incoming_item_shape():
    video = {"id": "v9", "titre": "T", "url": "https://youtu.be/v9",
             "description": "desc", "publie_le": "Sat, 28 Jun 2026 07:00:00 +0000"}
    item = make_incoming_item(video, chaine="@nateherk", resume_fr="résumé",
                              detecte_le="2026-06-28T07:30:00")
    assert item == {
        "source": "youtube",
        "video_id": "v9",
        "chaine": "@nateherk",
        "titre": "T",
        "url": "https://youtu.be/v9",
        "publie_le": "Sat, 28 Jun 2026 07:00:00 +0000",
        "resume_fr": "résumé",
        "detecte_le": "2026-06-28T07:30:00",
    }


def test_write_incoming_item_creates_file(briefs_dir: Path):
    item = {"video_id": "v9", "titre": "T"}
    path = write_incoming_item(item, briefs_dir / "incoming")
    assert path.name == "v9.json"
    assert json.loads(path.read_text(encoding="utf-8"))["titre"] == "T"
```

- [ ] **Step 2 : Lancer les tests (échec attendu)**

Run: `cd pipeline && ./.venv/bin/pytest tests/test_youtube_monitor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.youtube_monitor'` (ou ImportError).

- [ ] **Step 3 : Implémenter les fonctions pures**

Create `pipeline/youtube_monitor.py`:

```python
#!/usr/bin/env python3
"""YouTube Monitor — détecte les nouvelles vidéos suivies et écrit des
opportunités dans briefs/incoming/. Résumé via OpenRouter Gemini (économique).

Adapté de la version V1 (profil) : le routage personnel/OmegaSoft est retiré
(remplacé par le classement par pilier en aval, dans editorial-curator).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
import requests

OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def is_recent(published_str: str, hours: int = 25) -> bool:
    """True si la vidéo a été publiée dans les `hours` dernières heures."""
    if not published_str:
        return False
    try:
        pub_dt = parsedate_to_datetime(published_str)
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return pub_dt > cutoff
    except (TypeError, ValueError):
        return True  # parsing impossible → inclure par sécurité


def select_new_videos(videos: list[dict], seen: dict, hours: int = 25) -> list[dict]:
    """Garde les vidéos non vues et récentes."""
    result = []
    for v in videos:
        vid = v.get("id")
        if not vid or vid in seen:
            continue
        if not is_recent(v.get("publie_le", ""), hours=hours):
            continue
        result.append(v)
    return result


def make_incoming_item(video: dict, chaine: str, resume_fr: str, detecte_le: str) -> dict:
    """Façonne un item d'opportunité pour briefs/incoming/."""
    return {
        "source": "youtube",
        "video_id": video["id"],
        "chaine": chaine,
        "titre": video["titre"],
        "url": video["url"],
        "publie_le": video["publie_le"],
        "resume_fr": resume_fr,
        "detecte_le": detecte_le,
    }


def write_incoming_item(item: dict, incoming_dir: Path) -> Path:
    """Écrit l'item dans incoming/<video_id>.json et retourne le chemin."""
    incoming_dir = Path(incoming_dir)
    incoming_dir.mkdir(parents=True, exist_ok=True)
    path = incoming_dir / f"{item['video_id']}.json"
    path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def fetch_rss(channel_id: str) -> list[dict]:
    """Récupère les vidéos via le flux RSS YouTube (appel réseau, non testé)."""
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    videos = []
    for entry in feed.entries:
        videos.append({
            "id": entry.get("yt_videoid", entry.get("id", "")),
            "titre": entry.get("title", ""),
            "url": entry.get("link", ""),
            "description": entry.get("summary", "")[:500],
            "publie_le": entry.get("published", ""),
        })
    return videos


def summarize_with_gemini(chaine: str, titre: str, description: str, api_key: str) -> str:
    """Résumé FR court via OpenRouter Gemini (appel réseau, non testé)."""
    if not api_key:
        return "⚠️ Clé OpenRouter manquante — résumé non généré"
    prompt = (
        "Tu es l'assistant éditorial de M. Abdelilah Kahaji (expert IA, consultant "
        "ERP/Odoo).\n"
        f"Nouvelle vidéo YouTube de {chaine} :\nTitre : {titre}\nDescription : {description}\n\n"
        "En 3-4 phrases en français : (1) résume le sujet, (2) indique sa pertinence pour "
        "un expert IA / dirigeant d'ESN, (3) suggère un angle de contenu. Sois concis."
    )
    resp = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": OPENROUTER_MODEL,
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 300, "temperature": 0.3},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
```

- [ ] **Step 4 : Lancer les tests (succès attendu)**

Run: `cd pipeline && ./.venv/bin/pytest tests/test_youtube_monitor.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5 : Commit**

```bash
git add pipeline/youtube_monitor.py pipeline/tests/test_youtube_monitor.py
git commit -m "feat(pipeline): youtube_monitor — détection + écriture incoming (TDD)"
```

---

### Task 4 : youtube_monitor — config chaînes + main exécutable

**Files:**
- Create: `pipeline/config.py`
- Modify: `pipeline/youtube_monitor.py` (ajout `load_seen`, `save_seen`, `main`)
- Test: `pipeline/tests/test_config.py`

- [ ] **Step 1 : Test de la config**

Create `pipeline/tests/test_config.py`:

```python
from pipeline.config import CHANNELS, KNOWN_IDS, IDEAS_PER_RUN


def test_channels_have_known_ids():
    for handle in CHANNELS:
        assert handle in KNOWN_IDS and KNOWN_IDS[handle], f"id manquant pour {handle}"


def test_ideas_per_run_range():
    assert IDEAS_PER_RUN == (3, 5)
```

- [ ] **Step 2 : Lancer (échec attendu)**

Run: `cd pipeline && ./.venv/bin/pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.config'`.

- [ ] **Step 3 : Écrire la config**

Create `pipeline/config.py`:

```python
"""Paramètres du pipeline (chaînes, cadence, nombre d'idées).
À revalider avec Abdelilah avant le premier run réel.
"""

# handle YouTube → channel_id (résolu une fois, hardcodé pour éviter yt-dlp)
KNOWN_IDS = {
    "@nateherk": "UCBcRF18a7Qf58cCRy5xuWwQ",
    "@adev_cpl": "UCnXNIFvxP_x_LnJQNlOJFBg",
    "@ParlonsIATech": "UCBt6l-PqxDKVHcBTuEZASpw",
    "@Shubham_Sharma": "UCIz_lJqEoBT_yFxl0Y8HIEQ",
}

# Chaînes suivies (orientées IA/tech → pilier 1 majoritaire)
CHANNELS = list(KNOWN_IDS.keys())

# Nombre d'idées proposées par run (min, max)
IDEAS_PER_RUN = (3, 5)

# Fenêtre de récence RSS (heures)
RECENCY_HOURS = 25
```

- [ ] **Step 4 : Lancer (succès attendu)**

Run: `cd pipeline && ./.venv/bin/pytest tests/test_config.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5 : Ajouter load/save seen + main à youtube_monitor.py**

Append à `pipeline/youtube_monitor.py` :

```python
def load_seen(path: Path) -> dict:
    path = Path(path)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_seen(seen: dict, path: Path) -> None:
    Path(path).write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    """Exécution réelle : RSS → résumé → écriture incoming. Retourne le nb d'items écrits."""
    from dotenv import load_dotenv
    from pipeline.config import CHANNELS, KNOWN_IDS, RECENCY_HOURS

    load_dotenv("/opt/hermes/data/.env")
    load_dotenv("/opt/hermes/data/profiles/social-media/config/.env")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    base = Path(os.environ.get("HERMES_PROFILE",
               "/opt/hermes/data/profiles/social-media"))
    incoming = base / "briefs" / "incoming"
    seen_path = base / "scripts" / "seen_videos.json"
    seen_path.parent.mkdir(parents=True, exist_ok=True)

    seen = load_seen(seen_path)
    now_iso = datetime.now().isoformat(timespec="seconds")
    written = 0

    for handle in CHANNELS:
        channel_id = KNOWN_IDS.get(handle)
        if not channel_id:
            continue
        for v in select_new_videos(fetch_rss(channel_id), seen, hours=RECENCY_HOURS):
            resume = summarize_with_gemini(handle, v["titre"], v["description"], api_key)
            item = make_incoming_item(v, handle, resume, now_iso)
            write_incoming_item(item, incoming)
            seen[v["id"]] = {"titre": v["titre"], "chaine": handle, "vu_le": now_iso}
            written += 1

    save_seen(seen, seen_path)
    print(f"[youtube_monitor] {written} nouvelle(s) opportunité(s) écrite(s) dans {incoming}")
    return written


if __name__ == "__main__":
    raise SystemExit(0 if main() >= 0 else 1)
```

- [ ] **Step 6 : Lancer toute la suite**

Run: `cd pipeline && ./.venv/bin/pytest -v`
Expected: PASS (7 tests : 5 monitor + 2 config).

- [ ] **Step 7 : Commit**

```bash
git add pipeline/config.py pipeline/tests/test_config.py pipeline/youtube_monitor.py
git commit -m "feat(pipeline): config chaînes + main monitor (écrit briefs/incoming)"
```

---

### Task 5 : Agent editorial-curator + vérification d'intégration

**Files:**
- Create: `.claude/agents/editorial-curator.md`

- [ ] **Step 1 : Écrire l'agent**

Create `.claude/agents/editorial-curator.md`:

```markdown
---
name: editorial-curator
description: Analyse les opportunités détectées (file briefs/incoming/) et propose 3 à 5 idées de publication classées par pilier de marque, équilibrées selon la pondération, pour qu'Abdelilah en choisisse une. Lecture seule, sortie JSON.
tools: Read, Glob, Grep
---

Tu es le **curateur éditorial** d'Abdelilah Kahaji (OmegaSoft, ESN Agadir, secteur pêche).
À partir des opportunités détectées, tu proposes un **choix d'idées** ; tu ne rédiges pas les posts (c'est le rôle de `editorial-writer`).

## Entrée
- Les opportunités détectées, fournies **dans le prompt** (liste JSON d'items : source, titre, url, resume_fr, chaine…).
- Les 5 piliers : `philosophy/pillars.md` (lis-le, relatif à ton dossier de travail).
- L'historique récent : `memory/decisions.jsonl` (s'il existe) — pour équilibrer les piliers et éviter de répéter des sujets récents.

## Ce que tu produis
**3 à 5 idées** de publication, chacune rattachée à UN pilier, en visant l'équilibre de pondération (35/25/20/10/10) sur la durée — pas forcément à chaque run.

## Règles
- Ne jamais inventer de faits : une idée s'appuie sur une opportunité réelle de `incoming/`.
- Niveau `prudent` par défaut : aucun nom de client, chiffre d'affaires ou détail interne.
- Si `incoming/` est vide, renvoie `idees: []` et explique-le dans `equilibrage`.

## Sortie OBLIGATOIRE
Un **unique bloc JSON final** (rien après), au format :

```json
{
  "date": "AAAA-MM-JJ",
  "idees": [
    {
      "id": "idee-1",
      "pilier": 1,
      "titre": "pitch court de l'idée",
      "angle": "pourquoi c'est pertinent maintenant",
      "plateformes_suggerees": ["linkedin", "x"],
      "source": {"type": "youtube", "url": "...", "chaine": "@..."},
      "confidentialite": "public"
    }
  ],
  "equilibrage": "note sur la pondération des piliers respectée",
  "recommandation": {"id": "idee-1", "pourquoi": "justification courte"}
}
```
```

- [ ] **Step 2 : Vérifier que l'agent produit un JSON valide (items inline)**

Run (depuis la racine du repo, où l'agent est découvert via `.claude/agents/` et `philosophy/pillars.md` est lisible) :
```bash
claude -p 'Voici les opportunités détectées (JSON) :
[{"source":"youtube","video_id":"vtest","chaine":"@nateherk","titre":"Building agents with Claude Code","url":"https://youtu.be/vtest","resume_fr":"Comment orchestrer des agents avec Claude Code et MCP pour automatiser des tâches."}]
Lis "Hermes social media/philosophy/pillars.md" et propose 3-5 idées. Pas d historique.' \
  --agent editorial-curator --permission-mode dontAsk --max-turns 6 \
  2>/dev/null | sed -n '/^```json/,/^```/p' | sed '1d;$d' | python3 -m json.tool
```
Expected: un JSON valide avec `idees` (1 à 5 entrées), chaque idée ayant `pilier`, `titre`, `source`. (Avec une seule opportunité, 1-2 idées sont acceptables.)

> Note : si l'environnement n'a pas accès à `claude` ici, cette vérification est faite à l'étape de déploiement (Task 9) sur le serveur Hermes avec `HOME=/opt/hermes` et `cwd=workspace/editorial`.

- [ ] **Step 4 : Commit**

```bash
git add .claude/agents/editorial-curator.md
git commit -m "feat(social-media): agent editorial-curator (3-5 idées par pilier)"
```

---

### Task 6 : orchestrator — fonctions pures (TDD)

**Files:**
- Create: `pipeline/orchestrator.py`
- Test: `pipeline/tests/test_orchestrator.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Create `pipeline/tests/test_orchestrator.py`:

```python
import json
from pathlib import Path

from pipeline.orchestrator import (
    load_incoming,
    render_proposal_message,
    write_proposals,
    archive_processed,
)


def _write(path: Path, obj: dict):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def test_load_incoming_reads_all_items(briefs_dir: Path):
    _write(briefs_dir / "incoming" / "a.json", {"video_id": "a", "titre": "A"})
    _write(briefs_dir / "incoming" / "b.json", {"video_id": "b", "titre": "B"})
    items = load_incoming(briefs_dir / "incoming")
    titres = sorted(i["titre"] for i in items)
    assert titres == ["A", "B"]


def test_load_incoming_empty(briefs_dir: Path):
    assert load_incoming(briefs_dir / "incoming") == []


def test_render_proposal_message_numbers_ideas():
    proposals = {"idees": [
        {"id": "idee-1", "pilier": 1, "titre": "Orchestrer des agents"},
        {"id": "idee-2", "pilier": 5, "titre": "Pourquoi les PME marocaines"},
    ], "recommandation": {"id": "idee-1", "pourquoi": "fort sur LinkedIn"}}
    msg = render_proposal_message(proposals)
    assert "1." in msg and "2." in msg
    assert "Orchestrer des agents" in msg
    assert "Pourquoi les PME marocaines" in msg
    assert "recommand" in msg.lower()


def test_render_proposal_message_empty():
    msg = render_proposal_message({"idees": []})
    assert "aucune" in msg.lower()


def test_write_proposals_creates_dated_and_latest(briefs_dir: Path):
    proposals = {"date": "2026-06-28", "idees": [{"id": "idee-1"}]}
    dated, latest = write_proposals(proposals, briefs_dir / "proposals", date="2026-06-28")
    assert dated.name == "2026-06-28.json"
    assert latest.name == "latest.json"
    assert json.loads(latest.read_text(encoding="utf-8"))["date"] == "2026-06-28"


def test_archive_processed_moves_files(briefs_dir: Path):
    src = briefs_dir / "incoming" / "a.json"
    _write(src, {"video_id": "a"})
    archive_processed(["a"], briefs_dir / "incoming", briefs_dir / "processed")
    assert not src.exists()
    assert (briefs_dir / "processed" / "a.json").exists()
```

- [ ] **Step 2 : Lancer (échec attendu)**

Run: `cd pipeline && ./.venv/bin/pytest tests/test_orchestrator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.orchestrator'`.

- [ ] **Step 3 : Implémenter les fonctions pures**

Create `pipeline/orchestrator.py`:

```python
#!/usr/bin/env python3
"""Orchestrateur : incoming → editorial-curator → proposals → Telegram → archive.

Les fonctions pures (I/O fichier, formatage) sont testées. Les appels externes
(claude -p, hermes send) sont isolés dans des fonctions fines.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def load_incoming(incoming_dir: Path) -> list[dict]:
    """Charge tous les items JSON de briefs/incoming/."""
    incoming_dir = Path(incoming_dir)
    if not incoming_dir.exists():
        return []
    items = []
    for path in sorted(incoming_dir.glob("*.json")):
        try:
            items.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return items


def render_proposal_message(proposals: dict) -> str:
    """Message Telegram numéroté à partir des idées proposées."""
    idees = proposals.get("idees", [])
    if not idees:
        return "🟡 Aucune idée de publication aujourd'hui (pas de nouvelle source pertinente)."
    lines = ["💡 *Idées de publication du jour* — réponds avec un numéro :", ""]
    for i, idee in enumerate(idees, start=1):
        lines.append(f"{i}. [P{idee.get('pilier','?')}] {idee.get('titre','(sans titre)')}")
    reco = proposals.get("recommandation") or {}
    if reco.get("id"):
        lines += ["", f"⭐ Recommandé : {reco['id']} — {reco.get('pourquoi','')}"]
    return "\n".join(lines)


def write_proposals(proposals: dict, proposals_dir: Path, date: str) -> tuple[Path, Path]:
    """Écrit proposals/<date>.json et proposals/latest.json."""
    proposals_dir = Path(proposals_dir)
    proposals_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(proposals, ensure_ascii=False, indent=2)
    dated = proposals_dir / f"{date}.json"
    latest = proposals_dir / "latest.json"
    dated.write_text(payload, encoding="utf-8")
    latest.write_text(payload, encoding="utf-8")
    return dated, latest


def archive_processed(video_ids: list[str], incoming_dir: Path, processed_dir: Path) -> None:
    """Déplace incoming/<id>.json → processed/<id>.json."""
    incoming_dir, processed_dir = Path(incoming_dir), Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    for vid in video_ids:
        src = incoming_dir / f"{vid}.json"
        if src.exists():
            shutil.move(str(src), str(processed_dir / f"{vid}.json"))
```

- [ ] **Step 4 : Lancer (succès attendu)**

Run: `cd pipeline && ./.venv/bin/pytest tests/test_orchestrator.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5 : Commit**

```bash
git add pipeline/orchestrator.py pipeline/tests/test_orchestrator.py
git commit -m "feat(pipeline): orchestrator — fonctions pures (load/render/write/archive) TDD"
```

---

### Task 7 : orchestrator — intégration curator + envoi Telegram

**Files:**
- Modify: `pipeline/orchestrator.py` (ajout `call_curator`, `send_telegram`, `main`)
- Test: `pipeline/tests/test_orchestrator_main.py`

- [ ] **Step 1 : Test du main avec curator/telegram mockés**

Create `pipeline/tests/test_orchestrator_main.py`:

```python
import json
from pathlib import Path

import pipeline.orchestrator as orch


def test_main_writes_proposals_and_archives(briefs_dir: Path, monkeypatch):
    # une opportunité en file
    (briefs_dir / "incoming" / "v1.json").write_text(
        json.dumps({"video_id": "v1", "titre": "T", "url": "u", "chaine": "@x"}),
        encoding="utf-8")

    # curator mocké → renvoie 1 idée
    def fake_curator(workspace, items):
        return {"date": "2026-06-28",
                "idees": [{"id": "idee-1", "pilier": 1, "titre": "T",
                           "source": {"type": "youtube", "url": "u"}}],
                "recommandation": {"id": "idee-1", "pourquoi": "ok"}}

    sent = {}
    def fake_send(text):
        sent["text"] = text

    monkeypatch.setattr(orch, "call_curator", fake_curator)
    monkeypatch.setattr(orch, "send_telegram", fake_send)

    n = orch.main(base=briefs_dir.parent, workspace="/unused", date="2026-06-28",
                  briefs_root=briefs_dir)

    assert n == 1
    assert "1." in sent["text"]
    assert (briefs_dir / "proposals" / "latest.json").exists()
    # l'item a été archivé
    assert (briefs_dir / "processed" / "v1.json").exists()
    assert not (briefs_dir / "incoming" / "v1.json").exists()


def test_main_no_incoming_skips_send(briefs_dir: Path, monkeypatch):
    called = {"send": False}
    monkeypatch.setattr(orch, "call_curator", lambda *a, **k: {"idees": []})
    monkeypatch.setattr(orch, "send_telegram",
                        lambda text: called.__setitem__("send", True))
    n = orch.main(base=briefs_dir.parent, workspace="/unused", date="2026-06-28",
                  briefs_root=briefs_dir)
    assert n == 0
    assert called["send"] is False  # rien à envoyer si file vide
```

- [ ] **Step 2 : Lancer (échec attendu)**

Run: `cd pipeline && ./.venv/bin/pytest tests/test_orchestrator_main.py -v`
Expected: FAIL — `AttributeError: module 'pipeline.orchestrator' has no attribute 'call_curator'`.

- [ ] **Step 3 : Ajouter call_curator, send_telegram, main**

Append à `pipeline/orchestrator.py` :

```python
def _extract_json_block(text: str) -> dict:
    """Extrait le dernier bloc ```json ... ``` de la sortie de l'agent."""
    start = text.rfind("```json")
    if start == -1:
        raise ValueError("Aucun bloc JSON dans la sortie du curator")
    body = text[start + len("```json"):]
    end = body.find("```")
    return json.loads(body[:end if end != -1 else None])


def call_curator(workspace: str, items: list[dict]) -> dict:
    """Appelle l'agent editorial-curator via Claude Code (HOME=/opt/hermes requis).

    Les opportunités sont passées DANS le prompt (découplage des chemins). L'agent
    lit pillars.md et decisions.jsonl relativement à `workspace` (workspace/editorial).
    """
    import os
    prompt = (
        "Voici les opportunités détectées (JSON) :\n"
        + json.dumps(items, ensure_ascii=False)
        + "\nLis 'philosophy/pillars.md' et, si présent, 'memory/decisions.jsonl'. "
        "Propose 3-5 idées classées par pilier."
    )
    cmd = ["claude", "-p", prompt, "--agent", "editorial-curator",
           "--permission-mode", "dontAsk", "--max-turns", "6"]
    out = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True,
                         timeout=300, env={**os.environ, "HOME": "/opt/hermes"})
    return _extract_json_block(out.stdout)


def send_telegram(text: str) -> None:
    """Envoie un message sur le canal Telegram du profil via `hermes send`."""
    subprocess.run(
        ["hermes", "--profile", "social-media", "send", "--platform", "telegram", text],
        env={**__import__("os").environ, "HOME": "/opt/hermes",
             "HERMES_HOME": "/opt/hermes/data"},
        timeout=60, check=False,
    )


def main(base: Path, workspace: str, date: str, briefs_root: Path | None = None) -> int:
    """Pipeline complet. Retourne le nombre d'idées proposées."""
    base = Path(base)
    briefs = Path(briefs_root) if briefs_root else base / "briefs"
    incoming, processed, proposals_dir = (
        briefs / "incoming", briefs / "processed", briefs / "proposals")

    items = load_incoming(incoming)
    if not items:
        print("[orchestrator] file incoming vide — rien à proposer")
        return 0

    proposals = call_curator(workspace, items)
    write_proposals(proposals, proposals_dir, date=date)

    idees = proposals.get("idees", [])
    if idees:
        send_telegram(render_proposal_message(proposals))

    archive_processed([it["video_id"] for it in items if it.get("video_id")],
                      incoming, processed)
    print(f"[orchestrator] {len(idees)} idée(s) proposée(s) pour le {date}")
    return len(idees)
```

- [ ] **Step 4 : Lancer toute la suite**

Run: `cd pipeline && ./.venv/bin/pytest -v`
Expected: PASS (15 tests : 5 monitor + 2 config + 6 orchestrator + 2 orchestrator_main).

- [ ] **Step 5 : Créer l'entrée cron quotidienne**

Create `pipeline/run_daily.py`:

```python
#!/usr/bin/env python3
"""Entrée cron quotidienne : détection (monitor) puis curation+proposition (orchestrator)."""
from datetime import datetime
from pathlib import Path

from pipeline.youtube_monitor import main as monitor_main
from pipeline.orchestrator import main as orchestrate_main

PROFILE = Path("/opt/hermes/data/profiles/social-media")
WORKSPACE = PROFILE / "workspace" / "editorial"


def run() -> int:
    monitor_main()
    today = datetime.now().strftime("%Y-%m-%d")
    return orchestrate_main(base=PROFILE, workspace=str(WORKSPACE), date=today)


if __name__ == "__main__":
    raise SystemExit(0 if run() >= 0 else 1)
```

- [ ] **Step 6 : Vérifier l'import (pas d'exécution réseau)**

Run: `cd pipeline && ./.venv/bin/python -c "import pipeline.run_daily; print('import OK')"`
Expected: `import OK`.

- [ ] **Step 7 : Commit**

```bash
git add pipeline/orchestrator.py pipeline/tests/test_orchestrator_main.py pipeline/run_daily.py
git commit -m "feat(pipeline): orchestrator main + run_daily (cron) — curator + Telegram + archive"
```

---

### Task 8 : Règle de résolution du choix (SOUL.md) + déploiement

**Files:**
- Modify: `deploy/SOUL.md`
- Modify: `deploy.sh`

- [ ] **Step 1 : Ajouter la règle de choix au SOUL opératif**

Dans `deploy/SOUL.md`, après la section « ## Workflow V1 (...) », insérer cette nouvelle section :

```markdown
## Curation automatique (Phase 2 — YouTube)
Chaque matin, l'orchestrateur t'envoie sur Telegram une liste numérotée d'idées (issues de `editorial-curator`).
Quand Abdelilah **répond par un numéro** (ou « idée N ») :
1. Lis `briefs/proposals/latest.json` et prends l'idée à l'index correspondant (1 = première).
2. Construis le brief V1 à partir de cette idée (titre, angle, plateformes suggérées, source, confidentialité) et **délègue à `editorial-writer`** (même invocation que la V1).
3. Présente les variantes, attends la validation, puis journalise dans `memory/decisions.jsonl` (en notant le `pilier` et la `source`).
Si Abdelilah répond « aucune », n'génère rien et archive la journée.
```

- [ ] **Step 2 : Étendre deploy.sh pour déployer le pipeline et l'agent curator**

Dans `deploy.sh`, dans la section « Définition (toujours resynchronisée) », ajouter après la ligne qui synchronise `editorial-writer.md` :

```bash
sync_def "$REPO/.claude/agents/editorial-curator.md" "$WS/.claude/agents/editorial-curator.md"
sync_def "$REPO/Hermes social media/philosophy/pillars.md" "$WS/philosophy/pillars.md"
```

Puis, avant la section « Données vivantes », ajouter le déploiement du pipeline et la création des dossiers `briefs/` :

```bash
# --- Pipeline Phase 2 (scripts versionnés) ---
echo "Synchronisation du pipeline :"
sudo mkdir -p "$PROFILE/pipeline"
sudo cp "$REPO/pipeline/"*.py "$PROFILE/pipeline/"
sudo cp "$REPO/pipeline/requirements.txt" "$PROFILE/pipeline/"
sudo mkdir -p "$PROFILE/briefs/incoming" "$PROFILE/briefs/processed" "$PROFILE/briefs/proposals"
echo "  def   $PROFILE/pipeline/*.py"
```

Et dans le `chown` final, ajouter `"$PROFILE/pipeline" "$PROFILE/briefs"` à la liste des chemins.

- [ ] **Step 3 : Vérifier la syntaxe du script**

Run: `bash -n deploy.sh && echo "syntaxe OK"`
Expected: `syntaxe OK`.

- [ ] **Step 4 : Commit**

```bash
git add deploy/SOUL.md deploy.sh
git commit -m "feat(social-media): règle de choix SOUL + déploiement pipeline/curator/pillars"
```

---

### Task 9 : Déploiement serveur + vérification end-to-end

**Files:** (aucun fichier repo modifié — actions de déploiement)

- [ ] **Step 1 : Déployer vers le profil Hermes**

Run: `./deploy.sh`
Expected: lignes `def …editorial-curator.md`, `…pillars.md`, `…pipeline/*.py`, et création de `briefs/`.

- [ ] **Step 2 : Créer le venv du pipeline côté serveur**

Run:
```bash
sudo -u hermes -H bash -c 'cd /opt/hermes/data/profiles/social-media/pipeline && python3 -m venv .venv && ./.venv/bin/pip install -q -r requirements.txt && echo OK'
```
Expected: `OK`.

- [ ] **Step 3 : Lancer le monitor réel (détection)**

Run:
```bash
sudo -u hermes -H bash -c 'cd /opt/hermes/data/profiles/social-media && HERMES_PROFILE=$PWD pipeline/.venv/bin/python -m pipeline.youtube_monitor'
```
Expected: `[youtube_monitor] N nouvelle(s) opportunité(s)…`. Vérifier : `sudo ls /opt/hermes/data/profiles/social-media/briefs/incoming/`.
> Si 0 vidéo récente, déposer un item de test dans `briefs/incoming/` pour continuer.

- [ ] **Step 4 : Lancer l'orchestrateur réel (curation + Telegram)**

Run:
```bash
sudo -u hermes -H bash -c 'cd /opt/hermes/data/profiles/social-media && HOME=/opt/hermes HERMES_HOME=/opt/hermes/data pipeline/.venv/bin/python -c "
from pathlib import Path
from pipeline.orchestrator import main
main(base=Path.cwd(), workspace=str(Path.cwd()/\"workspace/editorial\"), date=\"2026-06-28\")
"'
```
Expected: `[orchestrator] N idée(s) proposée(s)…`, un message numéroté reçu sur Telegram, et `briefs/proposals/latest.json` créé.

> Note : `workspace` pointe vers `workspace/editorial` (où vivent `.claude/agents/`, `philosophy/`, `memory/`). Vérifier que `editorial-curator.md` et `pillars.md` y sont bien déployés.

- [ ] **Step 5 : Recharger le SOUL et tester le choix sur Telegram**

Run: `sudo systemctl restart hermes-gateway-social-media`
Puis, sur Telegram : envoyer `/new`, attendre la liste d'idées (ou la redéclencher), répondre un **numéro**.
Expected: Hermes lit `briefs/proposals/latest.json`, délègue à `editorial-writer`, présente les variantes pour validation.

- [ ] **Step 6 : Planifier le cron quotidien (matin ~07:30)**

Créer le cron Hermes du profil qui lance monitor puis orchestrateur :
```bash
sudo -u hermes -H bash -c 'cd /opt/hermes/hermes-agent && HERMES_HOME=/opt/hermes/data .venv/bin/python -m hermes_cli.main --profile social-media cron add \
  --name "youtube-curation" --schedule "30 7 * * *" \
  --command "cd /opt/hermes/data/profiles/social-media && HOME=/opt/hermes HERMES_HOME=/opt/hermes/data pipeline/.venv/bin/python -m pipeline.run_daily"'
```
> Prérequis : créer `pipeline/run_daily.py` qui appelle `youtube_monitor.main()` puis `orchestrator.main(...)` avec la date du jour. (Si la CLI `cron add` diffère, ajuster selon `hermes cron --help`.)

- [ ] **Step 7 : Vérification finale**

Confirmer : la suite pytest passe (`cd pipeline && ./.venv/bin/pytest -q`), un run manuel produit des propositions sur Telegram, un choix produit des variantes validables. Documenter tout écart.

---

## Notes d'implémentation
- **DRY** : `editorial-writer` et la mémoire V1 sont réutilisés tels quels.
- **YAGNI** : pas d'API de publication, pas d'autres sources, pas d'images en tranche 1.
- **Coût** : détection = Gemini ; curation + génération = Claude Code (Claude Max) ; Hermes-LLM seulement pour la conversation Telegram.
- **Risque crédits OpenRouter** : impacte la conversation Telegram (choix/validation), pas la génération.
