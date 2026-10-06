# CLAUDE.md — Projet F1 Strategy

> Contexte à lire en début de chaque session. Dernière mise à jour : 06/10/2026.

## 1. Le projet

**Titre** : Modélisation stochastique de dégradation des pneumatiques et simulateur d'optimisation d'arrêts aux stands (Undercut / Overcut) sous Python.

**Question centrale** (celle de l'ingénieur stratégie) : *À quel tour faire rentrer le pilote pour maximiser son temps total de course tout en minimisant le risque de ressortir dans le trafic ou sous neutralisation ?*

Le projet a deux volets :
- **Après course** : mesurer l'usure des pneus sur une course courue, calculer les meilleurs tours d'arrêt et les comparer aux stratégies réelles.
- **Avant course** : mesurer l'usure en essais libres, saisir les trains de pneus disponibles, obtenir la meilleure stratégie réalisable.

**Données** : chronométrage officiel F1 via `fastf1`, gratuit, sans compte ni clé API. Colonnes utiles : `LapTime`, `TyreLife`, `Compound`, `Stint`, `PitInTime`, `PitOutTime`, `TrackStatus`, `Time`, `Team`.

**Stack** : Python 3.12 dans `.venv`, `fastf1`, `pandas`, `numpy`, `matplotlib`, `jupyter`. `scipy`, `scikit-learn` et `seaborn` sont installés mais pas utilisés.

## 2. Mode de collaboration (IMPORTANT)

- L'utilisateur connaît Python mais découvre pandas : expliquer chaque notion pandas nouvelle quand elle apparaît.
- Il **délègue l'écriture du code** (« je te laisse coder », « on passe à l'étape suivante ») et attend ensuite un compte rendu : ce qui a changé, les résultats chiffrés, les limites. Quand il veut une explication avant le code, il le dit.
- **Pas d'exercices ni de questions pédagogiques.** Il pose ses questions lui-même. Pour un choix de modélisation, donner une recommandation argumentée plutôt que demander.
- Il veut comprendre : expliquer le *pourquoi* de chaque étape, et dire franchement ce qui est fragile ou non vérifié.
- Langue des échanges : **français**. Le README est en anglais.

## 3. Architecture

```
f1-strategy/
├── CLAUDE.md
├── README.md               # en anglais, décrit chaque fichier
├── notebooks/
│   ├── 01_exploration.ipynb                # analyse après course (Espagne 2024), autonome, n'utilise pas src/
│   ├── 02_prediction_essais.ipynb          # outil de stratège : prédiction depuis les essais libres
│   └── 03_validation_essais_course.ipynb   # usure essais contre usure course, sur plusieurs week-ends
├── src/
│   ├── data_loader.py      # load_laps, load_track_temperature, get_event_name
│   ├── cleaning.py         # add_gap_ahead, select_long_run_laps
│   ├── degradation.py      # fit_wear, select_wear
│   └── strategy.py         # measure_pit_loss, measure_max_tyre_age, find_best_strategies, describe_stints
├── data/
│   ├── cache/              # cache FastF1 (ignoré par git)
│   └── processed/          # vide pour l'instant
├── figures/                # graphiques enregistrés par les notebooks
└── requirements.txt
```

## 4. Ce qui est fait

### Notebook 01 : analyse après course (Espagne 2024)

Huit cellules : chargement et affichage, correction carburant, nettoyage, courbes d'usure, modèle complet du temps au tour, temps perdu aux stands, simulateur, carte des stratégies à deux arrêts.

