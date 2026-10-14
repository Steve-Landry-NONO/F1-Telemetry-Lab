# F1 Telemetry Lab — Beyond Dashboards

Projet portfolio de **Steve Landry KOUOKAM NONO** : explorer deux tours réels de Monza dans Power BI, comparer leurs performances et modifier une stratégie pneumatique pédagogique.

**Livraison v0.2 : sources générées et tests automatisés. L'ouverture, l'exécution DAX et le rendu doivent encore être validés dans Power BI Desktop Windows.**

## Démarrage rapide — sans Python

1. Télécharger le dépôt avec **Code → Download ZIP**, puis extraire tout le dossier.
2. Dans une version récente de Power BI Desktop, activer les fonctionnalités de projet PBIP et de format PBIR si elles figurent encore dans les options de préversion.
3. Ouvrir **powerbi/F1 Telemetry Lab.pbip**.
4. Cliquer **Actualiser** : les CSV sont embarqués dans les partitions Power Query. Aucun chemin local à modifier et aucun compte cloud requis.
5. Page Pit Wall : les valeurs **NOR** et **30 secondes** sont sélectionnées dès l’ouverture. Déplacer le curseur de chrono.
6. Page Comparison : choisir **NOR** en A et **LEC** en B. Le delta final B − A doit être **+0,134 s**.
7. Page Strategy : choisir **MEDIUM → HARD**, arrêt après le tour **24**, perte stand **22 s**, dégradation **1**, rythme **84 s**.

Les sélections initiales sont enregistrées : NOR à 30 s, NOR/LEC pour le duel, MEDIUM/HARD pour la stratégie. Les mesures disposent aussi de valeurs de repli si une sélection est effacée.

Voir [le guide Power BI Desktop](docs/DESKTOP.md) pour la recette et l'export PBIX.

## Trois pages

| Page | Fonction |
|---|---|
| Pit Wall | Circuit natif, position agrandie, jauge de vitesse, SVG des pédales, indicateurs synchronisés au chrono |
| Lap Performance | Courbes de vitesse alignées, delta cumulé B − A et écarts par secteur |
| Strategy Simulator | Deux composés, arrêt, perte stand, dégradation et rythme ; comparaison des 52 tours d'arrêt possibles |

Le replay avance **manuellement**, avec un curseur de temps continu dans l’interface ; les mesures prennent le dernier échantillon préparé avant cet instant. Cette version n’inclut pas de lecture automatique. La piste utilise un nuage de points natif ; les pédales et le plan des relais utilisent des mesures SVG compactes. Aucun visuel personnalisé à installer.

## Données

Le projet embarqué utilise **Monza, qualifications 2024** :

| Pilote | Tour retenu | Temps | Source |
|---|---:|---:|---|
| Lando Norris — NOR | 11 | 79,327 s | FastF1 |
| Charles Leclerc — LEC | 20 | 79,461 s | FastF1 |

Chaque tour comporte 501 points rééchantillonnés selon la progression normalisée. Les temps de tour et de secteur sont conservés ; les canaux continus sont interpolés et les canaux discrets utilisent l'échantillon suivant. Les temps télémétriques sont corrigés aux extrémités pour rejoindre le temps du tour. Cela convient à une démonstration analytique, avec une précision dépendant de l'échantillonnage.

data/sample/manifest.json contient la provenance, la version FastF1 et les empreintes des CSV. data/demo/ contient une alternative synthétique déterministe, avec géométrie stylisée et pilotes fictifs, identifiée dans le rapport.

Les données pneumatiques et les résultats stratégiques sont **simulés**. Pas de température ni d'usure mesurée inventée. Projet indépendant, sans affiliation à Formula 1.

## Développer

Python 3.10+ :

    python -m venv .venv
    # Windows : .venv\Scripts\Activate.ps1
    # Linux/macOS : source .venv/bin/activate
    python -m pip install -e ".[real,validation]"
    python -m unittest discover -s tests -v
    python scripts/build_powerbi.py
    python scripts/validate_report.py

Sur Windows, scripts/setup.ps1 exécute ces étapes. Le projet fourni peut être ouvert sans les exécuter.

Importer à nouveau les deux tours historiques (connexion Internet requise) :

    f1lab real --year 2024 --drivers NOR LEC --output data/real
    python scripts/build_powerbi.py --data data/real

Version synthétique hors ligne :

    f1lab demo
    python scripts/build_powerbi.py --data data/demo

Fermer Desktop avant de reconstruire. Le générateur remplace les définitions générées : sauvegarder les modifications manuelles dans Git avant de le relancer.

## Fonctionnalités Power BI démontrées

- Modèle dimensionnel : télémétrie au grain tour × progression, deux relations simples à sens unique.
- Power Query M : import portable, promotion des en-têtes et typage explicite.
- DAX : contexte de filtre, CALCULATE, TREATAS, REMOVEFILTERS, CONCATENATEX, ADDCOLUMNS, TOPN, LOOKUPVALUE.
- Tables déconnectées : sélections A/B, curseur et hypothèses de simulation.
- SVG dynamique : barres de pédales et plan des relais calculés dans le modèle.
- Curseur chronométrique, sélections persistantes, interactions contrôlées et messages analytiques.
- PBIP / TMDL / PBIR : modèle, mesures et pages versionnés, générateur reproductible.
- Performance Analyzer : protocole de mesure à exécuter dans Desktop.

Les paramètres déconnectés reproduisent le comportement what-if ; ils sont importés, pas créés par l'assistant What-if de Desktop. Deneb, field parameters, bookmarks et lecture automatique ne sont pas inclus dans cette version.

## Organisation

    src/f1lab/           Pipeline, contrôles qualité, modèle de stratégie
    scripts/            Génération PBIP, validation JSON, installation Windows
    data/sample/        Deux tours historiques préparés
    data/demo/          Alternative synthétique
    powerbi/            Rapport PBIR et modèle TMDL prêts à ouvrir
    schemas/            Schémas Microsoft mis en cache pour validation
    tests/              Qualité des données, invariants et intégrité du projet
    docs/               Architecture, recette Desktop, scénario vidéo

Les [aperçus de conception](docs/REFINEMENT.md) utilisent les données réelles et les positions PBIR. Ils ne remplacent pas des captures du rapport validé dans Desktop.

Voir [architecture et hypothèses](docs/ARCHITECTURE.md), [recette Desktop](docs/DESKTOP.md) et [vidéo portfolio](docs/VIDEO.md).
