# Pipeline vidéo HeyGen + ElevenLabs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produire à la demande une vidéo (avatar filmé + voix clonée d'Abdelilah) à partir d'une idée — format LinkedIn (60-90 s) ou Short (30-45 s, 9:16) — déposée sur Drive, notifiée sur Telegram, publiable sur LinkedIn après validation explicite.

**Architecture:** Extension du pipeline Python existant : un agent `video-scriptwriter` écrit le script parlé (JSON), `elevenlabs.py` fait le TTS (voix clonée), `heygen.py` génère la vidéo avatar (upload audio → job → polling → download), `develop_video.py` orchestre avec artefacts persistés par étape (relance sans regénérer) + upload Drive + notification. `linkedin.py` gagne `publish_video_post`. Alerte Telegram sur tout échec (mécanisme existant).

**Tech Stack:** Python 3.12 (requests, pytest — déjà en place), agents Claude Code, APIs ElevenLabs TTS v1 + HeyGen v2, Google Drive (connecteur existant), LinkedIn ugcPosts (connecteur existant).

**Prérequis externes (bloquants pour la Task 8 uniquement)** : clés `ELEVENLABS_API_KEY`/`ELEVENLABS_VOICE_ID`/`HEYGEN_API_KEY`/`HEYGEN_AVATAR_ID` dans `config/.env` du profil, et session Claude CLI serveur reconnectée (`HOME=/opt/hermes claude /login`). Les Tasks 1-7 (code + tests) n'en dépendent pas.

---

## Conventions
- Tests : `cd pipeline && ./.venv/bin/pytest -q` — **aucun appel réseau dans les tests** (fonctions pures testées ; appels externes = fonctions fines mockées).
- Chaque tâche : test rouge → implémentation → test vert → commit conventionnel.
- Chemins absolus dépôt : `/root/dev-projects/Social-media`.

---

### Task 1 : Config vidéo

**Files:**
- Modify: `pipeline/config.py` (fin de fichier)
- Test: `pipeline/tests/test_video_config.py`

- [ ] **Step 1 : Test qui échoue**

Create `pipeline/tests/test_video_config.py`:

```python
from pipeline.config import VIDEO_FORMATS, VIDEO_POLL_S, VIDEO_TIMEOUT_S


def test_video_formats_shape():
    assert set(VIDEO_FORMATS) == {"linkedin", "short"}
    for fmt in VIDEO_FORMATS.values():
        assert {"width", "height"} <= set(fmt["dimension"])
        lo, hi = fmt["target_words"]
        assert 0 < lo < hi


def test_short_is_vertical():
    d = VIDEO_FORMATS["short"]["dimension"]
    assert d["height"] > d["width"]


def test_polling_bounds():
    assert VIDEO_POLL_S >= 10
    assert VIDEO_TIMEOUT_S >= 600
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest tests/test_video_config.py -q`
Expected: FAIL — `ImportError: cannot import name 'VIDEO_FORMATS'`.

- [ ] **Step 3 : Implémenter**

Append à `pipeline/config.py` :

```python
# --- Vidéo (ElevenLabs + HeyGen) ----------------------------------------------
# Clés dans config/.env : ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
#                         HEYGEN_API_KEY, HEYGEN_AVATAR_ID
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVENLABS_MODEL = "eleven_multilingual_v2"
HEYGEN_UPLOAD_URL = "https://upload.heygen.com/v1/asset"
HEYGEN_GENERATE_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_URL = "https://api.heygen.com/v1/video_status.get"

# Formats de sortie : calibrage script (mots) + dimensions vidéo
VIDEO_FORMATS = {
    "linkedin": {"dimension": {"width": 1280, "height": 720},
                 "target_words": (150, 220)},   # ~60-90 s parlées
    "short": {"dimension": {"width": 720, "height": 1280},
              "target_words": (70, 110)},        # ~30-45 s, 9:16
}
VIDEO_POLL_S = 20       # intervalle de polling HeyGen
VIDEO_TIMEOUT_S = 900   # 15 min max par vidéo
```

