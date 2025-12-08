"""
Streamlit 웹 인터페이스
의학지식 AI Agent 대화형 UI (멀티턴 대화 지원)
"""

import streamlit as st
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.graph import run_agent, build_agent_graph
from agent.state import AgentState


# 페이지 설정
st.set_page_config(
    page_title="의학지식 AI Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []  # [{"role": "user"|"assistant", "content": "..."}]
if 'agent_graph' not in st.session_state:
    st.session_state.agent_graph = None


def initialize_agent():
    """Agent 그래프 초기화"""
    if st.session_state.agent_graph is None:
        try:
            st.session_state.agent_graph = build_agent_graph()
        except Exception as e:
            st.error(f"Agent 초기화 실패: {e}")
            return None
    return st.session_state.agent_graph


def format_conversation_history(messages: list) -> str:
    """
    대화 이력을 프롬프트용 텍스트로 포맷팅
    
    Args:
        messages: [{"role": "user"|"assistant", "content": "..."}, ...]
    
    Returns:
        포맷팅된 대화 이력 문자열
    """
    if not messages:
        return None
    
    history_lines = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            history_lines.append(f"사용자: {content}")
        elif role == "assistant":
            history_lines.append(f"AI: {content}")
    
    return "\n".join(history_lines)


def main():
    """메인 함수"""
    st.title("🏥 의학지식 AI Agent")
    st.markdown("---")
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        mode = st.selectbox(
            "모드 선택",
            ["ai_agent", "llm"],
            index=0,
            help="ai_agent: 전체 워크플로우 실행, llm: LLM만 사용"
        )
        
        st.markdown("---")
        st.header("📋 대화 관리")
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown(f"**대화 수:** {len([m for m in st.session_state.messages if m['role'] == 'user'])}")
        
        st.markdown("---")
        with st.expander("ℹ️ 사용 방법"):
            st.markdown("""
            ### 사용 방법
            
            1. **질문 입력**: 하단 입력창에 의학 관련 질문을 입력하세요.
            2. **모드 선택**: 
               - `ai_agent`: 전체 워크플로우 실행
               - `llm`: LLM만 사용
            3. **연속 대화**: 이전 대화 내용을 기억하여 연속적인 대화가 가능합니다.
            
            ### 주요 기능
            
            - **멀티턴 대화**: 이전 대화 내용을 기억하여 맥락 있는 답변 제공
            - **슬롯 추출**: 사용자 입력에서 의학 정보 추출
            - **하이브리드 검색**: BM25 + FAISS 검색
            - **개인화 답변**: 환자 정보 기반 맞춤 답변
            """)
        
        with st.expander("⚠️ 주의사항"):
            st.warning("""
            이 시스템은 의료 진단이나 치료를 대체하지 않습니다.
            응급 상황에서는 즉시 의료진에게 연락하세요.
            """)
    
    # 메인 채팅 영역
    # 대화 이력 표시
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("의학 관련 질문을 입력하세요..."):
        # 사용자 메시지 추가 및 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하는 중..."):
                try:
                    # 대화 이력 포맷팅 (현재 질문 제외)
                    conversation_history = format_conversation_history(
                        st.session_state.messages[:-1]  # 현재 질문 제외
                    )
                    
                    # Agent 실행
                    answer = run_agent(
                        user_text=prompt,
                        mode=mode,
                        conversation_history=conversation_history
                    )
                    
                    # AI 메시지 추가 및 표시
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
                except Exception as e:
                    error_msg = f"오류 발생: {e}"
                    st.error(error_msg)
                    st.exception(e)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # 푸터
    st.markdown("---")
    st.caption("의학지식 AI Agent v1.0 | 멀티턴 대화 지원 | Context Engineering 기반")


if __name__ == "__main__":
    main()

