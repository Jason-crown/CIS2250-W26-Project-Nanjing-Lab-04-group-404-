#!/usr/bin/env python3

'''
q3_build_vacancy_vs_participation.py
  Author(s): Joseph Lim (1375013), Huzaifa Memon (1373314), Jason Klutse (1381591), Hamza Paracha (1323053)

  Project: Team 404-Nanjing Term Project — Milestone II Scripts
  Date of Last Update: Mar 12, 2026

  Functional Summary
    Build a compact CSV for Q3: job vacancy rate vs participation quality.
    Reads Table 11 (both elections) and the StatsCan vacancy table.
    Prints CSV to stdout (redirect with >).

  Commandline Parameters: 3 (plus optional)
    argv[1] = Table 11 CSV for 2019 (table_tableau11_2019.csv)
    argv[2] = Table 11 CSV for 2021 (table_tableau11_2021.csv)
    argv[3] = Vacancy CSV (1410044201_databaseLoadingData.csv or 14100442.csv)
    Optional: argv[4] = quarters_windows (default: 1,2,4)
              argv[5] = statistics label (default: Job vacancy rate)

  Notes
    - This script follows the style of CIS*2250 labs:
      * robust error messages to stderr
      * CSV reading/writing using csv.reader and csv.writer
      * output can be redirected to a file using >
'''

import sys
import csv

from helpers import (
    eprint, safe_open_csv, GEO_ORDER, normalize_province,
    ELECTION_MONTH, quarter_start, quarters_window
)

DEFAULT_QWINS = [1,2,4]
DEFAULT_STAT = "Job vacancy rate"

def parse_list_int(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def read_table11_participation(path: str, year: int) -> dict:
    """Return participation[province] = (turnout, rejected_rate, valid_rate) aggregated."""
    fh = safe_open_csv(path)
    reader = csv.reader(fh)
    try:
        header = next(reader)
    except StopIteration:
        eprint(f"Error: empty file {path}")
        sys.exit(1)

    # Required columns (based on provided Table 11)
    required = [
        "Province",
        "Electors/Électeurs",
        "Total Ballots Cast/Total des bulletins déposés",
        "Valid Ballots/Bulletins valides",
        "Rejected Ballots/Bulletins rejetés",
    ]
    for col in required:
        if col not in header:
            eprint(f"Error: Table 11 missing required column '{col}'")
            sys.exit(1)

    i_prov = header.index("Province")
    i_elec = header.index("Electors/Électeurs")
    i_tot = header.index("Total Ballots Cast/Total des bulletins déposés")
    i_val = header.index("Valid Ballots/Bulletins valides")
    i_rej = header.index("Rejected Ballots/Bulletins rejetés")

    sums = {}
    for row in reader:
        if len(row) <= i_rej:
            continue
        prov = normalize_province(row[i_prov])
        try:
            electors = float(row[i_elec])
            total = float(row[i_tot])
            valid = float(row[i_val])
            rejected = float(row[i_rej])
        except ValueError:
            continue
        if prov not in sums:
            sums[prov] = [0.0,0.0,0.0,0.0]  # electors,total,valid,rejected
        sums[prov][0] += electors
        sums[prov][1] += total
        sums[prov][2] += valid
        sums[prov][3] += rejected

    fh.close()

    out = {}
    for prov,(electors,total,valid,rejected) in sums.items():
        if electors <= 0 or total <= 0:
            continue
        turnout = total/electors
        rejected_rate = rejected/total
        valid_rate = valid/total
        out[prov] = (turnout, rejected_rate, valid_rate)
    return out

def read_vacancy(vac_path: str, needed_quarters: set[str], needed_geos: set[str], stat_label: str) -> dict:
    """Return vac[(geo, naics, ref_date)] = value."""
    fh = safe_open_csv(vac_path)
    reader = csv.reader(fh)
    try:
        header = next(reader)
    except StopIteration:
        eprint(f"Error: empty file {vac_path}")
        sys.exit(1)

    required = ["REF_DATE","GEO","North American Industry Classification System (NAICS)","Statistics","VALUE"]
    for col in required:
        if col not in header:
            eprint(f"Error: vacancy file missing required column '{col}'")
            sys.exit(1)

    i_ref = header.index("REF_DATE")
    i_geo = header.index("GEO")
    i_naics = header.index("North American Industry Classification System (NAICS)")
    i_stat = header.index("Statistics")
    i_val = header.index("VALUE")

    vac = {}
    for row in reader:
        if len(row) <= i_val:
            continue
        ref = row[i_ref].strip()
        geo = row[i_geo].strip()
        if geo not in needed_geos:
            continue
        if ref not in needed_quarters:
            continue
        if row[i_stat].strip() != stat_label:
            continue
        naics = row[i_naics].strip()
        try:
            v = float(row[i_val])
        except ValueError:
            continue
        vac[(geo, naics, ref)] = v
    fh.close()
    return vac

def main(argv):
    if len(argv) < 4:
        eprint("Usage: q3_build_vacancy_vs_participation.py <table11_2019.csv> <table11_2021.csv> <vacancy.csv> [quarters_windows] [stat_label]")
        sys.exit(1)

    t11_2019 = argv[1]
    t11_2021 = argv[2]
    vac_path = argv[3]

    qwins = DEFAULT_QWINS
    stat_label = DEFAULT_STAT
    if len(argv) >= 5:
        qwins = parse_list_int(argv[4])
    if len(argv) >= 6:
        stat_label = argv[5]

    p19 = read_table11_participation(t11_2019, 2019)
    p21 = read_table11_participation(t11_2021, 2021)

    provinces = set(p19.keys()) | set(p21.keys())
    prov_order = [p for p in GEO_ORDER if p in provinces] + sorted([p for p in provinces if p not in GEO_ORDER])

    # quarters needed for both years and all windows
    needed_quarters = set()
    for year in (2019, 2021):
        end_q = quarter_start(ELECTION_MONTH[year])
        for qwin in qwins:
            for q in quarters_window(end_q, qwin):
                needed_quarters.add(q)

    vac = read_vacancy(vac_path, needed_quarters, provinces, stat_label)

    # discover NAICS labels present
    naics_set = set([k[1] for k in vac.keys()])
    naics_list = sorted(naics_set)

    writer = csv.writer(sys.stdout)
    writer.writerow(["province","year","naics","quarters_before","vacancy_rate_avg","turnout","rejected_rate","valid_rate"])

    for year in (2019, 2021):
        part = p19 if year == 2019 else p21
        end_q = quarter_start(ELECTION_MONTH[year])
        for naics in naics_list:
            for qwin in qwins:
                qs = quarters_window(end_q, qwin)
                for prov in prov_order:
                    if prov not in part:
                        continue
                    vals = []
                    for ref in qs:
                        v = vac.get((prov, naics, ref))
                        if v is not None:
                            vals.append(v)
                    if not vals:
                        continue
                    avg_v = sum(vals)/len(vals)
                    turnout, rej, valr = part[prov]
                    writer.writerow([prov, year, naics, qwin, f"{avg_v:.6f}", f"{turnout:.6f}", f"{rej:.6f}", f"{valr:.6f}"])

if __name__ == "__main__":
    main(sys.argv)
