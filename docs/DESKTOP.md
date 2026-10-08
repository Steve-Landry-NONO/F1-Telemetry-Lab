# Recette Power BI Desktop

## Ouvrir

Extraire le dépôt complet. Utiliser Power BI Desktop Windows récent, avec prise en charge des projets PBIP et des définitions PBIR/TMDL. Activer ces fonctions si nécessaire dans Fichier → Options et paramètres → Options → Fonctionnalités en préversion, puis redémarrer.

Ouvrir powerbi/F1 Telemetry Lab.pbip, puis Actualiser. Le chargement utilise les CSV embarqués dans le modèle, sans chemin externe.

## Résultats attendus

| Vérification | Résultat |
|---|---|
| Modèle | 16 tables, deux relations actives à sens unique |
| Volume | 1 002 points télémétriques, deux tours, 501 bins communs |
| NOR | 79,327 s ; secteurs 26,492 / 26,579 / 26,256 |
| LEC | 79,461 s ; secteurs 26,373 / 26,732 / 26,356 |
| Comparison A=NOR, B=LEC | Delta final +0,134 s ; secteurs −0,119 / +0,153 / +0,100 s |
| Comparison A=LEC, B=NOR | Signe de tous les deltas inversé |
| Comparison A=B | Courbes identiques et deltas nuls |
| Replay bin=0 | Temps écoulé 0 s ; marqueur au début du tour |
| Replay bin=500 | Temps écoulé égal au temps officiel du tour |
| MEDIUM/HARD, arrêt=24, perte=22, rythme=84, dégradation=1 | 4 514,410 s ; 75,24017 min ; meilleur arrêt=24 ; pénalité=0 |
| Perte au stand 22 → 32 | Total +10 s ; meilleur arrêt inchangé |
| Même composé deux fois | Message INVALID et sorties de stratégie vides |

Les segments n'ont pas de sélection initiale enregistrée : les mesures disposent de valeurs de repli. Pour une présentation, sélectionner explicitement les paramètres. Le curseur du replay est une liste de points de progression, pas un bouton Play.

## Vérifications visuelles et interactions

1. Les trois pages doivent afficher un fond sombre, des graphiques menthe/corail et des valeurs lisibles.
2. Changer NOR/LEC sur Replay : vitesse, pédales, temps, position et courbes doivent suivre le même tour.
3. Sélectionner plusieurs bins, dont 0, 75, 160, 320 et 500 : le point doit se déplacer et les KPI changer.
4. La piste doit apparaître comme une image SVG, pas du texte.
5. Changer les sélections A/B : les courbes et secteurs doivent suivre la sélection.
6. Modifier arrêt, composés et dégradation : les deux graphiques stratégiques doivent se recalculer.
7. Vérifier que le graphique des temps par tour présente un seul pic de perte au stand.

## Si un problème apparaît

| Symptôme | Contrôle |
|---|---|
| Erreur avant ouverture | Copier le message complet, la version Desktop et le chemin cité |
| Erreur sur une mesure | Copier le nom de la mesure et le texte du message |
| Piste affichée en texte | Vérifier que Metrics[Track SVG] est catégorisée Image URL dans Outils de mesure |
| Piste trop petite ou coupée | Ajuster la hauteur d'image et la largeur de colonne du visuel de table, puis sauvegarder |
| Segment sans valeur affichée | Sélectionner une valeur explicitement ; « Tout » utilise le repli documenté |
| Mise en forme différente | Indiquer la page et le visuel ; les noms de propriétés visuelles peuvent évoluer selon Desktop |

Pour les éventuelles corrections, envoyer le message d'erreur ou une capture accompagnée de la version de Desktop.

## Performance

Ouvrir Affichage → Analyseur de performances, puis Démarrer l'enregistrement. Mesurer le changement de curseur, le changement A/B et le calcul du meilleur arrêt. Exporter les résultats JSON et noter ordinateur/version. Un objectif initial raisonnable est une interaction ressentie fluide ; aucune latence n'est certifiée avant cette mesure.

## Sauvegarder et exporter

Après recette : enregistrer le projet PBIP pour conserver les réglages Desktop. Pour le fichier PBIX : Fichier → Enregistrer sous, choisir le format PBIX proposé par la version installée. Le PBIX est généré par Desktop et exclu du suivi Git pour éviter de versionner un binaire volumineux.

Avant de relancer le générateur, sauvegarder les modifications manuelles dans Git : il reconstruit les définitions.
