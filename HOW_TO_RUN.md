# How To Run (Milestone II)

Run all commands from the repository root.

## 0) Inputs used by scripts
Current repo includes these source files:
- `election43/table_tableau11.csv`
- `election44/table_tableau11.csv`
- `statscan/14100442.csv`

Additional files required for Q1/Q2 (if not yet committed):
- Table 8 election files for 2019/2021
- CPI table export (18-10-0004-11)

## 1) Q1 - CPI + vacancy vs participation quality
Build compact CSV (redirect stdout):
```bash
python3 src/q1_build_cpi_and_vacancy_vs_participation.py \
  <table11_2019.csv> <table11_2021.csv> <cpi.csv> <vacancy.csv> \
  > data/processed/q1_compact.csv
```

Plot PDF:
```bash
python3 src/q1_plot_cpi_or_vacancy_vs_participation.py \
  data/processed/q1_compact.csv q1_2021_turnout.pdf \
  2021 12 4 "All-items" cpi turnout
```

## 2) Q2 - CPI change vs party vote-share swing
Build compact CSV (redirect stdout):
```bash
python3 src/q2_build_party_swing.py \
  <table8_2019.csv> <table8_2021.csv> <cpi.csv> \
  > data/processed/q2_compact.csv
```

Plot PDF:
```bash
python3 src/q2_plot_party_swing.py \
  data/processed/q2_compact.csv q2_liberal.pdf \
  "Liberal" 12 "All-items"
```

## 3) Q3 - Vacancy rate vs participation quality
Build compact CSV (redirect stdout):
```bash
python3 src/q3_build_vacancy_vs_participation.py \
  election43/table_tableau11.csv election44/table_tableau11.csv statscan/14100442.csv \
  > data/processed/q3_compact.csv
```

Plot PDF:
```bash
python3 src/q3_plot_vacancy_vs_participation.py \
  data/processed/q3_compact.csv q3_2021_turnout.pdf \
  2021 "Total, all industries" 4 turnout
```

## Notes
- Build scripts are the preliminary processing step.
- Plot scripts are the demo-time processing step.
- For Milestone II report, include an example visualization for each question.
