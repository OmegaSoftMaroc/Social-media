# Bibliothèque de clips réutilisables — Spec

**Date :** 2026-07-15
**Auteur :** Abdelilah Kahaji (OmegaSoft) + Claude Code
**Statut :** Validé pour implémentation

## Contexte

Les clips animés image-to-video (fal.ai, `pipeline/animate.py`) sont ce qu'Abdelilah
valorise le plus dans les vidéos `narration-illustree`, mais leur **coût de génération**
freine leur usage (réf. incident kling-master 16,80 $/vidéo — mémoire
`feedback-videos-animations-cout`).

Aujourd'hui, chaque vidéo régénère ses clips depuis zéro :
- ils naissent dans `video-studio/public/illus/` (`idea-N.png` → `idea-N.mp4`),
- sont **écrasés** à chaque nouvelle vidéo (`idea-1`, `idea-2`… repartent de zéro),
- et **éparpillés** par projet dans `videos/*/`.

Aucun index → aucune réutilisation → on repaie fal à chaque fois, même pour un
mouvement abstrait déjà produit.

## Objectif

Centraliser et **indexer** les clips animés déjà générés pour pouvoir en **retrouver
et réutiliser** un *avant* tout appel fal. Réutilisation décidée par **tags/thème
manuels** (contrôle éditorial, zéro dépendance IA supplémentaire).

## Non-objectifs (YAGNI)

- Pas de recherche sémantique / embeddings (tags manuels suffisent).
- Pas de synchro Drive/multi-machine dans ce lot : **local d'abord**. L'index versionné
  suffit à la portabilité de la connaissance ; on ajoutera la synchro des binaires si le
  besoin se confirme.
- Pas de déduplication automatique par hash de still.
- Pas d'interface web : CLI uniquement.

## Architecture

### Emplacement — `clip-library/` à la racine du dépôt

```
clip-library/
├── clips/<clip-id>.mp4      # les clips (local, git-ignoré)
├── thumbs/<clip-id>.jpg     # vignette (1er frame) pour browse visuel
└── index.json               # LE catalogue, versionné dans git
```

**Principe clé : binaire local, manifeste versionné.** `clip-library/clips/` et
`clip-library/thumbs/` sont ajoutés au `.gitignore` racine (cohérent avec les MP4
déjà ignorés). `clip-library/index.json` est **suivi par git** — c'est la mémoire
portable « quel clip existe, taggé comment, coûté combien ».

Disque : ~255 Mo de clips actuels, 101 Go libres → aucune contrainte.

### Schéma `index.json`

Objet racine `{"version": 1, "clips": [ …entrées… ]}`. Une entrée :

```json
{
  "id": "flux-donnees-pushin-01",
  "file": "clips/flux-donnees-pushin-01.mp4",
  "thumb": "thumbs/flux-donnees-pushin-01.jpg",
  "tags": ["flux-donnees", "abstrait-corporate", "push-in", "bleu"],
  "description": "Flux de données bleus convergents, lent push-in",
  "model": "kling-turbo",
  "duration_s": 5,
  "cost_usd": 0.35,
  "created": "2026-07-12",
  "origin_video": "ia-securite-illustree",
  "source_still": "idea-3.png"
}
```

Champs obligatoires : `id`, `file`, `tags`, `description`. Les autres sont facultatifs
(métadonnées de provenance/coût, remplies si connues). `id` = slug `kebab-case` unique,
dérivé de la description/tags s'il n'est pas fourni ; suffixe numérique en cas de collision.

### Module `pipeline/clip_library.py` (logique métier, < 300 lignes)

Fonctions pures/services, aucune I/O réseau :

| Fonction | Rôle |
|---|---|
| `load_index(root) -> dict` | Lit `index.json` (retourne squelette vide si absent). |
| `save_index(root, data)` | Écrit `index.json` (indent 2, UTF-8, tri par `id`). |
| `add_clip(root, mp4_path, tags, description, *, clip_id=None, thumb=True, **meta) -> dict` | Copie le mp4 dans `clips/`, génère la vignette, enregistre l'entrée. **Idempotent** : réimporter le même `id` met à jour l'entrée sans dupliquer. Retourne l'entrée. |
| `make_thumb(mp4_path, out_jpg)` | 1er frame via ffmpeg (`-frames:v 1`). Échec ffmpeg → warning loggué, entrée créée sans `thumb` (non bloquant). |
| `search(root, tags=None, text=None) -> list[dict]` | Retourne les entrées classées par recouvrement de `tags` (décroissant), puis correspondance sous-chaîne sur `text` dans description/tags. |
| `get(root, clip_id) -> dict \| None` | Une entrée par `id`. |
| `reuse(root, clip_id, out_path) -> str` | Copie le clip catalogué vers `out_path`. Lève si `id` inconnu. Retourne `out_path`. |

