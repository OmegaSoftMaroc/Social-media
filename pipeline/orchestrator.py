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
    lines = ["💡 Idées de publication du jour — réponds avec un numéro :", ""]
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
    """Envoie un message sur le canal Telegram (home channel) du profil via `hermes send`.

    Lève une exception si l'envoi échoue → l'orchestrateur n'archivera pas (rejouable).
    `--to telegram` cible le canal par défaut du profil (TELEGRAM_HOME_CHANNEL).
    """
    import os
    from dotenv import dotenv_values
    profile = "/opt/hermes/data/profiles/social-media"
    hermes_bin = "/opt/hermes/hermes-agent/.venv/bin/hermes"
    env = {**os.environ, "HOME": "/opt/hermes", "HERMES_HOME": "/opt/hermes/data"}
    # Le token Telegram du profil vit dans config/.env (sourcé par le gateway au runtime) ;
    # `hermes send` standalone ne le lit pas → on l'injecte dans l'environnement.
    creds = dotenv_values(f"{profile}/config/.env")
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_HOME_CHANNEL", "TELEGRAM_ALLOWED_USERS"):
        if creds.get(key):
            env[key] = creds[key]
    subprocess.run(
        [hermes_bin, "--profile", "social-media", "send", "--to", "telegram", text],
        env=env, timeout=60, check=True,
    )


def push_to_sheet(ideas: list[dict], date: str) -> int:
    """Écrit les idées dans l'onglet 01_Idees (best-effort : n'interrompt pas le pipeline).

    Telegram reste le canal prioritaire ; un échec Sheets est loggué puis ignoré.
    """
    try:
        from pipeline.google_workspace import append_ideas
        n = append_ideas(ideas, date)
        print(f"[orchestrator] {n} idée(s) écrite(s) dans 01_Idees")
        return n
    except Exception as exc:  # noqa: BLE001 — best-effort
        print(f"[orchestrator] écriture Sheet ignorée (erreur : {exc})")
        return 0


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
        push_to_sheet(idees, date)
        send_telegram(render_proposal_message(proposals))

    archive_processed([it["video_id"] for it in items if it.get("video_id")],
                      incoming, processed)
    print(f"[orchestrator] {len(idees)} idée(s) proposée(s) pour le {date}")
    return len(idees)
