# CLAUDE.md — Projet F1 Strategy

> Contexte à lire en début de chaque session. Ce fichier est à placer à la racine du projet (`f1-strategy/CLAUDE.md`).

## 1. Le projet

**Titre** : Modélisation stochastique de dégradation des pneumatiques et simulateur d'optimisation d'arrêts aux stands (Undercut / Overcut) sous Python.

**Question centrale** (celle de l'ingénieur stratégie) : *À quel tour faire rentrer le pilote pour maximiser son temps total de course tout en minimisant le risque de ressortir dans le trafic ou sous neutralisation ?*

**Étapes du projet** :
1. Extraire les chronos tour par tour et la télémétrie d'un Grand Prix réel (FastF1).
2. Nettoyer les données : retirer les tours sous Safety Car / VSC, les tours d'entrée (in-lap) et de sortie (out-lap) des stands, et les tours pollués par le trafic.
3. Modéliser la courbe d'usure des pneus (Soft / Medium / Hard) par régression polynomiale.
4. Construire un simulateur qui teste différentes fenêtres d'arrêt (1 arrêt vs 2 arrêts) et calcule la probabilité de réussite d'un undercut en fonction du temps perdu aux stands (pit-loss).

**Données** : télémétrie officielle F1 via la bibliothèque open-source `fastf1`, gratuite, sans compte ni clé API. Colonnes utiles : `LapTime`, `Sector1Time`/`Sector2Time`/`Sector3Time`, `TyreLife`, `Compound`, `Stint`, `PitInTime`, `PitOutTime`, `TrackStatus`.

**Stack** : Python ≥ 3.10, `fastf1`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `jupyter`.

## 2. Mode de collaboration (IMPORTANT)

- L'utilisateur veut **construire le projet lui-même, pas à pas, en apprenant**. Il ne faut pas coder tout le projet d'un coup ni prendre d'avance sur les étapes.
- Rôle de Claude : **guide / mentor technique**. On explique le *pourquoi*, on propose une étape à la fois, puis on attend son retour (sortie du code, erreurs, observations) avant de passer à la suivante.
- Avant d'écrire ou de modifier du code dans le projet, **demander ou proposer d'abord**, sauf si l'utilisateur le demande explicitement.
- On discute ensemble des choix de modélisation (degré du polynôme, correction de l'effet carburant, définition du « trafic », etc.) au lieu de les imposer.
- Langue : **français**.

## 3. Architecture cible

```
f1-strategy/
├── CLAUDE.md
├── data/
│   ├── cache/          # cache FastF1 (volumineux, à ignorer dans git)
│   └── processed/      # données nettoyées (CSV / parquet)
├── notebooks/
│   └── 01_exploration.ipynb
├── src/
│   ├── __init__.py
│   ├── data_loader.py  # étape 1 : extraction FastF1
│   ├── cleaning.py     # étape 2 : filtrage SC/VSC, in/out laps, trafic
│   ├── degradation.py  # étape 3 : modèles d'usure par composé
│   └── strategy.py     # étape 4 : simulateur d'arrêts / undercut
├── figures/
├── requirements.txt
└── README.md
```

Principe : on explore d'abord dans les notebooks, puis on migre le code stabilisé vers `src/` (un module = une responsabilité).

## 4. Ce qui a été fait jusqu'ici (30/09/2026)

Étapes **proposées** à l'utilisateur. Leur exécution sur sa machine **reste à confirmer** :

1. **Environnement** : installer Python ≥ 3.10, VS Code (extensions Python + Jupyter) et, en option, Git.
2. **Arborescence** : créer le squelette ci-dessus avec des fichiers `.py` vides.
3. **Environnement virtuel** :
   ```bash
   python -m venv .venv
   # Windows : .venv\Scripts\activate   |   Mac/Linux : source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Contenu de `requirements.txt` : `fastf1 pandas numpy scipy scikit-learn matplotlib seaborn jupyter`
4. **Premier chargement** (première cellule de `notebooks/01_exploration.ipynb`) :
   ```python
   import fastf1
   fastf1.Cache.enable_cache('../data/cache')

   session = fastf1.get_session(2024, 'Spain', 'R')   # R = course
   session.load()

   laps = session.laps
   print(laps.shape)
   print(laps.columns.tolist())
   laps[['Driver', 'LapNumber', 'LapTime', 'Compound', 'TyreLife',
         'Stint', 'PitInTime', 'PitOutTime', 'TrackStatus']].head(20)
   ```
   Objectif : se familiariser avec `TrackStatus` (SC/VSC), `PitInTime`/`PitOutTime` (in/out laps) et `TyreLife` (futur axe X de la dégradation).

**Rien n'a encore été codé au-delà de ça.**

## 5. Décisions en attente

- **Choix du Grand Prix** (Barcelone 2024 par défaut) :
  - *Barcelone* : forte dégradation (virage 3), plusieurs stratégies viables, peu de neutralisations. C'est le choix le plus propre pour débuter.
  - *Bahreïn* : dégradation thermique et abrasive très marquée.
  - *Silverstone* : intéressant, mais météo et neutralisations compliquent le nettoyage.
- Résultat de l'exécution de la première cellule (sortie ou erreur) à analyser ensemble.

## 6. Prochaines étapes prévues (à ne lancer qu'avec l'utilisateur)

1. Exploration : distribution des chronos, stints par pilote, repérage des tours SC/VSC.
2. Logique de nettoyage (`cleaning.py`) : codes `TrackStatus`, in/out laps, seuil d'outliers, trafic (écart au pilote devant).
3. Correction de l'effet carburant (la voiture s'allège d'environ 0,03 à 0,06 s/tour), sinon la dégradation est sous-estimée.
4. Régression polynomiale par composé, puis comparaison des degrés et validation.
5. Simulateur : temps total de course pour chaque stratégie, pit-loss, puis Monte-Carlo pour la probabilité d'undercut (bruit sur les chronos, probabilité de SC).

## 7. Conventions

- Code commenté en français, noms de variables en anglais.
- Pas de valeurs magiques : les constantes (pit-loss, effet carburant…) sont regroupées et documentées.
- Chaque graphique est sauvegardé dans `figures/` avec un nom explicite.
- Ajouter `.venv/` et `data/cache/` au `.gitignore`.
