#!/usr/bin/env bash
# Montage « presentateur-anime » (template signature) : vidéo-avatar HeyGen -> clone en
# PiP rond bas-droite + phrases animées au centre (captions whisper) -> mp4 vertical 9:16.
#
# Règles visuelles gravées (cf. ../Hermes social media/philosophy/templates.md) :
#   - visage centré dans le PiP rond (yeux à mi-hauteur)
#   - signature sur 2 lignes (Enseignant-Chercheur / Expert en SI & IA)
#   - ZÉRO invitation à commenter / partager / s'abonner (règle stricte Abdelilah)
#
# Usage : ./montage-presentateur.sh <avatar.mp4> [sortie.mp4] [--frames=A-B]
#   sortie.mp4  : chemin de sortie (défaut out/presentateur-<nom>.mp4)
#   --frames=A-B: rendu partiel pour test rapide ; sans, rendu complet.
set -euo pipefail
cd "$(dirname "$0")"                       # -> video-studio/

SRC="${1:?Usage: montage-presentateur.sh <avatar.mp4> [sortie.mp4] [--frames=A-B]}"
shift
OUT=""
FRAMES=""
for a in "$@"; do
  case "$a" in
    --frames=*) FRAMES="$a" ;;
    *)          OUT="$a" ;;
  esac
done
OUT="${OUT:-out/presentateur-$(basename "${SRC%.*}").mp4}"

[ -f "$SRC" ] || { echo "Introuvable : $SRC" >&2; exit 1; }
mkdir -p out public

echo "[1/3] Préparation de l'entrée (public/input.mp4)…"
cp -f "$SRC" public/input.mp4
rm -f public/input.json                    # force une transcription fraîche

echo "[2/3] Sous-titres whisper (input.json)…"
node sub.mjs
[ -f public/input.json ] || { echo "Échec transcription : input.json absent" >&2; exit 2; }

echo "[3/3] Rendu PresenterPiP…"
npx remotion render PresenterPiP "$OUT" ${FRAMES:+$FRAMES}

echo "OK -> $OUT"
ffprobe -v error \
  -show_entries format=duration \
  -show_entries stream=width,height,codec_name \
  -of default=noprint_wrappers=1 "$OUT"