`ROOT` par défaut = `<repo>/clip-library`, surchargable (tests → `tmp_path`).
Journalisation via `logging` (jamais `print` dans la logique — charte).

### CLI `python -m pipeline.clip_library <cmd>`

- `add <mp4> --tags a,b,c --desc "…" [--id …] [--model …] [--cost …] [--origin …]`
  → catalogue un clip.
- `ingest <glob…> --tags a,b,c [--desc …]` → import en masse de clips existants
  (ex. `ingest "video-studio/public/illus/*.mp4" --tags abstrait-corporate`).
  Tags obligatoires (cœur de l'approche manuelle). Idempotent.
- `search <texte>` / `list [--tags a,b]` → affiche `id · chemin · tags` (une ligne/clip).
- `show <id>` → détail d'une entrée (JSON lisible).

Sortie CLI = `print` (interface utilisateur, autorisé) ; la logique métier appelée
reste sur `logging`.

### Hook `animate.py` — PHASE 2 (après catalogue peuplé)

Ajout opt-in, sans changer le comportement par défaut :

- Nouveau paramètre `reuse_tags: list[str] | None = None` sur `animate_image`.
- Si `reuse_tags` fourni : appeler `clip_library.search(tags=reuse_tags)` **avant** fal.
  - Match trouvé (recouvrement ≥ 1 tag, meilleur candidat) → `reuse()` vers `out_path`,
    **log explicite** : clip réutilisé + `cost_usd` économisé. Retour immédiat, **aucun
    appel fal**.
  - Aucun match → génération fal normale, puis proposition d'ajout au catalogue.
- Jamais de match auto silencieux : le clip réutilisé est toujours loggué (charte
  « zéro panne silencieuse »). Le flag CLI `--reuse-tags a,b,c` expose l'option.

## Gestion des erreurs

- `reuse`/`get` sur `id` inconnu → `KeyError`/`ValueError` explicite (jamais silencieux).
- ffmpeg absent/échec vignette → warning loggué, l'entrée est **quand même** créée
  (la vignette est un confort, pas un bloquant).
- `index.json` absent → traité comme catalogue vide (bootstrap naturel).
- `index.json` corrompu (JSON invalide) → exception explicite, pas d'écrasement.

## Tests (pytest, charte : ≥ 1 test)

Dans `pipeline/tests/test_clip_library.py`, avec `tmp_path` comme `root` :

1. `add_clip` copie le mp4 dans `clips/` et enregistre l'entrée dans l'index.
2. **Idempotence** : réimporter le même `id` met à jour sans dupliquer (1 seule entrée).
3. `search` classe par recouvrement de tags (plus de tags communs = premier).
4. `reuse` copie le fichier vers la cible ; `reuse` sur id inconnu lève.
5. `make_thumb` : mocké/ignoré si ffmpeg indispo (le test ne dépend pas de ffmpeg).
6. Génération d'`id` : slug kebab-case + suffixe anti-collision.

Fixture : un petit mp4 factice (quelques octets) suffit pour tester copie/index sans
dépendre d'un vrai encodage.

## Découpage en lots

- **Lot 1 — Catalogue** : `.gitignore`, `pipeline/clip_library.py` (module + CLI),
  vignettes, tests. Puis `ingest` des clips existants (`illus/`, `videos/*/`).
- **Lot 2 — Hook** : `reuse_tags` dans `animate.py` + flag CLI + test du chemin de
  réutilisation (mock fal, vérifier qu'aucun appel réseau n'a lieu sur match).

Le lot 1 est livrable et utile seul (catalogue + recherche + réutilisation manuelle) ;
le lot 2 branche l'automatisation une fois le catalogue fiable.
