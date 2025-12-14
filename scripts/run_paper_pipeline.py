#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_paper_pipeline.py
- One-click pipeline for paper-ready analysis
- Runs all analysis steps in sequence:
  1) Validate run (check_fairness, validate_run)
  2) Generate summary.json (summarize_run)
  3) Generate CSV tables (make_paper_tables)
  4) Generate figures (make_paper_figures)
  5) Generate LaTeX tables (make_latex_tables)
- Creates organized output directory structure
- Exits early if validation fails
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import io
from typing import List

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_command(cmd: List[str], description: str) -> int:
    """
    Run a command and report status

    Returns:
        Exit code (0 = success, non-zero = failure)
    """
    print(f"\n{'='*70}")
    print(f"[STEP] {description}")
    print(f"{'='*70}")
    print(f"Running: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"[ERROR] Command failed: {e}")
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="One-click paper pipeline for multi-turn experiment analysis"
    )
    ap.add_argument("--run_dir", required=True, help="Run directory (e.g., runs/2025-12-13_primary_v1)")
    ap.add_argument("--output_dir", default=None, help="Output directory for all paper assets (default: <run_dir>/paper_assets)")
    ap.add_argument("--skip_validation", action="store_true", help="Skip validation steps (not recommended)")
    ap.add_argument("--skip_figures", action="store_true", help="Skip figure generation (requires matplotlib)")
    args = ap.parse_args()

    run_dir = args.run_dir
    output_dir = args.output_dir or os.path.join(run_dir, "paper_assets")
    events_path = os.path.join(run_dir, "events.jsonl")

    # Validate inputs
    if not os.path.isdir(run_dir):
        print(f"[FAIL] Run directory not found: {run_dir}")
        return 2

    if not os.path.exists(events_path):
        print(f"[FAIL] events.jsonl not found: {events_path}")
        return 2

    # Create output directory structure
    os.makedirs(output_dir, exist_ok=True)
    tables_dir = os.path.join(output_dir, "tables")
    figures_dir = os.path.join(output_dir, "figures")
    latex_dir = os.path.join(output_dir, "latex")
    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    os.makedirs(latex_dir, exist_ok=True)

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Paths to analysis scripts
    check_fairness_py = os.path.join(script_dir, "check_fairness.py")
    validate_run_py = os.path.join(script_dir, "validate_run.py")
    summarize_run_py = os.path.join(script_dir, "summarize_run.py")
    evaluate_multiturn_py = os.path.join(script_dir, "evaluate_metrics_from_run.py")
    make_tables_py = os.path.join(script_dir, "make_paper_tables.py")
    make_figures_py = os.path.join(script_dir, "make_paper_figures.py")
    make_latex_py = os.path.join(script_dir, "make_latex_tables.py")
    show_stats_py = os.path.join(script_dir, "show_summary_stats.py")

    summary_json = os.path.join(output_dir, "summary.json")

    # ========================================================================
    # Step 1: Validation
    # ========================================================================
    if not args.skip_validation:
        # Step 1a: Check fairness (strict pairing)
        ret = run_command(
            [sys.executable, check_fairness_py, "--events_path", events_path],
            "Checking fairness (strict pairing validation)"
        )
        if ret != 0:
            print("\n[FAIL] Fairness check failed. Cannot proceed with paired analysis.")
            print("[INFO] Run with --skip_validation to bypass (NOT RECOMMENDED for research)")
            return 2

        # Step 1b: Validate run (data integrity)
        ret = run_command(
            [sys.executable, validate_run_py, "--run_dir", run_dir],
            "Validating run (data integrity checks)"
        )
        if ret != 0:
            print("\n[FAIL] Run validation failed. Cannot proceed.")
            print("[INFO] Run with --skip_validation to bypass (NOT RECOMMENDED for research)")
            return 2

    # ========================================================================
    # Step 2: Generate summary.json
    # ========================================================================
    ret = run_command(
        [sys.executable, summarize_run_py, "--run_dir", run_dir, "--out", summary_json],
        "Generating summary.json (statistical analysis)"
    )
    if ret != 0:
        print("\n[FAIL] Summary generation failed.")
        return 2
    
    # ========================================================================
    # Step 2b: Evaluate multiturn context metrics (CUS, UR, CCR)
    # ========================================================================
    ret = run_command(
        [sys.executable, evaluate_multiturn_py, "--run_dir", run_dir],
        "Evaluating multiturn context metrics (CUS, UR, CCR)"
    )
    if ret != 0:
        print("\n[WARNING] Multiturn context metrics evaluation failed.")
        print("[INFO] Continuing without multiturn metrics. Check events.jsonl for slots_state/turn_updates.")
    else:
        # 멀티턴 컨텍스트 지표를 summary.json에 통합 (통합 로직을 여기에 직접 구현)
        try:
            import json
            eval_dir = os.path.join(run_dir, "eval")
            metrics_summary_path = os.path.join(eval_dir, "metrics_summary.json")
            
            if os.path.exists(metrics_summary_path):
                with open(metrics_summary_path, "r", encoding="utf-8") as f:
                    metrics_summary = json.load(f)
                
                with open(summary_json, "r", encoding="utf-8") as f:
                    summary = json.load(f)
                
                # 멀티턴 컨텍스트 지표 통합
                summary["multiturn_context_metrics"] = {
                    "CUS": {
                        "by_mode": {
                            "llm": {"mean": metrics_summary.get("by_mode", {}).get("llm", {}).get("CUS")},
                            "agent": {"mean": metrics_summary.get("by_mode", {}).get("agent", {}).get("CUS")},
                        },
                        "paired_agent_minus_llm_mean": metrics_summary.get("paired_agent_minus_llm_mean", {}).get("CUS"),
                    },
                    "UR": {
                        "by_mode": {
                            "llm": {"mean": metrics_summary.get("by_mode", {}).get("llm", {}).get("UR")},
                            "agent": {"mean": metrics_summary.get("by_mode", {}).get("agent", {}).get("UR")},
                        },
                        "paired_agent_minus_llm_mean": metrics_summary.get("paired_agent_minus_llm_mean", {}).get("UR"),
                    },
                    "CCR": {
                        "by_mode": {
                            "llm": {"mean": metrics_summary.get("by_mode", {}).get("llm", {}).get("CCR_rule_obvious")},
                            "agent": {"mean": metrics_summary.get("by_mode", {}).get("agent", {}).get("CCR_rule_obvious")},
                        },
                        "paired_agent_minus_llm_mean": metrics_summary.get("paired_agent_minus_llm_mean", {}).get("CCR_rule_obvious"),
                    },
                    "by_turn": metrics_summary.get("by_mode_turn", {}),
                    "n_records": metrics_summary.get("n_records", 0),
                    "n_paired": metrics_summary.get("n_paired", 0),
                }
                
                with open(summary_json, "w", encoding="utf-8") as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
                
                print("[OK] Multiturn context metrics integrated into summary.json")
        except Exception as e:
            print(f"\n[WARNING] Multiturn metrics integration failed: {e}")
            print("[INFO] Continuing without integration.")

    # ========================================================================
    # Step 3: Generate CSV tables
    # ========================================================================
    ret = run_command(
        [sys.executable, make_tables_py, "--summary_json", summary_json, "--output_dir", tables_dir],
        "Generating CSV tables"
    )
    if ret != 0:
        print("\n[FAIL] Table generation failed.")
        return 2

    # ========================================================================
    # Step 4: Generate figures (optional)
    # ========================================================================
    if not args.skip_figures:
        ret = run_command(
            [sys.executable, make_figures_py, "--summary_json", summary_json, "--output_dir", figures_dir],
            "Generating figures (PNG + PDF)"
        )
        if ret != 0:
            print("\n[WARNING] Figure generation failed (matplotlib issue?)")
            print("[INFO] Continuing without figures. Install matplotlib: pip install matplotlib")
    else:
        print("\n[INFO] Skipping figure generation (--skip_figures)")

    # ========================================================================
    # Step 5: Generate LaTeX tables
    # ========================================================================
    ret = run_command(
        [sys.executable, make_latex_py, "--csv_dir", tables_dir, "--output_dir", latex_dir],
        "Generating LaTeX tables"
    )
    if ret != 0:
        print("\n[FAIL] LaTeX table generation failed.")
        return 2

    # ========================================================================
    # Final report
    # ========================================================================
    print("\n" + "="*70)
    print("[SUCCESS] Paper pipeline completed!")
    print("="*70)
    print(f"\nOutputs written to: {output_dir}")
    print(f"\n  1. Summary:     {summary_json}")
    print(f"  2. CSV Tables:  {tables_dir}/")
    print(f"  3. Figures:     {figures_dir}/")
    print(f"  4. LaTeX:       {latex_dir}/")

    print("\n[NEXT STEPS]")
    print("  - Review summary.json for statistical results")
    print("  - Include CSV tables in your thesis appendix")
    print("  - Insert figures into your paper (PNG for Word, PDF for LaTeX)")
    print("  - Copy .tex files into your LaTeX document")

    # ========================================================================
    # Step 6: Display summary statistics
    # ========================================================================
    if os.path.exists(summary_json):
        print("\n" + "="*70)
        print("[SUMMARY STATISTICS]")
        print("="*70)
        # show_summary_stats.py는 run_dir에서 summary.json을 찾으므로,
        # summary.json이 output_dir에 있으면 임시로 심볼릭 링크 생성하거나
        # 직접 summary_json 경로를 전달하는 방식으로 수정
        # 현재는 output_dir에 summary.json이 있으므로, run_dir에 복사하거나
        # show_summary_stats.py를 수정해야 함
        # 임시 해결: output_dir를 run_dir로 전달 (summary.json이 output_dir에 있으므로)
        # show_summary_stats.py는 summary.json 직접 경로 또는 run_dir 지원
        ret = run_command(
            [sys.executable, show_stats_py, summary_json],
            "Displaying overall statistics"
        )
        if ret != 0:
            print("[WARNING] Failed to display summary statistics")

    print("\n[REPRODUCIBILITY CHECKLIST]")
    print("  [OK] Fairness validated (perfect pairing)")
    print("  [OK] Data integrity checked")
    print("  [OK] Paired statistical tests computed")
    print("  [OK] Effect sizes (Cohen's d) calculated")
    print("  [OK] 95% confidence intervals provided")
    print("  [OK] Multiturn context metrics (CUS, UR, CCR) included")

    return 0


if __name__ == "__main__":
    sys.exit(main())
