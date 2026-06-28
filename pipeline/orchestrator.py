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
