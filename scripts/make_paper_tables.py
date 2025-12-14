#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_paper_tables.py
- Reads summary.json and produces CSV tables for paper/thesis
- Output CSVs:
  1) overall_comparison.csv: Paired comparison of LLM vs AI Agent (overall)
  2) per_turn_comparison.csv: Breakdown by turn
  3) efficiency_metrics.csv: Cost, latency, cache hit rates
- Uses only standard library (csv, json)
- Research-grade formatting with proper precision
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_float(val: Optional[float], precision: int = 3) -> str:
    """Format float with fixed precision, handle None"""
    if val is None:
        return "N/A"
    return f"{val:.{precision}f}"


def fmt_int(val: Optional[int]) -> str:
    """Format integer, handle None"""
    if val is None:
        return "N/A"
    return str(val)


def fmt_pct(val: Optional[float], precision: int = 1) -> str:
    """Format percentage (0.0-1.0 -> 0.0%-100.0%), handle None"""
    if val is None:
        return "N/A"
    return f"{val * 100:.{precision}f}%"


def write_overall_comparison_table(
    summary: Dict[str, Any],
    output_path: str
) -> None:
    """
    Overall paired comparison table (LLM vs AI Agent)

    Columns:
    - Metric
    - LLM (mean ± std)
    - AI Agent (mean ± std)
    - Δ (Agent - LLM)
    - Cohen's d
    - 95% CI
    - p-value
    - Significance
    """
    paired = summary.get("paired_comparison", {})

    # Metrics to include
    metrics = [
        ("faithfulness", "Faithfulness", 3),
        ("answer_relevance", "Answer Relevance", 3),
        ("context_precision", "Context Precision", 3),
        ("context_recall", "Context Recall", 3),
        ("context_relevancy", "Context Relevancy", 3),
    ]

    rows = []

    for metric_key, metric_name, precision in metrics:
        m = paired.get(metric_key, {})

        llm_mean = m.get("llm_mean")
        llm_std = m.get("llm_std")
        agent_mean = m.get("agent_mean")
        agent_std = m.get("agent_std")
        delta = m.get("delta_mean")
        cohens_d = m.get("cohens_d")
        ci_lower = m.get("ci95_lower")
        ci_upper = m.get("ci95_upper")
        p_value = m.get("p_value")
        n_pairs = m.get("n_pairs")

        # Format LLM and Agent as "mean ± std"
        llm_str = f"{fmt_float(llm_mean, precision)} ± {fmt_float(llm_std, precision)}" if llm_mean is not None else "N/A"
        agent_str = f"{fmt_float(agent_mean, precision)} ± {fmt_float(agent_std, precision)}" if agent_mean is not None else "N/A"

        # Format delta
        delta_str = fmt_float(delta, precision)

        # Format Cohen's d
        d_str = fmt_float(cohens_d, 3)

        # Format 95% CI
        if ci_lower is not None and ci_upper is not None:
            ci_str = f"[{fmt_float(ci_lower, precision)}, {fmt_float(ci_upper, precision)}]"
        else:
            ci_str = "N/A"

        # Format p-value
        if p_value is not None:
            if p_value < 0.001:
                p_str = "<0.001"
            else:
                p_str = fmt_float(p_value, 3)
        else:
            p_str = "N/A"

        # Significance
        if p_value is not None:
            if p_value < 0.001:
                sig = "***"
            elif p_value < 0.01:
                sig = "**"
            elif p_value < 0.05:
                sig = "*"
            else:
                sig = "ns"
        else:
            sig = "N/A"

        rows.append({
            "Metric": metric_name,
            "LLM": llm_str,
            "AI Agent": agent_str,
            "Δ (Agent - LLM)": delta_str,
            "Cohen's d": d_str,
            "95% CI": ci_str,
            "p-value": p_str,
            "Sig.": sig,
            "n": fmt_int(n_pairs)
        })

    # Write CSV
    fieldnames = ["Metric", "LLM", "AI Agent", "Δ (Agent - LLM)", "Cohen's d", "95% CI", "p-value", "Sig.", "n"]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Written: {output_path}")


