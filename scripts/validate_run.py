#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_run.py
- Validate that a run directory is "paper-ready" for reproducible reporting.
- Performs:
  1) Presence checks: events.jsonl (required)
  2) Field/type sanity checks for events.jsonl (streaming)
  3) Pairing sanity: (patient_id, turn_id, question_id) exists for both llm & agent (at least some)
  4) run_id consistency

No external deps.
Exit code: 0 if OK, 2 if validation failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"JSONL parse error: {path}:{i}: {e}") from e


def is_str(x: Any) -> bool:
    return isinstance(x, str) and len(x) > 0


def is_intlike(x: Any) -> bool:
    if isinstance(x, int):
        return True
    if isinstance(x, str):
        try:
            int(x)
            return True
        except Exception:
            return False
    return False


def to_int(x: Any) -> Optional[int]:
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        try:
            return int(x)
        except Exception:
            return None
    return None


def fail(msg: str, errors: List[str]) -> None:
    errors.append(msg)


@dataclass(frozen=True)
class BaseKey:
    patient_id: str
    turn_id: int
    question_id: str


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="runs/<run_id>")
    ap.add_argument("--max_lines", type=int, default=0, help="debug: validate only first N lines (0=all)")
    args = ap.parse_args()

    run_dir = args.run_dir
    events_path = os.path.join(run_dir, "events.jsonl")

    errors: List[str] = []
    warns: List[str] = []

    if not os.path.isdir(run_dir):
        print(f"[FAIL] run_dir not found: {run_dir}")
        return 2

    if not os.path.exists(events_path):
        fail(f"missing events.jsonl: {events_path}", errors)

    # Run-id checks
    expected_run_id = os.path.basename(os.path.normpath(run_dir))

    # Validate events.jsonl streaming
    base_keys_llm: Set[BaseKey] = set()
    base_keys_agent: Set[BaseKey] = set()
    total = 0
    bad = 0

    REQUIRED_FIELDS = ["run_id", "mode", "patient_id", "turn_id", "question"]
    ALLOWED_MODES = {"llm", "agent"}

    if os.path.exists(events_path):
        try:
            for e in read_jsonl(events_path):
                total += 1
                if args.max_lines and total > args.max_lines:
                    break

                # required fields
                for f in REQUIRED_FIELDS:
                    if f not in e:
                        bad += 1
                        fail(f"events.jsonl line#{total}: missing field '{f}'", errors)
                        break

                mode = e.get("mode")
                if mode not in ALLOWED_MODES:
                    bad += 1
                    fail(f"events.jsonl line#{total}: invalid mode={mode}", errors)
                    continue

                if not is_str(e.get("patient_id")):
                    bad += 1
                    fail(f"events.jsonl line#{total}: invalid patient_id={e.get('patient_id')}", errors)
                    continue

                if not is_intlike(e.get("turn_id")):
                    bad += 1
                    fail(f"events.jsonl line#{total}: invalid turn_id={e.get('turn_id')}", errors)
                    continue

                question = e.get("question")
                if not isinstance(question, dict):
                    bad += 1
                    fail(f"events.jsonl line#{total}: question must be dict, got={type(question).__name__}", errors)
                    continue

                question_id = question.get("question_id")
                if not is_str(question_id):
                    bad += 1
                    fail(f"events.jsonl line#{total}: invalid question_id={question_id}", errors)
                    continue

                turn_id = to_int(e.get("turn_id"))
                if turn_id is None or turn_id <= 0:
                    bad += 1
                    fail(f"events.jsonl line#{total}: turn_id must be positive int, got={e.get('turn_id')}", errors)
                    continue

                # run_id consistency (warn only)
                e_run_id = e.get("run_id")
                if is_str(expected_run_id) and is_str(e_run_id) and e_run_id != expected_run_id:
                    warns.append(f"events.jsonl line#{total}: run_id differs from directory ({e_run_id} vs {expected_run_id})")

                # pairing key capture
                bk = BaseKey(
                    patient_id=e["patient_id"],
                    turn_id=turn_id,
                    question_id=question_id,
                )
                if mode == "llm":
                    base_keys_llm.add(bk)
                else:
                    base_keys_agent.add(bk)

                # minimal type sanity for common blocks (warn only)
                usage = e.get("usage")
                if usage is not None and not isinstance(usage, dict):
                    warns.append(f"events.jsonl line#{total}: usage should be dict, got={type(usage).__name__}")

        except Exception as ex:
            fail(f"failed reading events.jsonl: {ex}", errors)

    paired = base_keys_llm.intersection(base_keys_agent)
    if total == 0:
        fail("events.jsonl has 0 valid lines", errors)
    if len(paired) == 0:
        fail("no paired keys between llm and agent found (cannot do fair comparison)", errors)

    # Report
    if warns:
        print("[WARN]")
        for w in warns[:50]:
            print(" -", w)
        if len(warns) > 50:
            print(f" - ... ({len(warns)-50} more)")

    if errors:
        print("[FAIL] validation errors:")
        for e in errors[:200]:
            print(" -", e)
        if len(errors) > 200:
            print(f" - ... ({len(errors)-200} more)")
        print(f"[STATS] total_lines={total}, bad_lines={bad}, llm_keys={len(base_keys_llm)}, agent_keys={len(base_keys_agent)}, paired={len(paired)}")
        return 2

    print(f"[OK] validation passed. total_lines={total}, llm_keys={len(base_keys_llm)}, agent_keys={len(base_keys_agent)}, paired={len(paired)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
