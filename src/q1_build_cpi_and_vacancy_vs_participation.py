#!/usr/bin/env python3

'''
q1_build_cpi_and_vacancy_vs_participation.py
  Author(s): Joseph Lim (1375013), Huzaifa Memon (1373314), Jason Klutse (1381591), Hamza Paracha (1323053)

  Project: Team 404-Nanjing Term Project — Milestone II Scripts
  Date of Last Update: Mar 12, 2026

  Functional Summary
    Build a compact CSV for Q1: CPI (YoY%) and vacancy rate vs participation quality.
    This combines CPI + vacancy + Table 11 into one output.
    Prints CSV to stdout (redirect with >).

  Commandline Parameters: 4 (plus optional)
    argv[1] = Table 11 CSV for 2019
    argv[2] = Table 11 CSV for 2021
    argv[3] = CPI CSV
    argv[4] = Vacancy CSV
    Optional: argv[5] = months_windows (default: 3,6,12,24)
              argv[6] = quarters_windows (default: 1,2,4)
              argv[7] = CPI categories (default: All-items,Food)
              argv[8] = statistics label (default: Job vacancy rate)
              argv[9] = NAICS sector (default: Total, all industries)

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
    ELECTION_MONTH, months_window, quarters_window, quarter_start, ym_to_int
)

DEFAULT_MONTHS = [3,6,12,24]
DEFAULT_QWINS = [1,2,4]
DEFAULT_CATS = ["All-items", "Food"]
DEFAULT_STAT = "Job vacancy rate"
DEFAULT_NAICS = "Total, all industries"

def parse_list(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]

def parse_list_int(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def read_table11_participation(path: str, year: int) -> dict:
    fh = safe_open_csv(path)
    reader = csv.reader(fh)
    try:
        header = next(reader)
    except StopIteration:
        eprint(f"Error: empty file {path}")
        sys.exit(1)

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
            electors = float(row[i_elec]); total = float(row[i_tot])
            valid = float(row[i_val]); rejected = float(row[i_rej])
        except ValueError:
            continue
        if prov not in sums:
            sums[prov] = [0.0,0.0,0.0,0.0]
        sums[prov][0] += electors
        sums[prov][1] += total
        sums[prov][2] += valid
        sums[prov][3] += rejected
    fh.close()

    out = {}
    for prov,(electors,total,valid,rejected) in sums.items():
        if electors <= 0 or total <= 0:
            continue
        out[prov] = {
            "turnout": total/electors,
            "rejected_rate": rejected/total,
            "valid_rate": valid/total,
        }
    return out

def read_cpi_index(cpi_path: str, categories: list[str], needed_months: set[str], needed_geos: set[str]) -> dict:
    fh = safe_open_csv(cpi_path)
    reader = csv.reader(fh)
    try:
        header = next(reader)
    except StopIteration:
        eprint(f"Error: empty CPI file {cpi_path}")
        sys.exit(1)

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
        ref = row[i_ref].strip(); geo = row[i_geo].strip(); cat = row[i_cat].strip()
        if cat not in cats or geo not in needed_geos or ref not in needed_months:
            continue
        try:
            val = float(row[i_val])
        except ValueError:
            continue
        idx[(geo, cat, ref)] = val
    fh.close()
    return idx

def compute_yoy(index: dict, geo: str, cat: str, ref: str) -> float | None:
    cur = index.get((geo, cat, ref))
    if cur is None:
        return None
    ref_i = ym_to_int(ref)
    lag_i = ref_i - 12
    lag_ref = f"{lag_i//12:04d}-{(lag_i%12)+1:02d}"
    lag = index.get((geo, cat, lag_ref))
    if lag is None or lag == 0:
        return None
    return (cur/lag - 1.0) * 100.0

def read_vacancy(vac_path: str, needed_quarters: set[str], needed_geos: set[str], stat_label: str, naics_filter: str) -> dict:
    fh = safe_open_csv(vac_path)
    reader = csv.reader(fh)
    try:
        header = next(reader)
    except StopIteration:
        eprint(f"Error: empty vacancy file {vac_path}")
        sys.exit(1)

    required = ["REF_DATE","GEO","North American Industry Classification System (NAICS)","Statistics","VALUE"]
    for col in required:
        if col not in header:
            eprint(f"Error: vacancy file missing required column '{col}'")
            sys.exit(1)

    i_ref = header.index("REF_DATE"); i_geo = header.index("GEO")
    i_naics = header.index("North American Industry Classification System (NAICS)")
    i_stat = header.index("Statistics"); i_val = header.index("VALUE")

    vac = {}
    for row in reader:
        if len(row) <= i_val:
            continue
        ref = row[i_ref].strip(); geo = row[i_geo].strip()
        if geo not in needed_geos or ref not in needed_quarters:
            continue
        if row[i_stat].strip() != stat_label:
            continue
        naics = row[i_naics].strip()
        if naics != naics_filter:
            continue
        try:
            v = float(row[i_val])
        except ValueError:
            continue
        vac[(geo, ref)] = v
    fh.close()
    return vac

def main(argv):
    if len(argv) < 5:
        eprint("Usage: q1_build_cpi_and_vacancy_vs_participation.py <table11_2019.csv> <table11_2021.csv> <cpi.csv> <vacancy.csv> [months_windows] [quarters_windows] [cpi_categories] [stat_label] [naics]")
        sys.exit(1)

    t11_2019 = argv[1]; t11_2021 = argv[2]; cpi_path = argv[3]; vac_path = argv[4]
    months_windows = DEFAULT_MONTHS
    qwins = DEFAULT_QWINS
    cats = DEFAULT_CATS
    stat_label = DEFAULT_STAT
    naics = DEFAULT_NAICS

    if len(argv) >= 6: months_windows = parse_list_int(argv[5])
    if len(argv) >= 7: qwins = parse_list_int(argv[6])
    if len(argv) >= 8: cats = parse_list(argv[7])
    if len(argv) >= 9: stat_label = argv[8]
    if len(argv) >= 10: naics = argv[9]

    p19 = read_table11_participation(t11_2019, 2019)
    p21 = read_table11_participation(t11_2021, 2021)
    provinces = set(p19.keys()) | set(p21.keys())
    prov_order = [p for p in GEO_ORDER if p in provinces] + sorted([p for p in provinces if p not in GEO_ORDER])

    # CPI months needed (windows + lag)
    needed_months = set()
    for year in (2019, 2021):
        end = ELECTION_MONTH[year]
        for mwin in months_windows:
            for m in months_window(end, mwin):
                needed_months.add(m)
                lag_i = ym_to_int(m)-12
                needed_months.add(f"{lag_i//12:04d}-{(lag_i%12)+1:02d}")

    cpi_index = read_cpi_index(cpi_path, cats, needed_months, provinces)

    # Vacancy quarters needed
    needed_quarters = set()
    for year in (2019, 2021):
        endq = quarter_start(ELECTION_MONTH[year])
        for qwin in qwins:
            for q in quarters_window(endq, qwin):
                needed_quarters.add(q)

    vac = read_vacancy(vac_path, needed_quarters, provinces, stat_label, naics)

    writer = csv.writer(sys.stdout)
    writer.writerow([
        "province","year",
        "months_before","cpi_category","cpi_yoy_avg",
        "quarters_before","naics","vacancy_rate_avg",
        "turnout","rejected_rate","valid_rate"
    ])

    for year in (2019, 2021):
        part = p19 if year == 2019 else p21
        endm = ELECTION_MONTH[year]
        endq = quarter_start(ELECTION_MONTH[year])
        for prov in prov_order:
            if prov not in part:
                continue
            for mwin in months_windows:
                for cat in cats:
                    months = months_window(endm, mwin)
                    vals = []
                    for ref in months:
                        yoy = compute_yoy(cpi_index, prov, cat, ref)
                        if yoy is not None:
                            vals.append(yoy)
                    if not vals:
                        continue
                    cpi_avg = sum(vals)/len(vals)

                    for qwin in qwins:
                        qs = quarters_window(endq, qwin)
                        vvals = []
                        for q in qs:
                            v = vac.get((prov, q))
                            if v is not None:
                                vvals.append(v)
                        if not vvals:
                            continue
                        vac_avg = sum(vvals)/len(vvals)

                        writer.writerow([
                            prov, year,
                            mwin, cat, f"{cpi_avg:.6f}",
                            qwin, naics, f"{vac_avg:.6f}",
                            f"{part[prov]['turnout']:.6f}", f"{part[prov]['rejected_rate']:.6f}", f"{part[prov]['valid_rate']:.6f}"
                        ])

if __name__ == "__main__":
    main(sys.argv)
