"""
멀티턴 벤치마크 스크립트
- synthetic_multiturn_train.jsonl 기반
- 기능 플래그 ablation: self-refine, memory, routing, medcat2
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent


def load_jsonl(path: Path, limit: int = None) -> List[Dict[str, Any]]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            if line.strip():
                data.append(json.loads(line))
    return data


def score_answer(answer: str, rubric: Dict[str, Any]) -> Dict[str, Any]:
    """단순 정밀도 점수: must_mention all 포함 && must_avoid 미포함"""
    answer_lower = answer.lower()
    must_mention = rubric.get("must_mention", [])
    must_avoid = rubric.get("must_avoid", [])

    mention_ok = all(m.lower() in answer_lower for m in must_mention)
    avoid_ok = not any(m.lower() in answer_lower for m in must_avoid)
    passed = mention_ok and avoid_ok

    return {
        "passed": passed,
        "mention_ok": mention_ok,
        "avoid_ok": avoid_ok,
    }


def run_scenario(scenario: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
    """시나리오 단위 실행 (모든 턴 순회)"""
    session_state = None
    conversation_history = ""
    answers = []

    for turn in scenario.get("turns", []):
        user_msg = turn.get("user_message", "")

        result_state = run_agent(
            user_msg,
            mode="ai_agent",
            conversation_history=conversation_history,
            session_state=session_state,
            feature_overrides=features,
            return_state=True,
        )
        answer = result_state.get("answer", "")
        answers.append(answer)

        # 대화 이력 업데이트
        conversation_history = (conversation_history + f"\nUser: {user_msg}\nAssistant: {answer}").strip()

        # 세션 상태 유지 (메모리/슬롯/프로필)
        session_state = {
            "profile_store": result_state.get("profile_store"),
            "profile_summary": result_state.get("profile_summary", ""),
            "conversation_history": conversation_history,
            "slot_out": result_state.get("slot_out", {}),
            "feature_flags": result_state.get("feature_flags", {}),
            "agent_config": result_state.get("agent_config", {}),
            "retriever_cache": result_state.get("retriever_cache", {}),
        }

    final_answer = answers[-1] if answers else ""
    rubric = scenario.get("rubric", {})
    score = score_answer(final_answer, rubric)
    score["last_answer"] = final_answer

    return score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(project_root / "data/labels/synthetic_multiturn_train.jsonl"),
        help="멀티턴 벤치마크 jsonl 경로",
    )
    parser.add_argument("--limit", type=int, default=20, help="평가 시나리오 개수 제한")
    parser.add_argument("--disable-self-refine", action="store_true")
    parser.add_argument("--disable-routing", action="store_true")
    parser.add_argument("--disable-medcat2", action="store_true")
    parser.add_argument("--memory-mode", type=str, default="structured", choices=["structured", "none"])
    parser.add_argument("--top-k", type=int, default=None)

    args = parser.parse_args()

    features = {}
    if args.disable_self_refine:
        features["self_refine_enabled"] = False
    if args.disable_routing:
        features["dynamic_rag_routing"] = False
    if args.disable_medcat2:
        features["medcat2_enabled"] = False
    if args.memory_mode:
        features["memory_mode"] = args.memory_mode
    if args.top_k:
        features["top_k"] = args.top_k

    dataset_path = Path(args.dataset)
    scenarios = load_jsonl(dataset_path, limit=args.limit)
    total = len(scenarios)

    passes = 0
    for scen in scenarios:
        res = run_scenario(scen, features)
        if res["passed"]:
            passes += 1

    pass_rate = passes / total if total else 0.0

    print("=" * 60)
    print(f"Dataset: {dataset_path.name} (n={total})")
    print(f"Features: {features}")
    print(f"Pass rate (must_mention & avoid): {pass_rate:.3f} ({passes}/{total})")
    print("Note: 단순 키워드 기준 평가이므로 정성 검토 병행 필요")


if __name__ == "__main__":
    main()

