"""
Active Retrieval Ablation Study 테스트 스크립트

사용법:
    # 베이스라인 실험 (Active Retrieval OFF)
    python experiments/test_active_retrieval.py --mode baseline --queries queries.txt

    # 처리 실험 (Active Retrieval ON)
    python experiments/test_active_retrieval.py --mode treatment --queries queries.txt

    # 비교 분석
    python experiments/test_active_retrieval.py --mode compare --baseline baseline.json --treatment treatment.json
"""

import sys
import time
import argparse
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent
from agent.metrics.ablation_metrics import AblationMetrics, compare_experiments


# 테스트 쿼리 세트
DEFAULT_TEST_QUERIES = [
    # 인사/간단한 질문 (검색 불필요 - Active Retrieval로 스킵 가능)
    "안녕하세요",
    "네, 알겠습니다",
    "고맙습니다",

    # 간단한 사실 질문 (simple, k=3)
    "정상 혈압 범위는?",
    "당뇨병이란?",
    "아스피린 부작용은?",

    # 보통 복잡도 질문 (moderate, k=8)
    "65세 남성, 혈압 140/90인데 위험한가요?",
    "두통과 어지러움이 있는데 무슨 병인가요?",
    "당뇨 약과 고혈압 약을 같이 먹어도 되나요?",

    # 복잡한 질문 (complex, k=15)
    "65세 남성, 당뇨병 10년, 고혈압 5년 환자입니다. 최근 두통, 어지러움, 가슴 답답함이 있고, 메트포르민과 아스피린을 복용 중입니다. 어떤 검사를 받아야 하나요?",
    "HbA1c 8.5%, 공복혈당 180, 혈압 150/95, BMI 28인 환자의 치료 계획은?",
]


def run_experiment(
    mode: str,
    queries: list,
    experiment_name: str = None,
    save_dir: str = "experiments/ablation"
) -> str:
    """
    실험 실행

    Args:
        mode: 'baseline' (OFF) 또는 'treatment' (ON)
        queries: 테스트 쿼리 리스트
        experiment_name: 실험 이름 (기본값: active_retrieval_{mode})
        save_dir: 결과 저장 디렉토리

    Returns:
        저장된 JSON 파일 경로
    """
    if experiment_name is None:
        experiment_name = f"active_retrieval_{mode}"

    # Feature flags 설정
    if mode == "baseline":
        feature_overrides = {'active_retrieval_enabled': False}
        print("\n" + "="*60)
        print("BASELINE EXPERIMENT (Active Retrieval: OFF)")
        print("="*60 + "\n")
    elif mode == "treatment":
        feature_overrides = {'active_retrieval_enabled': True}
        print("\n" + "="*60)
        print("TREATMENT EXPERIMENT (Active Retrieval: ON)")
        print("="*60 + "\n")
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 'baseline' or 'treatment'")

    # 메트릭 수집기 초기화
    metrics = AblationMetrics(
        experiment_name=experiment_name,
        save_dir=save_dir
    )

    # 쿼리 실행
    for idx, query in enumerate(queries, 1):
        print(f"\n[{idx}/{len(queries)}] Query: {query}")
        print("-" * 60)

        try:
            # 시작 시간
            start_time = time.time()

            # Agent 실행
            final_state = run_agent(
                user_text=query,
                mode='ai_agent',
                feature_overrides=feature_overrides,
                return_state=True
            )

            # 종료 시간
            end_time = time.time()

            # 메트릭 기록
            query_metrics = metrics.record_query(
                state=final_state,
                start_time=start_time,
                end_time=end_time
            )

            # 결과 출력
            print(f"Answer: {final_state.get('answer', 'N/A')[:100]}...")
            print(f"Latency: {query_metrics.total_latency_ms:.2f}ms")
            print(f"Quality Score: {query_metrics.quality_score:.3f}")

            if mode == "treatment":
                print(f"Complexity: {query_metrics.query_complexity}")
                print(f"Retrieval Executed: {query_metrics.retrieval_executed}")
                print(f"Dynamic K: {query_metrics.dynamic_k}")

        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            import traceback
            traceback.print_exc()
            continue

    # 통계 계산 및 출력
    print("\n" + "="*60)
    print("EXPERIMENT SUMMARY")
    print("="*60)

    stats = metrics.calculate_statistics()

    print(f"\nTotal Queries: {stats['total_queries']}")
    print(f"Avg Latency: {stats['avg_latency_ms']:.2f}ms")
    print(f"P95 Latency: {stats['p95_latency_ms']:.2f}ms")
    print(f"Avg Cost: ${stats['avg_cost_usd']:.6f}")
    print(f"Total Cost: ${stats['total_cost_usd']:.4f}")
    print(f"Avg Quality: {stats['avg_quality_score']:.3f}")

    if mode == "treatment":
        print(f"\nRetrieval Skip Rate: {stats['retrieval_skip_rate']*100:.1f}%")
        print(f"Complexity Distribution:")
        for complexity, ratio in stats['complexity_distribution'].items():
            print(f"  {complexity}: {ratio*100:.1f}%")

    # 결과 저장
    filepath = metrics.save_results()

    print(f"\nResults saved to: {filepath}")
    print("="*60 + "\n")

    return str(filepath)


