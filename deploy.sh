#!/usr/bin/env bash
#
# deploy.sh — Déploie le profil éditorial Hermes "social-media" depuis ce dépôt.
#
# Source de vérité = ce dépôt. Cible = le profil Hermes sur /opt/hermes.
# Idempotent : la DÉFINITION (SOUL, philosophy, agent, README) est toujours
# resynchronisée ; les DONNÉES VIVANTES (decisions.jsonl, preferences.md, output/)
# ne sont JAMAIS écrasées — créées seulement si absentes.
#
# Usage :  ./deploy.sh
# Override cible :  HERMES_PROFILE=/chemin/profil ./deploy.sh
#
set -euo pipefail

# --- Chemins ---------------------------------------------------------------
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="${HERMES_PROFILE:-/opt/hermes/data/profiles/social-media}"
WS="$PROFILE/workspace/editorial"
OWNER="${HERMES_OWNER:-hermes:hermes}"

SRC_SOUL="$REPO/deploy/SOUL.md"
SRC_AGENT="$REPO/.claude/agents/editorial-writer.md"
SRC_PHIL="$REPO/Hermes social media/philosophy"
SRC_MEM="$REPO/Hermes social media/memory"

# --- Pré-vérifications ------------------------------------------------------
[ -f "$SRC_SOUL" ]  || { echo "ERREUR: introuvable $SRC_SOUL" >&2; exit 1; }
[ -f "$SRC_AGENT" ] || { echo "ERREUR: introuvable $SRC_AGENT" >&2; exit 1; }
sudo test -d "$PROFILE" || { echo "ERREUR: profil cible introuvable: $PROFILE" >&2; exit 1; }

echo "Dépôt  : $REPO"
echo "Profil : $PROFILE"

# --- Helpers ----------------------------------------------------------------
# Copie un fichier de définition (toujours resynchronisé depuis le dépôt).
sync_def() { sudo install -m 644 "$1" "$2"; echo "  def   $2"; }
# Installe un fichier de données seulement s'il est absent (jamais écrasé).
seed_data() {
  if sudo test -e "$2"; then echo "  keep  $2 (donnée vivante préservée)";
  else sudo install -m 644 "$1" "$2"; echo "  seed  $2"; fi
}

# --- 1. Sauvegarde du SOUL.md cible s'il diffère ----------------------------
if sudo test -f "$PROFILE/SOUL.md" && ! sudo cmp -s "$SRC_SOUL" "$PROFILE/SOUL.md"; then
  ts="$(date +%Y%m%d-%H%M%S)"
  sudo cp -p "$PROFILE/SOUL.md" "$PROFILE/SOUL.md.bak-$ts"
  echo "Backup -> SOUL.md.bak-$ts"
else
  echo "SOUL.md inchangé — pas de sauvegarde."
fi

# --- 2. Arborescence du workspace -------------------------------------------
sudo mkdir -p "$WS/.claude/agents" "$WS/philosophy" "$WS/memory" "$WS/output"

# --- 3. Définition (toujours resynchronisée) --------------------------------
echo "Synchronisation de la définition :"
sync_def "$SRC_SOUL"  "$PROFILE/SOUL.md"
for f in "$REPO/.claude/agents/"*.md; do sync_def "$f" "$WS/.claude/agents/$(basename "$f")"; done
for f in "$SRC_PHIL"/*.md; do sync_def "$f" "$WS/philosophy/$(basename "$f")"; done
sync_def "$REPO/README.md"      "$WS/README.md"
sync_def "$SRC_MEM/README.md"   "$WS/memory/README.md"

# --- 3b. Pipeline Phase 2 (scripts versionnés) ------------------------------
echo "Synchronisation du pipeline :"
sudo mkdir -p "$PROFILE/pipeline" "$PROFILE/briefs/incoming" "$PROFILE/briefs/processed" "$PROFILE/briefs/proposals"
sudo install -m 644 "$REPO/pipeline/"*.py "$PROFILE/pipeline/"
sudo install -m 644 "$REPO/pipeline/requirements.txt" "$PROFILE/pipeline/"
echo "  def   $PROFILE/pipeline/*.py"

# --- 4. Données vivantes (créées seulement si absentes) ---------------------
echo "Données vivantes :"
seed_data "$SRC_MEM/preferences.md"  "$WS/memory/preferences.md"
sudo test -e "$WS/memory/decisions.jsonl" \
  && echo "  keep  $WS/memory/decisions.jsonl (journal préservé)" \
  || { sudo install -m 644 /dev/null "$WS/memory/decisions.jsonl"; echo "  seed  $WS/memory/decisions.jsonl"; }

# --- 5. Propriété -----------------------------------------------------------
sudo chown -R "$OWNER" "$WS" "$PROFILE/SOUL.md" "$PROFILE/pipeline" "$PROFILE/briefs"

echo ""
echo "✅ Déploiement terminé."
echo "Note : SOUL.md est lu à la CRÉATION d'une session, pas à chaque message."
echo "       Une session active garde l'ancienne définition jusqu'à son reset"
echo "       (inactivité min_idle_hours, ou 'systemctl restart hermes-gateway-social-media')."
echo "       ⚠️ NE PAS redémarrer 'hermes-gateway' (principal) : c'est un autre profil/bot."
echo "       (Token Telegram / crédits LLM : gérer .env séparément.)"
