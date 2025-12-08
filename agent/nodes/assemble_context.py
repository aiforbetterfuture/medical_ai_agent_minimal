"""
노드 3: 컨텍스트 조립
"""

from agent.state import AgentState
from core.prompts import build_system_prompt, format_user_prompt


def assemble_context_node(state: AgentState) -> AgentState:
    """
    컨텍스트 조립 노드
    
    슬롯 정보를 프롬프트에 주입합니다.
    mode에 따라 다른 프롬프트를 사용합니다.
    멀티턴 대화를 위해 conversation_history를 포함합니다.
    """
    print("[Node] assemble_context")
    
    mode = state.get('mode', 'ai_agent')
    conversation_history = state.get('conversation_history')
    
    # LLM 모드: 간단한 프롬프트만 사용
    if mode == 'llm':
        system_prompt = build_system_prompt(mode='llm')
        # 대화 이력이 있으면 포함
        user_prompt = format_user_prompt(
            state['user_text'],
            conversation_history=conversation_history
        )
    else:
        # AI Agent 모드: 기존 로직
        profile_summary = state.get('profile_summary', '')
        retrieved_docs = state.get('retrieved_docs', [])
        
        # 검색된 문서 포맷팅
        docs_text = ""
        if retrieved_docs:
            docs_text = "\n\n".join([
                f"[문서 {i+1}]\n{doc.get('text', '')}"
                for i, doc in enumerate(retrieved_docs[:5])
            ])
        
        # 시스템 프롬프트 생성
        system_prompt = build_system_prompt(
            mode='ai_agent',
            include_personalization=True,
            profile_summary=profile_summary,
            include_evidence=len(retrieved_docs) > 0,
            retrieved_docs=docs_text
        )
        
        # 사용자 프롬프트 생성 (대화 이력 포함)
        user_prompt = format_user_prompt(
            state['user_text'],
            conversation_history=conversation_history
        )
    
    return {
        **state,
        'system_prompt': system_prompt,
        'user_prompt': user_prompt
    }

