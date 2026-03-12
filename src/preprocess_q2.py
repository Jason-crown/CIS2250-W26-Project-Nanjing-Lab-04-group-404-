#!/usr/bin/env python3
"""
Preprocess Q2:
Inflation (CPI YoY%) vs party vote-share swing between 2019 and 2021, by province.

Uses Table 8 for both elections to compute vote shares for EVERY party in the file.

Outputs a compact table:
  province, party, vote_share_2019, vote_share_2021, delta_vote_share,
  cpi_category, months_before, cpi_change

Example:
  python3 src/preprocess_q2.py \
    --table8_2019 data/raw/table_tableau08_2019.csv \
    --table8_2021 data/raw/table_tableau08_2021.csv \
    --cpi data/raw/18100004.csv \
    --out data/processed/q2_compact.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from utils import (
    GEO_ORDER,
    ELECTION_DATES,
    CpiConfig,
    load_table8_party_votes,
    compute_vote_shares,
    load_cpi_index_filtered,
    compute_cpi_yoy,
    cpi_window_average,
)

DEFAULT_MONTH_WINDOWS = "3,6,12,24"
DEFAULT_CPI_CATS = "All-items,Food"

def parse_list_int(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def parse_list_str(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table8_2019", required=True, help="Election Table 8 CSV for 2019 (43rd)")
    ap.add_argument("--table8_2021", required=True, help="Election Table 8 CSV for 2021 (44th)")
    ap.add_argument("--cpi", required=True, help="StatsCan CPI index CSV (18100004.csv)")
    ap.add_argument("--out", default="data/processed/q2_compact.csv")
    ap.add_argument("--months_windows", default=DEFAULT_MONTH_WINDOWS)
    ap.add_argument("--cpi_categories", default=DEFAULT_CPI_CATS)
    args = ap.parse_args()

    months_windows = parse_list_int(args.months_windows)
    cpi_categories = parse_list_str(args.cpi_categories)

    # --- Party vote shares (every party)
    v19 = load_table8_party_votes(args.table8_2019, 2019)
    v21 = load_table8_party_votes(args.table8_2021, 2021)
    shares = compute_vote_shares(pd.concat([v19, v21], ignore_index=True))

    # wide for delta
    s19 = shares[shares["year"]==2019][["province","party","vote_share"]].rename(columns={"vote_share":"vote_share_2019"})
    s21 = shares[shares["year"]==2021][["province","party","vote_share"]].rename(columns={"vote_share":"vote_share_2021"})
    vote = s19.merge(s21, on=["province","party"], how="outer").fillna(0.0)
    vote["delta_vote_share"] = vote["vote_share_2021"] - vote["vote_share_2019"]

    geos = sorted(set(vote["province"].unique().tolist()))
    geos = [g for g in GEO_ORDER if g in geos] + [g for g in geos if g not in GEO_ORDER]

    # --- CPI YoY window averages for each election year, then difference
    from pandas import Timestamp
    e19m = Timestamp(ELECTION_DATES[2019]).replace(day=1)
    e21m = Timestamp(ELECTION_DATES[2021]).replace(day=1)
    max_m = max(months_windows)
    min_month = min(e19m, e21m) - pd.offsets.DateOffset(months=(max_m - 1 + 12))
    max_month = max(e19m, e21m)
    cpi_cfg = CpiConfig(
        cpi_path=args.cpi,
        categories=cpi_categories,
        geos=geos,
        min_ym=min_month.strftime("%Y-%m"),
        max_ym=max_month.strftime("%Y-%m"),
    )
    cpi_index = load_cpi_index_filtered(cpi_cfg)
    cpi_yoy = compute_cpi_yoy(cpi_index)

    cpi19_rows = []
    cpi21_rows = []
    for mwin in months_windows:
        for cat in cpi_categories:
            cpi19_rows.append(cpi_window_average(cpi_yoy, year=2019, months_before=mwin, category=cat))
            cpi21_rows.append(cpi_window_average(cpi_yoy, year=2021, months_before=mwin, category=cat))

    c19 = pd.concat(cpi19_rows, ignore_index=True).rename(columns={"GEO":"province", "cpi_yoy_avg":"cpi_yoy_avg_2019"})
    c21 = pd.concat(cpi21_rows, ignore_index=True).rename(columns={"GEO":"province", "cpi_yoy_avg":"cpi_yoy_avg_2021"})
    cpi_merge = c19.merge(
        c21[["province","months_before","cpi_category","cpi_yoy_avg_2021"]],
        on=["province","months_before","cpi_category"],
        how="inner"
    )
    cpi_merge["cpi_change"] = cpi_merge["cpi_yoy_avg_2021"] - cpi_merge["cpi_yoy_avg_2019"]

    out = vote.merge(cpi_merge[["province","months_before","cpi_category","cpi_change"]], on="province", how="left")
    out = out.sort_values(["party","province","months_before","cpi_category"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out):,} rows -> {args.out}")

if __name__ == "__main__":
    main()
