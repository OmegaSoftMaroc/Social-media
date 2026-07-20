# Pipeline vidéo — HeyGen + ElevenLabs (voix clonée + avatar filmé)
Date : 2026-07-06
Statut : design validé (en attente relecture)
Auteur : Abdelilah Kahaji (OmegaSoft) + Claude Code

## Contexte
La plateforme éditoriale produit aujourd'hui : idées (curation YouTube quotidienne) → posts + visuels brandés → Drive → publication LinkedIn après validation. Cette tranche ajoute la **vidéo multimédia** : l'avatar filmé d'Abdelilah présente le contenu avec **sa voix clonée**, pour des posts vidéo LinkedIn et des Shorts/Reels. C'était la vision initiale du profil (placeholders `ELEVENLABS_*`/`HEYGEN_*` déjà présents dans `config/.env`).

## Décisions de cadrage (validées)
- **Livrables** : vidéo LinkedIn (60-90 s, 16:9 ou 1:1) **et** Short/Reel (30-45 s, 9:16) — **au choix par idée** via un paramètre `--format`.
- **Voix** : voix clonée d'Abdelilah (ElevenLabs, `ELEVENLABS_VOICE_ID`).
- **Avatar** : avatar vidéo **custom filmé** (HeyGen, `HEYGEN_AVATAR_ID`).
- **Sortie V1** : dépôt **Drive (dossier Videos)** systématique + publication sur **canal au choix à la validation** — LinkedIn disponible en V1 ; YouTube/Instagram/TikTok en tranche 2.
- **Approche** : extension du pipeline Python existant (A) — pas d'orchestration LLM, pas de n8n.
- **Human-in-the-loop inchangé** : AUCUNE publication sans validation explicite d'Abdelilah.

## Flux de bout en bout
```
Idée (briefs/proposals ou 01_Idees)
  ↓  python -m pipeline.develop_video <N> --format linkedin|short
[1] Agent video-scriptwriter  → script parlé + titre + description (JSON)
[2] ElevenLabs TTS (voix clonée) → briefs/output/<slug>/audio.mp3
[3] HeyGen create_video (avatar + audio, ratio selon format) → job id
[4] Polling statut (intervalle 20 s, timeout 15 min) → download video.mp4
[5] Upload Drive (dossier Videos) + notification Telegram (lien + coût crédits)
  ↓  validation d'Abdelilah : « publie la vidéo N sur linkedin »
[6] publish_video_post (LinkedIn) → confirmation + journalisation decisions.jsonl
```

## Composants

### Agent `.claude/agents/video-scriptwriter.md` (nouveau, lecture seule)
- **Entrée** (dans le prompt) : l'idée (titre, angle, pilier) ou le post déjà développé, + le `format` demandé.
- **Production** : script **parlé** (oral, pas un post lu) : hook < 3 s, corps, CTA final ; en français ; longueur calibrée (linkedin : ~150-220 mots ≈ 60-90 s ; short : ~70-110 mots ≈ 30-45 s).
- **Règles** : mêmes garde-fous que `editorial-writer` (rien d'inventé, confidentialité `prudent`, pas de jargon).
- **Sortie JSON autoritative** : `{"format", "script", "titre", "description", "duree_estimee_s", "alertes"}` — le script est le livrable, aucun fichier écrit.

### `pipeline/elevenlabs.py` (nouveau)
- `synthesize(script: str, out_path: str) -> str` : POST `text-to-speech/{VOICE_ID}` (modèle multilingue), sortie mp3. Clé `ELEVENLABS_API_KEY`, voix `ELEVENLABS_VOICE_ID` (config/.env).
- Fonction pure associée : `estimate_cost_chars(script)` (suivi conso caractères).

### `pipeline/heygen.py` (nouveau)
- `upload_audio(path) -> asset_id`
- `create_video(audio_asset, avatar_id, ratio) -> video_id` — ratio `16:9`/`1:1` (linkedin) ou `9:16` (short), fond neutre brand (navy).
- `wait_and_download(video_id, out_path, poll_s=20, timeout_s=900) -> str`
- Fonctions pures : construction des payloads, parsing des statuts (`processing/completed/failed`).
- ⚠️ Endpoints/paramètres HeyGen v2 **à confirmer contre la doc au moment de l'implémentation** (comme fait pour Ideogram/Google — l'API évolue).

