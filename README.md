# CIS2250 W26 - Team 404 (Nanjing)

This repository contains milestone work for the **How Canada Votes** project.

## Current milestone status
- **Milestone II - Question 3** is complete and runnable in:
  - `milestone2/question3/scripts/q3_preprocess.py`
  - `milestone2/question3/scripts/q3_demo.py`
- Question 1 and Question 2 work-in-progress scripts are under `src/`.

## Folder guide
- `milestone2/question3/`: canonical Question 3 artifacts (scripts, processed files, sample outputs).
- `election43/`, `election44/`: federal election source CSV files used by scripts.
- `statscan/`: Statistics Canada source CSV files used by scripts.
- `src/`: earlier / team-in-progress scripts for Q1, Q2, Q3.
- `HOW_TO_RUN.md`: short command reference.

## Quick start (Question 3)
From repo root:

```bash
python3 milestone2/question3/scripts/q3_preprocess.py
```

```bash
python3 milestone2/question3/scripts/q3_demo.py \
  --year 2021 \
  --province ALL \
  --sector 'Total, all industries' \
  --metric turnout \
  --quarters-before 2 \
  --output-svg milestone2/question3/output/q3_scatter_2021_turnout.svg
```
