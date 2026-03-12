#!/usr/bin/env python3
"""
Demo Q3: plot job vacancy rate vs participation metric.

Reads data/processed/q3_compact.csv (created by preprocess_q3.py).

Example:
  python3 src/q3_demo.py --year 2021 --sector "Total, all industries" --quarters_before 4 --metric turnout
"""
from __future__ import annotations

import argparse
import pandas as pd
import matplotlib.pyplot as plt

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="data/processed/q3_compact.csv")
    ap.add_argument("--year", type=int, choices=[2019,2021], required=True)
    ap.add_argument("--sector", required=True, help='Exact NAICS label from vacancy table (e.g., "Total, all industries")')
    ap.add_argument("--quarters_before", type=int, required=True)
    ap.add_argument("--metric", choices=["turnout","rejected_rate","valid_rate"], default="turnout")
    ap.add_argument("--province", default="ALL")
    args = ap.parse_args()

    df = pd.read_csv(args.infile)
    d = df[
        (df["year"] == args.year) &
        (df["naics"] == args.sector) &
        (df["quarters_before"] == args.quarters_before)
    ].copy()

    if args.province != "ALL":
        d = d[d["province"] == args.province]

    if d.empty:
        raise SystemExit("No rows matched. Check sector spelling, quarters_before, and infile.")

    x = d["vacancy_rate_avg"]
    y = d[args.metric]

    plt.figure()
    if args.province == "ALL":
        plt.scatter(x, y)
        plt.title(f"Q3 ({args.year}) {args.sector}")
        plt.xlabel(f"Job vacancy rate avg (last {args.quarters_before} quarters)")
        plt.ylabel(args.metric.replace("_"," ").title())
        for _, row in d.iterrows():
            plt.annotate(row["province"][:3], (row["vacancy_rate_avg"], row[args.metric]))
    else:
        # compare both years for selected province
        all_df = pd.read_csv(args.infile)
        dd = all_df[(all_df["province"]==args.province) &
                    (all_df["naics"]==args.sector) &
                    (all_df["quarters_before"]==args.quarters_before)].copy().sort_values("year")
        years = dd["year"].astype(str).tolist()
        vals = dd[args.metric].tolist()
        plt.bar(years, vals)
        plt.title(f"{args.province}: {args.metric} ({args.sector})")
        plt.xlabel("Election year")
        plt.ylabel(args.metric.replace("_"," ").title())

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
