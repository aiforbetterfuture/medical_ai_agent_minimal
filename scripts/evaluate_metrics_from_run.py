#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
멀티턴 컨텍스트 평가 지표 계산 스크립트

events.jsonl에서 레코드를 빌드하고, CUS, UR, CCR 지표를 계산합니다.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple, Optional, DefaultDict
from collections import defaultdict
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiments.evaluation.build_records import build_records_from_events
from experiments.evaluation.multiturn_context_metrics import (
    compute_cus,
    compute_ur,
    ccr_rule_checks,
)
from experiments.evaluation.question_bank_mapper import get_question_metadata
from experiments.evaluation.io.jsonl import write_jsonl


def read_json(path: str) -> Dict[str, Any]:
    """JSON 파일 읽기"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def mean(xs: List[float]) -> Optional[float]:
    """평균 계산 (None 값 제외)"""
    xs2 = [x for x in xs if x is not None]
    if not xs2:
        return None
    return sum(xs2) / len(xs2)


def load_patient_map(run_dir: str) -> Dict[str, Any]:
    """환자 프로필 맵 로드"""
    # run_dir에서 우선 찾기, 없으면 프로젝트 루트에서 찾기
    cand = os.path.join(run_dir, "patient_list_80.json")
    if os.path.exists(cand):
        return read_json(cand)
    
    # 프로젝트 루트에서 찾기
    root_cand = os.path.join(project_root, "data", "patients", "patient_list_80.json")
    if os.path.exists(root_cand):
        return read_json(root_cand)
    
    raise FileNotFoundError("patient_list_80.json not found (expected in run_dir or data/patients)")


def load_question_bank(run_dir: str) -> Dict[str, Any]:
    """질문은행 로드"""
    # run_dir에서 우선 찾기, 없으면 프로젝트 루트에서 찾기
    cand = os.path.join(run_dir, "question_bank_5x15.v1.json")
    if os.path.exists(cand):
        return read_json(cand)
    
    # 프로젝트 루트에서 찾기
    root_cand = os.path.join(project_root, "experiments", "question_bank", "question_bank_5x15.v1.json")
    if os.path.exists(root_cand):
        return read_json(root_cand)
    
    raise FileNotFoundError("question_bank_5x15.v1.json not found (expected in run_dir or experiments/question_bank)")


def qb_lookup(qb: Dict[str, Any], q_id: str) -> Dict[str, Any]:
    """질문은행에서 질문 항목 찾기"""
    for it in qb.get("items", []):
        if it.get("id") == q_id:
            return it
    return {}


def main():
    ap = argparse.ArgumentParser(
        description="멀티턴 컨텍스트 평가 지표 계산"
    )
    ap.add_argument("--run_dir", required=True, help="실험 실행 디렉토리 (예: runs/2025-12-13_primary_v1)")
    ap.add_argument("--out_dir", default=None, help="출력 디렉토리 (기본값: run_dir/eval)")
    ap.add_argument("--use_llm_judge", action="store_true", help="LLM Judge 사용 (현재는 룰 기반만 지원)")
    args = ap.parse_args()
    
    run_dir = args.run_dir
    out_dir = args.out_dir or os.path.join(run_dir, "eval")
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"[INFO] 레코드 빌드 중: {run_dir}")
    records = build_records_from_events(run_dir)
    print(f"[INFO] {len(records)}개 레코드 로드 완료")
    
    print(f"[INFO] 환자 프로필 로드 중...")
    patient_map = load_patient_map(run_dir)
    print(f"[INFO] {len(patient_map)}개 환자 프로필 로드 완료")
    
    print(f"[INFO] 질문은행 로드 중...")
    qb = load_question_bank(run_dir)
    print(f"[INFO] {len(qb.get('items', []))}개 질문 항목 로드 완료")
    
    per_record_rows: List[Dict[str, Any]] = []
    
    for rec in records:
        q = rec.get("question_text") or ""
        a = rec.get("answer_text") or ""
        docs = rec.get("retrieved_docs") or []
        slots_state = rec.get("slots_state") or {}
        turn_updates = rec.get("turn_updates") or {}
        pid = rec["patient_id"]
        mode = rec["mode"]
        turn = int(rec["turn"])
        q_id = str(rec["q_id"])
        
        # 질문은행에서 메타데이터 가져오기 (질문 텍스트를 전달하여 구체적인 update_key 추출)
        qb_item = qb_lookup(qb, q_id)
        qb_metadata = get_question_metadata(qb_item, question_text=q)
        required_slots = qb_metadata.get("required_slots", [])
        update_key = qb_metadata.get("update_key")
        
        # 환자 프로필 가져오기
        patient_profile = patient_map.get(pid, {})
        
        # ---- 2층 지표 계산 (멀티턴 컨텍스트 전용)
        cus = compute_cus(a, required_slots, patient_profile, slots_state)
        ur = compute_ur(a, update_key, turn_updates, question_text=q) if update_key else {
            "metric": "UR",
            "applicable": False,
            "score": None,
            "notes": "no update_key in question bank"
        }
        
        # CCR 계산 (룰 기반, LLM Judge는 선택적)
        ccr_rule = ccr_rule_checks(a, slots_state)
        
        # LLM Judge 사용 여부 (환경 변수 또는 설정 파일에서 읽기)
        use_llm_judge = os.getenv("USE_LLM_JUDGE_CCR", "false").lower() == "true"
        if use_llm_judge:
            try:
                from experiments.evaluation.llm_judge_ccr import ccr_hybrid
                ccr_result = ccr_hybrid(
                    answer=a,
                    slots_state=slots_state,
                    question=q,
                    turn_updates=turn_updates,
                    use_llm_judge=True
                )
                # LLM Judge 결과를 사용하되, 룰 기반 결과도 보존
                ccr_rule = {
                    **ccr_result,
                    "rule_based": ccr_rule,  # 룰 기반 결과도 포함
                }
            except ImportError:
                # LLM Judge 모듈이 없으면 룰 기반만 사용
                pass
        
        row = {
            "run_id": os.path.basename(run_dir),
            "patient_id": pid,
            "mode": mode,
            "turn": turn,
            "q_id": q_id,
            "metrics": {
                "CUS": cus["score"],
                "UR": ur["score"] if ur.get("applicable") else None,
                "CCR_rule_obvious": ccr_rule["score"],
            },
            "details": {
                "CUS": cus,
                "UR": ur,
                "CCR_rule_obvious": ccr_rule,
            },
        }
        
        per_record_rows.append(row)
    
    # ---- 레코드별 메트릭 저장
    per_record_path = os.path.join(out_dir, "metrics_per_record.jsonl")
    write_jsonl(per_record_path, per_record_rows)
    print(f"[OK] 레코드별 메트릭 저장: {per_record_path}")
    
    # ---- 집계: 모드별 / 턴별
    agg: Dict[str, Any] = {"by_mode": {}, "by_mode_turn": {}}
    by_mode: DefaultDict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    by_mode_turn: DefaultDict[Tuple[str, int], Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    
    for r in per_record_rows:
        mode = r["mode"]
        turn = int(r["turn"])
        for m, v in r["metrics"].items():
            if v is None:
                continue
            by_mode[mode][m].append(float(v))
            by_mode_turn[(mode, turn)][m].append(float(v))
    
    for mode, md in by_mode.items():
        agg["by_mode"][mode] = {m: mean(vals) for m, vals in md.items()}
    
    for (mode, turn), md in by_mode_turn.items():
        agg["by_mode_turn"].setdefault(mode, {})
        agg["by_mode_turn"][mode][str(turn)] = {m: mean(vals) for m, vals in md.items()}
    
    # ---- Paired delta (Agent - LLM) on same patient/turn/q_id
    llm_map = {}
    agent_map = {}
    for r in per_record_rows:
        k = (r["patient_id"], int(r["turn"]), str(r["q_id"]))
        if r["mode"] == "llm":
            llm_map[k] = r
        elif r["mode"] == "agent":
            agent_map[k] = r
    
    paired = []
    for k, ar in agent_map.items():
        lr = llm_map.get(k)
        if not lr:
            continue
        delta = {}
        for m in ar["metrics"].keys():
            av = ar["metrics"].get(m)
            lv = lr["metrics"].get(m)
            if av is None or lv is None:
                continue
            delta[m] = float(av) - float(lv)
        paired.append({"key": {"patient_id": k[0], "turn": k[1], "q_id": k[2]}, "delta": delta})
    
    # Paired mean 계산
    paired_mean: Dict[str, Optional[float]] = {}
    per_metric: DefaultDict[str, List[float]] = defaultdict(list)
    for p in paired:
        for m, dv in p["delta"].items():
            per_metric[m].append(dv)
    for m, vals in per_metric.items():
        paired_mean[m] = mean(vals)
    
    agg["paired_agent_minus_llm_mean"] = paired_mean
    agg["n_records"] = len(per_record_rows)
    agg["n_paired"] = len(paired)
    
    # ---- 요약 저장
    summary_path = os.path.join(out_dir, "metrics_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(agg, f, ensure_ascii=False, indent=2)
    print(f"[OK] 요약 저장: {summary_path}")
    
    # ---- 요약 출력
    print("\n" + "="*80)
    print("평가 지표 요약")
    print("="*80)
    print(f"총 레코드 수: {agg['n_records']}")
    print(f"Paired 레코드 수: {agg['n_paired']}")
    print("\n모드별 평균:")
    for mode, metrics in agg["by_mode"].items():
        print(f"  [{mode.upper()}]")
        for m, v in metrics.items():
            if v is not None:
                print(f"    {m}: {v:.3f}")
    print("\nPaired Delta (Agent - LLM):")
    for m, v in paired_mean.items():
        if v is not None:
            print(f"  {m}: {v:+.3f}")
    print("="*80)


if __name__ == "__main__":
    main()

