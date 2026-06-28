#!/usr/bin/env python3
"""Run manuel d'actualité : ingère la DERNIÈRE vidéo de chaque chaîne (ignore seen/récence),
puis curation (5-7 idées) → écriture dans 01_Idees + envoi Telegram.

À déclencher à la demande (différent de run_daily qui ne prend que les vidéos récentes non vues).
"""
from datetime import datetime
from pathlib import Path

from pipeline.youtube_monitor import ingest_latest_per_channel
from pipeline.orchestrator import main as orchestrate_main

PROFILE = Path("/opt/hermes/data/profiles/social-media")
WORKSPACE = PROFILE / "workspace" / "editorial"


def run() -> int:
    ingest_latest_per_channel()
    today = datetime.now().strftime("%Y-%m-%d")
    return orchestrate_main(base=PROFILE, workspace=str(WORKSPACE), date=today)


if __name__ == "__main__":
    raise SystemExit(0 if run() >= 0 else 1)
