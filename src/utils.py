#!/usr/bin/env python3
"""
Utility functions for Team 404-Nanjing CIS*2250 project.

Design goals:
- Be robust to bilingual province labels in election tables.
- Keep processing small by filtering CPI/vacancy tables to only needed time ranges.
- Avoid heavyweight dependencies; pandas + matplotlib only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

import pandas as pd


# -----------------------------
# Province normalization
# -----------------------------
_PROV_NORMALIZE: Dict[str, str] = {
    # Election Table 11 bilingual forms
    "Newfoundland and Labrador/Terre-Neuve-et-Labrador": "Newfoundland and Labrador",
    "Prince Edward Island/Île-du-Prince-Édouard": "Prince Edward Island",
    "Nova Scotia/Nouvelle-Écosse": "Nova Scotia",
    "New Brunswick/Nouveau-Brunswick": "New Brunswick",
    "Quebec/Québec": "Quebec",
    "British Columbia/Colombie-Britannique": "British Columbia",
    "Northwest Territories/Territoires du Nord-Ouest": "Northwest Territories",
    # Already clean
    "Ontario": "Ontario",
    "Manitoba": "Manitoba",
    "Saskatchewan": "Saskatchewan",
    "Alberta": "Alberta",
    "Yukon": "Yukon",
    "Nunavut": "Nunavut",
    "Newfoundland and Labrador": "Newfoundland and Labrador",
    "Prince Edward Island": "Prince Edward Island",
    "Nova Scotia": "Nova Scotia",
    "New Brunswick": "New Brunswick",
    "Quebec": "Quebec",
    "British Columbia": "British Columbia",
    "Northwest Territories": "Northwest Territories",
}

# Table 8 province/territory column prefixes -> GEO names
_TABLE8_COL_TO_GEO: Dict[str, str] = {
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

GEO_ORDER: List[str] = [
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


def normalize_province(label: str) -> str:
    """Normalize province strings (bilingual -> English canonical)."""
    if label in _PROV_NORMALIZE:
        return _PROV_NORMALIZE[label]
    # Try to split bilingual "X/Y"
    if "/" in label:
        left = label.split("/", 1)[0].strip()
        return _PROV_NORMALIZE.get(left, left)
    return label.strip()


def table8_column_to_geo(col_name: str) -> str | None:
    """Map a Table 8 column name to canonical GEO, or None if not a province/territory column."""
    # Example: "Ont. Valid Votes/Votes valides Ont."
    prefix = col_name.split(" ", 1)[0].strip()
    return _TABLE8_COL_TO_GEO.get(prefix)


# -----------------------------
# Dates / windows
# -----------------------------
ELECTION_DATES = {
    2019: "2019-10-21",
    2021: "2021-09-20",
}

def _ym_to_dt(ym: str) -> pd.Timestamp:
    # ym like "2021-09"
    return pd.to_datetime(f"{ym}-01", errors="coerce")


def add_months(ts: pd.Timestamp, months: int) -> pd.Timestamp:
    # pandas offsets handle month rollovers
    return (ts + pd.offsets.DateOffset(months=months)).normalize()


def month_floor(ts: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(year=ts.year, month=ts.month, day=1)


def quarter_floor(ts: pd.Timestamp) -> pd.Timestamp:
    # quarters in vacancy table are represented by months 01/04/07/10
    m = ts.month
    q_start_month = ((m - 1) // 3) * 3 + 1
    return pd.Timestamp(year=ts.year, month=q_start_month, day=1)


def months_in_window(end_month: pd.Timestamp, months_before: int) -> List[str]:
    """
    Return list of REF_DATE strings (YYYY-MM) included in a window ending at end_month (inclusive).
    months_before=3 includes end_month and previous 2 months.
    """
    end_month = month_floor(end_month)
    start_month = add_months(end_month, -(months_before - 1))
    out = []
    cur = start_month
    while cur <= end_month:
        out.append(cur.strftime("%Y-%m"))
        cur = add_months(cur, 1)
    return out


def quarters_in_window(end_quarter: pd.Timestamp, quarters_before: int) -> List[str]:
    """
    Return list of REF_DATE strings (YYYY-MM) for quarter-start months included in window ending
    at end_quarter (inclusive). quarters_before=4 includes end_quarter and previous 3 quarters.
    """
    end_quarter = quarter_floor(end_quarter)
    start_quarter = add_months(end_quarter, -3 * (quarters_before - 1))
    out = []
    cur = start_quarter
    while cur <= end_quarter:
        out.append(cur.strftime("%Y-%m"))
        cur = add_months(cur, 3)
    return out


# -----------------------------
# CPI processing (from 18100004.csv: CPI index)
# -----------------------------
@dataclass(frozen=True)
class CpiConfig:
    cpi_path: str
    categories: List[str]                # e.g., ["All-items","Food"]
    geos: List[str]                      # canonical GEOs
    # range of REF_DATE (inclusive) to load, in YYYY-MM
    min_ym: str
    max_ym: str


def load_cpi_index_filtered(cfg: CpiConfig) -> pd.DataFrame:
    """
    Load CPI index rows from 18100004.csv, filtered to given categories/geos/date range.

    Returns a DataFrame with columns: REF_DATE (YYYY-MM), GEO (canonical), category, index_value (float)
    """
    usecols = ["REF_DATE", "GEO", "Products and product groups", "VALUE"]
    out_rows = []
    cats = set(cfg.categories)
    geos = set(cfg.geos)
    min_dt = _ym_to_dt(cfg.min_ym)
    max_dt = _ym_to_dt(cfg.max_ym)

    for chunk in pd.read_csv(cfg.cpi_path, usecols=usecols, chunksize=500_000):
        chunk = chunk.dropna(subset=["REF_DATE", "GEO", "Products and product groups", "VALUE"])
        # quick filters
        chunk = chunk[chunk["Products and product groups"].isin(cats)]
        chunk = chunk[chunk["GEO"].isin(geos)]
        if chunk.empty:
            continue
        dt = pd.to_datetime(chunk["REF_DATE"].astype(str) + "-01", errors="coerce")
        chunk = chunk.assign(_dt=dt)
        chunk = chunk[(chunk["_dt"] >= min_dt) & (chunk["_dt"] <= max_dt)]
        if chunk.empty:
            continue
        vals = pd.to_numeric(chunk["VALUE"], errors="coerce")
        chunk = chunk.assign(index_value=vals).dropna(subset=["index_value"])
        out_rows.append(chunk[["REF_DATE", "GEO", "Products and product groups", "index_value"]])

    if not out_rows:
        raise ValueError("No CPI rows matched your filters. Check file path, GEO/category names, and date range.")

    df = pd.concat(out_rows, ignore_index=True)
    df = df.rename(columns={"Products and product groups": "cpi_category"})
    return df


def compute_cpi_yoy(df_index: pd.DataFrame) -> pd.DataFrame:
    """
    Given CPI index (monthly), compute YoY percent change per GEO + category.

    Output columns:
    - REF_DATE (YYYY-MM)
    - GEO
    - cpi_category
    - cpi_yoy_pct
    """
    df = df_index.copy()
    df["dt"] = pd.to_datetime(df["REF_DATE"].astype(str) + "-01", errors="coerce")
    df = df.dropna(subset=["dt"])
    df = df.sort_values(["GEO", "cpi_category", "dt"])
    # compute YoY using 12-month lag of index_value
    df["index_lag12"] = df.groupby(["GEO", "cpi_category"])["index_value"].shift(12)
    df["cpi_yoy_pct"] = (df["index_value"] / df["index_lag12"] - 1.0) * 100.0
    df = df.dropna(subset=["cpi_yoy_pct"])
    return df[["REF_DATE", "GEO", "cpi_category", "cpi_yoy_pct"]]


def cpi_window_average(df_yoy: pd.DataFrame, year: int, months_before: int, category: str) -> pd.DataFrame:
    """
    Compute average YoY CPI over a window ending at the election month for the given year,
    per province/territory.

    Returns: GEO, cpi_yoy_avg
    """
    end_month = month_floor(pd.to_datetime(ELECTION_DATES[year]))
    keep_months = set(months_in_window(end_month, months_before))
    d = df_yoy[(df_yoy["REF_DATE"].isin(keep_months)) & (df_yoy["cpi_category"] == category)]
    out = d.groupby("GEO", as_index=False)["cpi_yoy_pct"].mean().rename(columns={"cpi_yoy_pct": "cpi_yoy_avg"})
    out["year"] = year
    out["months_before"] = months_before
    out["cpi_category"] = category
    return out


# -----------------------------
# Vacancy processing (from 14100442.csv: quarterly)
# -----------------------------
@dataclass(frozen=True)
class VacConfig:
    vac_path: str
    geos: List[str]
    stats_label: str                   # e.g., "Job vacancy rate"
    naics_list: List[str]              # list of NAICS strings to keep (or ["*"] for all)
    min_ym: str
    max_ym: str


def load_vacancy_filtered(cfg: VacConfig) -> pd.DataFrame:
    """
    Load vacancy table filtered to GEO/date range/statistic and optionally NAICS.

    Output columns:
    - REF_DATE (YYYY-MM, quarter starts)
    - GEO
    - naics
    - value
    """
    usecols = ["REF_DATE", "GEO", "North American Industry Classification System (NAICS)", "Statistics", "VALUE"]
    out_rows = []
    geos = set(cfg.geos)
    naics_keep = set(cfg.naics_list)
    min_dt = _ym_to_dt(cfg.min_ym)
    max_dt = _ym_to_dt(cfg.max_ym)

    for chunk in pd.read_csv(cfg.vac_path, usecols=usecols, chunksize=300_000):
        chunk = chunk.dropna(subset=["REF_DATE", "GEO", "Statistics", "VALUE"])
        chunk = chunk[chunk["GEO"].isin(geos)]
        chunk = chunk[chunk["Statistics"] == cfg.stats_label]
        if naics_keep != {"*"}:
            chunk = chunk[chunk["North American Industry Classification System (NAICS)"].isin(naics_keep)]
        if chunk.empty:
            continue
        dt = pd.to_datetime(chunk["REF_DATE"].astype(str) + "-01", errors="coerce")
        chunk = chunk.assign(_dt=dt)
        chunk = chunk[(chunk["_dt"] >= min_dt) & (chunk["_dt"] <= max_dt)]
        if chunk.empty:
            continue
        val = pd.to_numeric(chunk["VALUE"], errors="coerce")
        chunk = chunk.assign(value=val).dropna(subset=["value"])
        out_rows.append(chunk[["REF_DATE", "GEO", "North American Industry Classification System (NAICS)", "value"]])

    if not out_rows:
        raise ValueError("No vacancy rows matched your filters. Check file path, GEO names, and date range.")

    df = pd.concat(out_rows, ignore_index=True)
    df = df.rename(columns={"North American Industry Classification System (NAICS)": "naics"})
    return df


def vacancy_window_average(df_vac: pd.DataFrame, year: int, quarters_before: int, naics: str) -> pd.DataFrame:
    """
    Compute average job vacancy rate over last Q quarters ending at election quarter (inclusive),
    per GEO, for a given NAICS group.

    Returns: GEO, vacancy_rate_avg
    """
    end_q = quarter_floor(pd.to_datetime(ELECTION_DATES[year]))
    keep_q = set(quarters_in_window(end_q, quarters_before))
    d = df_vac[(df_vac["REF_DATE"].isin(keep_q)) & (df_vac["naics"] == naics)]
    out = d.groupby("GEO", as_index=False)["value"].mean().rename(columns={"value": "vacancy_rate_avg"})
    out["year"] = year
    out["quarters_before"] = quarters_before
    out["naics"] = naics
    return out


# -----------------------------
# Election tables
# -----------------------------
def load_table11(path: str, year: int) -> pd.DataFrame:
    """
    Load Table 11 (voter participation by riding) and aggregate to province totals.
    Returns:
      province (canonical), year, electors, total_ballots_cast, valid_ballots, rejected_ballots,
      turnout, rejected_rate, valid_rate
    """
    df = pd.read_csv(path)
    # normalize province labels
    df["province"] = df["Province"].astype(str).map(normalize_province)
    # numeric columns
    electors = pd.to_numeric(df["Electors/Électeurs"], errors="coerce")
    total = pd.to_numeric(df["Total Ballots Cast/Total des bulletins déposés"], errors="coerce")
    valid = pd.to_numeric(df["Valid Ballots/Bulletins valides"], errors="coerce")
    rejected = pd.to_numeric(df["Rejected Ballots/Bulletins rejetés"], errors="coerce")
    df = df.assign(electors=electors, total_ballots_cast=total, valid_ballots=valid, rejected_ballots=rejected)
    df = df.dropna(subset=["province", "electors", "total_ballots_cast"])
    grp = df.groupby("province", as_index=False).agg(
        electors=("electors", "sum"),
        total_ballots_cast=("total_ballots_cast", "sum"),
        valid_ballots=("valid_ballots", "sum"),
        rejected_ballots=("rejected_ballots", "sum"),
    )
    grp["year"] = year
    grp["turnout"] = grp["total_ballots_cast"] / grp["electors"]
    grp["rejected_rate"] = grp["rejected_ballots"] / grp["total_ballots_cast"]
    grp["valid_rate"] = grp["valid_ballots"] / grp["total_ballots_cast"]
    return grp


def load_table8_party_votes(path: str, year: int) -> pd.DataFrame:
    """
    Load Table 8 (valid votes by political affiliation, columns per province/territory).
    Output long format:
      province (canonical), party, votes (int/float), year
    """
    df = pd.read_csv(path)
    party_col = "Political affiliation/Appartenance politique"
    if party_col not in df.columns:
        raise ValueError(f"Expected column '{party_col}' in Table 8 file: {path}")
    df = df.rename(columns={party_col: "party"})
    records = []
    for col in df.columns:
        if col == "party":
            continue
        geo = table8_column_to_geo(col)
        if geo is None:
            continue
        vals = pd.to_numeric(df[col], errors="coerce").fillna(0)
        tmp = pd.DataFrame({"province": geo, "party": df["party"].astype(str), "votes": vals})
        records.append(tmp)
    out = pd.concat(records, ignore_index=True)
    out["year"] = year
    # clean party labels (trim)
    out["party"] = out["party"].str.strip()
    # drop empty party rows if any
    out = out[out["party"].ne("")]
    return out


def compute_vote_shares(df_votes: pd.DataFrame) -> pd.DataFrame:
    """
    Given long votes:
      province, party, votes, year
    compute vote_share per province-year-party.
    """
    df = df_votes.copy()
    totals = df.groupby(["province", "year"], as_index=False)["votes"].sum().rename(columns={"votes": "total_votes"})
    df = df.merge(totals, on=["province", "year"], how="left")
    df["vote_share"] = df["votes"] / df["total_votes"]
    return df[["province", "party", "year", "votes", "total_votes", "vote_share"]]
