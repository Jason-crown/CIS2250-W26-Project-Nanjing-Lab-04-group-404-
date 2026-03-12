#!/usr/bin/env python3

'''
q1_plot_cpi_or_vacancy_vs_participation.py
  Author(s): Joseph Lim (1375013), Huzaifa Memon (1373314), Jason Klutse (1381591), Hamza Paracha (1323053)

  Project: Team 404-Nanjing Term Project — Milestone II Scripts
  Date of Last Update: Mar 12, 2026

  Functional Summary
    Create a scatter plot for Q1 using the compact CSV produced by q1_build_cpi_and_vacancy_vs_participation.py.
    Saves a plot to a graphics file (PDF/PNG).

  Commandline Parameters: 8
    argv[1] = input compact CSV
    argv[2] = output graphics filename
    argv[3] = year (2019 or 2021)
    argv[4] = months_before (e.g., 12)
    argv[5] = quarters_before (e.g., 4)
    argv[6] = cpi_category (e.g., All-items)
    argv[7] = xvar (cpi | vacancy)
    argv[8] = metric (turnout | rejected_rate | valid_rate)

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
    if len(argv) != 9:
        eprint("Usage: q1_plot_cpi_or_vacancy_vs_participation.py <input.csv> <output.pdf> <year> <months_before> <quarters_before> <cpi_category> <xvar> <metric>")
        sys.exit(1)

    infile = argv[1]; outfile = argv[2]
    try:
        year = int(argv[3]); mwin = int(argv[4]); qwin = int(argv[5])
    except ValueError:
        eprint("Error: year/months_before/quarters_before must be integers")
        sys.exit(1)
    cat = argv[6]
    xvar = argv[7]
    metric = argv[8]

    if xvar not in ["cpi","vacancy"]:
        eprint("Error: xvar must be cpi or vacancy")
        sys.exit(1)
    if metric not in ["turnout","rejected_rate","valid_rate"]:
        eprint("Error: metric must be turnout, rejected_rate, or valid_rate")
        sys.exit(1)

    try:
        df = pd.read_csv(infile)
    except IOError as err:
        eprint(f"Unable to open input file '{infile}' : {err}")
        sys.exit(1)

    d = df[(df["year"] == year) &
           (df["months_before"] == mwin) &
           (df["quarters_before"] == qwin) &
           (df["cpi_category"] == cat)].copy()

    if d.empty:
        eprint("No rows matched. Check year, windows, and category.")
        sys.exit(1)

    x = d["cpi_yoy_avg"] if xvar == "cpi" else d["vacancy_rate_avg"]
    x_label = "CPI YoY% avg" if xvar == "cpi" else "Job vacancy rate avg"

    plt.figure()
    plt.scatter(x, d[metric])
    plt.title(f"Q1: {xvar} vs {metric} ({year})")
    plt.xlabel(x_label)
    plt.ylabel(metric.replace("_"," ").title())

    for _, row in d.iterrows():
        plt.annotate(str(row["province"])[:3], (float(row["cpi_yoy_avg"]) if xvar=="cpi" else float(row["vacancy_rate_avg"]), float(row[metric])))

    plt.tight_layout()
    plt.savefig(outfile)

if __name__ == "__main__":
    main(sys.argv)
