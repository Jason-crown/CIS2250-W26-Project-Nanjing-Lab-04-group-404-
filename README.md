# CIS2250 W26 - Team 404 (Nanjing)

This repository contains milestone work for the **How Canada Votes** project.

## Source-of-truth (Milestone II)
Per `CIS2250-W26-Project.pdf`, each question (Q1, Q2, Q3) includes:
- the question itself
- preliminary data processing (fields, selections/summarizations, final encodings, file organization)
- parameters
- final processing using parameters (demo-time)
- example visualization

## Milestone II implementation mapping (current)

### Q1 (CPI + vacancy vs participation quality)
- Build: `src/q1_build_cpi_and_vacancy_vs_participation.py`
- Processed output: `data/processed/q1_compact.csv`
- Plot: `src/q1_plot_cpi_or_vacancy_vs_participation.py`
- Visualization output: `q1_*.pdf`

### Q2 (CPI change vs party vote-share swing)
- Build: `src/q2_build_party_swing.py`
- Processed output: `data/processed/q2_compact.csv`
- Plot: `src/q2_plot_party_swing.py`
- Visualization output: `q2_*.pdf`

### Q3 (Vacancy rate vs participation quality)
- Build: `src/q3_build_vacancy_vs_participation.py`
- Processed output: `data/processed/q3_compact.csv`
- Plot: `src/q3_plot_vacancy_vs_participation.py`
- Visualization output: `q3_*.pdf`

## Build/plot convention
- Build scripts output CSV to `stdout`; redirect to `data/processed/*.csv` using `>`.
- Plot scripts read processed CSV and output a visualization file (PDF in current mapping).

## Folder guide
- `src/`: primary build/plot scripts for Q1/Q2/Q3.
- `election43/`, `election44/`: election source CSV files.
- `statscan/`: Statistics Canada source CSV files.
- `milestone2/question3/`: alternate Q3 artifact set used during development.
- `HOW_TO_RUN.md`: command examples.