- [ ] **Step 4 : Vérifier le succès**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest tests/test_video_config.py -q`
Expected: 3 passed.

- [ ] **Step 5 : Commit**

```bash
cd /root/dev-projects/Social-media
git add pipeline/config.py pipeline/tests/test_video_config.py
git commit -m "feat(pipeline): config vidéo (formats, endpoints ElevenLabs/HeyGen, polling)"
```

---

### Task 2 : Agent video-scriptwriter

**Files:**
- Create: `.claude/agents/video-scriptwriter.md`

- [ ] **Step 1 : Écrire l'agent**

Create `.claude/agents/video-scriptwriter.md`:

```markdown
---
name: video-scriptwriter
description: Écrit le script PARLÉ d'une vidéo (avatar + voix clonée d'Abdelilah) à partir d'une idée ou d'un post — format linkedin (60-90 s) ou short (30-45 s). Lecture seule, sortie JSON.
tools: Read, Glob, Grep
---

Tu écris les **scripts vidéo parlés** d'Abdelilah Kahaji (OmegaSoft, ESN Agadir).
Un avatar filmé le dit à voix haute : écris de l'**oral naturel** (phrases courtes,
première personne, rythme), PAS un post lu.

## Entrée (dans le prompt)
- L'idée (titre, angle, pilier) OU le post déjà rédigé.
- Le `format` demandé : `linkedin` ou `short`.

## Calibrage STRICT
- `linkedin` : 150-220 mots (≈ 60-90 s parlées). Ton posé, pédagogique.
- `short` : 70-110 mots (≈ 30-45 s). Rythme rapide, punchy.
- Structure : HOOK (< 3 s, une phrase qui accroche) → corps (2-3 points concrets)
  → CTA final (question ou invitation à commenter/suivre).

## Règles
- Français oral naturel. Aucun emoji, aucun hashtag, aucune didascalie dans `script`
  (le texte est envoyé TEL QUEL au text-to-speech).
- Ne jamais inventer de faits/chiffres ; confidentialité `prudent` (aucun nom de
  client, aucun chiffre interne OmegaSoft).
- `titre` court (pour le fichier/Drive), `description` = texte d'accompagnement
  du post (2-3 phrases + hashtags autorisés ici).

## Sortie OBLIGATOIRE — unique bloc JSON final, rien après
```json
{
  "format": "linkedin",
  "script": "le texte parlé intégral, prêt pour le TTS",
  "titre": "titre court de la vidéo",
  "description": "texte d'accompagnement du post (hashtags ok)",
  "duree_estimee_s": 75,
  "alertes": ["points à vérifier avant publication"]
}
```
```

- [ ] **Step 2 : Vérification locale de l'agent (JSON valide, calibrage)**

Run (depuis la racine du dépôt) :
```bash
cd /root/dev-projects/Social-media
claude -p 'Idée : "Agent personnel IA vs Claude Code : quel outil pour quel besoin en entreprise" (pilier IA appliquée). format=short. Écris le script.' \
  --agent video-scriptwriter --permission-mode dontAsk --max-turns 4 \
  2>/dev/null | sed -n '/^```json/,/^```/p' | sed '1d;$d' | python3 -c "
import sys, json
d = json.load(sys.stdin)
words = len(d['script'].split())
assert d['format'] == 'short', d['format']
assert 60 <= words <= 130, f'{words} mots hors calibrage'
assert '#' not in d['script'], 'hashtag dans le script TTS'
print('OK —', words, 'mots |', d['titre'])
"
```
Expected: `OK — <70-110> mots | <titre>`. Si hors calibrage → renforcer la section « Calibrage STRICT » et relancer.

- [ ] **Step 3 : Commit**

```bash
cd /root/dev-projects/Social-media
git add .claude/agents/video-scriptwriter.md
git commit -m "feat(social-media): agent video-scriptwriter (script parlé linkedin/short)"
```

---

### Task 3 : Connecteur ElevenLabs (TDD)

**Files:**
- Create: `pipeline/elevenlabs.py`
- Test: `pipeline/tests/test_elevenlabs.py`

- [ ] **Step 1 : Tests qui échouent**

Create `pipeline/tests/test_elevenlabs.py`:

```python
from pipeline.elevenlabs import build_tts_payload, tts_url


def test_build_tts_payload():
    p = build_tts_payload("Bonjour, parlons agents IA.")
    assert p["text"] == "Bonjour, parlons agents IA."
    assert p["model_id"] == "eleven_multilingual_v2"
    assert 0 <= p["voice_settings"]["stability"] <= 1


def test_tts_url_injects_voice_id():
    assert tts_url("abc123").endswith("/text-to-speech/abc123")
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest tests/test_elevenlabs.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.elevenlabs'`.

