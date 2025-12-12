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
if 'profile_store' not in st.session_state:
    # LangGraph 실행 결과로 전달되는 ProfileStore 객체를 유지해 멀티턴에서도 누적
    st.session_state.profile_store = None


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


def _extract_profile_snapshot(profile_store):
    """
    ProfileStore에서 UI용 스냅샷 추출
    """
    if not profile_store:
        return {
            "gender_age": "정보 없음",
            "conditions": [],
            "symptoms": [],
            "vitals": [],
            "labs": [],
            "medications": [],
        }
    
    ltm = profile_store.ltm
    gender = ltm.demographics.get("gender", "")
    age = ltm.demographics.get("age", "")
    gender_age = f"{age}세 / {gender}" if (gender or age) else "정보 없음"

    def _dedup_latest(items, key):
        seen = set()
        out = []
        for it in reversed(items):  # 최신순 역순 → 중복 제거 후 다시 뒤집기
            k = key(it)
            if k in seen:
                continue
            seen.add(k)
            out.append(it)
        return list(reversed(out))

    conditions = [c.name for c in _dedup_latest(ltm.conditions, lambda x: x.name) if c.name]
    symptoms = [
        f"{s.name}{' (부정)' if s.negated else ''}"
        for s in _dedup_latest(ltm.symptoms, lambda x: (x.name, x.negated))
        if s.name
    ]
    vitals = [
        f"{v.name}: {v.value}{v.unit}".strip()
        for v in _dedup_latest(ltm.vitals, lambda x: (x.name, x.value, x.unit))
        if v.name
    ]
    labs = [
        f"{l.name}: {l.value}{l.unit}".strip()
        for l in _dedup_latest(ltm.labs, lambda x: (x.name, x.value, x.unit))
        if l.name
    ]
    meds = [m.name for m in _dedup_latest(ltm.meds, lambda x: x.name) if m.name]

    return {
        "gender_age": gender_age,
        "conditions": conditions,
        "symptoms": symptoms,
        "vitals": vitals,
        "labs": labs,
        "medications": meds,
    }


def _render_tag_line(label: str, items: list):
    """간단한 태그형 표시"""
    if not items:
        st.markdown(f"**{label}**: 없음")
        return
    chips = " ".join([f"`{t}`" for t in items])
    st.markdown(f"**{label}**: {chips}")


def main():
    """메인 함수"""
    st.title("🏥 의학지식 AI Agent")
    st.markdown("---")
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 모드 선택")
        mode = st.selectbox(
            "모드",
            ["ai_agent", "llm"],
            index=0,
            help="ai_agent: 전체 워크플로우 실행, llm: LLM만 사용"
        )

        st.markdown("---")
        st.header("🧾 내 정보 (실시간)")
        snapshot = _extract_profile_snapshot(st.session_state.profile_store)
        st.markdown(f"**성별/나이:** {snapshot['gender_age']}")
        _render_tag_line("질환", snapshot["conditions"])
        _render_tag_line("증상", snapshot["symptoms"])
        _render_tag_line("약물", snapshot["medications"])
        _render_tag_line("활력징후", snapshot["vitals"])
        _render_tag_line("검사", snapshot["labs"])
        st.caption("잘못된 정보는 채팅창에서 바로잡아 주세요.")

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
                    
                    session_payload = {}
                    if st.session_state.profile_store is not None:
                        # LangGraph 상태에 기존 프로필을 전달해 멀티턴 누적
                        session_payload['profile_store'] = st.session_state.profile_store

                    # Agent 실행
                    final_state = run_agent(
                        user_text=prompt,
                        mode=mode,
                        conversation_history=conversation_history,
                        session_state=session_payload,
                        return_state=True
                    )

                    # 프로필 상태 업데이트 (사이드바 실시간 반영)
                    st.session_state.profile_store = final_state.get('profile_store', st.session_state.profile_store)
                    answer = final_state.get('answer', '')
                    
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

