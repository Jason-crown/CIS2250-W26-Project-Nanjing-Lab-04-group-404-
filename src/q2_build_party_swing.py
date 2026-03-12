#!/usr/bin/env python3

'''
q2_build_party_swing.py
  Author(s): Joseph Lim (1375013), Huzaifa Memon (1373314), Jason Klutse (1381591), Hamza Paracha (1323053)

  Project: Team 404-Nanjing Term Project — Milestone II Scripts
  Date of Last Update: Mar 12, 2026

  Functional Summary
    Build a compact CSV of party vote-share swing (2019->2021) vs CPI change.
    Reads Table 8 for both elections and CPI index table.
    Prints CSV to stdout (so you can redirect with >).

  Commandline Parameters: 3 (plus optional)
    argv[1] = Table 8 CSV for 2019 (table_tableau08_2019.csv)
    argv[2] = Table 8 CSV for 2021 (table_tableau08_2021.csv)
    argv[3] = CPI CSV (1810000411_databaseLoadingData.csv or 18100004.csv)
    Optional: argv[4] = months_windows (default: 3,6,12,24)
              argv[5] = CPI categories (default: All-items,Food)

  Notes
    - This script follows the style of CIS*2250 labs:
      * robust error messages to stderr
      * CSV reading/writing using csv.reader and csv.writer
      * output can be redirected to a file using >
'''

import sys
import csv

from helpers import (
    eprint, safe_open_csv, GEO_ORDER, TABLE8_PREFIX_TO_GEO,
    ELECTION_MONTH, months_window, ym_to_int, quarter_start
)

DEFAULT_MONTHS = [3,6,12,24]
DEFAULT_CATS = ["All-items", "Food"]

def parse_list(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]

