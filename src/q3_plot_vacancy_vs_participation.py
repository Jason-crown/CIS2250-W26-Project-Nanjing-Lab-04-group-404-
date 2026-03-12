#!/usr/bin/env python3

'''
q3_plot_vacancy_vs_participation.py
  Author(s): Joseph Lim (1375013), Huzaifa Memon (1373314), Jason Klutse (1381591), Hamza Paracha (1323053)

  Project: Team 404-Nanjing Term Project — Milestone II Scripts
  Date of Last Update: Mar 12, 2026

  Functional Summary
    Create a scatter plot for Q3 using the compact CSV produced by q3_build_vacancy_vs_participation.py.
    Saves a plot to a graphics file (PDF/PNG).

  Commandline Parameters: 6
    argv[1] = input compact CSV
    argv[2] = output graphics filename
    argv[3] = year (2019 or 2021)
    argv[4] = NAICS sector label (exact)
    argv[5] = quarters_before (e.g., 4)
    argv[6] = metric (turnout | rejected_rate | valid_rate)

  Notes
    - This script follows the style of CIS*2250 labs:
      * robust error messages to stderr
      * CSV reading/writing using csv.reader and csv.writer
      * output can be redirected to a file using >
'''

import sys
import pandas as pd
from matplotlib import pyplot as plt
from helpers import eprint

def main(argv):
    if len(argv) != 7:
        eprint("Usage: q3_plot_vacancy_vs_participation.py <input.csv> <output.pdf> <year> <naics> <quarters_before> <metric>")
        sys.exit(1)

    infile = argv[1]
    outfile = argv[2]
    try:
        year = int(argv[3])
    except ValueError:
        eprint("Error: year must be an integer")
        sys.exit(1)
    naics = argv[4]
    try:
        qwin = int(argv[5])
    except ValueError:
        eprint("Error: quarters_before must be an integer")
        sys.exit(1)
    metric = argv[6]

    if metric not in ["turnout","rejected_rate","valid_rate"]:
        eprint("Error: metric must be turnout, rejected_rate, or valid_rate")
        sys.exit(1)

    try:
        df = pd.read_csv(infile)
    except IOError as err:
        eprint(f"Unable to open input file '{infile}' : {err}")
        sys.exit(1)

    d = df[(df["year"] == year) & (df["naics"] == naics) & (df["quarters_before"] == qwin)].copy()
    if d.empty:
        eprint("No rows matched. Check year, naics, and quarters_before.")
        sys.exit(1)

    plt.figure()
    plt.scatter(d["vacancy_rate_avg"], d[metric])
    plt.title(f"Q3: Vacancy rate vs {metric} ({year})")
    plt.xlabel(f"Job vacancy rate avg (last {qwin} quarters), {naics}")
    plt.ylabel(metric.replace("_"," ").title())

    for _, row in d.iterrows():
        plt.annotate(str(row["province"])[:3], (row["vacancy_rate_avg"], row[metric]))

    plt.tight_layout()
    plt.savefig(outfile)

if __name__ == "__main__":
    main(sys.argv)
