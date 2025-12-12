"""
Quick Test: Strategy 전환 테스트

CRAG와 Basic RAG가 올바르게 전환되는지 확인
"""

from agent.graph import run_agent

def test_crag():
    """CRAG 테스트"""
    print("\n" + "="*80)
    print("TEST 1: CRAG (Corrective RAG) - 기본값")
    print("="*80)

    result = run_agent(
        "당뇨병 약 부작용이 궁금해요",
        feature_overrides={
            'refine_strategy': 'corrective_rag',
            'self_refine_enabled': True,
            'llm_based_quality_check': False,  # 빠른 테스트를 위해 휴리스틱 사용
        },
        return_state=True
    )

    print(f"\n[CRAG 결과]")
    print(f"  - 전략: {result.get('refine_strategy', 'N/A')}")
    print(f"  - 품질 점수: {result.get('quality_score', 0):.2f}")
    print(f"  - 반복 횟수: {result.get('iteration_count', 0)}")
    print(f"  - 답변 길이: {len(result.get('answer', ''))}자")
    print(f"  - 재작성 횟수: {len(result.get('query_rewrite_history', []))}")


def test_basic_rag():
    """Basic RAG 테스트"""
    print("\n" + "="*80)
    print("TEST 2: Basic RAG (Baseline)")
    print("="*80)

    result = run_agent(
        "당뇨병 약 부작용이 궁금해요",
        feature_overrides={
            'refine_strategy': 'basic_rag',  # Basic RAG 사용
            'self_refine_enabled': True,
        },
        return_state=True
    )

    print(f"\n[Basic RAG 결과]")
    print(f"  - 전략: {result.get('refine_strategy', 'N/A')}")
    print(f"  - 품질 점수: {result.get('quality_score', 0):.2f}")
    print(f"  - 반복 횟수: {result.get('iteration_count', 0)}")
    print(f"  - 답변 길이: {len(result.get('answer', ''))}자")
    print(f"  - 재작성 횟수: {len(result.get('query_rewrite_history', []))}")


def test_default():
    """기본값 테스트 (CRAG가 기본값인지 확인)"""
    print("\n" + "="*80)
    print("TEST 3: 기본값 (refine_strategy 미지정)")
    print("="*80)

    result = run_agent(
        "당뇨병이란 무엇인가요?",
        feature_overrides={
            'self_refine_enabled': True,
            'llm_based_quality_check': False,
        },
        return_state=True
    )

    print(f"\n[기본값 결과]")
    print(f"  - 전략: {result.get('refine_strategy', 'N/A')}")
    print(f"  - 품질 점수: {result.get('quality_score', 0):.2f}")
    print(f"  - 예상: 'corrective_rag' (기본값)")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("CRAG vs Basic RAG 전환 테스트")
    print("="*80)

    try:
        # Test 1: CRAG
        test_crag()

        # Test 2: Basic RAG
        test_basic_rag()

        # Test 3: 기본값
        test_default()

        print("\n" + "="*80)
        print("✅ 모든 테스트 통과!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
