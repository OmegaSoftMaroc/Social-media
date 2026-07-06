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
    contexte pour un script plus fidèle.
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


def make_video_from_text(script_text: str, out_path: Path, fmt: str) -> Path:
    """Mode voix HeyGen : texte → TTS intégré + avatar → mp4 (sans ElevenLabs)."""
    from pipeline.heygen import create_video_from_text, wait_and_download
    video_id = create_video_from_text(script_text, fmt)
    return Path(wait_and_download(video_id, str(out_path)))


def use_heygen_voice() -> bool:
    """Vrai si on utilise la voix HeyGen (pas de voix ElevenLabs configurée)."""
    import os
    return bool(os.environ.get("HEYGEN_VOICE_ID")) and \
        not os.environ.get("ELEVENLABS_VOICE_ID")


def load_idea(n: int, base: Path) -> dict:
    data = json.loads((Path(base) / "briefs" / "proposals" / "latest.json")
                      .read_text(encoding="utf-8"))
    return data["idees"][n - 1]


def main(n: int, fmt: str, base: Path = PROFILE) -> int:
    if fmt not in VIDEO_FORMATS:
        raise SystemExit(f"format inconnu : {fmt} (linkedin|short)")
    from dotenv import load_dotenv
    load_dotenv("/opt/hermes/data/.env")
    load_dotenv(str(PROFILE / "config" / ".env"))
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

        if use_heygen_voice():
            # Voix HeyGen intégrée : pas d'étape TTS séparée
            if not paths["video"].exists():
                make_video_from_text(script["script"], paths["video"], fmt)
        else:
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
