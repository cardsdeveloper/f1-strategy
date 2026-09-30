# F1 Race Strategy — Tyre Degradation Modelling & Pit Stop Simulator

**Work in progress**

## Overview

In a race, the strategy engineer constantly faces one question:
*"On which lap should the driver pit to minimise total race time, while limiting the risk of rejoining in traffic or under a neutralisation?"*

This project tackles that question with real data. It models tyre degradation for each compound (Soft / Medium / Hard) from official Formula 1 lap timing, then uses those models in a simulator that evaluates pit stop windows and estimates the probability of a successful undercut.

## Approach

1. **Data extraction:** lap-by-lap timing, sector times, tyre compound, tyre age, pit stop data and track status from a real Grand Prix, via [FastF1](https://github.com/theOehrly/Fast-F1).
2. **Data cleaning:** remove Safety Car / VSC laps, in-laps and out-laps, and laps affected by traffic.
3. **Tyre degradation model:** per-compound polynomial regression of lap time against tyre age, with fuel-effect correction.
4. **Strategy simulator:** compare one-stop and two-stop strategies across pit windows, and estimate undercut success probability as a function of pit-loss time (Monte Carlo).

## Tech stack

Python · FastF1 · pandas · NumPy · SciPy · scikit-learn · Matplotlib · Seaborn

## Project structure
f1-strategy/
├── data/processed/ # cleaned datasets
├── notebooks/ # exploration & analysis
├── src/
│ ├── data_loader.py # FastF1 data extraction
│ ├── cleaning.py # SC/VSC, in/out laps, traffic filtering
│ ├── degradation.py # tyre wear models
│ └── strategy.py # pit stop / undercut simulator
├── figures/
└── requirements.txt


## Getting started

```bash
git clone https://github.com/cardsdeveloper/f1-strategy.git
cd f1-strategy
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Roadmap

- [ ] Data extraction from a Grand Prix
- [ ] Data cleaning (SC/VSC, in/out laps, traffic)
- [ ] Tyre degradation model per compound
- [ ] Strategy simulator and undercut probability

## Data source

Official Formula 1 timing data accessed through the open-source FastF1 library. This project is unofficial and not associated with Formula 1 or the FIA.