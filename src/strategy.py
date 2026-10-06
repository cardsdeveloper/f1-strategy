"""Étape 4 : temps perdu aux stands et recherche de la meilleure stratégie d'arrêts."""

from itertools import combinations

import numpy as np
import pandas as pd

from src.cleaning import GREEN_TRACK_STATUS

MIN_COMPOUNDS = 2          # règlement : au moins deux composés différents en course
REFERENCE_LAPS = 3         # nombre de tours voisins servant de référence pour chiffrer un arrêt
MIN_REFERENCE_LAPS = 2     # il en faut au moins deux de valides pour retenir l'arrêt
MAX_AGE_QUANTILE = 0.9     # âge maximal d'un pneu : celui que 90 % des relais d'une course n'ont pas dépassé
MIN_STINT_LAPS_FOR_AGE = 5     # un relais plus court (abandon, arrêt forcé) ne dit rien de la durée de vie du pneu
MIN_STINTS_FOR_AGE = 4         # nombre minimal de relais sur un composé pour en tirer un âge maximal


def measure_pit_loss(race_laps):
    """Mesure sur une course le temps perdu à un arrêt (s) : (tour d'entrée, tour de sortie).

    Le tour d'entrée est comparé aux tours normaux qui le précèdent, le tour de sortie à ceux
    qui le suivent : on obtient le surcoût de chaque tour, médiane sur tous les arrêts de la course.
    """
    laps = race_laps.sort_values(['Driver', 'LapNumber']).copy()
    seconds = laps['LapTime'].dt.total_seconds()
    is_in_lap = laps['PitInTime'].notna()
    is_out_lap = laps['PitOutTime'].notna() & (laps['LapNumber'] > 1)    # hors départ de la voie des stands
    is_normal = (laps['PitInTime'].isna() & laps['PitOutTime'].isna() & (laps['LapNumber'] > 1)
                 & (laps['TrackStatus'] == GREEN_TRACK_STATUS))

    # Chrono médian des tours normaux juste avant, puis juste après, chaque tour (pilote par pilote)
    normal_seconds = seconds.where(is_normal).groupby(laps['Driver'])
    pace_before = normal_seconds.transform(
        lambda s: s.shift(1).rolling(REFERENCE_LAPS, min_periods=MIN_REFERENCE_LAPS).median())
    pace_after = normal_seconds.transform(
        lambda s: s[::-1].shift(1).rolling(REFERENCE_LAPS, min_periods=MIN_REFERENCE_LAPS).median()[::-1])

    pit_in_loss = (seconds - pace_before)[is_in_lap].median()
    pit_out_loss = (seconds - pace_after)[is_out_lap].median()
    return pit_in_loss, pit_out_loss


def measure_max_tyre_age(race_laps):
    """Mesure sur une course l'âge qu'atteignent les pneus en fin de relais, par composé.

    On retient l'âge que 90 % des relais n'ont pas dépassé : c'est la limite que les équipes se sont
    fixée en pratique. Les données ne montrent pas l'effondrement d'un pneu, justement parce que
    les équipes s'arrêtent avant ; cette limite en tient lieu.

    Renvoie un tableau (une ligne par composé utilisé) : âge maximal retenu et nombre de relais.
    """
    stints = race_laps.groupby(['Driver', 'Stint']).agg(
        compound=('Compound', 'first'), end_age=('TyreLife', 'max'), n_laps=('LapNumber', 'size'))
    stints = stints[stints['n_laps'] >= MIN_STINT_LAPS_FOR_AGE]    # on ignore les relais avortés
    by_compound = stints.groupby('compound')['end_age']
    table = pd.DataFrame({'Âge max (tours)': by_compound.quantile(MAX_AGE_QUANTILE).round(),
                          'Relais': by_compound.size()})
    return table[table['Relais'] >= MIN_STINTS_FOR_AGE].astype(int).rename_axis('Composé')


