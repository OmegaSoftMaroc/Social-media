# Goal : Pipeline vidéo — développer T1→T7 sans arrêt, stop à T8 (clés API requises)
Démarré : 2026-07-06 — Session : 1
Plan de référence : docs/superpowers/plans/2026-07-06-video-pipeline.md
Exécution : subagent-driven (1 implémenteur/tâche + revue contrôleur)

## Lots
- [x] T1 : Config vidéo — commit 03632a3, 25 tests verts
- [x] T2 : Agent video-scriptwriter — commit 1818b8a, vérifié réel (94 mots, calibrage short OK)
- [x] T3 : Connecteur ElevenLabs (TDD) — commit 1c367b2, 27 tests verts
- [ ] T4 : Connecteur HeyGen (TDD) — EN COURS : implémenteur dispatché
- [ ] T5 : Orchestrateur develop_video (TDD)
- [ ] T6 : Publication LinkedIn vidéo (publish_video_post + publish_idea video)
- [ ] T7 : Règles SOUL + push
- [ ] T8 : ARRÊT PRÉVU — déploiement + vérif réelle (exige : 4 clés ElevenLabs/HeyGen dans config/.env + re-login Claude serveur). Rapport final à cet arrêt.

## Décisions prises en autonomie
- 2026-07-06 : QA du run = suite pytest complète + vérifications locales réelles des agents (pas de staging web — projet pipeline serveur) ; push à T7.
- 2026-07-06 : à T8, exécuter uniquement le déploiement des fichiers (deploy.sh, sans risque) + contrôle des clés, puis s'arrêter et guider Abdelilah.

## Points en suspens (non bloquants)
- Refresh token LinkedIn (~03/09) non automatisé.
- Clé Ideogram à régénérer (exposée) ; /opt/hermes/.env à vider (actions Abdelilah).
- Panne curator serveur (re-login Claude) — même prérequis que T8.
