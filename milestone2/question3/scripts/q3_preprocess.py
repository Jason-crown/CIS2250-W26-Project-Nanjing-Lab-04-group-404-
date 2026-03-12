#!/usr/bin/env python3
"""Build Milestone II Question 3 encoded files.

Question 3:
Is provincial labour-market pressure (job vacancy rate) associated with
voter participation quality (turnout / rejected-ballot rate / valid-ballot rate)
in the 2019 and 2021 federal elections?
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ELECTION_MONTH = {2019: 10, 2021: 9}  # Oct 2019, Sep 2021 federal elections
WINDOW_QUARTERS = (1, 2, 4)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]
QUESTION3_DIR = SCRIPT_DIR.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess data for Milestone II Question 3")
    parser.add_argument(
        "--election2019",
        default=str(PROJECT_ROOT / "election43" / "table_tableau11.csv"),
        help="Path to 2019 election table_tableau11.csv",
    )
    parser.add_argument(
        "--election2021",
        default=str(PROJECT_ROOT / "election44" / "table_tableau11.csv"),
        help="Path to 2021 election table_tableau11.csv",
    )
    parser.add_argument(
        "--vacancy",
        default=str(PROJECT_ROOT / "statscan" / "14100442.csv"),
        help="Path to StatsCan 14-10-0442-01 CSV",
    )
    parser.add_argument(
        "--outdir",
        default=str(QUESTION3_DIR / "data" / "processed"),
        help="Output directory for encoded files",
    )
    return parser.parse_args()


def normalize_province(name: str) -> str:
    # Election tables are bilingual in some rows; keep English component.
    return name.split("/", 1)[0].strip()


def clean_number(raw: str) -> Optional[float]:
    text = (raw or "").strip().replace(",", "")
    if not text:
        return None
    if text in {"..", "x", "X", "F", "A", "B", "C", "D", "E", "M"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def find_column(fieldnames: Iterable[str], keyword: str) -> str:
    lowered = keyword.lower()
    for col in fieldnames:
        if lowered in col.lower():
            return col
    raise KeyError(f"Could not find column containing '{keyword}'")


def aggregate_election(path: str, year: int) -> List[Dict[str, object]]:
    totals: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing header in {path}")

        c_prov = find_column(reader.fieldnames, "province")
        c_electors = find_column(reader.fieldnames, "electors")
        c_valid = find_column(reader.fieldnames, "valid ballots")
        c_rejected = find_column(reader.fieldnames, "rejected ballots")
        c_total = find_column(reader.fieldnames, "total ballots cast")

        for row in reader:
            province = normalize_province(row[c_prov])
            electors = clean_number(row[c_electors])
            valid = clean_number(row[c_valid])
            rejected = clean_number(row[c_rejected])
            total = clean_number(row[c_total])

            if None in {electors, valid, rejected, total}:
                continue

            totals[province]["electors"] += electors  # type: ignore[operator]
            totals[province]["valid_ballots"] += valid  # type: ignore[operator]
            totals[province]["rejected_ballots"] += rejected  # type: ignore[operator]
            totals[province]["total_ballots"] += total  # type: ignore[operator]

    rows: List[Dict[str, object]] = []
    for province in sorted(totals):
        electors = totals[province]["electors"]
        total = totals[province]["total_ballots"]
        valid = totals[province]["valid_ballots"]
        rejected = totals[province]["rejected_ballots"]

        turnout = (total / electors * 100.0) if electors else 0.0
        valid_rate = (valid / total * 100.0) if total else 0.0
        rejected_rate = (rejected / total * 100.0) if total else 0.0

        rows.append(
            {
                "province": province,
                "year": year,
                "electors": int(round(electors)),
                "total_ballots": int(round(total)),
                "valid_ballots": int(round(valid)),
                "rejected_ballots": int(round(rejected)),
                "turnout": round(turnout, 4),
                "valid_rate": round(valid_rate, 4),
                "rejected_rate": round(rejected_rate, 4),
            }
        )
    return rows


def month_key_to_index(yyyymm: str) -> int:
    year = int(yyyymm[:4])
    month = int(yyyymm[5:7])
    return year * 12 + (month - 1)


def index_to_month_key(index: int) -> str:
    year = index // 12
    month = (index % 12) + 1
    return f"{year:04d}-{month:02d}"


def load_vacancy_series(path: str) -> Dict[Tuple[str, str], Dict[str, float]]:
    out: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(dict)

    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing header in {path}")

        c_ref = find_column(reader.fieldnames, "ref_date")
        c_geo = find_column(reader.fieldnames, "geo")
        c_naics = find_column(reader.fieldnames, "north american industry")
        c_stat = find_column(reader.fieldnames, "statistics")
        c_value = find_column(reader.fieldnames, "value")

        for row in reader:
            if row[c_stat].strip().lower() != "job vacancy rate":
                continue

            geo = row[c_geo].strip()
            if geo == "Canada":
                continue

            ref_date = row[c_ref].strip()
            if len(ref_date) != 7 or ref_date[4] != "-":
                continue

            value = clean_number(row[c_value])
            if value is None:
                continue

            sector = row[c_naics].strip()
            out[(geo, sector)][ref_date] = float(value)

    return out


def average_window(series: Dict[str, float], election_year: int, quarters_before: int) -> Tuple[Optional[float], int]:
    election_month = ELECTION_MONTH[election_year]
    end_idx = month_key_to_index(f"{election_year:04d}-{election_month:02d}") - 1
    start_idx = end_idx - (quarters_before * 3) + 1

    values: List[float] = []
    for idx in range(start_idx, end_idx + 1):
        key = index_to_month_key(idx)
        if key in series:
            values.append(series[key])

    if not values:
        return None, 0
    return sum(values) / len(values), len(values)


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    outdir = Path(args.outdir)

    election_rows = aggregate_election(args.election2019, 2019) + aggregate_election(args.election2021, 2021)

    election_lookup = {(r["province"], r["year"]): r for r in election_rows}
    vacancy_series = load_vacancy_series(args.vacancy)

    vacancy_rows: List[Dict[str, object]] = []
    matrix_rows: List[Dict[str, object]] = []

    provinces = sorted({k[0] for k in election_lookup.keys()})
    sectors = sorted({sector for (_geo, sector) in vacancy_series.keys()})

    for year in (2019, 2021):
        for province in provinces:
            election = election_lookup.get((province, year))
            if not election:
                continue

            for sector in sectors:
                series = vacancy_series.get((province, sector))
                if not series:
                    continue

                for quarters_before in WINDOW_QUARTERS:
                    avg, months_used = average_window(series, year, quarters_before)
                    if avg is None:
                        continue

                    vacancy_row = {
                        "province": province,
                        "year": year,
                        "sector": sector,
                        "quarters_before": quarters_before,
                        "vacancy_avg": round(avg, 4),
                        "months_used": months_used,
                    }
                    vacancy_rows.append(vacancy_row)

                    matrix_rows.append(
                        {
                            **vacancy_row,
                            "electors": election["electors"],
                            "total_ballots": election["total_ballots"],
                            "valid_ballots": election["valid_ballots"],
                            "rejected_ballots": election["rejected_ballots"],
                            "turnout": election["turnout"],
                            "valid_rate": election["valid_rate"],
                            "rejected_rate": election["rejected_rate"],
                        }
                    )

    election_file = outdir / "q3_election_summary.csv"
    vacancy_file = outdir / "q3_vacancy_windows.csv"
    matrix_file = outdir / "q3_analysis_matrix.csv"

    write_csv(
        election_file,
        election_rows,
        [
            "province",
            "year",
            "electors",
            "total_ballots",
            "valid_ballots",
            "rejected_ballots",
            "turnout",
            "valid_rate",
            "rejected_rate",
        ],
    )
    write_csv(
        vacancy_file,
        vacancy_rows,
        ["province", "year", "sector", "quarters_before", "vacancy_avg", "months_used"],
    )
    write_csv(
        matrix_file,
        matrix_rows,
        [
            "province",
            "year",
            "sector",
            "quarters_before",
            "vacancy_avg",
            "months_used",
            "electors",
            "total_ballots",
            "valid_ballots",
            "rejected_ballots",
            "turnout",
            "valid_rate",
            "rejected_rate",
        ],
    )

    print(f"Wrote: {election_file}")
    print(f"Wrote: {vacancy_file}")
    print(f"Wrote: {matrix_file}")
    print(f"Rows - election: {len(election_rows)}, vacancy: {len(vacancy_rows)}, matrix: {len(matrix_rows)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
