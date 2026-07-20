# Mémoire Hermes — format

## `decisions.jsonl`
Journal append-only : **une ligne JSON par décision d'Abdelilah**. Ne jamais réécrire les lignes passées.

Schéma d'une ligne :
```json
{
  "date": "2026-06-28T14:30:00+01:00",
  "slug": "retour-salon-peche",
  "idee": "Partager un retour du salon Halieutis",
  "contexte": {"theme": "...", "audience": "...", "plateformes": ["linkedin"], "confidentialite": "prudent"},
  "propositions": ["linkedin-a", "linkedin-b"],
  "reco_claude_code": "linkedin-a",
  "reco_hermes": "linkedin-a",
  "choix_abdelilah": "linkedin-b",
  "corrections": "raccourci l'accroche",
  "resultat": null,
  "enseignements": "préfère le format storytelling le mardi"
}
```

Champs `resultat` et `enseignements` peuvent être complétés a posteriori via une **nouvelle ligne** référençant le même `slug` (jamais en modifiant l'ancienne).

## `preferences.md`
Synthèse humaine des tendances dégagées de `decisions.jsonl`. Mise à jour uniquement après validation d'Abdelilah.
