"""Étape 1 : chargement des tours d'une séance via FastF1."""

from pathlib import Path

import fastf1
import pandas as pd

# Dossier du cache FastF1, repéré depuis ce fichier pour ne pas dépendre du dossier de lancement
CACHE_DIR = Path(__file__).resolve().parents[1] / 'data' / 'cache'


def get_event_name(year, grand_prix):
    """Renvoie le nom officiel du Grand Prix que FastF1 a reconnu à partir du texte saisi.

    FastF1 cherche le nom le plus proche (pays, ville ou nom officiel, en anglais) : une faute de frappe
    peut donc désigner une autre course sans provoquer d'erreur. Ce nom permet de le vérifier.
    """
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    return fastf1.get_event(year, grand_prix)['EventName']


def load_laps(year, grand_prix, session_name):
    """Renvoie les tours d'une séance sous forme de tableau, avec une colonne Session.

    session_name : 'FP1', 'FP2', 'FP3', 'Q' ou 'R' (course).
    Le premier appel télécharge les données, les suivants lisent le cache.
    """
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    session = fastf1.get_session(year, grand_prix, session_name)
    # On ne charge que les tours : la télémétrie, la météo et les messages ne servent pas ici
    session.load(telemetry=False, weather=False, messages=False)
    laps = pd.DataFrame(session.laps)
    laps['Session'] = session_name
    return laps


def load_track_temperature(year, grand_prix, session_name):
    """Renvoie la température moyenne de la piste (°C) pendant une séance."""
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    session = fastf1.get_session(year, grand_prix, session_name)
    session.load(laps=False, telemetry=False, weather=True, messages=False)
    return session.weather_data['TrackTemp'].mean()
