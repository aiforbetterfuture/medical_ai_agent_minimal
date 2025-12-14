#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_latex_tables.py
- Converts CSV tables to LaTeX tabular format for thesis inclusion
- Reads CSV files from paper tables and outputs .tex files
- Handles Korean text (uses UTF-8, requires kotex or similar in LaTeX)
- Properly formats numbers, percentages, and significance markers
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Any, Dict, List


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters (except for intentional markup)"""
    # Don't escape: %, $, ±, *, Δ (these are intentional)
    # Escape: &, #, _, {, }
    replacements = {
        '&': r'\&',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
    }

    for char, escaped in replacements.items():
        text = text.replace(char, escaped)

    return text


def csv_to_latex_table(
    csv_path: str,
    output_path: str,
    caption: str,
    label: str,
    column_format: str = None
) -> None:
    """
    Convert CSV to LaTeX tabular environment

    Args:
        csv_path: Path to input CSV file
        output_path: Path to output .tex file
        caption: Table caption
        label: LaTeX label for reference
        column_format: LaTeX column format (e.g., "lcccc"), auto-detected if None
    """
    # Read CSV
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print(f"[WARNING] Empty CSV: {csv_path}")
        return

    header = rows[0]
    data_rows = rows[1:]

    # Auto-detect column format if not provided
    if column_format is None:
        # First column: left-aligned, rest: centered
        column_format = 'l' + 'c' * (len(header) - 1)

    # Start building LaTeX
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{{label}}}")
    lines.append(f"\\begin{{tabular}}{{{column_format}}}")
    lines.append(r"\toprule")

    # Header row
    header_escaped = [escape_latex(h) for h in header]
    lines.append(" & ".join(header_escaped) + r" \\")
    lines.append(r"\midrule")

    # Data rows
    for row in data_rows:
        row_escaped = [escape_latex(cell) for cell in row]
        lines.append(" & ".join(row_escaped) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[OK] Written: {output_path}")


def convert_overall_comparison(csv_dir: str, output_dir: str):
    """Convert overall_comparison.csv to LaTeX"""
    csv_path = os.path.join(csv_dir, "overall_comparison.csv")
    tex_path = os.path.join(output_dir, "overall_comparison.tex")

    if not os.path.exists(csv_path):
        print(f"[WARNING] CSV not found: {csv_path}")
        return

    csv_to_latex_table(
        csv_path=csv_path,
        output_path=tex_path,
        caption="Overall Comparison: LLM vs AI Agent (Paired t-test)",
        label="tab:overall_comparison",
        column_format="lcccccccc"  # 9 columns
    )


def convert_per_turn_comparison(csv_dir: str, output_dir: str):
    """Convert per_turn_comparison.csv to LaTeX"""
    csv_path = os.path.join(csv_dir, "per_turn_comparison.csv")
    tex_path = os.path.join(output_dir, "per_turn_comparison.tex")

    if not os.path.exists(csv_path):
        print(f"[WARNING] CSV not found: {csv_path}")
        return

    csv_to_latex_table(
        csv_path=csv_path,
        output_path=tex_path,
        caption="Per-Turn Breakdown: Metric Trends Across Conversation Turns",
        label="tab:per_turn_breakdown",
        column_format="cccccc"  # 6 columns
    )


def convert_efficiency_metrics(csv_dir: str, output_dir: str):
    """Convert efficiency_metrics.csv to LaTeX"""
    csv_path = os.path.join(csv_dir, "efficiency_metrics.csv")
    tex_path = os.path.join(output_dir, "efficiency_metrics.tex")

    if not os.path.exists(csv_path):
        print(f"[WARNING] CSV not found: {csv_path}")
        return

    csv_to_latex_table(
        csv_path=csv_path,
        output_path=tex_path,
        caption="Efficiency Comparison: Cost, Latency, and Resource Usage",
        label="tab:efficiency_metrics",
        column_format="lccc"  # 4 columns
    )


def convert_ablation_comparison(csv_dir: str, output_dir: str):
    """Convert ablation_comparison.csv to LaTeX (if exists)"""
    csv_path = os.path.join(csv_dir, "ablation_comparison.csv")
    tex_path = os.path.join(output_dir, "ablation_comparison.tex")

    if not os.path.exists(csv_path):
        print(f"[INFO] No ablation CSV found: {csv_path}, skipping")
        return

    csv_to_latex_table(
        csv_path=csv_path,
        output_path=tex_path,
        caption="Ablation Study: Impact of Individual Features",
        label="tab:ablation_study",
        column_format="lcccc"  # 5 columns
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv_dir", required=True, help="Directory containing CSV tables")
    ap.add_argument("--output_dir", required=True, help="Directory to write .tex files")
    args = ap.parse_args()

    csv_dir = args.csv_dir
    output_dir = args.output_dir

    # Validate input
    if not os.path.isdir(csv_dir):
        print(f"[FAIL] CSV directory not found: {csv_dir}")
        return 2

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Convert all tables
    try:
        print("[INFO] Converting CSV tables to LaTeX...")

        convert_overall_comparison(csv_dir, output_dir)
        convert_per_turn_comparison(csv_dir, output_dir)
        convert_efficiency_metrics(csv_dir, output_dir)
        convert_ablation_comparison(csv_dir, output_dir)

        print(f"\n[OK] LaTeX tables written to: {output_dir}")
        print("\n[NOTE] LaTeX preamble requirements:")
        print("  \\usepackage{booktabs}  % for \\toprule, \\midrule, \\bottomrule")
        print("  \\usepackage{kotex}     % for Korean text (if needed)")

        return 0

    except Exception as e:
        print(f"[FAIL] Failed to convert tables: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
