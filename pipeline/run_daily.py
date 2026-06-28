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
