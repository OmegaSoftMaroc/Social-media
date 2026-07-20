# Overlay « Produire ne suffit plus » — mode d'emploi montage

Calque transparent (avatar + sous-titres + signature) à composer par-dessus **tes** visuels.
Format **1080×1920**, durée **~86 s**, **canal alpha** (centre transparent), **audio inclus** (voix avatar).

## Fichiers (2 options — choisis selon ton éditeur)
- **`metiers-overlay-chromakey.mp4`** — **8,4 Mo**, H.264 universel. Fond **magenta** à retirer par **incrustation (chroma key)**. Idéal transfert / CapCut / mobile.
- **`metiers-overlay-qtrle.mov`** — **766 Mo**, **vrai canal alpha** (QuickTime Animation). Se compose **directement**, sans keying. Pour Premiere / DaVinci / After Effects / Final Cut.
- `metiers.srt` — sous-titres (si tu veux les recaler / réutiliser).

*(Le WebM alpha léger n'est pas possible ici — le ffmpeg du serveur n'encode pas l'alpha WebM. Le ProRes 4444 2 Go a été retiré : le qtrle donne le même alpha en 3× plus léger.)*

## Comment monter

### Option A — MP4 chroma-key (léger)
1. Mets **tes visuels en piste du dessous** (plein cadre 1080×1920).
2. Pose le **MP4 au-dessus** et applique un effet **Chroma Key / Incrustation couleur** en ciblant le **magenta** (`#FF00FF`) → le fond disparaît, il ne reste que l'avatar + sous-titres + signature.
3. Règle *similarité/tolérance* pour des bords nets (le magenta n'existe nulle part dans le calque → key propre).

### Option B — qtrle alpha (direct)
1. Tes visuels en dessous, l'**overlay .mov au-dessus** → transparence native, rien à keyer.

Dans les deux cas, l'**audio** (voix) est dans le fichier — pas besoin de l'ajouter.

## Safe-zone (zones occupées par le calque — garde-les lisibles)
| Élément | Zone (x, y en px sur 1080×1920) |
|---|---|
| **Sous-titres** | bandeau **haut-milieu**, ~ y 600 → 850, pleine largeur (texte kinétique) |
| **Avatar (rond)** | **bas-droite**, ⌀380 → x 656–1036, y 1476–1856 |
| **Signature** | **bas-gauche**, ~ x 56–640, y 1700–1815 |

➡️ Ta **zone de contenu principale** = tout le centre (env. y 300 → 1450, pleine largeur) : mets-y tes visuels forts (les « 3 compétences » 1-2-3, schémas, chiffres). Le haut (sous-titres) et les deux coins bas restent au calque.

## Régénérer
- Script : `videos/produire-ne-suffit-plus/script.txt`
- Avatar source : `videos/Avatars/les_métiers_de_demain.mp4`
- Pipeline : composition `PresenterTemplate` (video-studio) → séquence PNG → encodage alpha ffmpeg. Voir mémoire `project-workflow-overlay-avatar`.
