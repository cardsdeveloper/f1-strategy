"""Étape 3 : mesure de l'usure des pneus par composé."""

import numpy as np
import pandas as pd

from src.cleaning import STINT_KEYS

COMPOUNDS = ['SOFT', 'MEDIUM', 'HARD']
# Pour un composé jamais roulé en long relais : composés dont on reprend l'usure, par ordre de préférence
NEAREST_COMPOUNDS = {'SOFT': ['MEDIUM', 'HARD'], 'MEDIUM': ['SOFT', 'HARD'], 'HARD': ['MEDIUM', 'SOFT']}
WEAR_COLUMNS = ['Composé', 'Usure (s/tour)', '± usure', 'Tours', 'Relais', 'Âge max (tours)', 'Dispersion (s)']


def fit_wear(long_run_laps, fuel_effect_per_lap):
    """Mesure l'usure de chaque composé (s perdues par tour d'âge) sur des tours de longs relais.

    Pour chaque composé, on ajuste un niveau de rythme propre à chaque relais et une pente commune :
    c'est ce qui rend comparables des voitures et des charges d'essence différentes.
    L'effet carburant ne peut pas se mesurer en essais : on le suppose (fuel_effect_per_lap, en s/tour).

    Renvoie un tableau (une ligne par composé) et, pour chaque tour, le temps perdu par rapport
    à un pneu neuf (s), utile pour tracer le nuage de points.
    """
    laps = long_run_laps.copy()
    # Chrono ramené au poids du début du relais : on rajoute le temps gagné grâce à l'allègement
    laps_since_stint_start = laps['LapNumber'] - laps.groupby(STINT_KEYS)['LapNumber'].transform('min')
    laps['CorrectedSeconds'] = laps['LapSeconds'] + fuel_effect_per_lap * laps_since_stint_start

    rows = []
    time_lost = pd.Series(np.nan, index=laps.index)
    for compound in COMPOUNDS:
        compound_laps = laps[laps['Compound'] == compound]
        n_stints = compound_laps.groupby(STINT_KEYS).ngroups
        if n_stints == 0:
            continue
        stint = [compound_laps[key] for key in STINT_KEYS]
        seconds = compound_laps['CorrectedSeconds']
        age = compound_laps['TyreLife'].astype(float)

        # On retire à chaque relais sa propre moyenne : il ne reste que les variations internes au relais
        seconds_centered = seconds - seconds.groupby(stint).transform('mean')
        age_centered = age - age.groupby(stint).transform('mean')
        wear = (age_centered * seconds_centered).sum() / (age_centered ** 2).sum()

        # Dispersion des tours autour de la droite, et incertitude (erreur type) sur la pente
        residuals = seconds_centered - wear * age_centered
        degrees_of_freedom = len(compound_laps) - n_stints - 1
        residual_std = np.sqrt((residuals ** 2).sum() / degrees_of_freedom)
        wear_error = residual_std / np.sqrt((age_centered ** 2).sum())

        # Temps perdu par rapport à un pneu neuf : chrono moins le rythme du relais à l'âge 0
        new_tyre_pace = (seconds - wear * age).groupby(stint).transform('mean')
        time_lost[compound_laps.index] = seconds - new_tyre_pace

        rows.append({'Composé': compound, 'Usure (s/tour)': wear, '± usure': wear_error,
                     'Tours': len(compound_laps), 'Relais': n_stints,
                     'Âge max (tours)': int(age.max()), 'Dispersion (s)': residual_std})

    # Les colonnes sont nommées explicitement pour que le tableau reste valide même sans aucun relais
    return pd.DataFrame(rows, columns=WEAR_COLUMNS).set_index('Composé'), time_lost


def select_wear(long_run_laps, scopes, fuel_effect_per_lap):
    """Choisit l'usure de chaque composé en partant des données les plus précises disponibles.

    scopes : dictionnaire {nom: masque booléen sur long_run_laps}, du périmètre le plus précis au plus
    large (par exemple pilote, puis écurie, puis tous les pilotes). Pour chaque composé, on retient
    le premier périmètre qui donne une usure mesurée et positive. Un composé que personne n'a roulé
    en long relais reprend l'usure du composé mesuré le plus proche.

    Renvoie un tableau (une ligne par composé) avec la colonne Source, qui dit d'où vient la valeur.
    """
    measures = {name: fit_wear(long_run_laps[mask], fuel_effect_per_lap)[0] for name, mask in scopes.items()}
    rows = {}
    for compound in COMPOUNDS:
        for name, table in measures.items():
            if compound in table.index and table.loc[compound, 'Usure (s/tour)'] > 0:
                rows[compound] = {'Usure essais (s/tour)': table.loc[compound, 'Usure (s/tour)'],
                                  '± usure': table.loc[compound, '± usure'],
                                  'Relais': table.loc[compound, 'Relais'], 'Source': name}
                break

    measured = list(rows)
    if not measured:
        raise ValueError("Aucun long relais exploitable dans ces essais : impossible de mesurer l'usure.")
    for compound in COMPOUNDS:
        if compound not in rows:
            nearest = next(other for other in NEAREST_COMPOUNDS[compound] if other in measured)
            rows[compound] = {'Usure essais (s/tour)': rows[nearest]['Usure essais (s/tour)'], '± usure': np.nan,
                              'Relais': 0, 'Source': f'non roulé, repris du {nearest}'}

    return pd.DataFrame.from_dict(rows, orient='index').loc[COMPOUNDS].rename_axis('Composé')
