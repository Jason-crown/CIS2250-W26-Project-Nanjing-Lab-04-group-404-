#!/usr/bin/env python3
"""
Milestone II Question 3 demo script.

Lab-style version:
- uses sys.argv parsing
- uses csv.reader and list-based rows
- no dictionaries
- writes SVG visualizations without external dependencies
"""

import csv
import math
import os
import sys

ROW_PROVINCE = 0
ROW_YEAR = 1
ROW_SECTOR = 2
ROW_QBEFORE = 3
ROW_VACANCY = 4
ROW_TURNOUT = 5
ROW_VALID = 6
ROW_REJECTED = 7


def usage():
    print(
        "Usage:\n"
        "  q3_demo.py [options]\n\n"
        "Options:\n"
        "  --matrix <path>\n"
        "  --year <2019|2021>\n"
        "  --province <ALL|Province Name>\n"
        "  --sector <NAICS sector name>\n"
        "  --metric <turnout|rejected_rate|valid_rate>\n"
        "  --quarters-before <1|2|4>\n"
        "  --output-svg <path>\n"
    )


def clean_province(name):
    return name.split("/", 1)[0].strip()


def metric_index(metric):
    if metric == "turnout":
        return ROW_TURNOUT
    if metric == "valid_rate":
        return ROW_VALID
    return ROW_REJECTED


def find_col(header, name):
    i = 0
    while i < len(header):
        if header[i].strip().lower() == name.lower():
            return i
        i += 1
    return -1


def parse_args(argv):
    script_dir = os.path.dirname(os.path.abspath(argv[0]))
    question3_dir = os.path.dirname(script_dir)

    matrix_path = os.path.join(question3_dir, "data", "processed", "q3_analysis_matrix.csv")
    year = 2021
    province = "ALL"
    sector = "Total, all industries"
    metric = "turnout"
    quarters_before = 2
    output_svg = os.path.join(question3_dir, "output", "q3_demo.svg")

    i = 1
    while i < len(argv):
        if argv[i] == "--matrix":
            i += 1
            if i >= len(argv):
                return None
            matrix_path = argv[i]
        elif argv[i] == "--year":
            i += 1
            if i >= len(argv):
                return None
            year = int(argv[i])
        elif argv[i] == "--province":
            i += 1
            if i >= len(argv):
                return None
            province = argv[i]
        elif argv[i] == "--sector":
            i += 1
            if i >= len(argv):
                return None
            sector = argv[i]
        elif argv[i] == "--metric":
            i += 1
            if i >= len(argv):
                return None
            metric = argv[i]
        elif argv[i] == "--quarters-before":
            i += 1
            if i >= len(argv):
                return None
            quarters_before = int(argv[i])
        elif argv[i] == "--output-svg":
            i += 1
            if i >= len(argv):
                return None
            output_svg = argv[i]
        else:
            return None
        i += 1

    if year not in [2019, 2021]:
        print("Error: --year must be 2019 or 2021", file=sys.stderr)
        return None
    if metric not in ["turnout", "rejected_rate", "valid_rate"]:
        print("Error: --metric must be turnout, rejected_rate, or valid_rate", file=sys.stderr)
        return None
    if quarters_before not in [1, 2, 4]:
        print("Error: --quarters-before must be 1, 2, or 4", file=sys.stderr)
        return None

    return [matrix_path, year, province, sector, metric, quarters_before, output_svg]


def load_rows(matrix_path):
    rows = []

    try:
        f = open(matrix_path, newline="", encoding="utf-8")
    except IOError as err:
        print("Error opening matrix file:", matrix_path, err, file=sys.stderr)
        return None

    reader = csv.reader(f)

    try:
        header = next(reader)
    except StopIteration:
        print("Matrix file is empty:", matrix_path, file=sys.stderr)
        f.close()
        return None

    c_province = find_col(header, "province")
    c_year = find_col(header, "year")
    c_sector = find_col(header, "sector")
    c_qbefore = find_col(header, "quarters_before")
    c_vacancy = find_col(header, "vacancy_avg")
    c_turnout = find_col(header, "turnout")
    c_valid = find_col(header, "valid_rate")
    c_rejected = find_col(header, "rejected_rate")

    needed = [c_province, c_year, c_sector, c_qbefore, c_vacancy, c_turnout, c_valid, c_rejected]
    if -1 in needed:
        print("Matrix file is missing one or more required columns.", file=sys.stderr)
        f.close()
        return None

    for row in reader:
        if max(needed) >= len(row):
            continue

        try:
            rows.append([
                row[c_province],
                int(row[c_year]),
                row[c_sector],
                int(row[c_qbefore]),
                float(row[c_vacancy]),
                float(row[c_turnout]),
                float(row[c_valid]),
                float(row[c_rejected]),
            ])
        except ValueError:
            continue

    f.close()
    return rows


