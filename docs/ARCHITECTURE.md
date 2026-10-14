# Architecture et périmètre v0.2

## Flux de données

FastF1 → contrôle des tours → grille de 501 points → CSV et manifeste → génération TMDL/PBIR → ouverture et actualisation Desktop.

Python prépare les observations. Power Query charge et type les données. DAX calcule les valeurs à afficher et simule la stratégie. Les visuels Power BI effectuent le rendu.

## Grain et relations

| Table | Grain / fonction |
|---|---|
| DimLap | Un tour ; pilote, séance, circuit, temps officiel et secteurs |
| FactTelemetry | Un tour × un bin de progression |
| DimDistance | Un bin ; progression 0–100 % ; dimension commune aux courbes |
| ReplayTime | Curseur déconnecté ; temps 0–80 secondes, pas de 0,1 s |
| LapA / LapB | Sélections indépendantes pour la comparaison |
| Compound | Hypothèses de rythme et de dégradation par composé |
| FirstCompound / SecondCompound | Composés sélectionnés, déconnectés |
| StopLap / PitLoss / BasePace / Degradation | Hypothèses sélectionnables, déconnectées |
| RaceLap | Axe de la simulation, tours 1–53 |
| CandidateStop | Axe de comparaison, tours d'arrêt 1–52 |
| Metrics | Mesures centralisées |

Deux relations actives, de la dimension vers le fait : DimLap.LapId → FactTelemetry.LapId et DimDistance.Bin → FactTelemetry.Bin. Les sélections indépendantes sont appliquées par TREATAS.

La dimension pilote/circuit/séance est volontairement intégrée à DimLap pour ce MVP à une séance. Une extension multisaison nécessitera des dimensions dédiées.

## Replay

Le curseur sélectionne un temps écoulé. DAX utilise MAX sur les valeurs visibles du segment Before, puis choisit le dernier bin dont TimeMs est inférieur ou égal au temps demandé. L’échantillonnage préparé comporte 501 points ; le temps affiché peut être légèrement inférieur au temps demandé. Au-delà du temps du tour, le curseur reste au dernier point.

Le nuage de points natif trace la géométrie X/Y, différencie les zones selon frein/vitesse et agrandit le point sélectionné. L’absence de filtre temporel sur le fait maintient toute la piste et toutes les courbes visibles. Les barres de pédales utilisent une mesure SVG indépendante, catégorisée ImageUrl. Le plan stratégique utilise aussi un SVG.

Les sélections sont enregistrées dans les objets des segments. Les graphiques n’appliquent pas de filtres aux autres visuels : seul le changement de paramètres pilote les interactions. Pas de lecture automatique dans cette version.

## Comparaison

Les deux tours sont rééchantillonnés sur la même progression normalisée. Le delta est temps(B) − temps(A) ; un résultat positif signifie que B est derrière A. Il ne s'agit pas d'une synchronisation à temps égal. Le delta final est contraint aux temps officiels ; le profil entre les extrémités reste une approximation issue de la télémétrie.

## Stratégie pédagogique

Course sèche de 53 tours, un arrêt, deux composés distincts, perte au stand constante. Les paramètres ne sont pas ajustés à partir de la qualification.

| Composé | Offset au rythme de base | Dégradation par tour d'âge |
|---|---:|---:|
| SOFT | −0,60 s | 0,090 s |
| MEDIUM | 0,00 s | 0,055 s |
| HARD | +0,45 s | 0,030 s |

Pour n tours, rythme de base b, offset o, dégradation d et multiplicateur m :

    Temps du relais = n × (b + o) + d × m × n × (n − 1) / 2
    Temps de course = temps relais 1 + temps relais 2 + perte au stand

L'âge vaut zéro au premier tour de chaque relais. L'arrêt est effectué après le tour sélectionné ; la perte au stand est comptée une seule fois, sur ce tour. Les 52 candidats sont évalués. En cas d'égalité, le tour le plus précoce est retenu.

Deux composés identiques rendent le scénario invalide et les sorties vides. Ce modèle n'intègre pas carburant, trafic, météo, safety car, évolution de piste, échauffement ni variabilité des arrêts. Il explique l'effet des hypothèses, sans prédire une course réelle.

## Vérification

- Tests Python : données reproductibles, intégrité de la grille, endpoints/secteurs, formule par relais confrontée à une somme tour par tour, perte stand, recherche exhaustive du meilleur arrêt.
- Projet : références des visuels, dimensions du canevas, aller-retour du CSV embarqué, références de mesures et relations.
- JSON : schémas Microsoft PBIR/PBIP/PBISM et dépendances mis en cache.
- Validation restante : parseur TMDL et moteur DAX de Desktop, rendu des visuels, interactions, performance et export PBIX.

Un schéma JSON valide ne constitue pas une validation de l'exécution du rapport.

## Références techniques

- [Power BI Projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [Format du rapport PBIR](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [TMDL](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview)
- [Schémas Microsoft](https://github.com/microsoft/json-schemas)
- [FastF1](https://docs.fastf1.dev/)
