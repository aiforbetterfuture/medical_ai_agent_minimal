"""
노드 2: 메모리 저장
"""

from agent.state import AgentState
from memory.profile_store import ProfileStore
from core.utils import is_llm_mode


def store_memory_node(state: AgentState) -> AgentState:
    """
    메모리 저장 노드
    
    추출된 슬롯을 프로필 저장소에 저장합니다.
    LLM 모드에서는 건너뜁니다.
    """
    print("[Node] store_memory")
    
    # LLM 모드: 메모리 저장 건너뛰기
    if is_llm_mode(state):
        return {
            **state,
            'profile_summary': ''
        }
    
    feature_flags = state.get('feature_flags', {})
    memory_mode = feature_flags.get('memory_mode', 'structured')

    if memory_mode == 'none':
        # 아예 메모리 저장 없이 진행 (ablations)
        return {
            **state,
            'profile_summary': ''
        }

    # 프로필 저장소 초기화 (첫 실행 시만)
    if 'profile_store' not in state:
        profile_store = ProfileStore()
        state['profile_store'] = profile_store
    else:
        profile_store = state['profile_store']
    
    # 슬롯 업데이트
    profile_store.update_slots(state['slot_out'])
    profile_store.apply_temporal_weights()
    
    # 프로필 요약 생성
    profile_summary = profile_store.get_profile_summary()
    
    return {
        **state,
        'profile_summary': profile_summary
    }

