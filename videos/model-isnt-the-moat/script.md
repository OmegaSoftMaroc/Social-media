# Le modèle n'est pas votre avantage concurrentiel
## Script narration — vidéo YouTube longue (avatar AKahaji_1) + extraction Shorts

> Narration parlée, français, 1ʳᵉ personne (Abdelilah). Zéro appel à l'engagement — chute = conviction.
> Zéro chiffre inventé : seuls les chiffres réels (page Anthropic Fable 5 + expérience vécue d'Abdelilah) sont cités.
> Découpage en **segments** = 1 clip voix+avatar par segment. Les segments marqués ⭐ = candidats **Short**.

---

### SEG 01 — Accroche / thèse ⭐ (≈ 35 s)

Depuis que j'ai accès à Fable 5, j'ai dépensé plusieurs milliers de dollars en crédits.
Pas pour produire — juste pour comprendre comment tirer le meilleur d'un modèle aussi puissant.

Et la leçon que j'en retire tient en une phrase :

Oui, Fable 5 est un modèle exceptionnel. Mais le véritable avantage ne réside pas dans le modèle.

Le modèle n'est pas votre avantage concurrentiel.

---

### SEG 02 — Le débutant vs Karpathy ⭐ (≈ 45 s)

Prenons un exemple.

Imaginez un débutant en IA, et un expert du niveau d'Andrej Karpathy.

Vous donnez Fable 5, le meilleur modèle, au débutant.
Vous donnez un modèle plus ancien à l'expert.

Malgré la supériorité technique de Fable 5, c'est l'expert qui construira la meilleure solution.

Pourquoi ? Parce que ce qui fait la différence, ce n'est pas la puissance brute du modèle. C'est :
la manière de lui donner les instructions,
l'architecture qu'on bâtit autour de lui,
et les boucles de vérification et d'amélioration qu'on met en place.

La qualité du système compte davantage que la qualité du modèle.

---

### SEG 03 — L'expérience des workflows (≈ 55 s)

J'ai beaucoup testé Fable, Opus et Sonnet.

Une de mes expériences préférées : les workflows dynamiques de Claude Code.
Je demande à Fable de concevoir un workflow, puis de créer plusieurs sous-agents — qui sont eux aussi des instances de Fable.

Ensuite, je refais exactement le même test. Fable reste l'orchestrateur, mais je remplace les sous-agents par Opus, puis par Sonnet.

Le résultat m'a surpris : les performances étaient quasiment identiques.
La seule vraie différence, c'était le coût. Le workflow tout-Fable coûtait beaucoup plus cher. Les versions avec Opus ou Sonnet donnaient une qualité très proche, pour une fraction du prix.

La conclusion est simple : on ne peut pas conserver l'intelligence d'un modèle propriétaire. Mais on peut reproduire sa manière de travailler.

---

### SEG 04 — Fable comme professeur (≈ 45 s)

Alors j'ai changé d'objectif. Le but n'est pas de remplacer Fable. C'est d'utiliser Fable pour enseigner aux autres modèles.

Il faut arrêter de le voir comme un simple exécutant, et le considérer comme un professeur, un mentor, un architecte.

Quand Fable est arrivé, beaucoup ont voulu lui faire exécuter toutes leurs tâches. Et il excelle là-dedans : il planifie, définit une stratégie, exécute, vérifie, corrige.

Mais ce n'est pas forcément sa meilleure utilisation.

---

### SEG 05 — Le model routing ⭐ (≈ 50 s)

La vraie question à se poser, pour chaque tâche, est simple :

Est-ce que cette tâche a réellement besoin du modèle le plus puissant ?

Si une tâche peut être faite avec la même qualité par un modèle plus petit et beaucoup moins cher, alors le modèle premium est inutile ici.

C'est ça, le model routing : réserver les modèles les plus puissants aux décisions stratégiques, et déléguer l'exécution aux modèles économiques.

Et ça ne s'arrête pas à Anthropic. Le même raisonnement vaut pour GPT, pour Gemini, pour les modèles open source. Le bon réflexe n'est jamais « quel est le meilleur modèle », mais « quel est le bon modèle pour CETTE tâche ».

Cette compétence sera l'une des plus importantes des prochaines années.

---

### SEG 06 — Extraire la façon de penser (≈ 40 s)

Plutôt que de demander à Fable de tout faire, je lui demande comment il pense :
comment il raisonne, comment il découpe un problème, comment il vérifie son travail, comment il organise ses décisions.

Une fois cette méthode comprise, je peux la transmettre à des modèles plus petits, qui reproduiront ce raisonnement à moindre coût.

L'objectif n'est plus « que Fable fasse le travail », mais « que Fable nous apprenne à construire un système qui produit les mêmes résultats avec d'autres modèles ».

---

### SEG 07 — Les prompts système : vérifier plutôt que supposer (≈ 50 s)

Les prompts système de Fable ont récemment été divulgués. Je les ai lus, puis analysés avec Fable lui-même. Ce qui m'a frappé, ce n'est pas les instructions — c'est la façon dont elles structurent le raisonnement.

Premier principe : vérifier plutôt que supposer.

Qu'une information soit en mémoire ne veut pas dire qu'elle est encore valide.
Qu'un fichier soit mentionné ne veut pas dire qu'il existe.

Le modèle est poussé à vérifier — les faits, les fichiers, les résultats — avant de conclure. Toujours vérifier avant de conclure.

---

### SEG 08 — Répondre avant de demander (≈ 35 s)

Deuxième principe, sur les demandes ambiguës.

Au lieu de répondre « je n'ai pas compris », le modèle tente d'abord la meilleure réponse possible avec ce qu'il a. Et seulement si nécessaire, il pose une seule question de clarification.

L'idée : faire avancer le travail, au lieu de multiplier les interruptions.

---

### SEG 09 — Adapter l'effort, et « plus d'effort ≠ meilleur » ⭐ (≈ 55 s)

Troisième notion : le niveau d'effort.

Toutes les tâches ne demandent pas le même calcul. Un fait simple, c'est un effort minimal. Une recherche approfondie ou une comparaison complexe, c'est un effort élevé. Ce n'est donc pas seulement le modèle qu'on choisit — c'est aussi l'effort qu'on lui alloue.

Et là, une surprise. En poussant l'effort au maximum, j'ai plusieurs fois observé que le modèle réfléchissait beaucoup plus longtemps, coûtait beaucoup plus cher, commençait à suranalyser, et remettait inutilement en cause ses propres conclusions. Résultat parfois moins bon qu'avec un effort simplement élevé.

La leçon : le meilleur réglage n'est pas toujours le plus puissant.

---

### SEG 10 — Le Skill « Fable Mode » (≈ 50 s)

De tout ça, j'ai voulu créer un mode de travail que d'autres modèles puissent reproduire.

Si Fable produit régulièrement d'excellents résultats, il faut comprendre pourquoi. Alors je reprends ses meilleures productions et je lui demande de les analyser : comment as-tu abordé le problème, pourquoi cette stratégie, quelles vérifications, comment as-tu validé la qualité.

J'ai transformé ça en une compétence réutilisable que j'appelle « Fable Mode ». Cinq étapes :
définir le périmètre,
collecter les preuves,
attaquer le problème,
vérifier les résultats,
présenter un rapport clair.

Quand je demande à Opus d'utiliser ce mode, il ne devient pas plus intelligent — mais il travaille avec beaucoup plus de rigueur.

---

### SEG 11 — Planifier ET remettre en question (≈ 40 s)

Une chose distingue Fable d'un simple planificateur.

Beaucoup de modèles savent produire une liste d'étapes. Fable, lui, prend une posture critique : qu'est-ce qui pourrait échouer ? Quels sont les risques ? Qu'est-ce qu'on ne sait pas ? Qu'a-t-on oublié ?

Il joue volontairement l'avocat du diable. Et c'est cette remise en question permanente qui rend ses plans robustes.

---

### SEG 12 — Orchestrer des équipes de modèles + routage intelligent (≈ 55 s)

Quand Fable construit un workflow, il ne fait pas tout lui-même. Il analyse, construit la stratégie, répartit les tâches entre des modèles plus petits, récupère leurs résultats, et ajuste.

Dans mes tests, un workflow « Fable orchestrateur, Sonnet exécutant » donnait une qualité très proche du tout-Fable, pour un coût largement inférieur. Le bon architecte fait produire un excellent travail à une équipe de modèles plus simples.

L'étape suivante, c'est d'apprendre au système à choisir le bon modèle tout seul. On lui donne une table : pour chaque modèle, son coût, sa force, son usage idéal. Haiku pour le simple, Sonnet pour l'exécution, Opus pour les décisions importantes, et des modèles open source quand ils suffisent. Parce qu'à terme, ce ne sera plus seulement la qualité qui comptera, mais aussi le coût, la vitesse et les ressources.

---

### SEG 13 — Conclusion ⭐ (≈ 45 s)

Beaucoup s'inquiètent de voir Fable devenir plus cher ou plus réservé. Mais ça rappelle une réalité simple : nous ne possédons pas les modèles.

Ce qu'on peut vraiment maîtriser, ce sont nos méthodes, nos processus, nos architectures d'agents, notre façon d'orchestrer les modèles — et, demain, nos propres modèles locaux et notre matériel.

La valeur durable ne réside pas dans le modèle. Elle réside dans les systèmes et les méthodes qu'on bâtit autour.

Le modèle n'est pas le fossé. Le fossé, c'est vous.
