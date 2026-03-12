#!/usr/bin/env python3
"""Demo-time script for Milestone II Question 3.

Uses preprocessed matrix data and performs parameterized filtering + visualization.
Visualization output is an SVG file so no plotting library is required.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
QUESTION3_DIR = SCRIPT_DIR.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo script for Question 3")
    parser.add_argument(
        "--matrix",
        default=str(QUESTION3_DIR / "data" / "processed" / "q3_analysis_matrix.csv"),
        help="Path to q3_analysis_matrix.csv",
    )
    parser.add_argument("--year", type=int, choices=[2019, 2021], default=2021)
    parser.add_argument("--province", default="ALL", help="Province name or ALL")
    parser.add_argument("--sector", default="Total, all industries")
    parser.add_argument("--metric", choices=["turnout", "rejected_rate", "valid_rate"], default="turnout")
    parser.add_argument("--quarters-before", type=int, choices=[1, 2, 4], default=2, dest="quarters_before")
    parser.add_argument(
        "--output-svg",
        default=str(QUESTION3_DIR / "output" / "q3_demo.svg"),
        help="Where to save the generated SVG",
    )
    return parser.parse_args()


def clean_province(name: str) -> str:
    return name.split("/", 1)[0].strip()


def load_rows(path: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "province": row["province"],
                    "year": int(row["year"]),
                    "sector": row["sector"],
                    "quarters_before": int(row["quarters_before"]),
                    "vacancy_avg": float(row["vacancy_avg"]),
                    "turnout": float(row["turnout"]),
                    "valid_rate": float(row["valid_rate"]),
                    "rejected_rate": float(row["rejected_rate"]),
                }
            )
    return rows


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return float("nan")
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den_x = math.sqrt(sum((a - mx) ** 2 for a in x))
    den_y = math.sqrt(sum((b - my) ** 2 for b in y))
    if den_x == 0 or den_y == 0:
        return float("nan")
    return num / (den_x * den_y)


def write_scatter_svg(rows: List[Dict[str, object]], metric: str, title: str, output_path: Path) -> None:
    width, height = 900, 540
    margin_left, margin_right, margin_top, margin_bottom = 90, 30, 70, 80
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    xs = [float(r["vacancy_avg"]) for r in rows]
    ys = [float(r[metric]) for r in rows]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    if x_max == x_min:
        x_min -= 1
        x_max += 1
    if y_max == y_min:
        y_min -= 1
        y_max += 1

    def px(x: float) -> float:
        return margin_left + (x - x_min) / (x_max - x_min) * plot_w

    def py(y: float) -> float:
        return margin_top + plot_h - (y - y_min) / (y_max - y_min) * plot_h

    elements: List[str] = []
    elements.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="white" />')
    elements.append(
        f'<text x="{width/2}" y="35" text-anchor="middle" font-size="22" font-family="Arial">{title}</text>'
    )

    # axes
    x_axis_y = margin_top + plot_h
    elements.append(
        f'<line x1="{margin_left}" y1="{x_axis_y}" x2="{margin_left+plot_w}" y2="{x_axis_y}" stroke="black" stroke-width="2" />'
    )
    elements.append(
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{x_axis_y}" stroke="black" stroke-width="2" />'
    )

    # axis labels
    elements.append(
        f'<text x="{margin_left + plot_w/2}" y="{height-25}" text-anchor="middle" font-size="16" font-family="Arial">Average Job Vacancy Rate (%)</text>'
    )
    elements.append(
        f'<text x="20" y="{margin_top + plot_h/2}" transform="rotate(-90 20 {margin_top + plot_h/2})" text-anchor="middle" font-size="16" font-family="Arial">{metric} (%)</text>'
    )

    # ticks
    for i in range(6):
        xv = x_min + (x_max - x_min) * i / 5
        xpix = px(xv)
        elements.append(f'<line x1="{xpix}" y1="{x_axis_y}" x2="{xpix}" y2="{x_axis_y+6}" stroke="black" />')
        elements.append(
            f'<text x="{xpix}" y="{x_axis_y+24}" text-anchor="middle" font-size="12" font-family="Arial">{xv:.2f}</text>'
        )

        yv = y_min + (y_max - y_min) * i / 5
        ypix = py(yv)
        elements.append(f'<line x1="{margin_left-6}" y1="{ypix}" x2="{margin_left}" y2="{ypix}" stroke="black" />')
        elements.append(
            f'<text x="{margin_left-12}" y="{ypix+4}" text-anchor="end" font-size="12" font-family="Arial">{yv:.2f}</text>'
        )

    for row in rows:
        x = float(row["vacancy_avg"])
        y = float(row[metric])
        label = str(row["province"])
        xpix, ypix = px(x), py(y)
        elements.append(f'<circle cx="{xpix}" cy="{ypix}" r="5" fill="#2b6cb0" />')
        elements.append(
            f'<text x="{xpix+8}" y="{ypix-6}" font-size="11" font-family="Arial" fill="#1a202c">{label}</text>'
        )

    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            *elements,
            "</svg>",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")


def write_two_year_bar_svg(rows: List[Dict[str, object]], metric: str, title: str, output_path: Path) -> None:
    width, height = 860, 520
    margin_left, margin_right, margin_top, margin_bottom = 90, 40, 70, 80
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    rows = sorted(rows, key=lambda r: int(r["year"]))
    values = [float(r[metric]) for r in rows]
    years = [int(r["year"]) for r in rows]

    vmax = max(values) if values else 1.0
    vmax = max(vmax * 1.2, 1.0)

    elements: List[str] = []
    elements.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="white" />')
    elements.append(
        f'<text x="{width/2}" y="35" text-anchor="middle" font-size="22" font-family="Arial">{title}</text>'
    )

    x_axis_y = margin_top + plot_h
    elements.append(
        f'<line x1="{margin_left}" y1="{x_axis_y}" x2="{margin_left+plot_w}" y2="{x_axis_y}" stroke="black" stroke-width="2" />'
    )
    elements.append(
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{x_axis_y}" stroke="black" stroke-width="2" />'
    )

    elements.append(
        f'<text x="{margin_left + plot_w/2}" y="{height-25}" text-anchor="middle" font-size="16" font-family="Arial">Election Year</text>'
    )
    elements.append(
        f'<text x="20" y="{margin_top + plot_h/2}" transform="rotate(-90 20 {margin_top + plot_h/2})" text-anchor="middle" font-size="16" font-family="Arial">{metric} (%)</text>'
    )

    # y ticks
    for i in range(6):
        yv = vmax * i / 5
        ypix = margin_top + plot_h - (yv / vmax) * plot_h
        elements.append(f'<line x1="{margin_left-6}" y1="{ypix}" x2="{margin_left}" y2="{ypix}" stroke="black" />')
        elements.append(
            f'<text x="{margin_left-12}" y="{ypix+4}" text-anchor="end" font-size="12" font-family="Arial">{yv:.1f}</text>'
        )

    if rows:
        slot = plot_w / max(len(rows), 1)
        for i, row in enumerate(rows):
            val = float(row[metric])
            bar_h = (val / vmax) * plot_h
            bar_w = slot * 0.45
            x = margin_left + (i + 0.5) * slot - bar_w / 2
            y = x_axis_y - bar_h
            elements.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" fill="#2c7a7b" />')
            elements.append(
                f'<text x="{x + bar_w/2}" y="{x_axis_y+22}" text-anchor="middle" font-size="12" font-family="Arial">{years[i]}</text>'
            )
            elements.append(
                f'<text x="{x + bar_w/2}" y="{y-8}" text-anchor="middle" font-size="12" font-family="Arial">{val:.2f}</text>'
            )

    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            *elements,
            "</svg>",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")


def print_rows_table(rows: List[Dict[str, object]], metric: str) -> None:
    print(f"{'Province':30} {'Year':>4} {'Vacancy':>9} {metric:>13}")
    print("-" * 62)
    for row in rows:
        print(
            f"{str(row['province'])[:30]:30} "
            f"{int(row['year']):>4} "
            f"{float(row['vacancy_avg']):>9.3f} "
            f"{float(row[metric]):>13.3f}"
        )


def main() -> int:
    args = parse_args()
    rows = load_rows(args.matrix)

    province_param = clean_province(args.province)
    filtered = [
        r
        for r in rows
        if r["sector"] == args.sector and int(r["quarters_before"]) == args.quarters_before
    ]

    if province_param.upper() == "ALL":
        filtered = [r for r in filtered if int(r["year"]) == args.year]
        filtered.sort(key=lambda r: str(r["province"]))
        if not filtered:
            print("No rows matched your filters.")
            return 1

        print_rows_table(filtered, args.metric)
        xs = [float(r["vacancy_avg"]) for r in filtered]
        ys = [float(r[args.metric]) for r in filtered]
        corr = pearson(xs, ys)
        if math.isnan(corr):
            print("Correlation: undefined (insufficient variance)")
        else:
            print(f"Correlation (vacancy_avg vs {args.metric}) = {corr:.4f}")

        title = (
            f"Q3 Scatter ({args.year}) - Vacancy vs {args.metric} "
            f"| sector={args.sector} | quarters_before={args.quarters_before}"
        )
        write_scatter_svg(filtered, args.metric, title, Path(args.output_svg))

    else:
        filtered = [r for r in filtered if clean_province(str(r["province"])) == province_param]
        filtered = [r for r in filtered if int(r["year"]) in (2019, 2021)]
        filtered.sort(key=lambda r: int(r["year"]))
        if not filtered:
            print("No rows matched your filters.")
            return 1

        print_rows_table(filtered, args.metric)
        title = (
            f"Q3 Province Comparison - {province_param} ({args.metric}) "
            f"| sector={args.sector} | quarters_before={args.quarters_before}"
        )
        write_two_year_bar_svg(filtered, args.metric, title, Path(args.output_svg))

    print(f"SVG written to: {args.output_svg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
