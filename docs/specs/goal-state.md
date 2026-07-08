# Goal : Nœud social-media opérationnel en autonomie (Telegram/Hermes → Claude Code)

Démarré : 2026-07-08 — Session : 1 (run autonome /goal)
(Goal précédent « pipeline vidéo T1→T8 » complété → archivé dans goal-state-2026-07-06-video-pipeline.md)

**Règle directrice (Abdelilah) :** Hermes = intermédiaire intelligent. Il ne fait
AUCUNE tâche : il interprète/reformule mes demandes en prompts, me remplace
vis-à-vis de Claude Code, apprend (mémoire + skills), et passe le relais.
**Toutes les tâches sont exécutées par Claude Code.** Donc le Claude Code que
hermes invoque (HOME=/opt/hermes) doit être aussi capable que l'atelier root.

**Critère de succès :** depuis Telegram (profil social-media), une demande de
production vidéo est reformulée par hermes → déléguée à Claude Code → Claude Code
dispose des skills + projet + toolchain pour produire le montage (presentateur-anime)
→ mp4 livré. Preuve = 1 rendu de bout en bout déclenchable côté hermes.

## Lots
- [x] Lot 1 : Skills copiées (19 skills vidéo : hyperframes*, talking-head-recut, embedded-captions, motion-graphics, remotion-to-hyperframes, media-use…) dans /opt/hermes/.claude/skills — assets (polices, gsap) + SKILL.md OK. Install LOCALE (pas canon).
- [x] Lot 2 : Workspace /opt/hermes/work/Social-media (owned hermes, git dev-kahaji 86b05f2, video-studio + node_modules 622M + whisper 487M + 16 pipeline .py).
- [x] Lot 3 : Toolchain OK sous hermes — Chrome Headless 149 démarre (0 lib manquante), Remotion 4.0.485 liste CaptionedVideo + PresenterPiP. ffmpeg/whisper via la copie.
- [x] Lot 4 : Preuve OK — rendu PresenterPiP frames 0-60 → out/proof-hermes.mp4 (h264 1080x1920+aac). Helper montage-presentateur.sh testé bout-en-bout (transcription whisper réelle + rendu) → out/test-helper.mp4.
- [x] Lot 5 : SOUL source + live enrichis (section « Montage presentateur-anime — DÉLÉGUÉ à Claude Code » : voie rapide helper / voie riche talking-head-recut, règles visuelles 3 lignes + visage centré + zéro CTA). Déployé via deploy.sh.

## Statut : ✅ COMPLET — nœud social-media capable en autonomie (Telegram/Hermes → Claude Code)
Verrou : SOUL lu à la création de session → la *connaissance* montage de hermes s'active au
prochain reset de session (inactivité ou restart hermes-gateway-social-media) ; la *capacité*
(skills+workspace+toolchain) est déjà opérationnelle.
Décision de scope : « alerte Telegram sur échec » = pour l'automatisé (cron run_daily, déjà en
place). Le montage est INTERACTIF (délégué par hermes à Claude Code qui rapporte nativement) →
pas de cron montage, donc pas d'alerte dédiée nécessaire.

## Décisions prises en autonomie
- 2026-07-08 : Skills HyperFrames installés LOCALEMENT sur hermes, PAS dans le canon
  claude-code-config partagé (éviterait de polluer modoosoft/logico/etc.). Réversible.
- 2026-07-08 : Workspace hermes = copie (rsync) du checkout root incluant node_modules
  + whisper.cpp compilé (même machine, même arch) → parité garantie, pas de rebuild lourd.

## Points en suspens (non bloquants)
- Refresh token LinkedIn (~03/09) ; clé Ideogram à régénérer ; /opt/hermes/.env à vider (actions Abdelilah).

## Environnement vérifié (2026-07-08)
- Disque : 105 Go libres. Node v24.14.1, npm 11, npx skills 1.5.15.
- ffmpeg 6.1.1 + ffprobe : système ✓. Chromium système : absent (Remotion DL son Chrome).
- Root video-studio : node_modules 612M + whisper.cpp/ggml-small.bin présents.
