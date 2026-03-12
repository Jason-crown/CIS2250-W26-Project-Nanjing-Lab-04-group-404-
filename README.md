# Team 404-Nanjing — Milestone II (Lab-Style Scripts)

These scripts are written **in the same style as the CIS*2250 labs**:
- command-line programs
- robust error messages to **stderr**
- CSV processing using `csv.reader` and `csv.writer`
- compact CSV output printed to **stdout** so you can redirect using `>` (as shown in labs) fileciteturn32file0

## Recommended folder layout
```
project-root/
  src/
    helpers.py
    q1_build_cpi_and_vacancy_vs_participation.py
    q1_plot_cpi_or_vacancy_vs_participation.py
    q2_build_party_swing.py
    q2_plot_party_swing.py
    q3_build_vacancy_vs_participation.py
    q3_plot_vacancy_vs_participation.py
  data/
    raw/
      table_tableau11_2019.csv
      table_tableau11_2021.csv
      table_tableau08_2019.csv
      table_tableau08_2021.csv
      1810000411_databaseLoadingData.csv   (CPI index)
      1410044201_databaseLoadingData.csv   (vacancies)
    processed/
```

## Install requirements
```
pip install pandas matplotlib
```

## Q2 workflow (example, lab style)
1) Build the compact CSV (redirect stdout to a file):
```
python3 src/q2_build_party_swing.py data/raw/table_tableau08_2019.csv data/raw/table_tableau08_2021.csv data/raw/1810000411_databaseLoadingData.csv > data/processed/q2_compact.csv
```

2) Plot one party (writes PDF/PNG to file, like the visualization lab) fileciteturn32file1
```
python3 src/q2_plot_party_swing.py data/processed/q2_compact.csv q2_liberal.pdf "Liberal" 12 "All-items"
```

## Q3 workflow (example)
1) Build compact CSV:
```
python3 src/q3_build_vacancy_vs_participation.py data/raw/table_tableau11_2019.csv data/raw/table_tableau11_2021.csv data/raw/1410044201_databaseLoadingData.csv > data/processed/q3_compact.csv
```

2) Plot:
```
python3 src/q3_plot_vacancy_vs_participation.py data/processed/q3_compact.csv q3_turnout.pdf 2021 "Total, all industries" 4 turnout
```

## Q1 workflow (example)
1) Build compact CSV:
```
python3 src/q1_build_cpi_and_vacancy_vs_participation.py data/raw/table_tableau11_2019.csv data/raw/table_tableau11_2021.csv data/raw/1810000411_databaseLoadingData.csv data/raw/1410044201_databaseLoadingData.csv > data/processed/q1_compact.csv
```

2) Plot:
```
python3 src/q1_plot_cpi_or_vacancy_vs_participation.py data/processed/q1_compact.csv q1_cpi_turnout.pdf 2021 12 4 "All-items" cpi turnout
```