def parse_list_int(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def read_table8_votes(table8_path: str, year: int) -> dict:
    """Return votes[(province, party)] = votes."""
    fh = safe_open_csv(table8_path)
    reader = csv.reader(fh)
    try:
        header = next(reader)
    except StopIteration:
        eprint(f"Error: empty file {table8_path}")
        sys.exit(1)

    # Find party column index
    party_col = "Political affiliation/Appartenance politique"
    if party_col not in header:
        eprint(f"Error: expected column '{party_col}' in {table8_path}")
        sys.exit(1)
    party_idx = header.index(party_col)

    # Identify province columns
    prov_cols = []  # list of (idx, province)
    for i, col in enumerate(header):
        if i == party_idx:
            continue
        prefix = col.split(" ",1)[0].strip()
        if prefix in TABLE8_PREFIX_TO_GEO:
            prov_cols.append((i, TABLE8_PREFIX_TO_GEO[prefix]))

    if not prov_cols:
        eprint("Error: could not find any province vote columns in Table 8 header.")
        sys.exit(1)

    votes = {}
    for row in reader:
        if not row:
            continue
        party = row[party_idx].strip()
        if party == "":
            continue
        for i, prov in prov_cols:
            if i >= len(row):
                continue
            try:
                v = float(row[i]) if row[i].strip() != "" else 0.0
            except ValueError:
                v = 0.0
            votes[(prov, party)] = votes.get((prov, party), 0.0) + v

    fh.close()
    return votes

def read_cpi_index(cpi_path: str, categories: list[str], needed_months: set[str], needed_geos: set[str]) -> dict:
    """Return index[(geo, category, ref_date)] = value."""
    fh = safe_open_csv(cpi_path)
    reader = csv.reader(fh)
    try:
        header = next(reader)
    except StopIteration:
        eprint(f"Error: empty CPI file {cpi_path}")
        sys.exit(1)

    # Required columns
    required = ["REF_DATE","GEO","Products and product groups","VALUE"]
    for col in required:
        if col not in header:
            eprint(f"Error: CPI file missing required column '{col}'")
            sys.exit(1)

    i_ref = header.index("REF_DATE")
    i_geo = header.index("GEO")
    i_cat = header.index("Products and product groups")
    i_val = header.index("VALUE")

    cats = set(categories)
    idx = {}

    for row in reader:
        if len(row) <= i_val:
            continue
        ref = row[i_ref].strip()
        geo = row[i_geo].strip()
        cat = row[i_cat].strip()
        if cat not in cats:
            continue
        if geo not in needed_geos:
            continue
        if ref not in needed_months:
            continue
        try:
            val = float(row[i_val])
        except ValueError:
            continue
        idx[(geo, cat, ref)] = val

    fh.close()
    return idx

def compute_yoy(index: dict, geo: str, cat: str, ref: str) -> float | None:
    """YoY% from CPI index: (idx/ref - idx/ref-12) - 1 * 100."""
    cur = index.get((geo, cat, ref))
    if cur is None:
        return None
    ref_i = ym_to_int(ref)
    lag_ref = None
    lag_i = ref_i - 12
    lag_ref = f"{lag_i//12:04d}-{(lag_i%12)+1:02d}"
    lag = index.get((geo, cat, lag_ref))
    if lag is None or lag == 0:
        return None
    return (cur/lag - 1.0) * 100.0

def main(argv):
    if len(argv) < 4:
        eprint("Usage: q2_build_party_swing.py <table8_2019.csv> <table8_2021.csv> <cpi.csv> [months_windows] [cpi_categories]")
        sys.exit(1)

    t8_2019 = argv[1]
    t8_2021 = argv[2]
    cpi_path = argv[3]
    months_windows = DEFAULT_MONTHS
    categories = DEFAULT_CATS

    if len(argv) >= 5:
        months_windows = parse_list_int(argv[4])
    if len(argv) >= 6:
        categories = parse_list(argv[5])

    # Votes by party & province
    v19 = read_table8_votes(t8_2019, 2019)
    v21 = read_table8_votes(t8_2021, 2021)

    provinces = set([k[0] for k in v19.keys()] + [k[0] for k in v21.keys()])
    parties = set([k[1] for k in v19.keys()] + [k[1] for k in v21.keys()])

    # Totals for vote share denominators
    tot19 = {}
    tot21 = {}
    for (prov, party), votes in v19.items():
        tot19[prov] = tot19.get(prov, 0.0) + votes
    for (prov, party), votes in v21.items():
        tot21[prov] = tot21.get(prov, 0.0) + votes

    # Determine CPI months needed: election month windows + 12-month lag
    needed_months = set()
    for year in (2019, 2021):
        end = ELECTION_MONTH[year]
        for mwin in months_windows:
            for m in months_window(end, mwin):
                needed_months.add(m)
                # also need lag month for YoY
                needed_months.add(f"{(ym_to_int(m)-12)//12:04d}-{((ym_to_int(m)-12)%12)+1:02d}")

    # Load CPI indices only for needed months and provinces
    cpi_index = read_cpi_index(cpi_path, categories, needed_months, provinces)

    # Precompute window averages per province/year/cat/mwin
    cpi_avg = {}
    for prov in provinces:
        for cat in categories:
            for mwin in months_windows:
                for year in (2019, 2021):
                    end = ELECTION_MONTH[year]
                    months = months_window(end, mwin)
                    vals = []
                    for ref in months:
                        yoy = compute_yoy(cpi_index, prov, cat, ref)
                        if yoy is not None:
                            vals.append(yoy)
                    if vals:
                        cpi_avg[(prov, year, cat, mwin)] = sum(vals)/len(vals)

    # Output CSV to stdout
    writer = csv.writer(sys.stdout)
    writer.writerow([
        "province","party","months_before","cpi_category",
        "vote_share_2019","vote_share_2021","delta_vote_share","cpi_change"
    ])

    # stable province ordering
    prov_order = [p for p in GEO_ORDER if p in provinces] + sorted([p for p in provinces if p not in GEO_ORDER])
    for party in sorted(parties):
        for prov in prov_order:
            vs19 = (v19.get((prov, party), 0.0) / tot19.get(prov, 1.0)) if tot19.get(prov, 0.0) > 0 else 0.0
            vs21 = (v21.get((prov, party), 0.0) / tot21.get(prov, 1.0)) if tot21.get(prov, 0.0) > 0 else 0.0
            d_vs = vs21 - vs19
            for mwin in months_windows:
                for cat in categories:
                    a19 = cpi_avg.get((prov, 2019, cat, mwin))
                    a21 = cpi_avg.get((prov, 2021, cat, mwin))
                    if a19 is None or a21 is None:
                        continue
                    cpi_change = a21 - a19
                    writer.writerow([prov, party, mwin, cat, f"{vs19:.10f}", f"{vs21:.10f}", f"{d_vs:.10f}", f"{cpi_change:.6f}"])

if __name__ == "__main__":
    main(sys.argv)
