#!/usr/bin/env bash
# Montage « narration-animee » — variante du presentateur-anime SANS avatar :
# fond animé + texte kinétique centré + icône contextuelle + signature + VOIX off.
# Pas de visage. Entrée : un fichier audio (voix ElevenLabs/HeyGen) OU une vidéo
# dont on extrait la voix.
#
# Règles visuelles (cf. ../Hermes social media/philosophy/templates.md) :
#   - signature sur 2 lignes (Enseignant-Chercheur / Expert en SI & IA)
#   - ZÉRO invitation à commenter / partager / s'abonner.
#
# Usage : ./montage-narration.sh <voix.mp3|video.mp4> [sortie.mp4] [--frames=A-B]
set -euo pipefail
cd "$(dirname "$0")"                        # -> video-studio/

SRC="${1:?Usage: montage-narration.sh <voix.mp3|video.mp4> [sortie.mp4] [--frames=A-B]}"
shift
OUT=""
FRAMES=""
for a in "$@"; do
  case "$a" in
    --frames=*) FRAMES="$a" ;;
    *)          OUT="$a" ;;
  esac
done
OUT="${OUT:-out/narration-$(basename "${SRC%.*}").mp4}"

[ -f "$SRC" ] || { echo "Introuvable : $SRC" >&2; exit 1; }
mkdir -p out public

echo "[1/3] Extraction de la voix (public/narration.mp3)…"
npx remotion ffmpeg -i "$SRC" -vn -acodec libmp3lame -q:a 2 public/narration.mp3 -y
rm -f public/narration.json                 # force une transcription fraîche

echo "[2/3] Sous-titres whisper (narration.json)…"
node sub.mjs
[ -f public/narration.json ] || { echo "Échec transcription : narration.json absent" >&2; exit 2; }

echo "[3/3] Rendu NarrationAnimee…"
npx remotion render NarrationAnimee "$OUT" ${FRAMES:+$FRAMES}

echo "OK -> $OUT"
ffprobe -v error \
  -show_entries format=duration \
  -show_entries stream=width,height,codec_name \
  -of default=noprint_wrappers=1 "$OUT"
