#!/usr/bin/env python3
"""
Milestone II Question 3 preprocessing script.

Lab-style version:
- uses csv.reader and index-based field access
- uses loops and lists for aggregation
- no dictionaries
"""

import csv
import os
import sys

WINDOW_QUARTERS = [1, 2, 4]


def usage():
    print(
        "Usage:\n"
        "  q3_preprocess.py\n"
        "  q3_preprocess.py <election2019.csv> <election2021.csv> <vacancy.csv> <outdir>"
    )


def normalize_province(name):
    return name.split("/", 1)[0].strip()


def clean_number(raw):
    text = raw.strip().replace(",", "")
    if text == "":
        return None
    if text in ["..", "x", "X", "F", "A", "B", "C", "D", "E", "M"]:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def find_column_index(header, keyword):
    key = keyword.lower()
    i = 0
    while i < len(header):
        if key in header[i].lower():
            return i
        i += 1
    return -1


def find_election_row(rows, province, year):
    i = 0
    while i < len(rows):
        if rows[i][0] == province and rows[i][1] == year:
            return i
        i += 1
    return -1


def aggregate_election(path, year):
    rows = []

    try:
        f = open(path, newline="", encoding="utf-8-sig")
    except IOError as err:
        print("Error opening election file:", path, err, file=sys.stderr)
        return None

    reader = csv.reader(f)

    try:
        header = next(reader)
    except StopIteration:
        print("Election file is empty:", path, file=sys.stderr)
        f.close()
        return None

    c_prov = find_column_index(header, "province")
    c_electors = find_column_index(header, "electors")
    c_valid = find_column_index(header, "valid ballots")
    c_rejected = find_column_index(header, "rejected ballots")
    c_total = find_column_index(header, "total ballots cast")

    needed = [c_prov, c_electors, c_valid, c_rejected, c_total]
    if -1 in needed:
        print("Missing required election columns in", path, file=sys.stderr)
        f.close()
        return None

    for row in reader:
        if max(needed) >= len(row):
            continue

        province = normalize_province(row[c_prov])
        electors = clean_number(row[c_electors])
        valid = clean_number(row[c_valid])
        rejected = clean_number(row[c_rejected])
        total = clean_number(row[c_total])

        if electors is None or valid is None or rejected is None or total is None:
            continue

        idx = find_election_row(rows, province, year)
        if idx == -1:
            rows.append([province, year, electors, total, valid, rejected])
        else:
            rows[idx][2] += electors
            rows[idx][3] += total
            rows[idx][4] += valid
            rows[idx][5] += rejected

    f.close()

    # compute final metrics
    summary = []
    i = 0
    while i < len(rows):
        province = rows[i][0]
        year_val = rows[i][1]
        electors = rows[i][2]
        total = rows[i][3]
        valid = rows[i][4]
        rejected = rows[i][5]

        if electors == 0 or total == 0:
            turnout = 0.0
            valid_rate = 0.0
            rejected_rate = 0.0
        else:
            turnout = (total / electors) * 100.0
            valid_rate = (valid / total) * 100.0
            rejected_rate = (rejected / total) * 100.0

        summary.append([
            province,
            year_val,
            int(round(electors)),
            int(round(total)),
            int(round(valid)),
            int(round(rejected)),
            round(turnout, 4),
            round(valid_rate, 4),
            round(rejected_rate, 4),
        ])
        i += 1

    return summary


def find_in_list(values, target):
    i = 0
    while i < len(values):
        if values[i] == target:
            return i
        i += 1
    return -1


def month_to_index(ref_date):
    # ref_date like "2021-07"
    year = int(ref_date[0:4])
    month = int(ref_date[5:7])
    return year * 12 + (month - 1)


def get_election_month(year):
    if year == 2019:
        return 10
    return 9


def average_vacancy_window(vacancy_rows, province, sector, year, quarters_before):
    election_month = get_election_month(year)
    end_index = (year * 12 + (election_month - 1)) - 1
    start_index = end_index - (quarters_before * 3) + 1

    total = 0.0
    count = 0

    i = 0
    while i < len(vacancy_rows):
        # vacancy row: [province, sector, ref_date, value]
        if vacancy_rows[i][0] == province and vacancy_rows[i][1] == sector:
            ref_idx = month_to_index(vacancy_rows[i][2])
            if ref_idx >= start_index and ref_idx <= end_index:
                total += vacancy_rows[i][3]
                count += 1
        i += 1

    if count == 0:
        return None, 0
    return (total / count), count


