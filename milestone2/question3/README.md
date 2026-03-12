# Milestone II - Question 3

## Question
Is provincial labour-market pressure (job vacancy rate) associated with voter participation quality (turnout, rejected-ballot rate, valid-ballot rate) in the 2019 and 2021 federal elections?

## Files in this folder
- `scripts/q3_preprocess.py`: preliminary conversion and summarization.
- `scripts/q3_demo.py`: demo-time parameterized selection + visualization.
- `data/processed/q3_election_summary.csv`: province-year election aggregates.
- `data/processed/q3_vacancy_windows.csv`: province-year-sector vacancy window averages.
- `data/processed/q3_analysis_matrix.csv`: final encoded matrix used by the demo script.
- `output/q3_scatter_2021_turnout.svg`: sample ALL-province scatter visualization.
- `output/q3_ontario_2year_turnout.svg`: sample single-province comparison visualization.

## Run
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

```bash
python3 milestone2/question3/scripts/q3_demo.py \
  --province Ontario \
  --sector 'Total, all industries' \
  --metric rejected_rate \
  --quarters-before 2 \
  --output-svg milestone2/question3/output/q3_ontario_2year_rejected.svg
```
