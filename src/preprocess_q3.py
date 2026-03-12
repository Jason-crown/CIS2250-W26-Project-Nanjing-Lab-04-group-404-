#!/usr/bin/env python3
"""
Preprocess Q3:
Job vacancy rate (labour-market pressure) vs participation quality (turnout / rejected_rate / valid_rate)
for 2019 and 2021, by province and NAICS sector.

Outputs a compact table with precomputed vacancy averages for a set of quarter windows.

Example:
  python3 src/preprocess_q3.py \
    --table11_2019 data/raw/table_tableau11_2019.csv \
    --table11_2021 data/raw/table_tableau11_2021.csv \
    --vac data/raw/14100442.csv \
    --out data/processed/q3_compact.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from utils import (
    GEO_ORDER,
    ELECTION_DATES,
    VacConfig,
    load_table11,
    load_vacancy_filtered,
    vacancy_window_average,
)

DEFAULT_QUARTER_WINDOWS = "1,2,4"
DEFAULT_STATS = "Job vacancy rate"

def parse_list_int(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table11_2019", required=True)
    ap.add_argument("--table11_2021", required=True)
    ap.add_argument("--vac", required=True, help="StatsCan job vacancies CSV (14100442.csv)")
    ap.add_argument("--out", default="data/processed/q3_compact.csv")
    ap.add_argument("--quarters_windows", default=DEFAULT_QUARTER_WINDOWS)
    ap.add_argument("--vac_stat", default=DEFAULT_STATS)
    args = ap.parse_args()

    quarter_windows = parse_list_int(args.quarters_windows)

    # Election outcomes
    e19 = load_table11(args.table11_2019, 2019)
    e21 = load_table11(args.table11_2021, 2021)
    election = pd.concat([e19, e21], ignore_index=True)
    geos = sorted(set(election["province"].unique().tolist()))
    geos = [g for g in GEO_ORDER if g in geos] + [g for g in geos if g not in GEO_ORDER]

    # Vacancy: load only quarters needed for max window across both years
    max_q = max(quarter_windows)

    def quarter_start(ts: pd.Timestamp) -> pd.Timestamp:
        m = ((ts.month - 1)//3)*3 + 1
        return pd.Timestamp(year=ts.year, month=m, day=1)

    e19q = quarter_start(pd.Timestamp(ELECTION_DATES[2019]))
    e21q = quarter_start(pd.Timestamp(ELECTION_DATES[2021]))
    end_q = max(e19q, e21q)
    start_q = min(e19q, e21q) - pd.offsets.DateOffset(months=3*(max_q-1))

    # keep all NAICS categories ("*") to support sector parameter
    vac_cfg = VacConfig(
        vac_path=args.vac,
        geos=geos,
        stats_label=args.vac_stat,
        naics_list=["*"],
        min_ym=start_q.strftime("%Y-%m"),
        max_ym=end_q.strftime("%Y-%m"),
    )
    vac = load_vacancy_filtered(vac_cfg)

    # precompute vacancy averages per sector
    sectors = sorted(vac["naics"].unique().tolist())

    rows = []
    for year in (2019, 2021):
        for qwin in quarter_windows:
            for sector in sectors:
                d = vacancy_window_average(vac, year=year, quarters_before=qwin, naics=sector)
                rows.append(d)
    vac_win = pd.concat(rows, ignore_index=True).rename(columns={"GEO":"province"})

    out = election.merge(vac_win, on=["province","year"], how="left")
    keep_cols = [
        "province","year",
        "naics","quarters_before","vacancy_rate_avg",
        "turnout","rejected_rate","valid_rate",
    ]
    out = out[keep_cols].sort_values(["year","naics","province","quarters_before"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out):,} rows -> {args.out}")

if __name__ == "__main__":
    main()