- Nettoyage : 1 310 tours, 992 gardés (premier tour, tours d'entrée et de sortie, tours à plus de 3 % du rythme médian du relais, tours à moins de 1,0 s de la voiture qui précède).
- Modèle : chrono = rythme du pilote + écart du composé + effet du numéro de tour + usure × âge. Usure linéaire (les degrés 2 et 3 n'apportent rien).
- Résultats : usure Soft 0,101, Medium 0,083, Hard 0,076 s/tour ; effet du numéro de tour −0,058 s/tour ; arrêt 22,7 s.
- Optimum simulé : deux arrêts, tours 21 et 43. Un arrêt +9,6 s, trois arrêts +5,2 s. La stratégie réelle de Verstappen simulée tombe à 0,1 s de son temps réel.

### Notebook 02 : outil de stratège

Sept cellules. La première est la seule à modifier : `YEAR`, `GRAND_PRIX`, `RACE_LAPS`, `DRIVER`, `TEAM`, `AVAILABLE_SETS` (composé, tours déjà roulés), `RACE_WEAR_COEFFICIENT`, plus les hypothèses (`FUEL_EFFECT_PER_LAP`, `COMPOUND_OFFSET_S`, `MAX_TYRE_AGE`, `MIN_STINT_LAPS`, `MAX_STOPS`).

- Usure mesurée sur les longs relais des essais, pour trois périmètres : pilote, écurie, tous les pilotes. Repli du plus précis au plus large quand un composé n'a pas été roulé ; un composé jamais roulé reprend l'usure du composé voisin.
- Temps perdu aux stands et âge maximal des pneus mesurés sur la course de l'année précédente (âge que 90 % des relais n'ont pas dépassé). `None` dans `MAX_TYRE_AGE` = valeur mesurée, un nombre = valeur imposée.
- Sortie : meilleure stratégie par périmètre, test de solidité, puis stratégies réelles de tous les pilotes si la course a eu lieu.

### Notebook 03 : essais contre course

Trois cellules, sur l'Espagne, Bahreïn, la Hongrie et Monza, en 2023 et 2024.

- L'usure en course vaut en général 35 % à 80 % de celle mesurée en essais.
- Le rapport n'est pas stable : deux mesures d'essais 2023 (Espagne Medium, Monza Medium) sont proches de zéro et inutilisables.
- La température de piste n'explique pas l'écart.
- Le rapport de l'année précédente sur le même circuit ne prédit pas mieux qu'un coefficient unique de 0,6 (erreur typique 25 %).

## 5. Limites connues

- **Choix des composés peu fiable.** Hongrie 2024 : l'outil propose Soft-Soft-Medium, 14 pilotes sur 20 n'ont roulé qu'en Medium et Hard.
- **Écart de rythme entre composés supposé**, pas mesuré (Medium +0,3 s, Hard +0,6 s). En course, sa mesure est fragile car les composés sont utilisés dans le même ordre par presque tous.
- **Composé principal de la course souvent absent des longs relais d'essais** (Hard à Bahreïn et à Monza en 2024).
- **Ordre des relais non modélisé** : toutes les permutations donnent le même temps.
- **Pas d'effondrement du pneu dans le modèle.** Les données ne le montrent pas, les équipes s'arrêtant avant. L'âge maximal en tient lieu, et il décide souvent du résultat.
- **Données d'un seul pilote très bruitées** (un ou deux relais).
- **Course de l'année précédente parfois mauvaise référence** : Bakou 2023 (Safety Car, Soft non utilisé), Monza (réasphalté en 2024).
- **Chaque voiture roule seule** : ni trafic, ni undercut, ni Safety Car.

## 6. Prochaines étapes

À ne lancer qu'à la demande de l'utilisateur.

1. Affiner la modélisation pour que les stratégies prévues se rapprochent des réelles : choix des composés d'abord (écart de rythme entre composés, ordre des relais).
2. Mieux corriger l'usure entre essais et course : tester sur davantage de Grands Prix, médiane sur plusieurs années par circuit, rôle de chaque séance d'essais.
3. Roulage dans le trafic et undercut. Le principe a été expliqué à l'utilisateur mais rien n'est codé : une voiture à moins d'une seconde ne roule pas plus vite que celle de devant ; duel tour par tour ; position à la sortie des stands ; Monte-Carlo sur la dispersion des chronos (environ 0,5 s) et la durée des arrêts.
4. Scénarios de Safety Car.

## 7. Environnement : pièges à connaître

- **Claude ne peut pas télécharger de données** depuis son shell (erreur SSL). Seul `data/cache/` est lisible. Pour un nouveau Grand Prix ou une nouvelle séance, l'utilisateur lance une cellule de chargement, puis Claude lit le cache.
- **VS Code garde les notebooks en mémoire.** Après une modification d'un `.ipynb` sur disque, l'utilisateur doit faire « File: Revert File » sans enregistrer, sinon son prochain enregistrement écrase la modification. Revert efface aussi sa saisie non enregistrée : reverter d'abord, saisir ensuite.
- **Après une modification de `src/`**, redémarrer le noyau du notebook.
- **Une cellule en erreur arrête l'exécution** : les cellules suivantes gardent leurs anciens résultats.
- **Nom du Grand Prix** : pays ou ville en anglais (`'Spain'`, `'Azerbaijan'`, `'Monza'`). FastF1 prend le nom le plus proche sans signaler une faute de frappe ; le notebook 02 affiche le nom reconnu.
- Le projet est dans un dossier OneDrive, qui synchronise aussi `.venv` et le cache.

## 8. Conventions

- Code commenté en français, noms de variables en anglais.
- Pas de valeurs magiques : les constantes sont regroupées et documentées, en tête de cellule ou de module.
- Chaque graphique est sauvegardé dans `figures/` avec un nom explicite.
- Dans les notebooks, les données saisies par l'utilisateur sont regroupées dans la première cellule.
- `.venv/` et `data/cache/` sont dans le `.gitignore`.
