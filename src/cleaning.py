"""Étape 2 : sélection des tours exploitables pour mesurer l'usure des pneus."""

import pandas as pd

GREEN_TRACK_STATUS = '1'    # code TrackStatus d'un tour entièrement sous piste libre
TRAFFIC_GAP_S = 1.0         # trafic : moins de 1,0 s derrière la voiture qui précède sur la piste
PACE_BAND = 0.03            # un tour de long relais reste à ± 3 % du chrono médian de son relais
MIN_LONG_RUN_LAPS = 6       # nombre minimal de tours retenus pour qu'un relais compte comme long relais

# Colonnes qui identifient un relais quand plusieurs séances sont regroupées
STINT_KEYS = ['Session', 'Driver', 'Stint']


def add_gap_ahead(laps):
    """Ajoute la colonne GapAhead : écart (s) à la voiture qui a franchi la ligne juste avant.

    Le calcul se fait séance par séance : on trie les passages sur la ligne par instant,
    puis on prend la différence entre lignes voisines.
    """
    laps = laps.copy()
    crossing_gap = laps.sort_values('Time').groupby('Session')['Time'].diff()
    laps['GapAhead'] = crossing_gap.dt.total_seconds()
    return laps


def select_long_run_laps(practice_laps):
    """Ne garde, dans des tours d'essais libres, que les tours de longs relais (simulations de course).

    En essais, les pilotes alternent tours rapides, tours lents de refroidissement et longs relais.
    Seuls les longs relais renseignent sur l'usure des pneus en rythme de course.
    """
    laps = add_gap_ahead(practice_laps)
    laps['LapSeconds'] = laps['LapTime'].dt.total_seconds()

    # Tours chronométrés, hors entrée et sortie des stands, sous piste libre
    is_timed = laps['LapSeconds'].notna()
    is_pit_lap = laps['PitInTime'].notna() | laps['PitOutTime'].notna()
    is_green = laps['TrackStatus'] == GREEN_TRACK_STATUS
    laps = laps[is_timed & ~is_pit_lap & is_green]

    # Rythme régulier : on écarte les tours trop rapides ou trop lents par rapport au relais
    stint_median = laps.groupby(STINT_KEYS)['LapSeconds'].transform('median')
    is_steady = (laps['LapSeconds'] - stint_median).abs() < PACE_BAND * stint_median
    is_in_traffic = laps['GapAhead'] < TRAFFIC_GAP_S
    laps = laps[is_steady & ~is_in_traffic]

    # Un relais ne compte que s'il lui reste assez de tours
    laps_in_stint = laps.groupby(STINT_KEYS)['LapSeconds'].transform('size')
    return laps[laps_in_stint >= MIN_LONG_RUN_LAPS]
