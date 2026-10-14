# Vidéo portfolio — 75 à 90 secondes

Enregistrer après la recette Desktop. Montrer le véritable rapport ouvert dans Desktop.

| Temps | Écran | Narration suggérée |
|---|---|---|
| 0–8 s | Circuit et KPI | « Et si Power BI permettait d'explorer un tour de Formule 1 ? » |
| 8–25 s | Pit Wall NOR ; chrono 0, 30, 60, 80 s | « J'ai préparé deux tours réels de Monza. Ici, la position et les indicateurs suivent le même instant du tour. » |
| 25–43 s | Comparison NOR/LEC ; delta et secteurs | « Je compare les pilotes au même endroit du circuit. Le delta permet de repérer où un pilote gagne ou perd du temps. » |
| 43–60 s | Strategy ; modifier stop et dégradation | « Ce modèle pédagogique simule un arrêt aux stands. Les hypothèses sont explicites et Power BI recalcule la meilleure option. » |
| 60–77 s | Vue modèle puis mesure Selected bin, Pedals SVG ou Candidate total s | « Derrière : Power Query, un modèle dimensionnel, du DAX avec TREATAS, un SVG dynamique et un projet PBIP versionné. » |
| 77–90 s | Retour rapport puis dépôt GitHub | « Une exploration manuelle de la télémétrie et une simulation, construites comme un projet logiciel reproductible. » |

Préparer toutes les sélections avant l'enregistrement. Montrer MEDIUM/HARD, dégradation 1, rythme 84 et perte 22 ; comparer arrêt 24 puis 35 pour obtenir une pénalité visible.

Éviter de présenter le curseur comme une lecture automatique, la qualification comme une prédiction de course ou les hypothèses pneus comme des mesures réelles.

## Message technique à défendre

- Python prépare les données ; les calculs et interactions de rapport sont exécutés dans Power BI.
- La comparaison repose sur la progression normalisée ; les canaux sont rééchantillonnés.
- La piste est un visuel natif ; les pédales et le plan des relais sont des SVG construits par DAX.
- Les tables déconnectées séparent le contexte des deux pilotes et celui des hypothèses.
- L'optimisation recherche le meilleur arrêt parmi les candidats du modèle ; elle ne prévoit pas les événements d'une vraie course.

## Extensions après validation

Lecture automatique dans un visuel dédié, comparaison multi-séance, field parameters, bookmarks de démonstration et stratégie à deux arrêts. Chaque extension doit conserver la distinction entre observations et hypothèses.
