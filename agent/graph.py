"""
LangGraph 워크플로우 정의
- 7개 노드로 구성된 최소 그래프
- 순환 구조 (Self-Refine 루프)
"""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.extract_slots import extract_slots_node
from agent.nodes.store_memory import store_memory_node
from agent.nodes.assemble_context import assemble_context_node
from agent.nodes.retrieve import retrieve_node
from agent.nodes.generate_answer import generate_answer_node
from agent.nodes.refine import refine_node
from agent.nodes.quality_check import quality_check_node
from core.config import get_agent_config

# 그래프 캐시 (성능 최적화)
_agent_graph_cache = None


def build_agent_graph():
    """
    Agent 그래프 빌드
    
    Returns:
        컴파일된 LangGraph
    """
    # StateGraph 생성
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("extract_slots", extract_slots_node)
    workflow.add_node("store_memory", store_memory_node)
    workflow.add_node("assemble_context", assemble_context_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("refine", refine_node)
    workflow.add_node("quality_check", quality_check_node)
    
    # 엣지 추가
    workflow.set_entry_point("extract_slots")
    workflow.add_edge("extract_slots", "store_memory")
    workflow.add_edge("store_memory", "assemble_context")
    workflow.add_edge("assemble_context", "retrieve")
    workflow.add_edge("retrieve", "generate_answer")
    workflow.add_edge("generate_answer", "refine")
    
    # 조건부 엣지 (품질 검사)
    workflow.add_conditional_edges(
        "refine",
        quality_check_node,
        {
            "retrieve": "retrieve",  # 재검색
            END: END  # 종료
        }
    )
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


def get_agent_graph():
    """
    Agent 그래프 가져오기 (캐싱)
    
    Returns:
        컴파일된 LangGraph (재사용)
    """
    global _agent_graph_cache
    if _agent_graph_cache is None:
        _agent_graph_cache = build_agent_graph()
    return _agent_graph_cache


def run_agent(
    user_text: str,
    mode: str = 'ai_agent',
    conversation_history: str = None,
    session_state: dict = None,
    feature_overrides: dict = None,
    return_state: bool = False
) -> str:
    """
    Agent 실행
    
    Args:
        user_text: 사용자 입력
        mode: 'llm' 또는 'ai_agent'
        conversation_history: 대화 이력 (멀티턴 대화용)
    
    Returns:
        생성된 답변
    """
    # 기능 플래그 로드 및 병합 (on/off 실험 지원)
    agent_config = get_agent_config()
    feature_flags = (agent_config.get('features') or {}).copy()
    if feature_overrides:
        feature_flags.update(feature_overrides)

    # 초기 상태 (세션 상태가 있으면 병합)
    initial_state = {
        'user_text': user_text,
        'mode': mode,
        'conversation_history': conversation_history,
        'slot_out': {},
        'profile_summary': '',
        'retrieved_docs': [],
        'query_vector': [],
        'system_prompt': '',
        'user_prompt': '',
        'answer': '',
        'quality_score': 0.0,
        'needs_retrieval': False,
        'iteration_count': 0,
        'feature_flags': feature_flags,
        'active_route': 'default',
        'query_for_retrieval': user_text,
        'agent_config': agent_config,
    }

    if session_state:
        initial_state.update(session_state)
    
    # 그래프 실행 (캐싱된 그래프 재사용)
    app = get_agent_graph()
    final_state = app.invoke(initial_state)
    
    if return_state:
        return final_state
    return final_state.get('answer', '')