def write_per_turn_comparison_table(
    summary: Dict[str, Any],
    output_path: str
) -> None:
    """
    Per-turn breakdown table

    Columns:
    - Turn
    - Metric
    - LLM
    - AI Agent
    - Δ
    - p-value
    """
    per_turn = summary.get("per_turn_breakdown", {})

    metrics = [
        ("faithfulness", "Faithfulness", 3),
        ("answer_relevance", "Answer Relevance", 3),
        ("context_precision", "Context Precision", 3),
    ]

    rows = []

    for turn_str, turn_data in sorted(per_turn.items(), key=lambda x: int(x[0].replace("turn_", ""))):
        turn_num = turn_str.replace("turn_", "")

        for metric_key, metric_name, precision in metrics:
            llm_data = turn_data.get("llm", {}).get(metric_key, {})
            agent_data = turn_data.get("agent", {}).get(metric_key, {})

            llm_mean = llm_data.get("mean")
            agent_mean = agent_data.get("mean")

            # Calculate delta
            if llm_mean is not None and agent_mean is not None:
                delta = agent_mean - llm_mean
            else:
                delta = None

            # p-value (from paired comparison if available)
            # Note: per_turn_breakdown doesn't include p-values in the current schema
            # We'd need to add this in summarize_run.py if needed
            p_value = None

            rows.append({
                "Turn": turn_num,
                "Metric": metric_name,
                "LLM": fmt_float(llm_mean, precision),
                "AI Agent": fmt_float(agent_mean, precision),
                "Δ": fmt_float(delta, precision),
                "p-value": fmt_float(p_value, 3)
            })

    # Write CSV
    fieldnames = ["Turn", "Metric", "LLM", "AI Agent", "Δ", "p-value"]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Written: {output_path}")


def write_efficiency_metrics_table(
    summary: Dict[str, Any],
    output_path: str
) -> None:
    """
    Efficiency metrics table (cost, latency, cache)

    Columns:
    - Metric
    - LLM
    - AI Agent
    - Δ (%)
    """
    efficiency = summary.get("efficiency", {})

    rows = []

    # Cost per turn
    cost_llm = efficiency.get("cost", {}).get("by_mode", {}).get("llm", {}).get("mean")
    cost_agent = efficiency.get("cost", {}).get("by_mode", {}).get("agent", {}).get("mean")
    if cost_llm is not None and cost_agent is not None and cost_llm > 0:
        cost_delta_pct = ((cost_agent - cost_llm) / cost_llm) * 100
    else:
        cost_delta_pct = None

    rows.append({
        "Metric": "Cost per turn ($)",
        "LLM": fmt_float(cost_llm, 6) if cost_llm is not None else "N/A",
        "AI Agent": fmt_float(cost_agent, 6) if cost_agent is not None else "N/A",
        "Δ (%)": fmt_float(cost_delta_pct, 1) if cost_delta_pct is not None else "N/A"
    })

    # Latency (convert ms to seconds)
    latency_llm_ms = efficiency.get("latency", {}).get("by_mode", {}).get("llm", {}).get("mean")
    latency_agent_ms = efficiency.get("latency", {}).get("by_mode", {}).get("agent", {}).get("mean")
    latency_llm = latency_llm_ms / 1000.0 if latency_llm_ms is not None else None
    latency_agent = latency_agent_ms / 1000.0 if latency_agent_ms is not None else None
    if latency_llm is not None and latency_agent is not None and latency_llm > 0:
        latency_delta_pct = ((latency_agent - latency_llm) / latency_llm) * 100
    else:
        latency_delta_pct = None

    rows.append({
        "Metric": "Latency (s)",
        "LLM": fmt_float(latency_llm, 2) if latency_llm is not None else "N/A",
        "AI Agent": fmt_float(latency_agent, 2) if latency_agent is not None else "N/A",
        "Δ (%)": fmt_float(latency_delta_pct, 1) if latency_delta_pct is not None else "N/A"
    })

    # Cache hit rate
    cache_llm = 0.0  # LLM mode doesn't use cache
    cache_agent = efficiency.get("cache", {}).get("agent_cache_hit_rate")
    if cache_agent is not None:
        cache_delta_pp = (cache_agent - cache_llm) * 100  # percentage points
    else:
        cache_delta_pp = None

    rows.append({
        "Metric": "Cache hit rate",
        "LLM": fmt_pct(cache_llm, 1),
        "AI Agent": fmt_pct(cache_agent, 1) if cache_agent is not None else "N/A",
        "Δ (%)": (fmt_float(cache_delta_pp, 1) + " pp" if cache_delta_pp is not None else "N/A")
    })

    # Token usage (not available in current summary.json structure)
    tokens_llm = None
    tokens_agent = None
    tokens_delta_pct = None

    rows.append({
        "Metric": "Total tokens",
        "LLM": fmt_int(tokens_llm) if tokens_llm is not None else "N/A",
        "AI Agent": fmt_int(tokens_agent) if tokens_agent is not None else "N/A",
        "Δ (%)": fmt_float(tokens_delta_pct, 1) if tokens_delta_pct is not None else "N/A"
    })

    # Write CSV
    fieldnames = ["Metric", "LLM", "AI Agent", "Δ (%)"]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Written: {output_path}")


