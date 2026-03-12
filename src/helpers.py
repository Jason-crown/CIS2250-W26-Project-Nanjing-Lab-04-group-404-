#!/usr/bin/env python3

'''
helpers.py
  Author(s): Joseph Lim (1375013), Huzaifa Memon (1373314), Jason Klutse (1381591), Hamza Paracha (1323053)

  Project: Team 404-Nanjing Term Project — Milestone II Scripts
  Date of Last Update: Mar 12, 2026

  Functional Summary
    Helper functions shared by the build scripts (province normalization, date windows, safe file opening).

  Commandline Parameters: (imported module)
    (none)

  Notes
    - This script follows the style of CIS*2250 labs:
      * robust error messages to stderr
      * CSV reading/writing using csv.reader and csv.writer
      * output can be redirected to a file using >
'''

import sys
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Iterable

# Canonical GEO names used across scripts
GEO_ORDER = [
    "Newfoundland and Labrador",
    "Prince Edward Island",
    "Nova Scotia",
    "New Brunswick",
    "Quebec",
    "Ontario",
    "Manitoba",
    "Saskatchewan",
    "Alberta",
    "British Columbia",
    "Yukon",
    "Northwest Territories",
    "Nunavut",
]

# Election dates (used to define "months_before" / "quarters_before" windows)
ELECTION_MONTH = {
    2019: "2019-10",  # election in Oct 2019
    2021: "2021-09",  # election in Sep 2021
}

# Table 8 column prefix mapping -> GEO
TABLE8_PREFIX_TO_GEO: Dict[str, str] = {
    "N.L.": "Newfoundland and Labrador",
    "P.E.I.": "Prince Edward Island",
    "N.S.": "Nova Scotia",
    "N.B.": "New Brunswick",
    "Que.": "Quebec",
    "Ont.": "Ontario",
    "Man.": "Manitoba",
    "Sask.": "Saskatchewan",
    "Alta.": "Alberta",
    "B.C.": "British Columbia",
    "Y.T.": "Yukon",
    "N.W.T.": "Northwest Territories",
    "Nun.": "Nunavut",
}

# Normalize bilingual province labels from Table 11
PROV_NORMALIZE = {
    "Newfoundland and Labrador/Terre-Neuve-et-Labrador": "Newfoundland and Labrador",
    "Prince Edward Island/Île-du-Prince-Édouard": "Prince Edward Island",
    "Nova Scotia/Nouvelle-Écosse": "Nova Scotia",
    "New Brunswick/Nouveau-Brunswick": "New Brunswick",
    "Quebec/Québec": "Quebec",
    "British Columbia/Colombie-Britannique": "British Columbia",
    "Northwest Territories/Territoires du Nord-Ouest": "Northwest Territories",
}

def eprint(*args):
    print(*args, file=sys.stderr)

def safe_open_csv(path: str):
    """Open a CSV file with lab-style BOM handling and newline protection."""
    try:
        return open(path, newline='', encoding='utf-8-sig')
    except IOError as err:
        eprint(f"Unable to open file '{path}' : {err}")
        sys.exit(1)

def normalize_province(label: str) -> str:
    label = str(label).strip()
    if label in PROV_NORMALIZE:
        return PROV_NORMALIZE[label]
    if "/" in label:
        left = label.split("/", 1)[0].strip()
        return PROV_NORMALIZE.get(left, left)
    return label

def parse_ym(ym: str) -> Tuple[int,int]:
    # ym format "YYYY-MM"
    parts = ym.split("-")
    return int(parts[0]), int(parts[1])

def ym_to_int(ym: str) -> int:
    y,m = parse_ym(ym)
    return y*12 + (m-1)

def int_to_ym(v: int) -> str:
    y = v//12
    m = (v%12)+1
    return f"{y:04d}-{m:02d}"

def months_window(end_ym: str, months_before: int) -> List[str]:
    """Inclusive window ending at end_ym."""
    end_i = ym_to_int(end_ym)
    start_i = end_i - (months_before-1)
    return [int_to_ym(i) for i in range(start_i, end_i+1)]

def quarter_start(ym: str) -> str:
    """Convert a month YYYY-MM into quarter-start YYYY-MM (01/04/07/10)."""
    y,m = parse_ym(ym)
    q_start = ((m-1)//3)*3 + 1
    return f"{y:04d}-{q_start:02d}"

def quarters_window(end_ym: str, quarters_before: int) -> List[str]:
    """Quarter starts window (inclusive) ending at end_ym (which should already be quarter-start)."""
    end_i = ym_to_int(end_ym)
    # step = 3 months per quarter
    start_i = end_i - 3*(quarters_before-1)
    vals = []
    i = start_i
    while i <= end_i:
        vals.append(int_to_ym(i))
        i += 3
    return vals
