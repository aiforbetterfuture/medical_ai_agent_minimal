"""
Context Compression Ablation Study 테스트 스크립트

Active Retrieval과 함께 Context Compression의 효과를 측정합니다.

사용법:
    # 베이스라인 (압축 OFF)
    python experiments/test_context_compression.py --mode baseline

    # 압축 ON (extractive)
    python experiments/test_context_compression.py --mode treatment --strategy extractive

    # 압축 ON (hybrid)
    python experiments/test_context_compression.py --mode treatment --strategy hybrid

    # 비교
    python experiments/test_context_compression.py --mode compare \
        --baseline baseline.json --treatment treatment.json
"""

import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent
from agent.metrics.ablation_metrics import AblationMetrics, compare_experiments


DEFAULT_TEST_QUERIES = [
    # 간단한 질문 (압축 효과 낮음)
    "정상 혈압 범위는?",
    "당뇨병이란?",

    # 보통 복잡도 (압축 효과 보통)
    "65세 남성, 혈압 140/90인데 위험한가요?",
    "두통과 어지러움이 있는데 무슨 병인가요?",
    "당뇨 약과 고혈압 약을 같이 먹어도 되나요?",

    # 복잡한 질문 (압축 효과 높음 - 많은 문서 검색됨)
    "65세 남성, 당뇨병 10년, 고혈압 5년 환자입니다. 최근 두통, 어지러움, 가슴 답답함이 있고, 메트포르민과 아스피린을 복용 중입니다. 어떤 검사를 받아야 하나요?",
    "HbA1c 8.5%, 공복혈당 180, 혈압 150/95, BMI 28인 환자의 치료 계획은?",
]


def run_experiment(
    mode: str,
    queries: list,
    strategy: str = 'extractive',
    experiment_name: str = None
):
    """실험 실행"""
    if experiment_name is None:
        experiment_name = f"context_compression_{mode}_{strategy}"

    # Feature flags 설정
    if mode == "baseline":
        feature_overrides = {
            'context_compression_enabled': False
        }
        print("\n" + "="*60)
        print("BASELINE (Context Compression: OFF)")
        print("="*60 + "\n")
    elif mode == "treatment":
        feature_overrides = {
            'context_compression_enabled': True,
            'compression_strategy': strategy
        }
        print("\n" + "="*60)
        print(f"TREATMENT (Context Compression: ON - {strategy.upper()})")
        print("="*60 + "\n")
    else:
        raise ValueError(f"Invalid mode: {mode}")

    # 메트릭 수집
    metrics = AblationMetrics(experiment_name=experiment_name)

    for idx, query in enumerate(queries, 1):
        print(f"\n[{idx}/{len(queries)}] Query: {query}")
        print("-" * 60)

        try:
            import time
            start_time = time.time()

            final_state = run_agent(
                user_text=query,
                mode='ai_agent',
                feature_overrides=feature_overrides,
                return_state=True
            )

            end_time = time.time()

            query_metrics = metrics.record_query(
                state=final_state,
                start_time=start_time,
                end_time=end_time
            )

            print(f"Answer: {final_state.get('answer', 'N/A')[:80]}...")
            print(f"Latency: {query_metrics.total_latency_ms:.2f}ms")
            print(f"Quality: {query_metrics.quality_score:.3f}")

            if mode == "treatment":
                if query_metrics.compression_applied:
                    print(f"Compression Applied: YES")
                    print(f"  Strategy: {query_metrics.compression_strategy}")
                    print(f"  Original Tokens: {query_metrics.original_doc_tokens}")
                    print(f"  Compressed Tokens: {query_metrics.compressed_doc_tokens}")
                    print(f"  Compression Ratio: {query_metrics.compression_ratio:.2%}")
                    print(f"  Tokens Saved: {query_metrics.tokens_saved_by_compression}")
                else:
                    print(f"Compression Applied: NO (within budget)")

        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            import traceback
            traceback.print_exc()

    # 통계
    print("\n" + "="*60)
    print("EXPERIMENT SUMMARY")
    print("="*60)

    stats = metrics.calculate_statistics()

    print(f"\nTotal Queries: {stats['total_queries']}")
    print(f"Avg Latency: {stats['avg_latency_ms']:.2f}ms")
    print(f"Avg Cost: ${stats['avg_cost_usd']:.6f}")
    print(f"Avg Quality: {stats['avg_quality_score']:.3f}")

    if mode == "treatment":
        print(f"\nCompression Stats:")
        print(f"  Applied Count: {stats['compression_applied_count']}")
        print(f"  Compression Rate: {stats['compression_rate']*100:.1f}%")
        print(f"  Avg Compression Ratio: {stats['avg_compression_ratio']:.2%}")
        print(f"  Total Tokens Saved: {stats['total_tokens_saved_by_compression']}")

    filepath = metrics.save_results()
    print(f"\nResults saved to: {filepath}")
    print("="*60 + "\n")

    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="Context Compression Ablation Study")

    parser.add_argument('--mode', choices=['baseline', 'treatment', 'compare'], required=True)
    parser.add_argument('--strategy', choices=['extractive', 'abstractive', 'hybrid'], default='extractive')
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
            queries = DEFAULT_TEST_QUERIES

        run_experiment(
            mode=args.mode,
            queries=queries,
            strategy=args.strategy,
            experiment_name=args.name
        )

    elif args.mode == 'compare':
        if not args.baseline or not args.treatment:
            print("Error: --baseline and --treatment required for compare mode")
            sys.exit(1)

        compare_experiments(
            baseline_path=args.baseline,
            treatment_path=args.treatment,
            output_path="experiments/ablation/compression_comparison.json"
        )


if __name__ == "__main__":
    main()
