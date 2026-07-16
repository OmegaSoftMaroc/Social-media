# Plan de production — « Le modèle n'est pas votre avantage concurrentiel »
Format : vidéo YouTube longue (~8–9 min) + extraction de Shorts · Avatar : AKahaji_1 (`a7dff6a62e1d4518b44f550ebf8f9aa0`)

## Architecture technique (recommandée)
Narration découpée en **13 segments** → 1 clip voix (ElevenLabs) + avatar (HeyGen) **par segment**.
Raison : contourne la limite de durée HeyGen par vidéo, étale le coût crédits, permet la prévisualisation
chapitre par chapitre, et **chaque segment ⭐ devient un Short** sans re-render.
Assemblage final : composition HyperFrames (thème custom-omegasoft) — avatar + cartes graphiques + tableaux,
transitions entre chapitres, musique de fond basse.

## Visuels & tableaux — DONNÉES RÉELLES UNIQUEMENT
Source : page Anthropic « Claude Fable 5 & Mythos 5 ». Le tableau de benchmarks y est une **image** :
scores chiffrés NON disponibles → **aucun chiffre de benchmark ne sera inventé**.

Cartes/graphics prévues (toutes sur données réelles ou clairement éditoriales) :
1. **Carte « Fable 5 est exceptionnel »** (faits réels, cités) : migration Ruby 50 M lignes en **1 jour vs 2 mois** ;
   drug design accéléré **~×10** ; hypothèses biologie préférées **~80 %** du temps ; repli sur Opus 4.8 pour **>95 %** des sessions.
2. **Carte prix** : Fable 5 / Mythos 5 = **$10 / M tokens en entrée, $50 / M tokens en sortie** (réel).
3. **Tableau model routing** = heuristique éditoriale (PAS des scores mesurés, libellé comme tel) :
   tâche simple → Haiku · exécution → Sonnet · décision importante → Opus · open source quand ça suffit.
4. **Carte « effort »** : niveau minimal → élevé ; note « plus d'effort ≠ meilleur » — **qualitatif**, présenté comme expérience vécue.
5. **Carte « Fable Mode »** : les 5 étapes (périmètre / preuves / attaque / vérification / rapport).
6. **Carte thèse/chute** : « La valeur est dans le système, pas dans le modèle. »

⚠️ Pas de reproduction du graphe de benchmark d'Anthropic (image propriétaire + chiffres non lisibles).
⚠️ La comparaison « Fable faible effort ≈ Opus effort élevé » et « GPT-5.5 » restent **qualitatives** (ton expérience), jamais un tableau chiffré.

## Carte des Shorts (segments ⭐ auto-extractibles)
- **Short A** — SEG 01 + 02 : « Le débutant avec le meilleur modèle vs l'expert avec l'ancien » (thèse). ~70 s
- **Short B** — SEG 05 : « Le model routing en 1 minute » (+ généralisation GPT/Gemini/open source). ~50 s
- **Short C** — SEG 09 : « Plus d'effort ≠ meilleur résultat ». ~55 s
- **Short D** — SEG 13 : « Nous ne possédons pas les modèles » (chute). ~45 s

## Pipeline d'exécution (après validation)
1. Générer la voix ElevenLabs par segment (13 clips).
2. Générer l'avatar HeyGen par segment (AKahaji_1) — surveiller les crédits (715 dispo).
3. Transcrire chaque segment (whisper) pour caler les cartes.
4. Assembler la composition HyperFrames longue + les 4 Shorts.
5. Rendre, QA visuel (visage centré, zéro CTA, signature), déposer sur Drive — NON publié.

## Risques / points ouverts à valider
- **Coût crédits HeyGen** : 13 clips avatar. À confirmer que 715 crédits suffisent (dépend de la durée totale ~8 min).
- **Longueur** : ~8–9 min. OK pour toi, ou version condensée ~5 min ?
- **Redondance de fond** : la thèse « le modèle = outil, la valeur = le système » recoupe le cœur de `cadrage-metier`
  (chute « le modèle = un outil / le cadrage = ton actif »). Différenciateurs ici : format long, profondeur technique
  (model routing, Fable Mode, niveaux d'effort, orchestration). À confirmer que cet approfondissement te convient.
- **Titre** : « Le modèle n'est pas votre avantage concurrentiel » (alt : « The Model Isn't the Moat »).