- [ ] **Step 3 : Implémenter**

Create `pipeline/elevenlabs.py`:

```python
#!/usr/bin/env python3
"""Connecteur ElevenLabs — synthèse vocale avec la voix clonée d'Abdelilah.

Fonctions pures testées ; `synthesize` (réseau) reste fine et non testée.
Clés : ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID (config/.env du profil).
"""
from __future__ import annotations

from pipeline.config import ELEVENLABS_TTS_URL, ELEVENLABS_MODEL


def tts_url(voice_id: str) -> str:
    """URL TTS pour une voix donnée."""
    return ELEVENLABS_TTS_URL.format(voice_id=voice_id)


def build_tts_payload(script: str) -> dict:
    """Payload TTS : texte + modèle multilingue + réglages voix stables."""
    return {
        "text": script,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }


def synthesize(script: str, out_path: str, api_key: str | None = None,
               voice_id: str | None = None) -> str:
    """Génère le mp3 du script (réseau). Retourne out_path."""
    import os
    import requests

    key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
    voice = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "")
    if not key or not voice:
        raise RuntimeError("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID manquant")
    resp = requests.post(
        tts_url(voice),
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json=build_tts_payload(script),
        timeout=120,
    )
    resp.raise_for_status()
    with open(out_path, "wb") as fh:
        fh.write(resp.content)
    return out_path
```

- [ ] **Step 4 : Vérifier le succès**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest tests/test_elevenlabs.py -q`
Expected: 2 passed.

- [ ] **Step 5 : Commit**

```bash
cd /root/dev-projects/Social-media
git add pipeline/elevenlabs.py pipeline/tests/test_elevenlabs.py
git commit -m "feat(pipeline): connecteur ElevenLabs (TTS voix clonée) TDD"
```

---

### Task 4 : Connecteur HeyGen (TDD)

**Files:**
- Create: `pipeline/heygen.py`
- Test: `pipeline/tests/test_heygen.py`

- [ ] **Step 1 : Tests qui échouent**

Create `pipeline/tests/test_heygen.py`:

```python
import pytest

from pipeline.heygen import build_video_payload, parse_video_status


def test_build_video_payload_linkedin():
    p = build_video_payload("asset42", "avatarX", "linkedin")
    inp = p["video_inputs"][0]
    assert inp["character"] == {"type": "avatar", "avatar_id": "avatarX",
                                "avatar_style": "normal"}
    assert inp["voice"] == {"type": "audio", "audio_asset_id": "asset42"}
    assert p["dimension"] == {"width": 1280, "height": 720}


def test_build_video_payload_short_is_vertical():
    p = build_video_payload("a", "b", "short")
    assert p["dimension"] == {"width": 720, "height": 1280}


def test_build_video_payload_rejects_unknown_format():
    with pytest.raises(KeyError):
        build_video_payload("a", "b", "tiktok-4k")


def test_parse_video_status_completed():
    status, info = parse_video_status(
        {"data": {"status": "completed", "video_url": "https://x/v.mp4"}})
    assert status == "completed" and info == "https://x/v.mp4"


def test_parse_video_status_failed_with_error():
    status, info = parse_video_status(
        {"data": {"status": "failed", "error": {"message": "bad avatar"}}})
    assert status == "failed" and "bad avatar" in info


def test_parse_video_status_processing():
    status, info = parse_video_status({"data": {"status": "processing"}})
    assert status == "processing" and info is None
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest tests/test_heygen.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.heygen'`.

- [ ] **Step 3 : Implémenter**

Create `pipeline/heygen.py`:

