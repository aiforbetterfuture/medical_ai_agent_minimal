#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_paper_figures.py
- Reads summary.json and produces publication-quality figures
- Output formats: PNG (high DPI) and PDF (vector)
- Figures:
  1) overall_comparison.png/pdf: Bar chart of paired comparison
  2) per_turn_trends.png/pdf: Line plots showing trend across turns
  3) efficiency_comparison.png/pdf: Cost and latency comparison
  4) effect_sizes.png/pdf: Cohen's d visualization
- Uses matplotlib for visualization
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("[WARNING] matplotlib not available. Install with: pip install matplotlib")


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_figure(fig, output_dir: str, filename: str):
    """Save figure as both PNG (300 DPI) and PDF (vector)"""
    png_path = os.path.join(output_dir, f"{filename}.png")
    pdf_path = os.path.join(output_dir, f"{filename}.pdf")

    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')

    print(f"[OK] Saved: {png_path}")
    print(f"[OK] Saved: {pdf_path}")


def plot_overall_comparison(summary: Dict[str, Any], output_dir: str):
    """
    Bar chart: LLM vs AI Agent across key metrics

    Shows mean values with error bars (±1 std)
    Highlights statistical significance with asterisks
    """
    paired = summary.get("paired_comparison", {})

    metrics = [
        ("faithfulness", "Faithfulness"),
        ("answer_relevance", "Answer\nRelevance"),
        ("context_precision", "Context\nPrecision"),
        ("context_recall", "Context\nRecall"),
        ("context_relevancy", "Context\nRelevancy"),
    ]

    metric_names = []
    llm_means = []
    llm_stds = []
    agent_means = []
    agent_stds = []
    p_values = []

    for metric_key, metric_label in metrics:
        m = paired.get(metric_key, {})

        llm_mean = m.get("llm_mean")
        llm_std = m.get("llm_std")
        agent_mean = m.get("agent_mean")
        agent_std = m.get("agent_std")
        p_value = m.get("p_value")

        if llm_mean is None or agent_mean is None:
            continue

        metric_names.append(metric_label)
        llm_means.append(llm_mean)
        llm_stds.append(llm_std if llm_std is not None else 0)
        agent_means.append(agent_mean)
        agent_stds.append(agent_std if agent_std is not None else 0)
        p_values.append(p_value)

    if not metric_names:
        print("[WARNING] No metrics available for overall comparison plot")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(metric_names))
    width = 0.35

    # Bars
    llm_bars = ax.bar([i - width/2 for i in x], llm_means, width,
                      yerr=llm_stds, label='LLM',
                      color='#3498db', alpha=0.8, capsize=5)
    agent_bars = ax.bar([i + width/2 for i in x], agent_means, width,
                        yerr=agent_stds, label='AI Agent',
                        color='#e74c3c', alpha=0.8, capsize=5)

    # Add significance markers
    max_height = max(max(llm_means), max(agent_means)) + max(max(llm_stds), max(agent_stds))

    for i, p in enumerate(p_values):
        if p is None:
            continue

        # Determine significance
        if p < 0.001:
            sig = "***"
        elif p < 0.01:
            sig = "**"
        elif p < 0.05:
            sig = "*"
        else:
            continue  # Not significant

        # Draw significance marker
        y_pos = max_height * 1.05
        ax.text(i, y_pos, sig, ha='center', va='bottom', fontsize=14, fontweight='bold')

    # Formatting
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_xlabel('Metric', fontsize=12, fontweight='bold')
    ax.set_title('Overall Comparison: LLM vs AI Agent', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metric_names, fontsize=10)
    ax.legend(fontsize=11, loc='lower right')
    ax.set_ylim(0, max_height * 1.15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Save
    save_figure(fig, output_dir, "overall_comparison")
    plt.close(fig)


def plot_per_turn_trends(summary: Dict[str, Any], output_dir: str):
    """
    Line plots: Metric trends across turns (LLM vs AI Agent)

    Separate subplots for each key metric
    """
    per_turn = summary.get("per_turn_breakdown", {})

    if not per_turn:
        print("[WARNING] No per-turn data available for trend plot")
        return

    # Extract turn numbers
    turn_nums = sorted([int(k.replace("turn_", "")) for k in per_turn.keys()])

    metrics = [
        ("faithfulness", "Faithfulness"),
        ("answer_relevance", "Answer Relevance"),
        ("context_precision", "Context Precision"),
    ]

    # Create subplots
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    for idx, (metric_key, metric_label) in enumerate(metrics):
        ax = axes[idx]

        llm_values = []
        agent_values = []

        for turn in turn_nums:
            turn_key = f"turn_{turn}"
            turn_data = per_turn.get(turn_key, {})

            llm_mean = turn_data.get("llm", {}).get(metric_key, {}).get("mean")
            agent_mean = turn_data.get("agent", {}).get(metric_key, {}).get("mean")

            llm_values.append(llm_mean if llm_mean is not None else 0)
            agent_values.append(agent_mean if agent_mean is not None else 0)

        # Plot lines
        ax.plot(turn_nums, llm_values, marker='o', label='LLM',
                color='#3498db', linewidth=2, markersize=6)
        ax.plot(turn_nums, agent_values, marker='s', label='AI Agent',
                color='#e74c3c', linewidth=2, markersize=6)

        # Formatting
        ax.set_xlabel('Turn', fontsize=11, fontweight='bold')
        ax.set_ylabel('Score', fontsize=11, fontweight='bold')
        ax.set_title(metric_label, fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3, linestyle='--')
        ax.set_xticks(turn_nums)

    plt.tight_layout()
    save_figure(fig, output_dir, "per_turn_trends")
    plt.close(fig)


def plot_efficiency_comparison(summary: Dict[str, Any], output_dir: str):
    """
    Bar charts: Cost and latency comparison

    Two subplots side by side
    """
    efficiency = summary.get("efficiency_comparison", {})

    cost_llm = efficiency.get("cost_per_turn_llm")
    cost_agent = efficiency.get("cost_per_turn_agent")
    latency_llm = efficiency.get("latency_mean_llm")
    latency_agent = efficiency.get("latency_mean_agent")

    if all(v is None for v in [cost_llm, cost_agent, latency_llm, latency_agent]):
        print("[WARNING] No efficiency data available for plot")
        return

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Cost comparison
    if cost_llm is not None and cost_agent is not None:
        modes = ['LLM', 'AI Agent']
        costs = [cost_llm, cost_agent]
        colors = ['#3498db', '#e74c3c']

        bars1 = ax1.bar(modes, costs, color=colors, alpha=0.8, width=0.6)
        ax1.set_ylabel('Cost per Turn ($)', fontsize=11, fontweight='bold')
        ax1.set_title('Cost Comparison', fontsize=12, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3, linestyle='--')

        # Add value labels on bars
        for bar, cost in zip(bars1, costs):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, height,
                    f'${cost:.4f}', ha='center', va='bottom', fontsize=10)

    # Latency comparison
    if latency_llm is not None and latency_agent is not None:
        modes = ['LLM', 'AI Agent']
        latencies = [latency_llm, latency_agent]
        colors = ['#3498db', '#e74c3c']

        bars2 = ax2.bar(modes, latencies, color=colors, alpha=0.8, width=0.6)
        ax2.set_ylabel('Mean Latency (s)', fontsize=11, fontweight='bold')
        ax2.set_title('Latency Comparison', fontsize=12, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')

        # Add value labels on bars
        for bar, latency in zip(bars2, latencies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2, height,
                    f'{latency:.2f}s', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    save_figure(fig, output_dir, "efficiency_comparison")
    plt.close(fig)


def plot_effect_sizes(summary: Dict[str, Any], output_dir: str):
    """
    Horizontal bar chart: Cohen's d effect sizes

    Color-coded by effect size magnitude
    - Small: |d| < 0.5 (light)
    - Medium: 0.5 <= |d| < 0.8 (medium)
    - Large: |d| >= 0.8 (dark)
    """
    paired = summary.get("paired_comparison", {})

    metrics = [
        ("faithfulness", "Faithfulness"),
        ("answer_relevance", "Answer Relevance"),
        ("context_precision", "Context Precision"),
        ("context_recall", "Context Recall"),
        ("context_relevancy", "Context Relevancy"),
    ]

    metric_names = []
    cohens_ds = []

    for metric_key, metric_label in metrics:
        m = paired.get(metric_key, {})
        d = m.get("cohens_d")

        if d is None:
            continue

        metric_names.append(metric_label)
        cohens_ds.append(d)

    if not metric_names:
        print("[WARNING] No Cohen's d values available for effect size plot")
        return

    # Determine colors based on effect size
    colors = []
    for d in cohens_ds:
        abs_d = abs(d)
        if abs_d >= 0.8:
            colors.append('#e74c3c')  # Large effect - red
        elif abs_d >= 0.5:
            colors.append('#f39c12')  # Medium effect - orange
        else:
            colors.append('#95a5a6')  # Small effect - gray

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = range(len(metric_names))
    bars = ax.barh(y_pos, cohens_ds, color=colors, alpha=0.8)

    # Reference lines for effect size thresholds
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.axvline(x=0.5, color='gray', linestyle='--', linewidth=0.6, alpha=0.5)
    ax.axvline(x=-0.5, color='gray', linestyle='--', linewidth=0.6, alpha=0.5)
    ax.axvline(x=0.8, color='gray', linestyle='--', linewidth=0.6, alpha=0.5)
    ax.axvline(x=-0.8, color='gray', linestyle='--', linewidth=0.6, alpha=0.5)

    # Add value labels
    for i, (bar, d) in enumerate(zip(bars, cohens_ds)):
        width = bar.get_width()
        label_x = width + (0.05 if width >= 0 else -0.05)
        ha = 'left' if width >= 0 else 'right'
        ax.text(label_x, i, f'{d:.3f}', ha=ha, va='center', fontsize=9)

    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(metric_names, fontsize=10)
    ax.set_xlabel("Cohen's d (Effect Size)", fontsize=12, fontweight='bold')
    ax.set_title("Effect Sizes: AI Agent vs LLM", fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Legend for effect sizes
    small_patch = mpatches.Patch(color='#95a5a6', alpha=0.8, label='Small (|d| < 0.5)')
    medium_patch = mpatches.Patch(color='#f39c12', alpha=0.8, label='Medium (0.5 ≤ |d| < 0.8)')
    large_patch = mpatches.Patch(color='#e74c3c', alpha=0.8, label='Large (|d| ≥ 0.8)')
    ax.legend(handles=[small_patch, medium_patch, large_patch],
             loc='lower right', fontsize=9)

    # Save
    save_figure(fig, output_dir, "effect_sizes")
    plt.close(fig)


def main() -> int:
    if not HAS_MATPLOTLIB:
        print("[FAIL] matplotlib is required. Install with: pip install matplotlib")
        return 2

    ap = argparse.ArgumentParser()
    ap.add_argument("--summary_json", required=True, help="Path to summary.json")
    ap.add_argument("--output_dir", required=True, help="Directory to write figures")
    args = ap.parse_args()

    summary_path = args.summary_json
    output_dir = args.output_dir

    # Validate input
    if not os.path.exists(summary_path):
        print(f"[FAIL] summary.json not found: {summary_path}")
        return 2

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Read summary
    try:
        summary = read_json(summary_path)
    except Exception as e:
        print(f"[FAIL] Failed to read summary.json: {e}")
        return 2

    # Generate figures
    try:
        print("[INFO] Generating figures...")

        plot_overall_comparison(summary, output_dir)
        plot_per_turn_trends(summary, output_dir)
        plot_efficiency_comparison(summary, output_dir)
        plot_effect_sizes(summary, output_dir)

        print(f"\n[OK] All figures saved to: {output_dir}")
        return 0

    except Exception as e:
        print(f"[FAIL] Failed to generate figures: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
