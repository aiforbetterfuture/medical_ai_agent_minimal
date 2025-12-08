"""
노드 7: 품질 검사 및 재검색 결정
"""

from agent.state import AgentState
from langgraph.graph import END
from core.utils import is_llm_mode


def quality_check_node(state: AgentState) -> str:
    """
    품질 검사 노드
    
    품질이 낮으면 재검색, 높으면 종료합니다.
    LLM 모드에서는 항상 종료합니다.
    """
    print("[Node] quality_check")
    
    feature_flags = state.get('feature_flags', {})
    self_refine_enabled = feature_flags.get('self_refine_enabled', True)
    max_iter = feature_flags.get('max_refine_iterations', 2)

    # LLM 모드 또는 셀프 리파인 off: 항상 종료
    if is_llm_mode(state) or not self_refine_enabled:
        print("[Quality Check] 셀프 리파인 비활성 또는 LLM 모드: 종료")
        return END
    
    needs_retrieval = state.get('needs_retrieval', False)
    iteration_count = state.get('iteration_count', 0)
    
    if needs_retrieval and iteration_count < max_iter:
        # 재검색 루프
        print(f"[Quality Check] 품질 낮음 (점수: {state.get('quality_score', 0):.2f}), 재검색 수행")
        return "retrieve"  # retrieve 노드로 돌아감
    else:
        # 종료
        print(f"[Quality Check] 품질 양호 (점수: {state.get('quality_score', 0):.2f}), 종료")
        return END

