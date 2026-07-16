# model-isnt-the-moat — Studio Remotion autonome

Projet **self-contained** de la vidéo « model-isnt-the-moat » : ouvrable et exécutable seul
(VS Code / terminal), sans dépendre du `video-studio/` partagé. Extrait de ce dernier.

## Démarrer

```bash
cd videos/model-isnt-the-moat/studio
npm install          # installe Remotion + deps (crée node_modules/)
npm run dev          # ouvre le studio interactif Remotion (aperçu + réglages)
```

## Rendre les shorts (1080×1920)

```bash
npm run render:fusion   # short fusionné A+B  → out/short-fusion.mp4
npm run render:a        # short A « le sursis » → out/short-A.mp4
npm run render:b        # short B « le vrai prix » → out/short-B.mp4
```

Chaque short = même composition `NarrationIllustree`, seuls changent la **voix** et les
**clips** (fichier de props dans `props/`).

## Structure

```
studio/
├── src/
│   ├── Root.tsx                 # registre des compositions (NarrationIllustree, MotionBrief)
│   ├── index.ts                 # point d'entrée Remotion
│   ├── load-font.ts             # chargement TheBoldFont
│   ├── NarrationIllustree/      # compo principale (clips + sous-titres + signature)
│   ├── MotionBrief/             # compo pilote (cartes graphiques)
│   └── PresenterPiP/            # briques partagées (fond animé, sous-titres, signature)
├── public/                      # voix (.mp3), sous-titres (.json), clips (illus/*.mp4), police, photo
├── props/                       # 1 fichier de props par short (src voix + mapping clips)
├── package.json · remotion.config.ts · tsconfig.json
```

## Notes

- `NarrationIllustree` accepte un `src` **brut** (nom de fichier) : `resolveSrc()` le résout via
  `staticFile` au runtime — c'est ce qui permet le rendu via `--props`.
- Les sous-titres (`public/*-voice.json`) sont alignés à la voix (timestamps ElevenLabs) et
  affichés **désaccentués** en capitales (TheBoldFont n'a pas de majuscules accentuées).
- Les **médias** (`public/**/*.mp4`, `*.mp3`) ne sont pas versionnés sur GitHub (trop lourds) —
  ils sont présents localement pour travailler/rendre. Pour les régénérer : voix via ElevenLabs,
  clips via `pipeline/animate.py` (fal), stills via `pipeline/visuals.py` (Ideogram).
- Scripts, plans et déclinaisons éditoriales : dossier parent `videos/model-isnt-the-moat/`.