def write_ablation_table(
    summary: Dict[str, Any],
    output_path: str
) -> None:
    """
    Ablation study table (if ablation_breakdown exists)

    Shows impact of each feature (Active Retrieval, Context Compression, etc.)

    Columns:
    - Feature
    - Enabled
    - Faithfulness
    - Answer Relevance
    - Cost per turn
    - n_pairs
    """
    ablation = summary.get("ablation_breakdown")
    if not ablation:
        print("[INFO] No ablation_breakdown in summary.json, skipping ablation table")
        return

    rows = []

    for feature_key, feature_data in sorted(ablation.items()):
        # feature_data should have: enabled, metrics, n_pairs
        enabled = feature_data.get("enabled", "N/A")
        metrics = feature_data.get("metrics", {})
        n_pairs = feature_data.get("n_pairs")

        faithfulness = metrics.get("faithfulness", {}).get("mean")
        answer_rel = metrics.get("answer_relevance", {}).get("mean")
        cost = metrics.get("cost_per_turn")

        rows.append({
            "Feature": feature_key,
            "Enabled": str(enabled),
            "Faithfulness": fmt_float(faithfulness, 3),
            "Answer Relevance": fmt_float(answer_rel, 3),
            "Cost ($)": fmt_float(cost, 4),
            "n": fmt_int(n_pairs)
        })

    # Write CSV
    fieldnames = ["Feature", "Enabled", "Faithfulness", "Answer Relevance", "Cost ($)", "n"]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Written: {output_path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary_json", required=True, help="Path to summary.json")
    ap.add_argument("--output_dir", required=True, help="Directory to write CSV tables")
    args = ap.parse_args()

    summary_path = args.summary_json
    output_dir = args.output_dir

    # Validate input
    if not os.path.exists(summary_path):
        print(f"[FAIL] summary.json not found: {summary_path}")
        return 2

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Read summary
    try:
        summary = read_json(summary_path)
    except Exception as e:
        print(f"[FAIL] Failed to read summary.json: {e}")
        return 2

    # Write tables
    try:
        # 1. Overall comparison
        overall_path = os.path.join(output_dir, "overall_comparison.csv")
        write_overall_comparison_table(summary, overall_path)

        # 2. Per-turn comparison
        per_turn_path = os.path.join(output_dir, "per_turn_comparison.csv")
        write_per_turn_comparison_table(summary, per_turn_path)

        # 3. Efficiency metrics
        efficiency_path = os.path.join(output_dir, "efficiency_metrics.csv")
        write_efficiency_metrics_table(summary, efficiency_path)

        # 4. Ablation (if exists)
        ablation_path = os.path.join(output_dir, "ablation_comparison.csv")
        write_ablation_table(summary, ablation_path)

        print(f"\n[OK] All tables written to: {output_dir}")
        return 0

    except Exception as e:
        print(f"[FAIL] Failed to write tables: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
