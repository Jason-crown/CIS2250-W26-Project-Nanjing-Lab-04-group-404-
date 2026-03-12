#!/usr/bin/env python3

'''
q2_plot_party_swing.py
  Author(s): Joseph Lim (1375013), Huzaifa Memon (1373314), Jason Klutse (1381591), Hamza Paracha (1323053)

  Project: Team 404-Nanjing Term Project — Milestone II Scripts
  Date of Last Update: Mar 12, 2026

  Functional Summary
    Create a scatter plot for Q2 using the compact CSV produced by q2_build_party_swing.py.
    Saves a plot to a graphics file (PDF/PNG).

  Commandline Parameters: 5
    argv[1] = input compact CSV (from q2_build_party_swing.py)
    argv[2] = output graphics filename (e.g., q2.pdf)
    argv[3] = party name (exact label from Table 8)
    argv[4] = months_before (e.g., 12)
    argv[5] = cpi_category (e.g., All-items)

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
    if len(argv) != 6:
        eprint("Usage: q2_plot_party_swing.py <input.csv> <output.pdf> <party> <months_before> <cpi_category>")
        sys.exit(1)

    infile = argv[1]
    outfile = argv[2]
    party = argv[3]
    try:
        months_before = int(argv[4])
    except ValueError:
        eprint("Error: months_before must be an integer")
        sys.exit(1)
    cpi_category = argv[5]

    try:
        df = pd.read_csv(infile)
    except IOError as err:
        eprint(f"Unable to open input file '{infile}' : {err}")
        sys.exit(1)

    d = df[(df["party"] == party) &
           (df["months_before"] == months_before) &
           (df["cpi_category"] == cpi_category)].copy()

    if d.empty:
        eprint("No rows matched. Check party spelling, months_before, and cpi_category.")
        sys.exit(1)

    plt.figure()
    plt.scatter(d["cpi_change"], d["delta_vote_share"])
    plt.title(f"Q2: CPI change vs vote-share swing ({party})")
    plt.xlabel(f"CPI YoY% avg change (2021 window - 2019 window), last {months_before} months ({cpi_category})")
    plt.ylabel("Δ vote share (2021 - 2019)")

    # annotate points with province short labels
    for _, row in d.iterrows():
        plt.annotate(str(row["province"])[:3], (row["cpi_change"], row["delta_vote_share"]))

    plt.tight_layout()
    plt.savefig(outfile)
    # do not call plt.show() (lab style writes to file)

if __name__ == "__main__":
    main(sys.argv)