```python
#!/usr/bin/env python3
"""Connecteur HeyGen — vidéo avatar filmé à partir d'un audio.

Fonctions pures testées (payload, parsing statut) ; réseau isolé.
Clés : HEYGEN_API_KEY + HEYGEN_AVATAR_ID (config/.env du profil).
NB : endpoints v2 vérifiés contre la doc au premier test réel (l'API évolue).
"""
from __future__ import annotations

import time

from pipeline.config import (
    HEYGEN_UPLOAD_URL, HEYGEN_GENERATE_URL, HEYGEN_STATUS_URL,
    VIDEO_FORMATS, VIDEO_POLL_S, VIDEO_TIMEOUT_S,
)


def build_video_payload(audio_asset_id: str, avatar_id: str, fmt: str) -> dict:
    """Payload /v2/video/generate : avatar filmé + audio uploadé + dimensions."""
    dimension = VIDEO_FORMATS[fmt]["dimension"]  # KeyError si format inconnu
    return {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": avatar_id,
                          "avatar_style": "normal"},
            "voice": {"type": "audio", "audio_asset_id": audio_asset_id},
        }],
        "dimension": dimension,
    }


def parse_video_status(resp: dict) -> tuple[str, str | None]:
    """(statut, info) — info = video_url si completed, message si failed, sinon None."""
    data = resp.get("data") or {}
    status = data.get("status", "unknown")
    if status == "completed":
        return status, data.get("video_url")
    if status == "failed":
        err = data.get("error") or {}
        return status, str(err.get("message") or err or "échec HeyGen")
    return status, None


def _key(api_key: str | None) -> str:
    import os
    key = api_key or os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        raise RuntimeError("HEYGEN_API_KEY manquant")
    return key


def upload_audio(path: str, api_key: str | None = None) -> str:
    """Upload l'audio (asset) ; retourne l'asset_id."""
    import requests
    with open(path, "rb") as fh:
        resp = requests.post(HEYGEN_UPLOAD_URL, data=fh.read(), timeout=120,
                             headers={"x-api-key": _key(api_key),
                                      "Content-Type": "audio/mpeg"})
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def create_video(audio_asset_id: str, fmt: str, api_key: str | None = None,
                 avatar_id: str | None = None) -> str:
    """Lance la génération ; retourne le video_id."""
    import os
    import requests
    avatar = avatar_id or os.environ.get("HEYGEN_AVATAR_ID", "")
    if not avatar:
        raise RuntimeError("HEYGEN_AVATAR_ID manquant")
    resp = requests.post(HEYGEN_GENERATE_URL, timeout=60,
                         headers={"x-api-key": _key(api_key)},
                         json=build_video_payload(audio_asset_id, avatar, fmt))
    resp.raise_for_status()
    return resp.json()["data"]["video_id"]


def wait_and_download(video_id: str, out_path: str, api_key: str | None = None,
                      poll_s: int = VIDEO_POLL_S,
                      timeout_s: int = VIDEO_TIMEOUT_S) -> str:
    """Polle le statut puis télécharge le mp4. Lève RuntimeError si failed/timeout."""
    import requests
    key = _key(api_key)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        resp = requests.get(HEYGEN_STATUS_URL, params={"video_id": video_id},
                            headers={"x-api-key": key}, timeout=30)
        resp.raise_for_status()
        status, info = parse_video_status(resp.json())
        if status == "completed":
            video = requests.get(info, timeout=300)
            video.raise_for_status()
            with open(out_path, "wb") as fh:
                fh.write(video.content)
            return out_path
        if status == "failed":
            raise RuntimeError(f"HeyGen a échoué : {info}")
        time.sleep(poll_s)
    raise RuntimeError(f"HeyGen : timeout après {timeout_s}s (video_id={video_id})")
```

- [ ] **Step 4 : Vérifier le succès**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest tests/test_heygen.py -q`
Expected: 6 passed.

- [ ] **Step 5 : Commit**

```bash
cd /root/dev-projects/Social-media
git add pipeline/heygen.py pipeline/tests/test_heygen.py
git commit -m "feat(pipeline): connecteur HeyGen (upload audio, génération, polling) TDD"
```

---

### Task 5 : Orchestrateur develop_video (TDD)

**Files:**
- Create: `pipeline/develop_video.py`
- Test: `pipeline/tests/test_develop_video.py`

- [ ] **Step 1 : Tests qui échouent**

Create `pipeline/tests/test_develop_video.py`:

```python
import json
from pathlib import Path

import pipeline.develop_video as dv


def test_artifact_paths(tmp_path):
    paths = dv.artifact_paths(tmp_path, "idee3")
    assert paths["script"] == tmp_path / "briefs" / "output" / "idee3" / "video-script.json"
    assert paths["audio"].name == "audio.mp3"
    assert paths["video"].name == "video.mp4"


def test_render_video_notification():
    msg = dv.render_video_notification(
        {"titre": "Agents IA", "duree_estimee_s": 40, "format": "short"},
        "https://drive/x")
    assert "Agents IA" in msg
    assert "short" in msg
    assert "https://drive/x" in msg
    assert "publie la vidéo" in msg.lower()


