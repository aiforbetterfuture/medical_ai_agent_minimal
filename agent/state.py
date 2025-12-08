"""
AgentState 정의 (TypedDict)
"""

from typing import TypedDict, Annotated, Dict, Any, List, Optional
from operator import add


class AgentState(TypedDict):
    """
    LangGraph 에이전트 상태 정의
    
    모든 노드는 이 상태를 받아서 업데이트된 상태를 반환합니다.
    """
    # 입력
    user_text: str
    mode: str  # 'llm' 또는 'ai_agent'
    conversation_history: Optional[str]  # 대화 이력 (멀티턴 대화용)
    
    # 슬롯 추출 결과
    slot_out: Dict[str, Any]
    
    # 메모리
    profile_summary: str
    
    # 검색 관련
    retrieved_docs: Annotated[List[Dict[str, Any]], add]
    query_vector: List[float]  # 임베딩 벡터
    
    # 생성 관련
    system_prompt: str
    user_prompt: str
    answer: str
    
    # Self-Refine 관련
    quality_score: float
    needs_retrieval: bool
    iteration_count: int  # 재검색 횟수

    # 기능 플래그 / 라우팅
    feature_flags: Dict[str, Any]
    active_route: str
    query_for_retrieval: str
    agent_config: Dict[str, Any]

