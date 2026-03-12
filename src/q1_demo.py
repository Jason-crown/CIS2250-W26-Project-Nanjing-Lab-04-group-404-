#!/usr/bin/env python3
"""
Demo Q1: plot CPI inflation / vacancy rate vs participation quality.

Reads data/processed/q1_compact.csv (created by preprocess_q1.py).

Example:
  python3 src/q1_demo.py --year 2021 --months_before 12 --quarters_before 4 --cpi_category All-items --xvar cpi --metric turnout
"""
from __future__ import annotations

import argparse
import math

import pandas as pd
import matplotlib.pyplot as plt

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="data/processed/q1_compact.csv")
    ap.add_argument("--year", type=int, choices=[2019,2021], required=True)
    ap.add_argument("--months_before", type=int, required=True)
    ap.add_argument("--quarters_before", type=int, required=True)
    ap.add_argument("--cpi_category", default="All-items")
    ap.add_argument("--xvar", choices=["cpi","vacancy"], default="cpi")
    ap.add_argument("--metric", choices=["turnout","rejected_rate","valid_rate"], default="turnout")
    ap.add_argument("--province", default="ALL")
    args = ap.parse_args()

    df = pd.read_csv(args.infile)

    d = df[
        (df["year"] == args.year) &
        (df["months_before"] == args.months_before) &
        (df["quarters_before"] == args.quarters_before) &
        (df["cpi_category"] == args.cpi_category)
    ].copy()

    if args.province != "ALL":
        d = d[d["province"] == args.province]

    if d.empty:
        raise SystemExit("No rows matched. Check your parameters and infile.")

    if args.xvar == "cpi":
        x = d["cpi_yoy_avg"]
        x_label = f"CPI YoY% avg (last {args.months_before} months, {args.cpi_category})"
    else:
        x = d["vacancy_rate_avg"]
        x_label = f"Job vacancy rate avg (last {args.quarters_before} quarters)"

    y = d[args.metric]
    y_label = args.metric.replace("_"," ").title()

    plt.figure()
    if args.province == "ALL":
        plt.scatter(x, y)
        # correlation (Pearson)
        if len(d) >= 2 and x.std() > 0 and y.std() > 0:
            corr = float(pd.Series(x).corr(pd.Series(y)))
            title = f"Q1 ({args.year})  r={corr:.3f}"
        else:
            title = f"Q1 ({args.year})"
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        # annotate points with province abbreviations (first 3 letters)
        for _, row in d.iterrows():
            plt.annotate(row["province"][:3], (row[x.name], row[args.metric]))
    else:
        # province selected: show both years comparison for metric and xvar using bars
        # (the file contains rows for both years; reload for both)
        all_df = pd.read_csv(args.infile)
        dd = all_df[
            (all_df["province"] == args.province) &
            (all_df["months_before"] == args.months_before) &
            (all_df["quarters_before"] == args.quarters_before) &
            (all_df["cpi_category"] == args.cpi_category)
        ].copy().sort_values("year")
        if dd.empty:
            raise SystemExit("No rows for that province with those parameters.")
        years = dd["year"].astype(str).tolist()
        vals = dd[args.metric].tolist()
        plt.bar(years, vals)
        plt.title(f"{args.province}: {args.metric} (windowed)")
        plt.xlabel("Election year")
        plt.ylabel(y_label)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
