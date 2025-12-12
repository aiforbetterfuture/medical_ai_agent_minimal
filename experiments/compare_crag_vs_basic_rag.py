"""
CRAG vs Basic RAG 비교 실험 스크립트

목적:
- CRAG의 효과를 정량적으로 측정
- Basic RAG와의 성능 차이 분석
- Ablation Study 데이터 수집

실험 설정:
- Baseline: Basic RAG (refine_strategy='basic_rag')
- Treatment: Corrective RAG (refine_strategy='corrective_rag')
- 동일한 쿼리 세트로 비교
"""

import json
import time
from typing import List, Dict, Any
from agent.graph import run_agent


# 실험용 쿼리 세트 (의료 도메인)
TEST_QUERIES = [
    # 간단한 쿼리
    "당뇨병이란 무엇인가요?",
    "혈압 정상 범위를 알려주세요.",

    # 중간 복잡도 쿼리
    "당뇨병 환자가 주의해야 할 음식은 무엇인가요?",
    "고혈압 약을 복용 중인데 부작용이 있나요?",

    # 복잡한 쿼리 (개인화 필요)
    "65세 남성, 당뇨병과 고혈압이 있는데 메트포르민과 아스피린을 함께 복용해도 되나요?",
    "임신 중인데 혈당이 높게 나왔어요. 어떻게 관리해야 하나요?",

    # 모호한 쿼리 (재검색 필요 가능성 높음)
    "약 먹고 어지러운데 괜찮을까요?",
    "최근 피로하고 목이 자주 마른데 당뇨일까요?",
]