### `pipeline/develop_video.py` (nouveau, orchestrateur)
- CLI : `python -m pipeline.develop_video <N> [--format linkedin|short]` (défaut : linkedin). `<N>` = index dans `briefs/proposals/latest.json`, ou `--slug ideeN` pour partir d'un post déjà développé.
- Étapes [1]→[5] ; chaque artefact conservé dans `briefs/output/<slug>/` (`script.json`, `audio.mp3`, `video.mp4`) → **relance possible à mi-chemin** sans regénérer ce qui existe.
- Upload Drive via `google_workspace.upload_file` (dossier **Videos** existant, id résolu par `find_or_create_folder`).
- Notification Telegram via `send_telegram` (lien Drive + durée + crédits consommés).

### `pipeline/linkedin.py` (extension)
- `publish_video_post(text, video_path)` : même mécanique que `publish_image_post` (register upload `feedshare-video`, PUT binaire, post `shareMediaCategory=VIDEO`).

### `deploy/SOUL.md` (extension)
- Règle : quand Abdelilah demande une vidéo (« fais la vidéo de l'idée N », « en short ») → `develop_video` ; quand il **valide** (« publie la vidéo N sur linkedin ») → `publish_video_post`. Jamais de publication sans validation explicite.

### Config (`pipeline/config.py` + `config/.env`)
- `.env` : `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `HEYGEN_API_KEY`, `HEYGEN_AVATAR_ID` (placeholders déjà présents, à renseigner).
- `config.py` : endpoints, ratios par format, timeouts, dossier Drive Videos.

## Prérequis externes (actions Abdelilah, guidées pas à pas)
1. **ElevenLabs** : compte + plan avec voice cloning (Starter ~5 $/mois ou Creator ~22 $/mois) ; upload **10-20 min d'audio propre** de sa voix → récupérer `VOICE_ID` + clé API.
2. **HeyGen** : compte + plan permettant l'avatar custom (Creator ~29 $/mois) ; **tournage 2-5 min** selon le protocole HeyGen → `AVATAR_ID` ; activer l'**offre API** (tier gratuit limité puis payant — tarifs exacts vérifiés à l'implémentation).
3. Renseigner les 4 clés dans `config/.env` (chmod 600 conservé).

## Gestion d'erreurs & coûts
- Toute exception dans `develop_video` → **alerte Telegram** (réutilise le mécanisme de `run_daily`) ; les artefacts déjà produits restent sur disque (idempotence par étape : si `audio.mp3` existe, on ne refait pas le TTS).
- Polling HeyGen borné (timeout 15 min) ; statut `failed` → message d'erreur HeyGen remonté dans l'alerte.
- Coûts affichés dans la notification (caractères ElevenLabs, crédits HeyGen) pour suivi de conso.
- Les fichiers vidéo (Mo) ne sont **pas commités** ; ils vivent dans `briefs/output/` (serveur) + Drive.

## Tests
- **Unitaires (pytest, sans réseau)** : payloads ElevenLabs/HeyGen, parsing des statuts, calibrage longueur script par format, nommage/chemins artefacts, logique « skip si artefact existant ».
- **Intégration au déploiement (réel, étape par étape)** : (1) TTS seul sur une phrase → écoute ; (2) vidéo test courte (10 s) → coût minimal ; (3) chaîne complète sur une idée réelle → Drive + Telegram ; (4) publication LinkedIn après validation explicite.

## Hors scope V1 (YAGNI)
- Upload automatisé YouTube / Instagram / TikTok (tranche 2 — OAuth dédiés).
- Sous-titres incrustés, B-roll, montage multi-scènes, musiques.
- Génération vidéo planifiée automatique (V1 = à la demande, idée par idée).
- Traductions/versions multilingues.

## Critères de succès
1. `develop_video <N> --format short` produit un mp4 9:16 avec la voix clonée et l'avatar filmé, déposé sur Drive, notifié sur Telegram.
2. « publie la vidéo N sur linkedin » publie le post vidéo — uniquement après validation.
3. Un échec quelconque notifie Telegram (zéro panne silencieuse).
4. Relance après échec sans regénérer les étapes déjà réussies.