def test_main_skips_existing_artifacts(tmp_path, monkeypatch):
    # Prépare une idée + artefacts déjà présents (script + audio)
    proposals = tmp_path / "briefs" / "proposals"
    proposals.mkdir(parents=True)
    (proposals / "latest.json").write_text(json.dumps(
        {"idees": [{"id": "idee-1", "pilier": 1, "titre": "T", "angle": "A"}]}),
        encoding="utf-8")
    paths = dv.artifact_paths(tmp_path, "idee1")
    paths["script"].parent.mkdir(parents=True)
    paths["script"].write_text(json.dumps(
        {"format": "short", "script": "s", "titre": "T", "description": "d"}),
        encoding="utf-8")
    paths["audio"].write_bytes(b"mp3")

    calls = {"script": 0, "tts": 0, "video": 0}
    monkeypatch.setattr(dv, "call_scriptwriter",
                        lambda *a, **k: calls.__setitem__("script", 1) or {})
    monkeypatch.setattr(dv, "make_audio",
                        lambda *a, **k: calls.__setitem__("tts", 1))
    monkeypatch.setattr(dv, "make_video",
                        lambda script, audio, out, fmt: Path(out).write_bytes(b"v")
                        or calls.__setitem__("video", 1))
    monkeypatch.setattr(dv, "upload_to_drive", lambda p, name: "https://drive/ok")
    monkeypatch.setattr(dv, "send_telegram", lambda t: None)

    assert dv.main(1, "short", base=tmp_path) == 0
    assert calls == {"script": 0, "tts": 0, "video": 1}  # script+audio réutilisés
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest tests/test_develop_video.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.develop_video'`.

- [ ] **Step 3 : Implémenter**

Create `pipeline/develop_video.py`:

```python
#!/usr/bin/env python3
"""Orchestrateur vidéo : idée N → script parlé → TTS (voix clonée) → HeyGen
(avatar filmé) → Drive (dossier Videos) → notification Telegram.

Idempotent par étape : si un artefact existe déjà (script/audio/vidéo), il est
réutilisé — relance sans regénérer. Tout échec alerte sur Telegram.
Publication = étape séparée, UNIQUEMENT après validation (cf. SOUL.md).

Usage : python -m pipeline.develop_video <N> [--format linkedin|short]
"""
from __future__ import annotations

import json
import subprocess
import sys
import traceback
from pathlib import Path

from pipeline.config import VIDEO_FORMATS, GOOGLE_SOURCES_PARENT
from pipeline.orchestrator import send_telegram

PROFILE = Path("/opt/hermes/data/profiles/social-media")
WORKSPACE = PROFILE / "workspace" / "editorial"


def artifact_paths(base: Path, slug: str) -> dict[str, Path]:
    """Chemins des artefacts persistés d'une vidéo (relance possible par étape)."""
    outdir = Path(base) / "briefs" / "output" / slug
    return {"dir": outdir,
            "script": outdir / "video-script.json",
            "audio": outdir / "audio.mp3",
            "video": outdir / "video.mp4"}


def render_video_notification(script: dict, drive_link: str) -> str:
    """Message Telegram : vidéo prête + suivi conso + comment la publier."""
    return ("🎬 Vidéo prête : " + script.get("titre", "(sans titre)")
            + f"\nFormat : {script.get('format')} — ~{script.get('duree_estimee_s', '?')} s"
            + f" — {len(script.get('script', ''))} caractères TTS"
            + f"\n📁 {drive_link}"
            + "\n\nPour publier : réponds « publie la vidéo N sur linkedin ». "
            "Sinon elle reste sur Drive.")


def call_scriptwriter(idea: dict, fmt: str, post_text: str = "") -> dict:
    """Appelle l'agent video-scriptwriter (HOME=/opt/hermes requis).

    Si le post a déjà été développé (variants.json), son texte est fourni en
    contexte pour un script plus fidèle (cf. spec : partir du post existant).
    """
    import os
    prompt = ("Idée : " + json.dumps(idea, ensure_ascii=False)
              + (f"\nPost déjà rédigé (à adapter en oral) :\n{post_text}"
                 if post_text else "")
              + f"\nformat={fmt}. Écris le script.")
    out = subprocess.run(
        ["claude", "-p", prompt, "--agent", "video-scriptwriter",
         "--permission-mode", "dontAsk", "--max-turns", "4"],
        cwd=str(WORKSPACE), capture_output=True, text=True, timeout=300,
        env={**os.environ, "HOME": "/opt/hermes"})
    text = out.stdout
    start = text.rfind("```json")
    if start == -1:
        raise ValueError("Aucun bloc JSON du scriptwriter | stderr: "
                         + out.stderr[-200:])
    body = text[start + 7:]
    return json.loads(body[:body.find("```")])


