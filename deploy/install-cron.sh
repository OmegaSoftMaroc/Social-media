#!/usr/bin/env bash
#
# install-cron.sh — Installe (idempotent) le cron quotidien du pipeline YouTube.
#
# run_daily s'exécute chaque matin à 07:30 sous l'utilisateur hermes :
# détection des nouvelles vidéos → curation (3-5 idées) → envoi Telegram.
#
# Usage :  ./deploy/install-cron.sh
#
set -euo pipefail

PROFILE="${HERMES_PROFILE:-/opt/hermes/data/profiles/social-media}"
JOB="30 7 * * * cd $PROFILE && HOME=/opt/hermes HERMES_HOME=/opt/hermes/data pipeline/.venv/bin/python -m pipeline.run_daily >> $PROFILE/logs/youtube-curation.log 2>&1"

current="$(sudo crontab -u hermes -l 2>/dev/null || true)"

if printf '%s\n' "$current" | grep -qF "pipeline.run_daily"; then
  echo "Cron déjà présent — aucune modification."
else
  {
    printf '%s\n' "$current" | grep -vE '^PATH=/usr/bin:/bin$' | grep -v '^$' || true
    echo "PATH=/usr/bin:/bin"
    echo "$JOB"
  } | sudo crontab -u hermes -
  echo "✅ Cron installé (07:30 quotidien)."
fi

echo "--- crontab hermes (ligne pipeline) ---"
sudo crontab -u hermes -l | grep -F "pipeline.run_daily"
