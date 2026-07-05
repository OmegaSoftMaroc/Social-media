#!/usr/bin/env python3
"""Entrée cron quotidienne : détection (monitor) puis curation+proposition (orchestrator).

Tout échec est notifié sur Telegram (sinon la panne est silencieuse — vécu :
4 jours d'échecs muets quand la session Claude CLI a expiré).
"""
import traceback
from datetime import datetime
from pathlib import Path

from pipeline.youtube_monitor import main as monitor_main
from pipeline.orchestrator import main as orchestrate_main, send_telegram

PROFILE = Path("/opt/hermes/data/profiles/social-media")
WORKSPACE = PROFILE / "workspace" / "editorial"


def run() -> int:
    monitor_main()
    today = datetime.now().strftime("%Y-%m-%d")
    return orchestrate_main(base=PROFILE, workspace=str(WORKSPACE), date=today)


def main() -> int:
    """Exécute le pipeline ; en cas d'échec, alerte Abdelilah sur Telegram."""
    try:
        return 0 if run() >= 0 else 1
    except Exception as exc:  # noqa: BLE001 — on veut TOUT notifier
        traceback.print_exc()
        try:
            send_telegram(
                "🔴 Pipeline éditorial en ÉCHEC "
                f"({datetime.now():%Y-%m-%d %H:%M}) : "
                f"{type(exc).__name__}: {str(exc)[:300]}\n"
                "Les opportunités restent en file (briefs/incoming), rien n'est perdu."
            )
        except Exception:
            traceback.print_exc()  # l'alerte elle-même a échoué → visible dans le log cron
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