def make_audio(script_text: str, out_path: Path) -> None:
    """TTS ElevenLabs → mp3."""
    from pipeline.elevenlabs import synthesize
    synthesize(script_text, str(out_path))


def make_video(script: dict, audio_path: Path, out_path: Path, fmt: str) -> Path:
    """Audio → asset HeyGen → génération → download mp4."""
    from pipeline.heygen import upload_audio, create_video, wait_and_download
    asset = upload_audio(str(audio_path))
    video_id = create_video(asset, fmt)
    return Path(wait_and_download(video_id, str(out_path)))


def upload_to_drive(path: Path, name: str) -> str:
    """Dépose le mp4 dans le dossier Drive Videos ; retourne le lien."""
    from pipeline.google_workspace import find_or_create_folder, upload_file
    folder = find_or_create_folder("Videos", GOOGLE_SOURCES_PARENT)
    f = upload_file(name, str(path), folder, mime="video/mp4")
    return f.get("webViewLink", "")


def load_idea(n: int, base: Path) -> dict:
    data = json.loads((Path(base) / "briefs" / "proposals" / "latest.json")
                      .read_text(encoding="utf-8"))
    return data["idees"][n - 1]


def main(n: int, fmt: str, base: Path = PROFILE) -> int:
    if fmt not in VIDEO_FORMATS:
        raise SystemExit(f"format inconnu : {fmt} (linkedin|short)")
    try:
        idea = load_idea(n, base)
        slug = f"idee{n}"
        paths = artifact_paths(base, slug)
        paths["dir"].mkdir(parents=True, exist_ok=True)

        if paths["script"].exists():
            script = json.loads(paths["script"].read_text(encoding="utf-8"))
            print("[video] script réutilisé")
        else:
            post_text = ""
            variants_file = paths["dir"] / "variants.json"
            if variants_file.exists():  # post déjà développé → source du script
                vdata = json.loads(variants_file.read_text(encoding="utf-8"))
                reco = vdata.get("recommandation", {}).get("id")
                var = next((v for v in vdata.get("variantes", [])
                            if v.get("id") == reco), None)
                post_text = (var or {}).get("contenu", "")
            script = call_scriptwriter(idea, fmt, post_text)
            paths["script"].write_text(
                json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

        if paths["audio"].exists():
            print("[video] audio réutilisé")
        else:
            make_audio(script["script"], paths["audio"])

        if not paths["video"].exists():
            make_video(script, paths["audio"], paths["video"], fmt)

        link = upload_to_drive(paths["video"], f"{slug}-{fmt}.mp4")
        send_telegram(render_video_notification(script, link))
        print(f"[video] OK — {paths['video']} → {link}")
        return 0
    except Exception as exc:  # noqa: BLE001 — zéro panne silencieuse
        traceback.print_exc()
        try:
            send_telegram(f"🔴 Génération vidéo en ÉCHEC (idée {n}, {fmt}) : "
                          f"{type(exc).__name__}: {str(exc)[:300]}\n"
                          "Artefacts conservés — relance possible sans regénérer.")
        except Exception:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    fmt_arg = "linkedin"
    if "--format" in sys.argv:
        fmt_arg = sys.argv[sys.argv.index("--format") + 1]
    raise SystemExit(main(idx, fmt_arg))
```

- [ ] **Step 4 : Vérifier le succès (suite complète)**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest -q`
Expected: tous les tests passent (les 22 existants + 3 config + 2 elevenlabs + 6 heygen + 3 develop_video = 36).

- [ ] **Step 5 : Commit**

```bash
cd /root/dev-projects/Social-media
git add pipeline/develop_video.py pipeline/tests/test_develop_video.py
git commit -m "feat(pipeline): develop_video — orchestrateur idée→script→voix→avatar→Drive (idempotent)"
```

---

### Task 6 : Publication vidéo LinkedIn

**Files:**
- Modify: `pipeline/linkedin.py` (fin de fichier)
- Modify: `pipeline/publish_idea.py`

- [ ] **Step 1 : Ajouter publish_video_post**

Append à `pipeline/linkedin.py` :

```python
def _register_video_upload(token: str, urn: str):
    """Enregistre un upload vidéo, retourne (upload_url, asset_urn)."""
    import requests
    body = {"registerUploadRequest": {
        "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
        "owner": urn,
        "serviceRelationships": [
            {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
        ],
    }}
    r = requests.post(REGISTER_URL, json=body, timeout=30, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r.raise_for_status()
    val = r.json()["value"]
    upload_url = val["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    return upload_url, val["asset"]


def publish_video_post(text: str, video_path: str, access_token: str | None = None,
                       person_urn: str | None = None) -> dict:
    """Publie un post vidéo (PUBLIC). APRÈS validation explicite uniquement."""
    import requests
    c = _env()
    token = access_token or c.get("LINKEDIN_ACCESS_TOKEN")
    urn = person_urn or c.get("LINKEDIN_PERSON_URN")
    if not token or not urn:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN / LINKEDIN_PERSON_URN manquant")

    upload_url, asset = _register_video_upload(token, urn)
    with open(video_path, "rb") as fh:
        requests.put(upload_url, data=fh.read(), timeout=300,
                     headers={"Authorization": f"Bearer {token}"}).raise_for_status()

    body = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "VIDEO",
                "media": [{"status": "READY", "media": asset,
                           "title": {"text": "Vidéo OmegaSoft"}}],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = requests.post(POSTS_URL, json=body, timeout=30, headers={
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    })
    r.raise_for_status()
    return {"status": r.status_code, "post_id": r.headers.get("x-restli-id")}
```

- [ ] **Step 2 : Étendre publish_idea au support vidéo**

Dans `pipeline/publish_idea.py`, remplacer la fonction `publish` par :

```python
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
```

Et adapter le `__main__` :

```python
if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage : python -m pipeline.publish_idea <slug> [image|video]")
    print(publish(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "auto"))
```

- [ ] **Step 3 : Suite complète + imports**

Run: `cd /root/dev-projects/Social-media/pipeline && ./.venv/bin/pytest -q && ./.venv/bin/python -c "import pipeline.linkedin, pipeline.publish_idea; print('imports OK')"`
Expected: tous les tests passent + `imports OK`.

- [ ] **Step 4 : Commit**

```bash
cd /root/dev-projects/Social-media
git add pipeline/linkedin.py pipeline/publish_idea.py
git commit -m "feat(pipeline): publication vidéo LinkedIn (publish_video_post + publish_idea video)"
```

---

### Task 7 : Règles SOUL + déploiement

**Files:**
- Modify: `deploy/SOUL.md`
- (deploy.sh copie déjà `pipeline/*.py` et `.claude/agents/*.md` par glob — aucun changement)

- [ ] **Step 1 : Ajouter la règle vidéo au SOUL**

Dans `deploy/SOUL.md`, juste APRÈS la section « ## Publication LinkedIn (UNIQUEMENT après validation explicite) », insérer :

```markdown
## Vidéos (voix clonée + avatar — UNIQUEMENT sur demande, publication sur validation)
Quand Abdelilah demande une vidéo (« fais la vidéo de l'idée N », « en short ») :
```bash
cd /opt/hermes/data/profiles/social-media
HOME=/opt/hermes pipeline/.venv/bin/python -m pipeline.develop_video <N> --format <linkedin|short>
```
La vidéo est déposée sur Drive (dossier Videos) et notifiée sur Telegram — elle N'EST PAS publiée.
Quand Abdelilah **valide explicitement** (« publie la vidéo N sur linkedin ») :
```bash
HOME=/opt/hermes pipeline/.venv/bin/python -m pipeline.publish_idea idee<N> video
```
NE JAMAIS publier sans cette validation. Confirme le lien du post et journalise dans `memory/decisions.jsonl`.
```

- [ ] **Step 2 : Vérifier la syntaxe de deploy.sh (inchangé mais on redéploiera)**

Run: `cd /root/dev-projects/Social-media && bash -n deploy.sh && echo OK`
Expected: `OK`.

- [ ] **Step 3 : Commit + push**

```bash
cd /root/dev-projects/Social-media
git add deploy/SOUL.md
git commit -m "feat(social-media): règles SOUL vidéo (génération sur demande, publication sur validation)"
git push origin dev-kahaji
```

---

### Task 8 : Déploiement + vérification réelle étape par étape

**⚠️ Prérequis (actions Abdelilah, guidées)** : les 4 clés dans `config/.env` du profil (`ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `HEYGEN_API_KEY`, `HEYGEN_AVATAR_ID`) ET session Claude serveur reconnectée (`sudo -u hermes -H bash -c 'cd /opt/hermes && claude /login'`). Sans elles, s'arrêter ici et livrer les Tasks 1-7.

- [ ] **Step 1 : Déployer**

Run: `cd /root/dev-projects/Social-media && ./deploy.sh`
Expected: `def .../pipeline/*.py`, `def .../video-scriptwriter.md`, `✅ Déploiement terminé.`

- [ ] **Step 2 : Vérifier les clés (noms seuls, jamais les valeurs)**

Run:
```bash
sudo grep -oE '^(ELEVENLABS|HEYGEN)_[A-Z_]+=' /opt/hermes/data/profiles/social-media/config/.env
```
Expected: les 4 noms. Sinon → guider Abdelilah (comptes, upload voix 10-20 min, tournage avatar, activation API) et s'arrêter.

- [ ] **Step 3 : Test réel TTS seul (coût minime)**

Run:
```bash
sudo -u hermes -H bash -c 'cd /opt/hermes/data/profiles/social-media && pipeline/.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv(\"config/.env\")
from pipeline.elevenlabs import synthesize
import os
out = synthesize(\"Bonjour, ceci est un test de ma voix clonée pour OmegaSoft.\", \"/tmp/tts-test.mp3\")
print(\"OK\", os.path.getsize(out), \"octets\")
"'
```
Expected: `OK <taille> octets`. Faire écouter le mp3 à Abdelilah (dépôt Drive via `upload_file` si besoin) — **validation de la voix avant de continuer**.

- [ ] **Step 4 : Test réel HeyGen vidéo courte (1 phrase → coût minimal)**

Run:
```bash
sudo -u hermes -H bash -c 'cd /opt/hermes/data/profiles/social-media && pipeline/.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv(\"config/.env\")
from pipeline.heygen import upload_audio, create_video, wait_and_download
a = upload_audio(\"/tmp/tts-test.mp3\")
vid = create_video(a, \"short\")
print(\"video_id:\", vid)
print(\"OK:\", wait_and_download(vid, \"/tmp/heygen-test.mp4\"))
"'
```
Expected: mp4 téléchargé (~1-3 min de polling). Si erreur d'endpoint/payload → ajuster `heygen.py` contre la doc officielle, committer le fix (pattern Ideogram).

- [ ] **Step 5 : Chaîne complète sur une idée réelle**

Run:
```bash
sudo -u hermes -H bash -c 'cd /opt/hermes/data/profiles/social-media && HOME=/opt/hermes HERMES_HOME=/opt/hermes/data pipeline/.venv/bin/python -m pipeline.develop_video 1 --format short'
```
Expected: `[video] OK — .../video.mp4 → https://drive...` + notification Telegram reçue. Vérifier la vidéo sur Drive avec Abdelilah.

- [ ] **Step 6 : Publication (UNIQUEMENT si Abdelilah valide explicitement)**

Attendre la validation d'Abdelilah (« publie la vidéo 1 sur linkedin »), puis :
```bash
sudo -u hermes -H bash -c 'cd /opt/hermes/data/profiles/social-media && HOME=/opt/hermes pipeline/.venv/bin/python -m pipeline.publish_idea idee1 video'
```
Expected: `{'status': 201, 'post_id': 'urn:li:share:...'}`.

- [ ] **Step 7 : Redémarrer le service (nouvelles règles SOUL) + push final**

Run:
```bash
sudo systemctl restart hermes-gateway-social-media && sleep 6 && sudo systemctl is-active hermes-gateway-social-media
cd /root/dev-projects/Social-media && git push origin dev-kahaji
```
Expected: `active` + push OK.

---

## Notes
- **DRY** : réutilise `send_telegram`, `upload_file`/`find_or_create_folder`, patterns `.env`, alerting.
- **YAGNI** : pas d'upload YouTube/Insta/TikTok, pas de sous-titres, pas de planification auto (spec §Hors scope).
- **Coûts** : Task 8 étape 3-4 conçues pour dépenser le minimum (1 phrase) avant la chaîne complète.
- Les mp4 ne sont jamais commités (vivent dans `briefs/output/` + Drive).