def run_experiment_single_query(
    query: str,
    strategy: str,
    feature_overrides: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    단일 쿼리 실험 실행

    Args:
        query: 사용자 쿼리
        strategy: 'corrective_rag' 또는 'basic_rag'
        feature_overrides: 추가 feature flags

    Returns:
        실험 결과 딕셔너리
    """
    # 기본 설정
    base_flags = {
        'refine_strategy': strategy,
        'self_refine_enabled': True,
        'quality_check_enabled': True,
    }

    # 추가 설정 병합
    if feature_overrides:
        base_flags.update(feature_overrides)

    # 시작 시간
    start_time = time.time()

    # Agent 실행 (상태 전체 반환)
    try:
        final_state = run_agent(
            user_text=query,
            mode='ai_agent',
            feature_overrides=base_flags,
            return_state=True
        )
        success = True
        error = None
    except Exception as e:
        print(f"[ERROR] 쿼리 실행 실패: {e}")
        final_state = {}
        success = False
        error = str(e)

    # 종료 시간
    end_time = time.time()
    latency = end_time - start_time

    # 결과 추출
    result = {
        # 메타데이터
        'query': query,
        'strategy': strategy,
        'success': success,
        'error': error,
        'latency_seconds': latency,

        # 답변 정보
        'answer': final_state.get('answer', ''),
        'answer_length': len(final_state.get('answer', '')),

        # 품질 정보
        'quality_score': final_state.get('quality_score', 0.0),
        'quality_score_history': final_state.get('quality_score_history', []),
        'quality_feedback': final_state.get('quality_feedback', {}),

        # 검색 정보
        'num_docs': len(final_state.get('retrieved_docs', [])),
        'iteration_count': final_state.get('iteration_count', 0),
        'retrieved_docs_history': final_state.get('retrieved_docs_history', []),

        # 재작성 정보
        'query_rewrite_history': final_state.get('query_rewrite_history', []),

        # Iteration 로그
        'refine_iteration_logs': final_state.get('refine_iteration_logs', []),

        # 메트릭
        'refine_metrics': final_state.get('refine_metrics', {}),
    }

    return result


def run_experiment_batch(
    queries: List[str],
    strategies: List[str] = ['basic_rag', 'corrective_rag']
) -> Dict[str, List[Dict[str, Any]]]:
    """
    배치 실험 실행

    Args:
        queries: 쿼리 리스트
        strategies: 비교할 전략 리스트

    Returns:
        전략별 결과 딕셔너리
    """
    results = {strategy: [] for strategy in strategies}

    total = len(queries) * len(strategies)
    current = 0

    for query in queries:
        for strategy in strategies:
            current += 1
            print(f"\n{'='*80}")
            print(f"[{current}/{total}] 실험 중...")
            print(f"쿼리: {query}")
            print(f"전략: {strategy}")
            print(f"{'='*80}\n")

            result = run_experiment_single_query(query, strategy)
            results[strategy].append(result)

            # 간단한 요약 출력
            print(f"\n[결과 요약]")
            print(f"  - 품질 점수: {result['quality_score']:.2f}")
            print(f"  - 답변 길이: {result['answer_length']}자")
            print(f"  - 반복 횟수: {result['iteration_count']}회")
            print(f"  - 지연 시간: {result['latency_seconds']:.2f}초")

    return results


def calculate_metrics(results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, float]]:
    """
    전략별 평균 메트릭 계산

    Args:
        results: 전략별 결과

    Returns:
        전략별 평균 메트릭
    """
    metrics = {}

    for strategy, result_list in results.items():
        # 성공한 쿼리만 분석
        successful_results = [r for r in result_list if r['success']]

        if not successful_results:
            metrics[strategy] = {
                'success_rate': 0.0,
                'error': 'No successful queries'
            }
            continue

        # 평균 계산
        metrics[strategy] = {
            'success_rate': len(successful_results) / len(result_list) * 100,
            'avg_quality_score': sum(r['quality_score'] for r in successful_results) / len(successful_results),
            'avg_answer_length': sum(r['answer_length'] for r in successful_results) / len(successful_results),
            'avg_iteration_count': sum(r['iteration_count'] for r in successful_results) / len(successful_results),
            'avg_latency': sum(r['latency_seconds'] for r in successful_results) / len(successful_results),
            'avg_num_docs': sum(r['num_docs'] for r in successful_results) / len(successful_results),
            'total_queries': len(result_list),
            'successful_queries': len(successful_results),
        }

    return metrics


def print_comparison_table(metrics: Dict[str, Dict[str, float]]):
    """
    비교 표 출력

    Args:
        metrics: 전략별 메트릭
    """
    print("\n" + "="*100)
    print("CRAG vs Basic RAG 비교 결과")
    print("="*100)

    print(f"\n{'메트릭':<30} {'Basic RAG':>20} {'Corrective RAG':>20} {'차이 (%)':>20}")
    print("-"*100)

    basic = metrics.get('basic_rag', {})
    crag = metrics.get('corrective_rag', {})

    # 각 메트릭 비교
    metric_names = {
        'success_rate': '성공률 (%)',
        'avg_quality_score': '평균 품질 점수',
        'avg_answer_length': '평균 답변 길이 (자)',
        'avg_iteration_count': '평균 반복 횟수',
        'avg_latency': '평균 지연 시간 (초)',
        'avg_num_docs': '평균 문서 개수',
    }

    for key, name in metric_names.items():
        basic_val = basic.get(key, 0)
        crag_val = crag.get(key, 0)

        if basic_val > 0:
            diff_pct = ((crag_val - basic_val) / basic_val) * 100
        else:
            diff_pct = 0.0

        print(f"{name:<30} {basic_val:>20.2f} {crag_val:>20.2f} {diff_pct:>+19.1f}%")

    print("="*100)


def save_results(
    results: Dict[str, List[Dict[str, Any]]],
    metrics: Dict[str, Dict[str, float]],
    output_file: str = 'experiments/crag_vs_basic_rag_results.json'
):
    """
    결과 저장

    Args:
        results: 전략별 결과
        metrics: 전략별 메트릭
        output_file: 출력 파일 경로
    """
    output = {
        'experiment_name': 'CRAG vs Basic RAG Comparison',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'metrics': metrics,
        'detailed_results': results,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[결과 저장] {output_file}")


def main():
    """
    메인 실험 실행
    """
    print("CRAG vs Basic RAG 비교 실험 시작")
    print(f"총 {len(TEST_QUERIES)}개 쿼리 × 2개 전략 = {len(TEST_QUERIES) * 2}회 실행")

    # 실험 실행
    results = run_experiment_batch(
        queries=TEST_QUERIES,
        strategies=['basic_rag', 'corrective_rag']
    )

    # 메트릭 계산
    metrics = calculate_metrics(results)

    # 결과 출력
    print_comparison_table(metrics)

    # 결과 저장
    save_results(results, metrics)

    print("\n실험 완료!")


if __name__ == '__main__':
    main()
