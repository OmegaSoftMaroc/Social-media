# Social Media — Profil Hermes `social-media` (omegabot)

Workspace Claude Code du profil éditorial **Hermes Social Media** d'Abdelilah Kahaji.
Modèle de gouvernance : **Hermes orchestre · Claude Code produit · Abdelilah décide.**

## Structure
```
Social-media/
├── .claude/
│   └── agents/
│       └── editorial-writer.md     # agent de production (découvert par Claude Code)
├── Hermes social media/
│   ├── soul.md                     # prompt opérationnel d'Hermes (point d'entrée)
│   ├── philosophy/                 # canon de référence (condensé v1.1)
│   │   ├── principles.md           # vision, principes, rôles
│   │   ├── workflow.md             # mission, priorités, boucle V1
│   │   ├── memory.md               # mémoire & apprentissage
│   │   └── rules.md                # règles & limites & confidentialité
│   ├── memory/
│   │   ├── decisions.jsonl         # journal append-only des décisions
│   │   ├── preferences.md          # préférences apprises (lisible)
│   │   └── README.md               # format de la mémoire
│   └── output/                     # variantes générées (1 dossier par idée)
└── README.md
```

## Périmètre V1
- **Entrée unique : Telegram.** (Veille, YouTube, GitHub, emails, omegadev → prévus, hors V1.)
- **Pas de publication automatique.** Tout passe par la validation d'Abdelilah.
- **Un seul agent** : `editorial-writer`. Les skills viendront quand une étape de production se répète.

## Contrat I/O Hermes ⇄ Claude Code

### Invocation (headless)
Hermes appelle Claude Code en mode non interactif avec l'agent `editorial-writer` :
```bash
claude -p "<brief>" --agent editorial-writer
```
> Note : en headless, les serveurs MCP à authentification interactive peuvent être absents. La production éditoriale V1 ne doit dépendre d'aucun MCP interactif.

### Brief envoyé par Hermes (entrée)
```json
{
  "idee": "texte brut de l'idée",
  "theme": "sujet / angle",
  "audience": "à qui ça s'adresse",
  "plateformes": ["linkedin", "x"],
  "confidentialite": "public | prudent",
  "ton": "optionnel",
  "slug": "identifiant-court-kebab-case"
}
```

### Sortie attendue de Claude Code
Un **bloc JSON final autoritatif** : `slug`, `variantes[]` (chaque variante porte son **texte complet** dans `contenu`), `recommandation`, `alertes[]` (voir `.claude/agents/editorial-writer.md`).
> Le contenu vit **dans le JSON**, pas dans des fichiers : en headless, l'écriture fichier est un effet de bord non garanti. L'agent `editorial-writer` n'a donc **pas** l'outil Write.

Hermes parse ce JSON, ajoute une note issue de `memory/preferences.md`, présente le tout sur Telegram, attend la décision, **archive le JSON dans `output/<slug>/result.json`** (traçabilité gérée par Hermes), puis journalise dans `memory/decisions.jsonl`.

## Boucle V1 (10 étapes)
Idée (Telegram) → qualifier (thème/audience/confidentialité) → déléguer à `editorial-writer` → recevoir variantes + reco → enrichir via mémoire → présenter à Abdelilah → décision → journaliser → apprendre.

## Confidentialité
Secteur pêche + données clients OmegaSoft : niveau `prudent` par défaut. En `prudent`, aucun nom de client / chiffre / détail interne. Voir `Hermes social media/philosophy/rules.md`.

## Branche de travail
Développement sur `dev-kahaji` (charte OmegaSoft : jamais de commit direct sur `main`).