def run_comparison(baseline_path: str, treatment_path: str, output_dir: str = "experiments/ablation"):
    """
    두 실험 비교

    Args:
        baseline_path: 베이스라인 JSON 경로
        treatment_path: 처리 JSON 경로
        output_dir: 출력 디렉토리
    """
    output_path = Path(output_dir) / "comparison_result.json"

    comparison = compare_experiments(
        baseline_path=baseline_path,
        treatment_path=treatment_path,
        output_path=str(output_path)
    )

    print(f"\nComparison saved to: {output_path}")

    # 주요 결과 요약
    print("\n" + "="*60)
    print("KEY FINDINGS")
    print("="*60)

    metrics_of_interest = [
        ('avg_latency_ms', 'Average Latency', 'ms', 'lower_is_better'),
        ('p95_latency_ms', 'P95 Latency', 'ms', 'lower_is_better'),
        ('avg_cost_usd', 'Average Cost', '$', 'lower_is_better'),
        ('total_cost_usd', 'Total Cost', '$', 'lower_is_better'),
        ('avg_quality_score', 'Average Quality', '', 'higher_is_better'),
    ]

    for metric_key, metric_name, unit, direction in metrics_of_interest:
        if metric_key in comparison['metrics_comparison']:
            values = comparison['metrics_comparison'][metric_key]
            change = values['percent_change']

            if direction == 'lower_is_better':
                indicator = "✓" if change < 0 else "✗"
            else:
                indicator = "✓" if change > 0 else "✗"

            print(f"\n{indicator} {metric_name}:")
            print(f"  Baseline:  {values['baseline']:.4f}{unit}")
            print(f"  Treatment: {values['treatment']:.4f}{unit}")
            print(f"  Change:    {change:+.2f}%")

    print("\n" + "="*60)

    # 결론
    latency_improvement = comparison['metrics_comparison']['avg_latency_ms']['percent_change']
    cost_reduction = comparison['metrics_comparison']['avg_cost_usd']['percent_change']
    quality_change = comparison['metrics_comparison']['avg_quality_score']['percent_change']

    print("\nCONCLUSION:")
    if latency_improvement < -10 and cost_reduction < -10 and quality_change > -5:
        print("✓✓✓ Active Retrieval shows significant improvement!")
        print(f"  - {abs(latency_improvement):.1f}% faster")
        print(f"  - {abs(cost_reduction):.1f}% cheaper")
        print(f"  - Quality maintained (±{abs(quality_change):.1f}%)")
    elif latency_improvement < 0 and cost_reduction < 0:
        print("✓✓ Active Retrieval shows moderate improvement")
    else:
        print("✗ Active Retrieval needs tuning or may not be beneficial")

    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Active Retrieval Ablation Study")

    parser.add_argument(
        '--mode',
        choices=['baseline', 'treatment', 'compare'],
        required=True,
        help="Experiment mode"
    )

    parser.add_argument(
        '--queries',
        type=str,
        default=None,
        help="Path to queries file (one query per line). If not provided, uses default queries."
    )

    parser.add_argument(
        '--baseline',
        type=str,
        help="Path to baseline experiment JSON (for compare mode)"
    )

    parser.add_argument(
        '--treatment',
        type=str,
        help="Path to treatment experiment JSON (for compare mode)"
    )

    parser.add_argument(
        '--output',
        type=str,
        default="experiments/ablation",
        help="Output directory"
    )

    parser.add_argument(
        '--name',
        type=str,
        help="Experiment name"
    )

    args = parser.parse_args()

    # 쿼리 로드
    if args.mode in ['baseline', 'treatment']:
        if args.queries:
            with open(args.queries, 'r', encoding='utf-8') as f:
                queries = [line.strip() for line in f if line.strip()]
        else:
            queries = DEFAULT_TEST_QUERIES
            print(f"Using default test queries (n={len(queries)})")

        # 실험 실행
        run_experiment(
            mode=args.mode,
            queries=queries,
            experiment_name=args.name,
            save_dir=args.output
        )

    elif args.mode == 'compare':
        if not args.baseline or not args.treatment:
            print("Error: --baseline and --treatment are required for compare mode")
            sys.exit(1)

        run_comparison(
            baseline_path=args.baseline,
            treatment_path=args.treatment,
            output_dir=args.output
        )


if __name__ == "__main__":
    main()
