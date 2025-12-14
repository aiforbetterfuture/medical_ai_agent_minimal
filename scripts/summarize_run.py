#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
summarize_run.py
- Reads runs/<run_id>/events.jsonl (+ optional node_trace.jsonl)
- Produces runs/<run_id>/summary.json in schema_version summary.v1

Assumptions (robust to partial logs):
- Each events.jsonl line is a JSON object that includes:
  - run_id, mode in {"llm","agent"}, patient_id, turn_id, question_id
  - metrics: dict (e.g., faithfulness, answer_relevance, judge_total, grounding, completeness, accuracy, ...)
  - usage: dict (input_tokens, output_tokens, estimated_cost_usd)
  - timing: latency_ms or timing_ms.elapsed
  - optional flags: cache_hit, refine_triggered, refine_iterations, query_rewrite_applied, retrieval_empty
- If multiple events exist for same (mode, patient_id, turn_id, question_id), we keep the latest "final-ish" one.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -------------------------
# Small utilities
# -------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"JSONL parse error: {path}:{line_no}: {e}") from e


def safe_get(d: Dict[str, Any], *keys: str, default=None):
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def to_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def quantile(sorted_vals: List[float], q: float) -> float:
    """Linear interpolation quantile. q in [0,1]. Requires sorted input."""
    if not sorted_vals:
        return float("nan")
    if q <= 0:
        return sorted_vals[0]
    if q >= 1:
        return sorted_vals[-1]
    n = len(sorted_vals)
    pos = (n - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def summarize_numeric(values: List[float]) -> Dict[str, float]:
    values = [v for v in values if v is not None and not math.isnan(v)]
    if not values:
        return {
            "mean": float("nan"),
            "std": float("nan"),
            "median": float("nan"),
            "p25": float("nan"),
            "p75": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
        }
    values_sorted = sorted(values)
    mean = statistics.fmean(values_sorted)
    std = statistics.pstdev(values_sorted) if len(values_sorted) > 1 else 0.0
    med = statistics.median(values_sorted)
    return {
        "mean": mean,
        "std": std,
        "median": med,
        "p25": quantile(values_sorted, 0.25),
        "p75": quantile(values_sorted, 0.75),
        "min": values_sorted[0],
        "max": values_sorted[-1],
    }


def normal_cdf(x: float) -> float:
    """Standard normal CDF using erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def paired_p_value_normal_approx(deltas: List[float]) -> Optional[float]:
    """
    For large n, paired t-test ~ normal approx on mean(delta)/(std(delta)/sqrt(n)).
    Returns two-sided p-value.
    """
    deltas = [d for d in deltas if d is not None and not math.isnan(d)]
    n = len(deltas)
    if n < 2:
        return None
    mean = statistics.fmean(deltas)
    std = statistics.pstdev(deltas)  # population std; close enough for large n
    if std == 0:
        return 0.0 if mean != 0 else 1.0
    z = mean / (std / math.sqrt(n))
    p = 2.0 * (1.0 - normal_cdf(abs(z)))
    return max(0.0, min(1.0, p))


def ci95_mean(deltas: List[float]) -> Optional[Dict[str, float]]:
    deltas = [d for d in deltas if d is not None and not math.isnan(d)]
    n = len(deltas)
    if n < 2:
        return None
    mean = statistics.fmean(deltas)
    std = statistics.pstdev(deltas)
    if std == 0:
        return {"low": mean, "high": mean}
    se = std / math.sqrt(n)
    # 95% normal approx
    low = mean - 1.96 * se
    high = mean + 1.96 * se
    return {"low": low, "high": high}


def cohens_d_paired(deltas: List[float]) -> Optional[float]:
    deltas = [d for d in deltas if d is not None and not math.isnan(d)]
    if len(deltas) < 2:
        return None
    mean = statistics.fmean(deltas)
    std = statistics.pstdev(deltas)
    if std == 0:
        return None
    return mean / std


# -------------------------
# Data extraction
# -------------------------

FINAL_EVENT_TYPES = {
    "turn_end",
    "answer_final",
    "final_answer",
    "evaluation",
    "turn_complete",
}

@dataclass(frozen=True)
class Key:
    mode: str
    patient_id: str
    turn_id: int
    question_id: str


def is_finalish_event(e: Dict[str, Any]) -> bool:
    et = safe_get(e, "event_type", default=None)
    phase = safe_get(e, "phase", default=None)
    if isinstance(et, str) and et in FINAL_EVENT_TYPES:
        return True
    if isinstance(phase, str) and phase in ("final", "end", "complete"):
        return True
    # fallback: if metrics exist, treat as candidate
    if isinstance(e.get("metrics"), dict) and e.get("mode") in ("llm", "agent"):
        return True
    # For our current events.jsonl format, all events are "final" per turn
    return True


def event_timestamp(e: Dict[str, Any]) -> str:
    # Try multiple fields; fallback to empty string.
    for path in [
        ("timestamps", "ended_at_utc"),
        ("timestamps", "created_at_utc"),
        ("timestamp_utc",),
        ("created_at_utc",),
    ]:
        v = safe_get(e, *path, default=None)
        if isinstance(v, str):
            return v
    return ""


def parse_key(e: Dict[str, Any]) -> Optional[Key]:
    mode = e.get("mode")
    patient_id = e.get("patient_id")
    turn_id = e.get("turn_id")
    question_id = safe_get(e, "question", "question_id", default=None)
    if mode not in ("llm", "agent"):
        return None
    if not isinstance(patient_id, str):
        return None
    if not isinstance(turn_id, int):
        # sometimes saved as string
        try:
            turn_id = int(turn_id)
        except Exception:
            return None
    if not isinstance(question_id, str):
        return None
    return Key(mode=mode, patient_id=patient_id, turn_id=turn_id, question_id=question_id)


def pick_final_records(events_path: str) -> Dict[Key, Dict[str, Any]]:
    """
    Choose one 'final' record per Key. If multiple, choose the latest by timestamp string.
    """
    chosen: Dict[Key, Dict[str, Any]] = {}
    chosen_ts: Dict[Key, str] = {}

    for e in read_jsonl(events_path):
        if not is_finalish_event(e):
            continue
        k = parse_key(e)
        if k is None:
            continue
        ts = event_timestamp(e)
        if k not in chosen or ts >= chosen_ts.get(k, ""):
            chosen[k] = e
            chosen_ts[k] = ts
    return chosen


def extract_metric_value(rec: Dict[str, Any], metric: str) -> Optional[float]:
    m = rec.get("metrics")
    if isinstance(m, dict) and metric in m:
        return to_float(m.get(metric))
    # allow top-level convenience fields
    if metric in rec:
        return to_float(rec.get(metric))
    # 멀티턴 컨텍스트 지표는 metadata에서 추출 시도
    if metric in ["CUS", "UR", "CCR"]:
        metadata = rec.get("metadata", {})
        # metadata에 직접 저장된 경우 (향후 확장)
        if metric in metadata:
            return to_float(metadata.get(metric))
    return None


def extract_latency_ms(rec: Dict[str, Any]) -> Optional[float]:
    # prefer explicit latency_ms
    v = rec.get("latency_ms")
    if v is not None:
        return to_float(v)
    v = safe_get(rec, "timing_ms", "total", default=None)
    if v is not None:
        return to_float(v)
    return None


def extract_cost_usd(rec: Dict[str, Any]) -> Optional[float]:
    v = safe_get(rec, "usage", "estimated_cost_usd", default=None)
    if v is not None:
        return to_float(v)
    return None


# -------------------------
# Aggregation
# -------------------------

DEFAULT_MAIN_METRICS = [
    "faithfulness",
    "answer_relevance",
    "judge_total",
    "grounding",
    "completeness",
    "accuracy",
]

def collect_metric_values(records: Dict[Key, Dict[str, Any]], mode: str, metric: str) -> List[float]:
    vals: List[float] = []
    for k, rec in records.items():
        if k.mode != mode:
            continue
        v = extract_metric_value(rec, metric)
        if v is None:
            continue
        vals.append(v)
    return vals


def build_mode_metric_rows(records: Dict[Key, Dict[str, Any]], mode: str, metrics: List[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for metric in metrics:
        vals = collect_metric_values(records, mode, metric)
        if not vals:
            continue
        s = summarize_numeric(vals)
        rows.append({
            "metric": metric,
            **s
        })
    return rows


def paired_deltas(records: Dict[Key, Dict[str, Any]], metric: str) -> Tuple[int, List[float]]:
    """
    Pair by (patient_id, turn_id, question_id) across llm and agent.
    """
    # index per mode
    llm_map: Dict[Tuple[str,int,str], Dict[str, Any]] = {}
    agent_map: Dict[Tuple[str,int,str], Dict[str, Any]] = {}

    for k, rec in records.items():
        base_key = (k.patient_id, k.turn_id, k.question_id)
        if k.mode == "llm":
            llm_map[base_key] = rec
        elif k.mode == "agent":
            agent_map[base_key] = rec

    deltas: List[float] = []
    n_pairs = 0

    for base_key, a_rec in agent_map.items():
        l_rec = llm_map.get(base_key)
        if not l_rec:
            continue
        a = extract_metric_value(a_rec, metric)
        l = extract_metric_value(l_rec, metric)
        if a is None or l is None:
            continue
        deltas.append(a - l)
        n_pairs += 1

    return n_pairs, deltas


def build_paired_comparisons(records: Dict[Key, Dict[str, Any]], metrics: List[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for metric in metrics:
        n_pairs, deltas = paired_deltas(records, metric)
        if n_pairs < 2:
            continue
        s = summarize_numeric(deltas)
        ci = ci95_mean(deltas)
        p = paired_p_value_normal_approx(deltas)
        d = cohens_d_paired(deltas)
        out.append({
            "metric": metric,
            "n_pairs": n_pairs,
            "delta_mean": s["mean"],
            "delta_std": s["std"],
            "ci95": ci if ci is not None else {"low": float("nan"), "high": float("nan")},
            "t_test_p_value": p,
            "effect_size_cohens_d": d,
        })
    return out


def breakdown_by_turn(records: Dict[Key, Dict[str, Any]], metrics: List[str]) -> List[Dict[str, Any]]:
    # group_key: turn=1..5
    rows: List[Dict[str, Any]] = []
    for mode in ("llm", "agent"):
        for turn in range(1, 6):
            for metric in metrics:
                vals: List[float] = []
                for k, rec in records.items():
                    if k.mode != mode or k.turn_id != turn:
                        continue
                    v = extract_metric_value(rec, metric)
                    if v is None:
                        continue
                    vals.append(v)
                if not vals:
                    continue
                s = summarize_numeric(vals)
                rows.append({
                    "group_key": f"turn={turn}",
                    "mode": mode,
                    "metric": metric,
                    "n": len(vals),
                    "mean": s["mean"],
                    "std": s["std"],
                })
    return rows


def compute_efficiency(records: Dict[Key, Dict[str, Any]]) -> Dict[str, Any]:
    # cost + latency summaries
    def mode_values(mode: str, extractor) -> List[float]:
        vals = []
        for k, rec in records.items():
            if k.mode != mode:
                continue
            v = extractor(rec)
            if v is None:
                continue
            vals.append(float(v))
        return vals

    # cost
    llm_cost = mode_values("llm", extract_cost_usd)
    agent_cost = mode_values("agent", extract_cost_usd)

    # latency
    llm_lat = mode_values("llm", extract_latency_ms)
    agent_lat = mode_values("agent", extract_latency_ms)

    cost_block = {
        "by_mode": {
            "llm": {"metric": "estimated_cost_usd", **summarize_numeric(llm_cost)} if llm_cost else {"metric": "estimated_cost_usd", **summarize_numeric([])},
            "agent": {"metric": "estimated_cost_usd", **summarize_numeric(agent_cost)} if agent_cost else {"metric": "estimated_cost_usd", **summarize_numeric([])}
        }
    }
    lat_block = {
        "by_mode": {
            "llm": {"metric": "latency_ms", **summarize_numeric(llm_lat)} if llm_lat else {"metric": "latency_ms", **summarize_numeric([])},
            "agent": {"metric": "latency_ms", **summarize_numeric(agent_lat)} if agent_lat else {"metric": "latency_ms", **summarize_numeric([])}
        }
    }

    # cache + refine rates if present
    def rate(mode: str, field: str) -> Optional[float]:
        flags = []
        for k, rec in records.items():
            if k.mode != mode:
                continue
            v = safe_get(rec, "metadata", field, default=None)
            if isinstance(v, bool):
                flags.append(1.0 if v else 0.0)
            elif v in (0, 1):
                flags.append(float(v))
        if not flags:
            return None
        return statistics.fmean(flags)

    agent_cache_hit = rate("agent", "cache_hit")

    cache_block = {}
    if agent_cache_hit is not None:
        cache_block["agent_cache_hit_rate"] = agent_cache_hit

    return {
        "cost": cost_block,
        "latency": lat_block,
        "retrieval": {},
        "cache": cache_block,
    }


def build_artifacts_block(run_dir: str) -> Dict[str, Any]:
    return {
        "tables": [
            {
                "id": "T1_main_metrics",
                "title": "Main metrics (mean±std) for LLM vs Agent",
                "suggested_columns": ["metric", "llm_mean", "llm_std", "agent_mean", "agent_std", "delta", "p_value", "cohens_d"]
            },
            {
                "id": "T2_cost_latency",
                "title": "Cost & latency comparison",
                "suggested_columns": ["mode", "mean_cost_usd", "mean_latency_ms", "p75_latency_ms"]
            }
        ],
        "figures": [
            {
                "id": "F1_by_turn_faithfulness",
                "title": "Faithfulness by turn (LLM vs Agent)",
                "plot_type": "line",
                "x": "turn",
                "y": "mean_faithfulness",
                "group": "mode"
            },
            {
                "id": "F2_metric_deltas",
                "title": "Paired deltas (Agent-LLM) with 95% CI",
                "plot_type": "bar_ci",
                "x": "metric",
                "y": "delta_mean",
                "ci": "ci95"
            }
        ],
        "paths": {
            "events_jsonl": os.path.join(run_dir, "events.jsonl"),
            "node_trace_jsonl": os.path.join(run_dir, "node_trace.jsonl"),
            "retrieval_snapshot_dir": os.path.join(run_dir, "retrieval_snapshot")
        }
    }


# -------------------------
# Main
# -------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="e.g., runs/2025-12-13_primary_v1")
    ap.add_argument("--metrics", default=",".join(DEFAULT_MAIN_METRICS),
                    help="comma-separated metrics to summarize (default: common set)")
    ap.add_argument("--out", default=None, help="output summary.json path (default: <run_dir>/summary.json)")
    ap.add_argument("--pretty", action="store_true", help="pretty-print json with indent=2")
    args = ap.parse_args()

    run_dir = args.run_dir
    events_path = os.path.join(run_dir, "events.jsonl")

    if not os.path.exists(events_path):
        raise FileNotFoundError(f"events.jsonl not found: {events_path}")

    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]
    if not metrics:
        metrics = DEFAULT_MAIN_METRICS

    # 1) pick final records per key
    records = pick_final_records(events_path)

    # counts
    base_keys_llm = set((k.patient_id, k.turn_id, k.question_id) for k in records if k.mode == "llm")
    base_keys_agent = set((k.patient_id, k.turn_id, k.question_id) for k in records if k.mode == "agent")
    completed_pairs = len(base_keys_llm.intersection(base_keys_agent))

    # mode metrics
    mode_rows_llm = build_mode_metric_rows(records, "llm", metrics)
    mode_rows_agent = build_mode_metric_rows(records, "agent", metrics)

    # paired comparisons
    comparisons = build_paired_comparisons(records, metrics)

    # breakdowns
    by_turn = breakdown_by_turn(records, metrics)

    efficiency = compute_efficiency(records)

    summary = {
        "schema_version": "summary.v1",
        "run_id": os.path.basename(os.path.normpath(run_dir)),
        "created_at_utc": utc_now_iso(),

        "inputs": {
            "events_jsonl": events_path,
        },

        "counts": {
            "total_events": sum(1 for _ in read_jsonl(events_path)),
            "completed_pairs": completed_pairs,
        },

        "metrics": {
            "by_mode": {
                "llm": {"n": len(base_keys_llm), "metric_rows": mode_rows_llm},
                "agent": {"n": len(base_keys_agent), "metric_rows": mode_rows_agent}
            }
        },

        "comparisons": {
            "paired_agent_minus_llm": comparisons
        },

        "breakdowns": {
            "by_turn": by_turn,
        },

        "efficiency": {
            "cost": efficiency["cost"],
            "latency": efficiency["latency"],
            "retrieval": efficiency.get("retrieval", {}),
            "cache": efficiency.get("cache", {})
        },

        "quality_gates": {
            "note": "Add self-refine and judge metrics if available in events.jsonl"
        },

        "artifacts": build_artifacts_block(run_dir)
    }
    
    # 멀티턴 컨텍스트 지표 통합 (선택적)
    if multiturn_metrics_available:
        try:
            metrics_summary = read_json(metrics_summary_path)
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
        except Exception as e:
            print(f"[WARNING] 멀티턴 컨텍스트 지표 통합 실패: {e}")

    out_path = args.out or os.path.join(run_dir, "summary.json")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        if args.pretty:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        else:
            json.dump(summary, f, ensure_ascii=False)
    print(f"[OK] wrote: {out_path}")


if __name__ == "__main__":
    main()