def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 2:
        return None

    i = 0
    sum_x = 0.0
    sum_y = 0.0
    while i < len(xs):
        sum_x += xs[i]
        sum_y += ys[i]
        i += 1

    mean_x = sum_x / len(xs)
    mean_y = sum_y / len(ys)

    num = 0.0
    den_x = 0.0
    den_y = 0.0

    i = 0
    while i < len(xs):
        dx = xs[i] - mean_x
        dy = ys[i] - mean_y
        num += dx * dy
        den_x += dx * dx
        den_y += dy * dy
        i += 1

    if den_x == 0.0 or den_y == 0.0:
        return None

    return num / math.sqrt(den_x * den_y)


def print_rows_table(rows, metric):
    m_index = metric_index(metric)
    print("%-30s %4s %9s %13s" % ("Province", "Year", "Vacancy", metric))
    print("-" * 62)

    i = 0
    while i < len(rows):
        print(
            "%-30s %4d %9.3f %13.3f"
            % (rows[i][ROW_PROVINCE][:30], rows[i][ROW_YEAR], rows[i][ROW_VACANCY], rows[i][m_index])
        )
        i += 1


def write_scatter_svg(rows, metric, title, output_path):
    m_index = metric_index(metric)

    width = 900
    height = 540
    left = 90
    right = 30
    top = 70
    bottom = 80

    plot_w = width - left - right
    plot_h = height - top - bottom

    # min/max
    x_min = rows[0][ROW_VACANCY]
    x_max = rows[0][ROW_VACANCY]
    y_min = rows[0][m_index]
    y_max = rows[0][m_index]

    i = 1
    while i < len(rows):
        x = rows[i][ROW_VACANCY]
        y = rows[i][m_index]
        if x < x_min:
            x_min = x
        if x > x_max:
            x_max = x
        if y < y_min:
            y_min = y
        if y > y_max:
            y_max = y
        i += 1

    if x_max == x_min:
        x_min -= 1.0
        x_max += 1.0
    if y_max == y_min:
        y_min -= 1.0
        y_max += 1.0

    def px(x):
        return left + (x - x_min) / (x_max - x_min) * plot_w

    def py(y):
        return top + plot_h - (y - y_min) / (y_max - y_min) * plot_h

    elements = []
    elements.append('<rect x="0" y="0" width="%d" height="%d" fill="white" />' % (width, height))
    elements.append('<text x="%d" y="35" text-anchor="middle" font-size="22" font-family="Arial">%s</text>' % (width // 2, title))

    x_axis_y = top + plot_h
    elements.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="black" stroke-width="2" />' % (left, x_axis_y, left + plot_w, x_axis_y))
    elements.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="black" stroke-width="2" />' % (left, top, left, x_axis_y))

    elements.append('<text x="%d" y="%d" text-anchor="middle" font-size="16" font-family="Arial">Average Job Vacancy Rate (%%)</text>' % (left + (plot_w // 2), height - 25))
    elements.append('<text x="20" y="%d" transform="rotate(-90 20 %d)" text-anchor="middle" font-size="16" font-family="Arial">%s (%%)</text>' % (top + (plot_h // 2), top + (plot_h // 2), metric))

    t = 0
    while t <= 5:
        xv = x_min + (x_max - x_min) * t / 5.0
        xp = px(xv)
        elements.append('<line x1="%.2f" y1="%d" x2="%.2f" y2="%d" stroke="black" />' % (xp, x_axis_y, xp, x_axis_y + 6))
        elements.append('<text x="%.2f" y="%d" text-anchor="middle" font-size="12" font-family="Arial">%.2f</text>' % (xp, x_axis_y + 24, xv))

        yv = y_min + (y_max - y_min) * t / 5.0
        yp = py(yv)
        elements.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="black" />' % (left - 6, yp, left, yp))
        elements.append('<text x="%d" y="%.2f" text-anchor="end" font-size="12" font-family="Arial">%.2f</text>' % (left - 12, yp + 4, yv))
        t += 1

    i = 0
    while i < len(rows):
        x = px(rows[i][ROW_VACANCY])
        y = py(rows[i][m_index])
        label = rows[i][ROW_PROVINCE]
        elements.append('<circle cx="%.2f" cy="%.2f" r="5" fill="#2b6cb0" />' % (x, y))
        elements.append('<text x="%.2f" y="%.2f" font-size="11" font-family="Arial" fill="#1a202c">%s</text>' % (x + 8, y - 6, label))
        i += 1

    outdir = os.path.dirname(output_path)
    if outdir != "" and not os.path.exists(outdir):
        os.makedirs(outdir)

    f = open(output_path, "w", encoding="utf-8")
    f.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">\n' % (width, height))
    i = 0
    while i < len(elements):
        f.write(elements[i] + "\n")
        i += 1
    f.write('</svg>\n')
    f.close()


def write_bar_svg(rows, metric, title, output_path):
    m_index = metric_index(metric)

    # ensure order by year
    if len(rows) == 2 and rows[0][ROW_YEAR] > rows[1][ROW_YEAR]:
        tmp = rows[0]
        rows[0] = rows[1]
        rows[1] = tmp

    width = 860
    height = 520
    left = 90
    right = 40
    top = 70
    bottom = 80
    plot_w = width - left - right
    plot_h = height - top - bottom

    vmax = 1.0
    i = 0
    while i < len(rows):
        if rows[i][m_index] > vmax:
            vmax = rows[i][m_index]
        i += 1
    vmax = vmax * 1.2

    elements = []
    elements.append('<rect x="0" y="0" width="%d" height="%d" fill="white" />' % (width, height))
    elements.append('<text x="%d" y="35" text-anchor="middle" font-size="22" font-family="Arial">%s</text>' % (width // 2, title))

    x_axis_y = top + plot_h
    elements.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="black" stroke-width="2" />' % (left, x_axis_y, left + plot_w, x_axis_y))
    elements.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="black" stroke-width="2" />' % (left, top, left, x_axis_y))

    elements.append('<text x="%d" y="%d" text-anchor="middle" font-size="16" font-family="Arial">Election Year</text>' % (left + (plot_w // 2), height - 25))
    elements.append('<text x="20" y="%d" transform="rotate(-90 20 %d)" text-anchor="middle" font-size="16" font-family="Arial">%s (%%)</text>' % (top + (plot_h // 2), top + (plot_h // 2), metric))

    t = 0
    while t <= 5:
        yv = vmax * t / 5.0
        yp = top + plot_h - (yv / vmax) * plot_h
        elements.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="black" />' % (left - 6, yp, left, yp))
        elements.append('<text x="%d" y="%.2f" text-anchor="end" font-size="12" font-family="Arial">%.1f</text>' % (left - 12, yp + 4, yv))
        t += 1

    if len(rows) > 0:
        slot = plot_w / float(len(rows))
        i = 0
        while i < len(rows):
            val = rows[i][m_index]
            bar_h = (val / vmax) * plot_h
            bar_w = slot * 0.45
            x = left + (i + 0.5) * slot - (bar_w / 2.0)
            y = x_axis_y - bar_h

            elements.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#2c7a7b" />' % (x, y, bar_w, bar_h))
            elements.append('<text x="%.2f" y="%d" text-anchor="middle" font-size="12" font-family="Arial">%d</text>' % (x + (bar_w / 2.0), x_axis_y + 22, rows[i][ROW_YEAR]))
            elements.append('<text x="%.2f" y="%.2f" text-anchor="middle" font-size="12" font-family="Arial">%.2f</text>' % (x + (bar_w / 2.0), y - 8, val))
            i += 1

    outdir = os.path.dirname(output_path)
    if outdir != "" and not os.path.exists(outdir):
        os.makedirs(outdir)

    f = open(output_path, "w", encoding="utf-8")
    f.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">\n' % (width, height))
    i = 0
    while i < len(elements):
        f.write(elements[i] + "\n")
        i += 1
    f.write('</svg>\n')
    f.close()


def main(argv):
    args = parse_args(argv)
    if args is None:
        usage()
        return 1

    matrix_path = args[0]
    year = args[1]
    province = args[2]
    sector = args[3]
    metric = args[4]
    q_before = args[5]
    output_svg = args[6]

    rows = load_rows(matrix_path)
    if rows is None:
        return 1

    filtered = []
    i = 0
    while i < len(rows):
        if rows[i][ROW_SECTOR] == sector and rows[i][ROW_QBEFORE] == q_before:
            filtered.append(rows[i])
        i += 1

    if clean_province(province).upper() == "ALL":
        year_rows = []
        i = 0
        while i < len(filtered):
            if filtered[i][ROW_YEAR] == year:
                year_rows.append(filtered[i])
            i += 1

        # simple alphabetical sort by province (no lambda)
        a = 0
        while a < len(year_rows):
            b = a + 1
            while b < len(year_rows):
                if year_rows[b][ROW_PROVINCE] < year_rows[a][ROW_PROVINCE]:
                    tmp = year_rows[a]
                    year_rows[a] = year_rows[b]
                    year_rows[b] = tmp
                b += 1
            a += 1

        if len(year_rows) == 0:
            print("No rows matched your filters.")
            return 1

        print_rows_table(year_rows, metric)

        m_index = metric_index(metric)
        xs = []
        ys = []
        i = 0
        while i < len(year_rows):
            xs.append(year_rows[i][ROW_VACANCY])
            ys.append(year_rows[i][m_index])
            i += 1

        corr = pearson(xs, ys)
        if corr is None:
            print("Correlation: undefined")
        else:
            print("Correlation (vacancy_avg vs %s) = %.4f" % (metric, corr))

        title = "Q3 Scatter (%d) - Vacancy vs %s | sector=%s | quarters_before=%d" % (year, metric, sector, q_before)
        write_scatter_svg(year_rows, metric, title, output_svg)
    else:
        p_name = clean_province(province)
        prov_rows = []

        i = 0
        while i < len(filtered):
            if clean_province(filtered[i][ROW_PROVINCE]) == p_name and filtered[i][ROW_YEAR] in [2019, 2021]:
                prov_rows.append(filtered[i])
            i += 1

        if len(prov_rows) == 0:
            print("No rows matched your filters.")
            return 1

        print_rows_table(prov_rows, metric)

        title = "Q3 Province Comparison - %s (%s) | sector=%s | quarters_before=%d" % (p_name, metric, sector, q_before)
        write_bar_svg(prov_rows, metric, title, output_svg)

    print("SVG written to:", output_svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
