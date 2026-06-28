# Rapport : Visuels Réseaux Sociaux B2B — OmegaSoft
Date : 2026-06-28 · Destinataire : Abdelilah Kahaji

Objectif : choisir des outils et une stratégie visuelle pour les publications LinkedIn/X/Facebook du pipeline éditorial automatisé.

## 1. Bonnes pratiques visuelles LinkedIn B2B 2025-2026

### Formats qui performent
| Format | Engagement moyen | Atout clé |
|---|---|---|
| Carrousel PDF (Document post) | ~6,6 % (meilleur) | +39 % reach, +30 % engagement vs post standard |
| Vidéo native verticale | ~5,6 % | +71 % d'impressions vs horizontal |
| Infographie statique | ~5,4× vs texte | Très « sauvegardable », fort signal algo |
| Post texte seul | ~1-2 % | Facile mais peu différenciant |

Règle d'or : carrousel pour un processus en étapes ; infographie pour prouver un point avec des données.

### Dimensions techniques 2026
| Usage | Dimensions | Format |
|---|---|---|
| Slide carrousel (portrait 4:5) | 1080 × 1350 px | PDF (1 doc = 1 carrousel) |
| Carrousel carré (safe) | 1080 × 1080 px | PDF |
| Image unique | 1080 × 1350 px | JPG/PNG < 3 Mo |
| Aperçu lien | 1200 × 627 px | JPG/PNG |
| Zone safe | centre 880 × 880 px | marge 80 px |

Slides : viser 8-12 (max 20).

### Cohérence de marque
1. Palette verrouillée : 1 primaire + 1 secondaire + 1 accent + neutre (codes HEX dans un Brand Kit). Pistes OmegaSoft : bleu marine / vert foncé / ardoise + accent énergie.
2. Typographie 2 niveaux : 1 police titre (Inter Bold, Sora, DM Sans) + 1 corps (Inter/Lato). Éviter 3+ polices.
3. Template modulaire : 4-5 layouts (intro, contenu, citation, statistique, CTA) ; reconnaissable « OmegaSoft » en 0,3 s.

## 2. Comparatif outils de génération d'images IA
| Outil | Type | Texte dans image | API Python | Prix indicatif | Usage commercial |
|---|---|---|---|---|---|
| GPT Image 1.5 (OpenAI) | Généraliste | Bon | Oui (SDK) | 0,02 → 0,19 $/img | Oui |
| **Ideogram 4.0** | Spécialiste texte+image | **Excellent (~82 %)** | Oui (REST) | 0,03-0,09 $/img ; 7-42 $/mois | Oui |
| Midjourney v7 | Artistique | Moyen | Non officielle (risqué) | 10-120 $/mois | Oui (< 1 M$) |
| Recraft V4 | Design/vecteur SVG | Bon | Oui (REST) | 0,04 $/img ; SVG 0,08 $ | Oui (payant) |
| Adobe Firefly | Photo/IP-safe | Moyen | Oui (enterprise) | min. 1000 $/mois | Meilleur (indemnisation IP) |
| FLUX 1.1 Pro | Polyvalent | Moyen | Oui | 0,04 $/img ; Schnell gratuit | Pro payant ; Schnell Apache 2.0 |
| Leonardo AI | Photo-réaliste | Faible | Oui | 10-49 $/mois | Oui |

Points clés : **Ideogram** = n°1 pour le texte intégré (citations/titres/stats). GPT Image 1.5 = n°2 si clé OpenAI déjà présente. Recraft = unique pour SVG vectoriel. Midjourney/Firefly à exclure (pas d'API fiable / coût enterprise).

## 3. Outils de design templaté
- **Canva** : 1170+ templates, Brand Kit, mais **pas d'API publique stable** pour le bulk → production manuelle (15 $/mois).
- **Contentdrips** (recommandé API) : spécialiste carrousel LinkedIn, **API REST**, bulk CSV, intégration n8n/Make → PDF prêt. 26 $/mois (Pro/API).
- **Taplio** : rédaction IA + carrousels, mais 39-199 $/mois et extension Chrome risquée (CGU LinkedIn).
- **AuthoredUp** : éditeur natif LinkedIn (mise en forme, preview, analytics), pas d'IA/API. 19,95 $/mois.

## 4. Infographies / schémas (vulgariser IA/ERP)
| Outil | Texte→visuel auto | Style | Export | Pipeline | Prix |
|---|---|---|---|---|---|
| Napkin.ai | Oui (IA) | Pro, clean | PNG/SVG/PDF | Non (manuel) | Freemium |
| Mermaid | Oui (code) | Minimal technique | PNG/SVG | Oui (lib Python) | Gratuit |
| Excalidraw | Non (manuel) | Whiteboard sketch | PNG/SVG | Oui (self-host) | Gratuit |

## 5. Recommandation — Stack visuelle de départ
- **Niveau 1 — Images avec texte/marque** → Ideogram 4.0 API (~5-15 $/mois pour 150 posts).
- **Niveau 2 — Carrousels** → Contentdrips API (26 $/mois).
- **Niveau 3 — Schémas** → Napkin.ai (gratuit) + Mermaid (auto, pipeline).
- **Budget ≈ 40-55 $/mois.**

### Intégration au pipeline
L'agent génère un **prompt visuel** → selon le besoin : Ideogram (image avec texte), Contentdrips (carrousel PDF), ou Mermaid (schéma) → asset joint au post.

### Prochaines étapes
1. Tester Ideogram API (clé + 10 visuels aux couleurs OmegaSoft, valider le texte FR).
2. Créer 4-5 templates Brand Kit (Contentdrips/Canva).
3. Brancher les API dans le pipeline (nœud « génération visuelle »).
4. Tester Napkin.ai sur les piliers IA/industrie.
5. Évaluer FLUX Schnell si le volume augmente (~0,003 $/img).

## Sources principales
ContentIn, Morphica, Postiv, Contentdrips, LumiChats, MindStudio, APIScout, CostGoat, Black Forest Labs, CheckThat.ai, Evolink, ConnectSafely, AI Tool Finder, FrontMatter (URLs dans le rapport d'origine).
