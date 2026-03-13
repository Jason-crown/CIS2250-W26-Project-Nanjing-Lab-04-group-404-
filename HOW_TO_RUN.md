# How To Run

## Question 3 (Milestone II - stable)
Run from repo root.

1) Build processed files:
```bash
python3 milestone2/question3/scripts/q3_preprocess.py
```

2) All-province demo view:
```bash
python3 milestone2/question3/scripts/q3_demo.py \
  --year 2021 \
  --province ALL \
  --sector 'Total, all industries' \
  --metric turnout \
  --quarters-before 2 \
  --output-svg milestone2/question3/output/q3_scatter_2021_turnout.svg
```

3) Single-province demo view:
```bash
python3 milestone2/question3/scripts/q3_demo.py \
  --province Ontario \
  --sector 'Total, all industries' \
  --metric rejected_rate \
  --quarters-before 2 \
  --output-svg milestone2/question3/output/q3_ontario_2year_rejected.svg
```

## Question 1 / Question 2
Q1 and Q2 scripts are in `src/` and are still team work-in-progress.
For Milestone II, each question should have at least some working code underway for demo feedback.
