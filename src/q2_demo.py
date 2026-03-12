#!/usr/bin/env python3
"""
Demo Q2: plot CPI change vs party vote-share swing (2019 -> 2021).

Reads data/processed/q2_compact.csv (created by preprocess_q2.py).

Example:
  python3 src/q2_demo.py --party "Liberal" --months_before 12 --cpi_category All-items
"""
from __future__ import annotations

import argparse

import pandas as pd
import matplotlib.pyplot as plt

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="data/processed/q2_compact.csv")
    ap.add_argument("--party", required=True, help='Exact party label from Table 8 (e.g., "Liberal")')
    ap.add_argument("--months_before", type=int, required=True)
    ap.add_argument("--cpi_category", default="All-items")
    ap.add_argument("--province", default="ALL")
    args = ap.parse_args()

    df = pd.read_csv(args.infile)
    d = df[
        (df["party"] == args.party) &
        (df["months_before"] == args.months_before) &
        (df["cpi_category"] == args.cpi_category)
    ].copy()

    if args.province != "ALL":
        d = d[d["province"] == args.province]

    if d.empty:
        raise SystemExit("No rows matched. Check party spelling, months_before, cpi_category, and infile.")

    x = d["cpi_change"]
    y = d["delta_vote_share"]

    plt.figure()
    plt.scatter(x, y)
    plt.title(f'Q2: CPI change vs vote-share swing ({args.party})')
    plt.xlabel(f"CPI YoY% avg change (2021 window - 2019 window), last {args.months_before} months")
    plt.ylabel("Δ vote share (2021 - 2019)")
    for _, row in d.iterrows():
        plt.annotate(row["province"][:3], (row["cpi_change"], row["delta_vote_share"]))
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
