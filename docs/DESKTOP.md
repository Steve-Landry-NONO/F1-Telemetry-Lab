# Recette Power BI Desktop — version 0.2

## Ouvrir la bonne version

Fermer le projet précédent. Télécharger la branche feat/telemetry-lab-mvp, puis extraire le dossier dans un **nouveau dossier**. Cela évite de réutiliser le cache ou les modifications de la version 0.1.

Ouvrir powerbi/F1 Telemetry Lab.pbip dans Power BI Desktop Windows récent. Si demandé, activer le format de métadonnées amélioré PBIR dans les options de préversion, puis redémarrer Desktop.

Cliquer **Actualiser** et attendre la fin du chargement. Les CSV sont embarqués, sans chemin externe. Le bandeau doit indiquer deux tours et 1 002 points.

Les pages attendues sont **01 · Pit Wall**, **02 · Duel de pilotes**, **03 · Stratégie**. Si les anciens intitulés apparaissent, la version ouverte n'est pas la 0.2.

## Vérifier le replay

NOR et 30 s sont sélectionnés initialement. Le curseur est de type « Avant » : son maximum sélectionné représente le temps demandé. Si le style varie selon la version Desktop, conserver ce mode.

| Pilote / chrono | Temps de l'échantillon | Vitesse | Rapport | Progression |
|---|---:|---:|---:|---:|
| NOR / 0 s | 0,000 s | 319,925 km/h | 8 | 0 % |
| NOR / 30 s | 29,916 s | 117,237 km/h | 3 | 36,6 % |
| NOR / 60 s | 59,964 s | 273,888 km/h | 7 | 72,8 % |
| NOR / 80 s | 79,327 s | 318,170 km/h | 8 | 100 % |
| LEC / 30 s | 29,963 s | 112,494 km/h | 4 | 36,8 % |
| LEC / 80 s | 79,461 s | 321,000 km/h | 8 | 100 % |

Tolérance : arrondi d'affichage, maximum 0,001 s / 0,01 km/h sur les valeurs non arrondies. La jauge peut afficher la vitesse entière.

Le point agrandi, la jauge, le rapport, la progression, les pédales et le marqueur du profil de vitesse doivent suivre le même instant. Les courbes et la piste doivent rester complètes. Un clic sur une courbe ne doit pas changer les autres vues.

## Vérifier le duel

| Sélection | Résultat |
|---|---|
| A=NOR / B=LEC | 79,327 s / 79,461 s ; delta final +0,134 s |
| A=NOR / B=LEC, secteurs | −0,119 / +0,153 / +0,100 s |
| A=LEC / B=NOR | Tous les deltas changent de signe |
| A=B | Courbes superposées, deltas nuls |

Le message « Lecture du duel » doit suivre les sélections. Le delta est toujours B − A.

## Vérifier la stratégie

Hypothèses de départ : MEDIUM → HARD, arrêt après le tour 24, perte au stand 22 s, rythme de base 84 s, multiplicateur de dégradation 1.

| Changement | Total attendu | Meilleur arrêt | Écart au meilleur |
|---|---:|---:|---:|
| Valeurs de départ | 4 514,410 s / 75 min 14,4 s | 24 | 0 s |
| Arrêt au tour 35 | 4 519,415 s | 24 | 5,005 s |
| Perte au stand 32 s | 4 524,410 s | 24 | 0 s |
| Dégradation ×2 | 4 541,770 s | 21 | 0,510 s |
| Deux composés identiques | Scénario invalide, sorties vides | Vide | Vide |

Le plan des relais doit changer avec le tour d'arrêt et les pneus. La perte au stand doit apparaître une seule fois, sur le tour d'entrée aux stands. Le graphique des candidats affiche une pénalité relative à l'optimum, pas un temps total.

Le fichier [expected.json](validation/expected.json) donne les contrôles numériques complets, calculés indépendamment depuis les CSV et les formules Python.

## Validation visuelle

- Piste complète, point agrandi repérable, légende lisible.
- Jauge, cards et segments sans texte tronqué.
- SVG des pédales et du plan des relais rendus comme images.
- Couleurs des deux pilotes distinctes et stables.
- Cases initiales NOR/LEC et MEDIUM/HARD visibles.
- Aucune page vide après actualisation.

Le nuage de points peut avoir une proportion légèrement différente selon la zone réservée aux axes et à la légende. Les aperçus SVG du dépôt sont des aperçus de conception : ils ne prouvent pas le rendu Desktop.

## En cas d'erreur

Envoyer le message complet et la version de Power BI Desktop. Pour un problème de mise en forme, envoyer une capture de la page entière, puis du visuel concerné. Les définitions seront corrigées dans le générateur, afin de conserver un projet reproductible.

## Performance et sauvegarde

Dans Affichage → Analyseur de performances, enregistrer un changement de chrono, un changement de pilote et un changement de stratégie. Exporter les résultats ; aucune latence n'est certifiée avant cette mesure.

Après recette, enregistrer le PBIP. Pour le PBIX, utiliser Enregistrer sous dans Desktop. Avant de reconstruire le projet avec Python, sauvegarder les réglages manuels dans Git : le générateur remplace les définitions.