def stint_costs(tyre_set, total_laps, wear_per_lap, compound_offset):
    """Temps perdu cumulé (s) par un train de pneus selon la longueur du relais : costs[n] pour n tours.

    tyre_set : (composé, tours déjà roulés). Le premier tour du relais se fait à l'âge « déjà roulés + 1 ».
    """
    compound, used_laps = tyre_set
    ages = used_laps + np.arange(1, total_laps + 1)
    lap_costs = compound_offset[compound] + wear_per_lap[compound] * ages
    return np.concatenate([[0.0], np.cumsum(lap_costs)])


def find_best_strategies(available_sets, total_laps, wear_per_lap, compound_offset, pit_loss, max_stops,
                         max_tyre_age, min_stint_laps):
    """Teste toutes les stratégies réalisables avec les trains de pneus disponibles.

    Chaque train ne sert qu'une fois. Pour chaque nombre d'arrêts et chaque sélection de trains,
    on garde les longueurs de relais qui donnent le temps le plus court.
    Un relais doit durer au moins min_stint_laps tours, et le pneu ne doit pas dépasser en fin de relais
    l'âge max_tyre_age[composé] : l'usure est supposée linéaire, ce qui n'est plus vrai sur un pneu à bout.
    Les relais sont listés dans l'ordre de available_sets : le modèle est indifférent à leur ordre.

    Renvoie un tableau trié du meilleur au moins bon, avec l'écart au meilleur (s).
    """
    costs = [stint_costs(tyre_set, total_laps, wear_per_lap, compound_offset) for tyre_set in available_sets]
    rows = []
    for n_stops in range(1, max_stops + 1):
        # Toutes les façons de placer les arrêts : une ligne par combinaison, une colonne par relais
        pit_laps = np.array(list(combinations(range(1, total_laps), n_stops)))
        boundaries = np.column_stack([np.zeros(len(pit_laps), int), pit_laps, np.full(len(pit_laps), total_laps)])
        stint_lengths = np.diff(boundaries, axis=1)

        for chosen in combinations(range(len(available_sets)), n_stops + 1):
            if len({available_sets[i][0] for i in chosen}) < MIN_COMPOUNDS:
                continue
            # Temps perdu de chaque combinaison d'arrêts avec ces trains, calculé d'un coup
            seconds = sum(costs[i][stint_lengths[:, k]] for k, i in enumerate(chosen)) + n_stops * pit_loss
            # On écarte les combinaisons dont un relais est trop court ou use un pneu au-delà de son âge maximal
            for k, i in enumerate(chosen):
                compound, used_laps = available_sets[i]
                is_allowed = ((stint_lengths[:, k] >= min_stint_laps)
                              & (used_laps + stint_lengths[:, k] <= max_tyre_age[compound]))
                seconds = np.where(is_allowed, seconds, np.inf)
            best = seconds.argmin()
            if not np.isfinite(seconds[best]):
                continue    # aucune combinaison d'arrêts possible avec ces trains
            rows.append({'Arrêts': n_stops,
                         'Relais': tuple((*available_sets[i], int(stint_lengths[best, k]))
                                         for k, i in enumerate(chosen)),
                         "Tours d'arrêt": tuple(int(lap) for lap in pit_laps[best]),
                         'Temps perdu (s)': seconds[best]})

    if not rows:
        raise ValueError('Aucune stratégie réalisable : pas assez de trains de pneus, ou relais trop longs '
                         "pour l'âge maximal autorisé.")
    strategies = pd.DataFrame(rows).drop_duplicates('Relais').sort_values('Temps perdu (s)')
    strategies['Écart (s)'] = strategies['Temps perdu (s)'] - strategies['Temps perdu (s)'].min()
    return strategies.reset_index(drop=True)


def describe_stints(stints):
    """Texte lisible d'une liste de relais (composé, tours déjà roulés, longueur du relais)."""
    parts = []
    for compound, used_laps, n_laps in stints:
        state = 'neuf' if used_laps == 0 else f"{used_laps} t. roulé{'s' if used_laps > 1 else ''}"
        parts.append(f'{compound} {state} : {n_laps} tours')
    return ' / '.join(parts)
