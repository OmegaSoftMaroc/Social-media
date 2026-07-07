# Banque de templates — contenus OmegaSoft
Version : 1.0 (créée le 2026-07-06, validée par Abdelilah)

> Registre des formats réutilisables. Quand Abdelilah demande un contenu, utiliser
> le template par son nom. Tout nouveau format validé DOIT être ajouté ici.
> Règle transverse (stricte) : **jamais d'appel à l'engagement** — finir sur une conviction.

## 🖼️ visuel-accroche — post image
- **Usage** : visuel des posts LinkedIn texte+image (défaut de `develop_idea`).
- **Recette** : fond Ideogram abstrait (prompt_visuel de l'agent, sans personnage/texte)
  → accroche incrustée (bandeau navy, `add_headline`) → photo Abdelilah en rond bas-droite.
- **Specs** : 1080×1350 (4:5), palette navy/teal/accent.
- **Exemple validé** : « Données propres d'abord, IA ensuite » (idee2, Drive/Visuels).

## 🎥 avatar-plein-ecran — vidéo brute
- **Usage** : posts vidéo LinkedIn sobres (l'avatar parle plein cadre).
- **Recette** : `develop_video N --format linkedin|short` (HeyGen seul, sans post-traitement).
- **Specs** : 1280×720 ou 720×1280 ; voix clonée ElevenLabs par défaut.

## 💬 sous-titres-tiktok — vidéo sous-titrée
- **Usage** : Shorts/Reels sobres (regardés sans le son).
- **Recette** : vidéo avatar → `video-studio` : `public/input.mp4` + `node sub.mjs`
  (whisper FR) → rendu composition Remotion **CaptionedVideo**.
- **Specs** : 1080×1920, sous-titres word-by-word style TikTok.

## ⭐ presentateur-anime — LE template signature (validé 2026-07-06)
- **Usage** : Shorts/Reels à fort engagement — format préféré d'Abdelilah.
- **Recette** : vidéo avatar (voix clonée) → `video-studio` : `public/input.mp4` +
  `node sub.mjs` → rendu composition Remotion **PresenterPiP**.
- **Composition (v4, réglages validés — NE PAS modifier sans validation)** :
  - Fond navy dégradé + formes géométriques dérivantes (teal/accent discrets).
  - **Texte centré sur le tableau** : pile de 3 phrases (2 précédentes estompées 46px,
    courante 66px animée mot-à-mot ; mot courant en ACCENT #FFB454, mots ≥8 lettres en TEAL #2AA7A0).
  - **Icône SVG line-art bas-gauche** (badge arrondi, trait teal) UNIQUEMENT si un
    mot-clé du propos le justifie (cible/graph/puce/usine/fusée/check/prise/ampoule) — jamais d'émoji.
  - **Clone en rond bas-droite** : Ø380px, liseré blanc 7px, zoom ×2.05, cadrage visage
    (objectPosition center 30% / origin center 34%).
  - Signature bas-gauche — RÈGLE STRICTE (précisée 2026-07-07) : **exactement 3 lignes** —
    ligne 1 « **Abdelilah Kahaji** » ·
    ligne 2 « Enseignant-Chercheur » ·
    ligne 3 « Expert en Systèmes d'Information & Intelligence Artificielle ».
    S'applique à TOUS les templates vidéo.
  - RÈGLE STRICTE (remarque récurrente d'Abdelilah) : dans tout PiP rond, le **visage
    doit être centré dans le cercle** (yeux ≈ mi-hauteur). Toujours vérifier sur une
    frame rendue avant le rendu final ; ajuster object-position/zoom selon le cadrage
    source (chaque vidéo HeyGen a un cadrage différent).
  - Chute du script = conviction (JAMAIS de « dites-le-moi en commentaire »).
- **Specs** : 1080×1920 (9:16), whisper `small` FR (passer à `medium` si transcription imparfaite).
- **Exemple validé & publié** : idee2 v4 — LinkedIn `urn:li:ugcPost:7480042921208139777`.

## Comment ajouter un template
1. Itérer le format avec Abdelilah jusqu'à validation explicite.
2. L'ajouter ici (nom kebab-case, usage, recette, specs, exemple).
3. L'ajouter dans la feuille « Planning Editorial » onglet 04_Resources (type=template).
4. Si Remotion : la composition vit dans `video-studio/src/<Nom>/`.
