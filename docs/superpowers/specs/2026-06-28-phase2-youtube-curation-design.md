# Phase 2 — Tranche 1 : Pipeline YouTube → curation d'idées → draft validé
Date : 2026-06-28
Statut : design validé (en attente relecture)
Auteur : Abdelilah Kahaji (OmegaSoft) + Claude Code

## Contexte
La V1 du profil éditorial Hermes `social-media` est opérationnelle : Abdelilah envoie une idée sur Telegram, Hermes délègue à l'agent `editorial-writer`, présente les variantes, Abdelilah décide. Aucune ingestion automatique, aucune publication automatique.

La Phase 2 vise à **automatiser l'amont** : analyser des sources selon un planning et **proposer des idées de publication**, tout en gardant la validation humaine. Cette tranche 1 couvre **une seule source (YouTube)** de bout en bout, pour prouver la valeur avant de répliquer aux autres sources.

## Objectifs (scope tranche 1)
- Détecter automatiquement les nouvelles vidéos des chaînes suivies (planning **quotidien, matin**).
- **Proposer 3 à 5 idées** de publication par run, classées selon les **5 piliers de marque** et équilibrées dans le temps selon leur pondération.
- Double validation : Abdelilah **choisit une idée**, puis **valide le draft final**.
- Sortie = **draft prêt à copier-coller** (pas d'API de publication en tranche 1).
- Réutiliser au maximum l'existant : `youtube_monitor.py`, agent `editorial-writer`, mémoire V1.

## Hors scope (tranches suivantes)
- APIs de publication (LinkedIn / X) et auto-post.
- Autres sources (cours ENSA, déploiements Docker, tests Claude Code, réunions, projets/réponses clients…).
- Génération d'images / prompts visuels.

## Les 5 piliers de marque (source de vérité)
À matérialiser dans `Hermes social media/philosophy/pillars.md` (lisible par `editorial-curator` et `editorial-writer`) :

| # | Pilier | Poids | Exemples |
|---|---|---|---|
| 1 | IA appliquée | ~35% | Claude Code, agents IA, GPT, Gemini, automatisation, MCP, n8n |
| 2 | Transformation numérique industrielle | ~25% | ERP, digitalisation, industrie, pêche, PME |
| 3 | Coulisses OmegaSoft (sans confidentiel) | ~20% | « automatisé un déploiement qui prenait 2h » |
| 4 | Enseignement | ~10% | séances ENSA |
| 5 | Vision | ~10% | « pourquoi les PME marocaines doivent adopter les agents IA » |

## Architecture (approche C — hybride avec file)
Découplage en étapes à responsabilité unique. Coût maîtrisé : détection = Gemini (économique) ; curation + génération = **Claude Code** (Claude Max via `HOME=/opt/hermes`, hors crédits OpenRouter d'Hermes) ; Hermes-LLM uniquement pour la conversation Telegram.

```
PLANNING (cron quotidien, matin ~07:30)
  1. DÉTECTION   youtube_monitor.py → nouvelles vidéos + résumé Gemini → briefs/incoming/<id>.json
  2. CURATION    editorial-curator (Claude Code) lit briefs/incoming/ + pillars.md + decisions.jsonl
                  → 3-5 idées classées/équilibrées par pilier → briefs/proposals/<date>.json
  3. PRÉSENTATION orchestrateur envoie la liste numérotée sur Telegram (hermes send)
  4. CHOIX        Abdelilah répond un numéro → Hermes lit briefs/proposals/latest.json → brief
  5. GÉNÉRATION   editorial-writer (réutilisé) → variantes multi-plateformes
  6. VALIDATION   variantes sur Telegram → Abdelilah valide → DRAFT prêt à copier-coller
  7. MÉMOIRE      decisions.jsonl (idée retenue, pilier, source) + preferences.md
```

## Composants

### youtube_monitor.py (réutilisé, retouches mineures)
- Garder : détection RSS, fenêtre récence, dédup `seen_videos.json`, résumé Gemini.
- Retirer : le routage `personnel/OmegaSoft` (remplacé par le classement par pilier en aval).
- Ajouter : écriture de chaque nouvelle vidéo comme item dans `briefs/incoming/<video_id>.json` (au lieu du seul print JSON).
- Liste des chaînes : à revalider avec Abdelilah (les 6 actuelles sont orientées IA/tech → pilier 1).

### File `briefs/`
- `briefs/incoming/<video_id>.json` — opportunités détectées non encore curées.
- `briefs/processed/<video_id>.json` — déplacées après curation (rejouable, traçable).
- `briefs/proposals/<date>.json` + `briefs/proposals/latest.json` — les 3-5 idées du jour.

### Agent `editorial-curator` (nouveau, lecture seule)
- **Entrée** : items de `briefs/incoming/`, `pillars.md`, historique `decisions.jsonl` (pour pondération + éviter répétition).
- **Sortie JSON** (autoritative) :
```json
{
  "date": "2026-06-28",
  "idees": [
    {
      "id": "idee-1",
      "pilier": 1,
      "titre": "pitch court de l'idée",
      "angle": "pourquoi c'est pertinent maintenant",
      "plateformes_suggerees": ["linkedin", "x"],
      "source": {"type": "youtube", "url": "...", "chaine": "@..."},
      "confidentialite": "public"
    }
  ],
  "equilibrage": "note sur la pondération des piliers respectée",
  "recommandation": {"id": "idee-1", "pourquoi": "..."}
}
```
- **Règles** : 3 à 5 idées ; respecter la pondération 35/25/20/10/10 dans la durée ; ne pas inventer ; niveau `prudent` par défaut.

### Agent `editorial-writer` (réutilisé tel quel)
Reçoit le brief construit à partir de l'idée choisie (schéma V1 inchangé) → variantes + recommandation + alertes.

### Orchestrateur (wrapper léger, nouveau)
Script lancé par le cron : exécute le monitor, lance `editorial-curator` via `HOME=/opt/hermes claude -p ... --agent editorial-curator`, écrit `proposals/latest.json`, puis envoie la liste numérotée sur Telegram via `hermes send`. Si une étape échoue, les items restent dans `incoming/` (rejouable).

### SOUL.md (règle de résolution du choix)
Ajouter au workflow V1 : « Quand Abdelilah répond par un numéro d'idée, lire `briefs/proposals/latest.json`, prendre l'idée correspondante, construire le brief et déléguer à `editorial-writer`. Après validation, déplacer l'item de `incoming/` vers `processed/` et journaliser dans `decisions.jsonl`. »

## Confidentialité
YouTube = public → risque faible. Le design conserve le niveau `prudent` et un emplacement « filtre confidentialité » (no-op en tranche 1) pour les sources sensibles des tranches suivantes.

## Mémoire & apprentissage
`decisions.jsonl` enregistre : idée retenue, pilier, source, draft choisi, corrections. `editorial-curator` exploite cet historique pour équilibrer les piliers et éviter les répétitions. `preferences.md` synthétise les tendances (jours/formats/piliers préférés).

## Planning
- Cron **quotidien, matin (~07:30)** : détection + curation → propositions sur Telegram.
- **3 à 5 idées** par run.
- Paramètres (cadence, nombre d'idées, heure, liste de chaînes) centralisés dans un fichier de config du profil.

## Vérification (test bout-en-bout)
1. Lancer `youtube_monitor.py` manuellement → vérifier des items dans `briefs/incoming/`.
2. Lancer `editorial-curator` sur la file → vérifier un JSON 3-5 idées valide, piliers cohérents.
3. Simuler l'envoi Telegram (`hermes send`) de la liste numérotée.
4. Répondre un numéro → vérifier que Hermes résout via `proposals/latest.json`, construit le brief et appelle `editorial-writer` (déjà validé en V1).
5. Valider un draft → vérifier journalisation `decisions.jsonl` + déplacement vers `processed/`.
6. Run réel via cron le lendemain matin.

## Risques / dépendances
- **Crédits OpenRouter** (cerveau Hermes) : impactent seulement la conversation Telegram, pas la génération (Claude Code). Surveiller le `402`.
- **Qualité de la curation** : dépend des résumés Gemini ; itérer le prompt `editorial-curator` après les premiers runs.
- **Liste de chaînes** : à revalider pour coller aux piliers.

## Tranches suivantes (aperçu)
T2 : API LinkedIn (auto-post après validation). T3 : sources « activité technique » (Docker/Claude Code) → pilier Coulisses. T4 : sources semi-manuelles (ENSA, réunions) avec filtre confidentialité renforcé.
