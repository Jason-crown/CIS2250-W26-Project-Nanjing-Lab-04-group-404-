# Team 404-Nanjing — Milestone II scripts

## Requirements
- Python 3.10+
- `pip install pandas matplotlib`

## Suggested repo layout
- `data/raw/` for downloaded CSVs
- `data/processed/` for compact outputs
- `src/` for scripts

## 0) Rename your raw files (recommended)
So you never mix years:

- `data/raw/table_tableau11_2019.csv`
- `data/raw/table_tableau11_2021.csv`
- `data/raw/table_tableau08_2019.csv`
- `data/raw/table_tableau08_2021.csv`
- `data/raw/18100004.csv`  (CPI index)
- `data/raw/14100442.csv`  (vacancies)

## 1) Preprocess
### Q1
```bash
python3 src/preprocess_q1.py \
  --table11_2019 data/raw/table_tableau11_2019.csv \
  --table11_2021 data/raw/table_tableau11_2021.csv \
  --cpi data/raw/18100004.csv \
  --vac data/raw/14100442.csv \
  --out data/processed/q1_compact.csv
```

### Q2
```bash
python3 src/preprocess_q2.py \
  --table8_2019 data/raw/table_tableau08_2019.csv \
  --table8_2021 data/raw/table_tableau08_2021.csv \
  --cpi data/raw/18100004.csv \
  --out data/processed/q2_compact.csv
```

### Q3
```bash
python3 src/preprocess_q3.py \
  --table11_2019 data/raw/table_tableau11_2019.csv \
  --table11_2021 data/raw/table_tableau11_2021.csv \
  --vac data/raw/14100442.csv \
  --out data/processed/q3_compact.csv
```

## 2) Demo commands
### Q1 example
```bash
python3 src/q1_demo.py --year 2021 --months_before 12 --quarters_before 4 --cpi_category "All-items" --xvar cpi --metric turnout
```

### Q2 example
```bash
python3 src/q2_demo.py --party "Liberal" --months_before 12 --cpi_category "All-items"
```

### Q3 example
```bash
python3 src/q3_demo.py --year 2021 --sector "Total, all industries" --quarters_before 4 --metric turnout
```