def load_vacancy_rows(path):
    rows = []

    try:
        f = open(path, newline="", encoding="utf-8-sig")
    except IOError as err:
        print("Error opening vacancy file:", path, err, file=sys.stderr)
        return None

    reader = csv.reader(f)

    try:
        header = next(reader)
    except StopIteration:
        print("Vacancy file is empty:", path, file=sys.stderr)
        f.close()
        return None

    c_ref = find_column_index(header, "ref_date")
    c_geo = find_column_index(header, "geo")
    c_naics = find_column_index(header, "north american industry")
    c_stat = find_column_index(header, "statistics")
    c_value = find_column_index(header, "value")

    needed = [c_ref, c_geo, c_naics, c_stat, c_value]
    if -1 in needed:
        print("Missing required vacancy columns in", path, file=sys.stderr)
        f.close()
        return None

    for row in reader:
        if max(needed) >= len(row):
            continue

        stat = row[c_stat].strip().lower()
        if stat != "job vacancy rate":
            continue

        geo = row[c_geo].strip()
        if geo == "Canada":
            continue

        ref_date = row[c_ref].strip()
        if len(ref_date) != 7 or ref_date[4] != '-':
            continue

        value = clean_number(row[c_value])
        if value is None:
            continue

        sector = row[c_naics].strip()
        rows.append([geo, sector, ref_date, value])

    f.close()
    return rows


def write_csv(path, header, rows):
    outdir = os.path.dirname(path)
    if outdir != "" and not os.path.exists(outdir):
        os.makedirs(outdir)

    f = open(path, "w", newline="", encoding="utf-8")
    writer = csv.writer(f)
    writer.writerow(header)

    i = 0
    while i < len(rows):
        writer.writerow(rows[i])
        i += 1

    f.close()


def main(argv):
    script_dir = os.path.dirname(os.path.abspath(argv[0]))
    question3_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(os.path.dirname(question3_dir))

    election2019 = os.path.join(project_root, "election43", "table_tableau11.csv")
    election2021 = os.path.join(project_root, "election44", "table_tableau11.csv")
    vacancy = os.path.join(project_root, "statscan", "14100442.csv")
    outdir = os.path.join(question3_dir, "data", "processed")

    if len(argv) == 5:
        election2019 = argv[1]
        election2021 = argv[2]
        vacancy = argv[3]
        outdir = argv[4]
    elif len(argv) != 1:
        usage()
        return 1

    rows2019 = aggregate_election(election2019, 2019)
    if rows2019 is None:
        return 1

    rows2021 = aggregate_election(election2021, 2021)
    if rows2021 is None:
        return 1

    election_rows = rows2019 + rows2021

    vacancy_rows_raw = load_vacancy_rows(vacancy)
    if vacancy_rows_raw is None:
        return 1

    # collect unique provinces from election rows
    provinces = []
    i = 0
    while i < len(election_rows):
        province = election_rows[i][0]
        if find_in_list(provinces, province) == -1:
            provinces.append(province)
        i += 1

    # collect unique sectors from vacancy rows
    sectors = []
    i = 0
    while i < len(vacancy_rows_raw):
        sector = vacancy_rows_raw[i][1]
        if find_in_list(sectors, sector) == -1:
            sectors.append(sector)
        i += 1

    vacancy_rows = []
    matrix_rows = []

    # build vacancy and matrix rows
    year_values = [2019, 2021]
    y = 0
    while y < len(year_values):
        year = year_values[y]

        p = 0
        while p < len(provinces):
            province = provinces[p]

            # find election summary row for province/year
            election_idx = find_election_row(election_rows, province, year)
            if election_idx == -1:
                p += 1
                continue

            s = 0
            while s < len(sectors):
                sector = sectors[s]

                w = 0
                while w < len(WINDOW_QUARTERS):
                    q_before = WINDOW_QUARTERS[w]
                    avg, count = average_vacancy_window(vacancy_rows_raw, province, sector, year, q_before)

                    if avg is not None:
                        vacancy_row = [
                            province,
                            year,
                            sector,
                            q_before,
                            round(avg, 4),
                            count,
                        ]
                        vacancy_rows.append(vacancy_row)

                        er = election_rows[election_idx]
                        # er format: [province,year,electors,total,valid,rejected,turnout,valid_rate,rejected_rate]
                        matrix_rows.append([
                            province,
                            year,
                            sector,
                            q_before,
                            round(avg, 4),
                            count,
                            er[2],
                            er[3],
                            er[4],
                            er[5],
                            er[6],
                            er[7],
                            er[8],
                        ])

                    w += 1
                s += 1
            p += 1
        y += 1

    election_path = os.path.join(outdir, "q3_election_summary.csv")
    vacancy_path = os.path.join(outdir, "q3_vacancy_windows.csv")
    matrix_path = os.path.join(outdir, "q3_analysis_matrix.csv")

    write_csv(
        election_path,
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
        election_rows,
    )

    write_csv(
        vacancy_path,
        ["province", "year", "sector", "quarters_before", "vacancy_avg", "months_used"],
        vacancy_rows,
    )

    write_csv(
        matrix_path,
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
        matrix_rows,
    )

    print("Wrote:", election_path)
    print("Wrote:", vacancy_path)
    print("Wrote:", matrix_path)
    print("Rows - election:", len(election_rows), "vacancy:", len(vacancy_rows), "matrix:", len(matrix_rows))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
