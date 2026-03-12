#!/usr/bin/env python3
"""
Preprocess Q1:
CPI inflation (YoY%) + job vacancy rate (labour tightness) vs voter participation quality
(turnout / rejected_rate / valid_rate) for 2019 and 2021.

Outputs a compact table with precomputed window averages so the demo script is fast.

Example:
  python3 src/preprocess_q1.py \
    --table11_2019 data/raw/table_tableau11_2019.csv \
    --table11_2021 data/raw/table_tableau11_2021.csv \
    --cpi data/raw/18100004.csv \
    --vac data/raw/14100442.csv \
    --out data/processed/q1_compact.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from utils import (
    GEO_ORDER,
    ELECTION_DATES,
    CpiConfig,
    VacConfig,
    load_table11,
    load_cpi_index_filtered,
    compute_cpi_yoy,
    cpi_window_average,
    load_vacancy_filtered,
    vacancy_window_average,
)

DEFAULT_MONTH_WINDOWS = "3,6,12,24"
DEFAULT_QUARTER_WINDOWS = "1,2,4"
DEFAULT_CPI_CATS = "All-items,Food"
DEFAULT_NAICS = "Total, all industries"
DEFAULT_STATS = "Job vacancy rate"

def parse_list_int(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def parse_list_str(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table11_2019", required=True, help="Election Table 11 CSV for 2019 (43rd)")
    ap.add_argument("--table11_2021", required=True, help="Election Table 11 CSV for 2021 (44th)")
    ap.add_argument("--cpi", required=True, help="StatsCan CPI index CSV (18100004.csv)")
    ap.add_argument("--vac", required=True, help="StatsCan job vacancies CSV (14100442.csv)")
    ap.add_argument("--out", default="data/processed/q1_compact.csv")
    ap.add_argument("--months_windows", default=DEFAULT_MONTH_WINDOWS)
    ap.add_argument("--quarters_windows", default=DEFAULT_QUARTER_WINDOWS)
    ap.add_argument("--cpi_categories", default=DEFAULT_CPI_CATS)
    ap.add_argument("--naics", default=DEFAULT_NAICS)
    ap.add_argument("--vac_stat", default=DEFAULT_STATS)
    args = ap.parse_args()

    months_windows = parse_list_int(args.months_windows)
    quarter_windows = parse_list_int(args.quarters_windows)
    cpi_categories = parse_list_str(args.cpi_categories)

    # --- Election outcomes (province-year)
    e19 = load_table11(args.table11_2019, 2019)
    e21 = load_table11(args.table11_2021, 2021)
    election = pd.concat([e19, e21], ignore_index=True)

    geos = sorted(set(election["province"].unique().tolist()))
    # keep stable ordering for plots
    geos = [g for g in GEO_ORDER if g in geos] + [g for g in geos if g not in GEO_ORDER]

    # --- CPI: load only months needed for YoY + windows
    # determine earliest month needed:
    # - earliest election month minus (max months_window - 1)
    # - minus 12 months for YoY lag
    from pandas import Timestamp
    e19m = Timestamp(ELECTION_DATES[2019]).replace(day=1)
    e21m = Timestamp(ELECTION_DATES[2021]).replace(day=1)
    max_m = max(months_windows)
    min_month = min(e19m, e21m) - pd.offsets.DateOffset(months=(max_m - 1 + 12))
    max_month = max(e19m, e21m)  # inclusive
    min_ym = min_month.strftime("%Y-%m")
    max_ym = max_month.strftime("%Y-%m")

    cpi_cfg = CpiConfig(
        cpi_path=args.cpi,
        categories=cpi_categories,
        geos=geos,
        min_ym=min_ym,
        max_ym=max_ym,
    )
    cpi_index = load_cpi_index_filtered(cpi_cfg)
    cpi_yoy = compute_cpi_yoy(cpi_index)

    cpi_rows = []
    for year in (2019, 2021):
        for mwin in months_windows:
            for cat in cpi_categories:
                cpi_rows.append(cpi_window_average(cpi_yoy, year=year, months_before=mwin, category=cat))
    cpi_win = pd.concat(cpi_rows, ignore_index=True)  # GEO, cpi_yoy_avg, year, months_before, cpi_category

    # --- Vacancy: load only quarters needed
    # quarters table uses YYYY-01/04/07/10 as quarter-start.
    # need from earliest election quarter minus 3*(max_q-1) months.
    max_q = max(quarter_windows)
    e19q = pd.Timestamp(ELECTION_DATES[2019]).replace(day=1)
    e21q = pd.Timestamp(ELECTION_DATES[2021]).replace(day=1)
    # quarter floor by month; easiest just take quarter-start months directly:
    def quarter_start(ts: pd.Timestamp) -> pd.Timestamp:
        m = ((ts.month - 1)//3)*3 + 1
        return pd.Timestamp(year=ts.year, month=m, day=1)
    end_q = max(quarter_start(e19q), quarter_start(e21q))
    start_q = min(quarter_start(e19q), quarter_start(e21q)) - pd.offsets.DateOffset(months=3*(max_q-1))
    vac_cfg = VacConfig(
        vac_path=args.vac,
        geos=geos,
        stats_label=args.vac_stat,
        naics_list=[args.naics],
        min_ym=start_q.strftime("%Y-%m"),
        max_ym=end_q.strftime("%Y-%m"),
    )
    vac = load_vacancy_filtered(vac_cfg)

    vac_rows = []
    for year in (2019, 2021):
        for qwin in quarter_windows:
            vac_rows.append(vacancy_window_average(vac, year=year, quarters_before=qwin, naics=args.naics))
    vac_win = pd.concat(vac_rows, ignore_index=True)  # GEO, vacancy_rate_avg, year, quarters_before, naics

    # --- Join: election (province) with CPI and vacancy windows
    # Rename GEO to province to join
    cpi_win = cpi_win.rename(columns={"GEO": "province"})
    vac_win = vac_win.rename(columns={"GEO": "province"})
    out = (
        election.merge(cpi_win, on=["province", "year"], how="left")
                .merge(vac_win, on=["province", "year"], how="left")
    )

    # Keep only rows where CPI & vacancy exist for selected window parameters
    keep_cols = [
        "province","year",
        "months_before","cpi_category","cpi_yoy_avg",
        "quarters_before","naics","vacancy_rate_avg",
        "turnout","rejected_rate","valid_rate",
        "electors","total_ballots_cast","valid_ballots","rejected_ballots",
    ]
    out = out[keep_cols].sort_values(["year","province","months_before","quarters_before","cpi_category"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out):,} rows -> {args.out}")

if __name__ == "__main__":
    main()
