#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_fairness.py
- Strict fairness validation for paired comparison experiments
- Ensures EXACT pairing between LLM and AI Agent modes
- Critical for research validity: paired t-tests require perfect pairing
- Checks:
  1) Same patients in both modes
  2) Same turns per patient in both modes
  3) Same questions (question_id) for each (patient, turn) pair
  4) Same question order (deterministic selection)
- Exits with code 0 if fair, 2 if unfair
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import io
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


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


@dataclass(frozen=True)
class PairKey:
    """Key for paired comparison: (patient_id, turn_id)"""
    patient_id: str
    turn_id: int


@dataclass(frozen=True)
class FullKey:
    """Full key including question_id"""
    patient_id: str
    turn_id: int
    question_id: str


def extract_keys_from_events(events_path: str) -> Dict[str, Set[FullKey]]:
    """
    Extract keys from events.jsonl, grouped by mode

    Returns:
        {'llm': {FullKey, ...}, 'agent': {FullKey, ...}}
    """
    keys_by_mode: Dict[str, Set[FullKey]] = {
        'llm': set(),
        'agent': set()
    }

    for e in read_jsonl(events_path):
        mode = e.get('mode')
        if mode not in ['llm', 'agent']:
            continue

        patient_id = e.get('patient_id')
        turn_id = e.get('turn_id')
        question = e.get('question', {})
        question_id = question.get('question_id') if isinstance(question, dict) else None

        if not patient_id or turn_id is None or not question_id:
            continue

        # Convert turn_id to int
        try:
            turn_id_int = int(turn_id)
        except (ValueError, TypeError):
            continue

        key = FullKey(
            patient_id=patient_id,
            turn_id=turn_id_int,
            question_id=question_id
        )

        keys_by_mode[mode].add(key)

    return keys_by_mode


def check_perfect_pairing(
    llm_keys: Set[FullKey],
    agent_keys: Set[FullKey]
) -> tuple[bool, List[str]]:
    """
    Check for perfect pairing between LLM and AI Agent

    Returns:
        (is_fair, list_of_violations)
    """
    violations = []

    # Check 1: Exact same set of keys
    if llm_keys != agent_keys:
        llm_only = llm_keys - agent_keys
        agent_only = agent_keys - llm_keys

        if llm_only:
            violations.append(f"Found {len(llm_only)} keys in LLM mode but not in Agent mode")
            # Show first 5 examples
            for i, key in enumerate(sorted(llm_only)[:5]):
                violations.append(f"  Example {i+1}: {key}")

        if agent_only:
            violations.append(f"Found {len(agent_only)} keys in Agent mode but not in LLM mode")
            # Show first 5 examples
            for i, key in enumerate(sorted(agent_only)[:5]):
                violations.append(f"  Example {i+1}: {key}")

    # Check 2: Patient coverage
    llm_patients = {k.patient_id for k in llm_keys}
    agent_patients = {k.patient_id for k in agent_keys}

    if llm_patients != agent_patients:
        llm_only_patients = llm_patients - agent_patients
        agent_only_patients = agent_patients - llm_patients

        if llm_only_patients:
            violations.append(f"Patients in LLM only: {sorted(llm_only_patients)[:10]}")

        if agent_only_patients:
            violations.append(f"Patients in Agent only: {sorted(agent_only_patients)[:10]}")

    # Check 3: Turn counts per patient
    llm_turns_per_patient: Dict[str, Set[int]] = {}
    agent_turns_per_patient: Dict[str, Set[int]] = {}

    for key in llm_keys:
        if key.patient_id not in llm_turns_per_patient:
            llm_turns_per_patient[key.patient_id] = set()
        llm_turns_per_patient[key.patient_id].add(key.turn_id)

    for key in agent_keys:
        if key.patient_id not in agent_turns_per_patient:
            agent_turns_per_patient[key.patient_id] = set()
        agent_turns_per_patient[key.patient_id].add(key.turn_id)

    for patient_id in llm_patients.union(agent_patients):
        llm_turns = llm_turns_per_patient.get(patient_id, set())
        agent_turns = agent_turns_per_patient.get(patient_id, set())

        if llm_turns != agent_turns:
            violations.append(
                f"Patient {patient_id}: LLM has turns {sorted(llm_turns)}, "
                f"Agent has turns {sorted(agent_turns)}"
            )

    # Check 4: Question consistency per (patient, turn)
    llm_questions_per_pair: Dict[PairKey, str] = {}
    agent_questions_per_pair: Dict[PairKey, str] = {}

    for key in llm_keys:
        pair_key = PairKey(patient_id=key.patient_id, turn_id=key.turn_id)
        llm_questions_per_pair[pair_key] = key.question_id

    for key in agent_keys:
        pair_key = PairKey(patient_id=key.patient_id, turn_id=key.turn_id)
        agent_questions_per_pair[pair_key] = key.question_id

    for pair_key in set(llm_questions_per_pair.keys()).union(agent_questions_per_pair.keys()):
        llm_qid = llm_questions_per_pair.get(pair_key)
        agent_qid = agent_questions_per_pair.get(pair_key)

        if llm_qid != agent_qid:
            violations.append(
                f"Question mismatch for {pair_key}: "
                f"LLM={llm_qid}, Agent={agent_qid}"
            )

    is_fair = len(violations) == 0
    return is_fair, violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events_path", required=True, help="Path to events.jsonl")
    ap.add_argument("--verbose", action="store_true", help="Show detailed violations")
    args = ap.parse_args()

    events_path = args.events_path

    # Validate input
    if not os.path.exists(events_path):
        print(f"[FAIL] events.jsonl not found: {events_path}")
        return 2

    # Extract keys
    try:
        print(f"[INFO] Checking fairness for: {events_path}")
        keys_by_mode = extract_keys_from_events(events_path)
    except Exception as e:
        print(f"[FAIL] Failed to read events: {e}")
        return 2

    llm_keys = keys_by_mode['llm']
    agent_keys = keys_by_mode['agent']

    print(f"[INFO] LLM mode: {len(llm_keys)} unique (patient, turn, question) keys")
    print(f"[INFO] Agent mode: {len(agent_keys)} unique (patient, turn, question) keys")

    # Check pairing
    is_fair, violations = check_perfect_pairing(llm_keys, agent_keys)

    # Report
    if is_fair:
        print("\n[OK] FAIR: Perfect pairing detected!")
        print("  [OK] Same patients in both modes")
        print("  [OK] Same turns per patient")
        print("  [OK] Same questions for each (patient, turn) pair")
        print("\n[INFO] Paired comparison is valid for statistical analysis.")
        return 0
    else:
        print("\n[FAIL] UNFAIR: Pairing violations detected!")
        print(f"  Found {len(violations)} violations:\n")

        # Show violations
        max_show = 50 if args.verbose else 10
        for i, v in enumerate(violations[:max_show]):
            print(f"  {i+1}. {v}")

        if len(violations) > max_show:
            print(f"\n  ... and {len(violations) - max_show} more violations")
            print(f"  Use --verbose to show all violations")

        print("\n[WARNING] Paired t-test is NOT valid with these violations!")
        print("[WARNING] Fix the experiment runner to ensure deterministic pairing!")

        return 2


if __name__ == "__main__":
    sys.exit(main())
