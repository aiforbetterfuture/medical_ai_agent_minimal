"""
Hierarchical Memory Ablation Study 테스트 스크립트

3-tier Hierarchical Memory의 효과를 측정합니다.

사용법:
    # 베이스라인 (Hierarchical Memory OFF)
    python experiments/test_hierarchical_memory.py --mode baseline

    # 처리 (Hierarchical Memory ON)
    python experiments/test_hierarchical_memory.py --mode treatment

    # 비교
    python experiments/test_hierarchical_memory.py --mode compare \
        --baseline baseline.json --treatment treatment.json
"""

import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent
from agent.metrics.ablation_metrics import AblationMetrics, compare_experiments


DEFAULT_MULTITURN_SCENARIO = [
    # Turn 1: 초기 증상
    "최근 두통과 어지러움이 자주 있어요.",

    # Turn 2: 추가 정보
    "고혈압 진단 받은 지 5년 됐고, 당뇨병도 3년 전부터 있습니다.",

    # Turn 3: 약물 정보
    "메트포르민 500mg을 하루 2번 먹고, 아스피린도 먹고 있어요.",

    # Turn 4: 알레르기
    "참고로 페니실린 알레르기가 있습니다.",

    # Turn 5: 복잡한 질문 (여기서 압축 발생)
    "최근 가슴이 답답하고 숨이 찬 증상도 있는데 어떤 검사를 받아야 하나요?",

    # Turn 6: 후속 질문 (Tier 2 컨텍스트 활용)
    "혈압약을 추가로 먹어야 할까요?",

    # Turn 7: 장기 정보 활용 (Tier 3 컨텍스트 활용)
    "제 만성질환 때문에 특별히 주의해야 할 음식이 있나요?"
]


def run_multiturn_experiment(
    mode: str,
    turns: list,
    experiment_name: str = None
):
    """멀티턴 실험 실행"""
    if experiment_name is None:
        experiment_name = f"hierarchical_memory_{mode}"

    # Feature flags 설정
    if mode == "baseline":
        feature_overrides = {
            'hierarchical_memory_enabled': False
        }
        print("\n" + "="*60)
        print("BASELINE (Hierarchical Memory: OFF)")
        print("="*60 + "\n")
    elif mode == "treatment":
        feature_overrides = {
            'hierarchical_memory_enabled': True,
            'working_memory_capacity': 5,
            'compression_threshold': 5
        }
        print("\n" + "="*60)
        print("TREATMENT (Hierarchical Memory: ON)")
        print("="*60 + "\n")
    else:
        raise ValueError(f"Invalid mode: {mode}")

    # 메트릭 수집
    metrics = AblationMetrics(experiment_name=experiment_name)

    # 세션 상태 (멀티턴 유지)
    session_state = None
    conversation_history = ""

    for idx, query in enumerate(turns, 1):
        print(f"\n[Turn {idx}/{len(turns)}] Query: {query}")
        print("-" * 60)

        try:
            import time
            start_time = time.time()

            final_state = run_agent(
                user_text=query,
                mode='ai_agent',
                conversation_history=conversation_history,
                session_state=session_state,
                feature_overrides=feature_overrides,
                return_state=True
            )

            end_time = time.time()

            # 세션 상태 업데이트 (메모리 유지)
            if feature_overrides.get('hierarchical_memory_enabled'):
                # Hierarchical Memory는 state 내부에 저장됨
                session_state = {
                    'hierarchical_memory': final_state.get('hierarchical_memory'),
                    'profile_store': final_state.get('profile_store'),
                }
            else:
                # 베이스라인은 ProfileStore만 유지
                session_state = {
                    'profile_store': final_state.get('profile_store'),
                }

            # 대화 이력 업데이트
            answer = final_state.get('answer', 'N/A')
            conversation_history += f"User: {query}\nAssistant: {answer}\n\n"

            query_metrics = metrics.record_query(
                state=final_state,
                start_time=start_time,
                end_time=end_time
            )

            print(f"Answer: {answer[:80]}...")
            print(f"Latency: {query_metrics.total_latency_ms:.2f}ms")
            print(f"Quality: {query_metrics.quality_score:.3f}")

            if mode == "treatment":
                if query_metrics.hierarchical_memory_enabled:
                    print(f"Hierarchical Memory: ENABLED")
                    print(f"  Total Turns: {query_metrics.total_turns}")
                    print(f"  Working Memory: {query_metrics.working_memory_size} turns")
                    print(f"  Compressed Memory: {query_metrics.compressed_memory_count} summaries")
                    print(f"  Semantic Conditions: {query_metrics.semantic_conditions_count}")
                    print(f"  Semantic Medications: {query_metrics.semantic_medications_count}")
                else:
                    print(f"Hierarchical Memory: NOT YET INITIALIZED")

        except Exception as e:
            print(f"[ERROR] Turn failed: {e}")
            import traceback
            traceback.print_exc()

    # 통계
    print("\n" + "="*60)
    print("EXPERIMENT SUMMARY")
    print("="*60)

    stats = metrics.calculate_statistics()

    print(f"\nTotal Turns: {stats['total_queries']}")
    print(f"Avg Latency: {stats['avg_latency_ms']:.2f}ms")
    print(f"Avg Cost: ${stats['avg_cost_usd']:.6f}")
    print(f"Avg Quality: {stats['avg_quality_score']:.3f}")

    if mode == "treatment":
        print(f"\nHierarchical Memory Stats:")
        print(f"  Enabled Rate: {stats['hierarchical_memory_enabled_rate']*100:.1f}%")
        print(f"  Avg Working Memory Size: {stats['avg_working_memory_size']:.1f} turns")
        print(f"  Avg Compressed Memory: {stats['avg_compressed_memory_count']:.1f} summaries")
        print(f"  Avg Semantic Conditions: {stats['avg_semantic_conditions']:.1f}")
        print(f"  Avg Semantic Medications: {stats['avg_semantic_medications']:.1f}")

    filepath = metrics.save_results()
    print(f"\nResults saved to: {filepath}")
    print("="*60 + "\n")

    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="Hierarchical Memory Ablation Study")

    parser.add_argument('--mode', choices=['baseline', 'treatment', 'compare'], required=True)
    parser.add_argument('--queries', type=str, help="Path to queries file")
    parser.add_argument('--baseline', type=str, help="Baseline JSON path (for compare)")
    parser.add_argument('--treatment', type=str, help="Treatment JSON path (for compare)")
    parser.add_argument('--name', type=str, help="Experiment name")

    args = parser.parse_args()

    if args.mode in ['baseline', 'treatment']:
        if args.queries:
            with open(args.queries, 'r', encoding='utf-8') as f:
                queries = [line.strip() for line in f if line.strip()]
        else:
            queries = DEFAULT_MULTITURN_SCENARIO

        run_multiturn_experiment(
            mode=args.mode,
            turns=queries,
            experiment_name=args.name
        )

    elif args.mode == 'compare':
        if not args.baseline or not args.treatment:
            print("Error: --baseline and --treatment required for compare mode")
            sys.exit(1)

        compare_experiments(
            baseline_path=args.baseline,
            treatment_path=args.treatment,
            output_path="experiments/ablation/hierarchical_memory_comparison.json"
        )


if __name__ == "__main__":
    main()
