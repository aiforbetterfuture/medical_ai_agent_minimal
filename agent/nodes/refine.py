"""
노드 6: Self-Refine
"""

from agent.state import AgentState
from core.utils import is_llm_mode


def refine_node(state: AgentState) -> AgentState:
    """
    Self-Refine 노드
    
    생성된 답변의 품질을 검증합니다.
    LLM 모드에서는 품질 검증을 건너뛰고 바로 통과시킵니다.
    """
    print("[Node] refine")
    
    feature_flags = state.get('feature_flags', {})
    self_refine_enabled = feature_flags.get('self_refine_enabled', True)

    # LLM 모드 또는 셀프 리파인 비활성화: 품질 검증 건너뛰기
    if is_llm_mode(state) or not self_refine_enabled:
        return {
            **state,
            'quality_score': 1.0,
            'needs_retrieval': False
        }
    
    answer = state.get('answer', '')
    retrieved_docs = state.get('retrieved_docs', [])
    
    # 간단한 품질 평가
    # 1. 답변 길이 체크
    length_score = min(len(answer) / 500, 1.0)  # 500자 이상이면 1.0
    
    # 2. 근거 문서 존재 여부
    evidence_score = 1.0 if len(retrieved_docs) > 0 else 0.0
    
    # 3. 개인화 정보 포함 여부
    profile_summary = state.get('profile_summary', '')
    personalization_score = 1.0 if profile_summary else 0.0
    
    # 전체 품질 점수 (가중 평균)
    quality_score = (
        length_score * 0.3 +
        evidence_score * 0.4 +
        personalization_score * 0.3
    )
    
    # 재검색 필요 여부 결정 (최대 횟수는 기능 플래그 기준)
    max_iter = feature_flags.get('max_refine_iterations', 2)
    needs_retrieval = (
        quality_score < 0.5 and
        state.get('iteration_count', 0) < max_iter
    )
    
    return {
        **state,
        'quality_score': quality_score,
        'needs_retrieval': needs_retrieval
    }

