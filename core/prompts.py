"""
시스템 프롬프트 템플릿
"""

from typing import Optional

# LLM 모드용 간단한 프롬프트 (원문 그대로 출력)
SYSTEM_PROMPT_LLM = "당신은 의료 정보 제공자입니다. 사용자 질의에 답변해주세요"

# AI Agent 모드용 기본 시스템 프롬프트
SYSTEM_PROMPT_BASE = """당신은 개인화된 의료 정보 전문가입니다. 다음 원칙들을 자연스럽게 답변에 반영하되, 소제목이나 번호를 사용하지 말고 자연스러운 문장으로 작성하세요:

- 환자의 구체적 상황(나이, 성별, 과거병력)을 분석하여 답변에 반영
- 증상의 의료적 의미와 메커니즘을 설명
- 단계별 대응 계획을 제시
- 위험 이유를 근거 기반으로 설명
- 환자의 불안감을 고려한 따뜻한 톤으로 설명

답변은 소제목, 번호, 카테고리 구분 없이 자연스러운 문단 형태로 작성하세요."""

# 개인화 프롬프트 템플릿
PERSONALIZATION_PROMPT_TEMPLATE = """
## 환자 정보
{profile_summary}

위 환자 정보를 바탕으로 개인화된 의학적 답변을 제공해주세요.
"""

# 근거 기반 프롬프트 템플릿
EVIDENCE_PROMPT_TEMPLATE = """
## 참고 문서
{retrieved_docs}

위 문서를 근거로 답변을 생성하되, 문서에 명시되지 않은 내용은 추측하지 마세요.
"""


def build_system_prompt(
    mode: str = 'ai_agent',
    include_personalization: bool = True,
    profile_summary: Optional[str] = None,
    include_evidence: bool = True,
    retrieved_docs: Optional[str] = None
) -> str:
    """
    시스템 프롬프트 생성
    
    Args:
        mode: 'llm' 또는 'ai_agent'
        include_personalization: 개인화 정보 포함 여부 (ai_agent 모드에서만 사용)
        profile_summary: 프로필 요약 (ai_agent 모드에서만 사용)
        include_evidence: 근거 문서 포함 여부 (ai_agent 모드에서만 사용)
        retrieved_docs: 검색된 문서 (ai_agent 모드에서만 사용)
    
    Returns:
        완성된 시스템 프롬프트
    """
    # LLM 모드: 간단한 프롬프트만 사용
    if mode == 'llm':
        return SYSTEM_PROMPT_LLM
    
    # AI Agent 모드: 기존 로직 사용
    prompt = SYSTEM_PROMPT_BASE
    
    if include_personalization and profile_summary:
        prompt += "\n\n" + PERSONALIZATION_PROMPT_TEMPLATE.format(
            profile_summary=profile_summary
        )
    
    if include_evidence and retrieved_docs:
        prompt += "\n\n" + EVIDENCE_PROMPT_TEMPLATE.format(
            retrieved_docs=retrieved_docs
        )
    
    return prompt


def format_user_prompt(user_text: str, conversation_history: Optional[str] = None) -> str:
    """
    사용자 프롬프트 포맷팅
    
    Args:
        user_text: 사용자 입력
        conversation_history: 대화 이력
    
    Returns:
        포맷팅된 사용자 프롬프트
    """
    if conversation_history:
        return f"""## 대화 이력
{conversation_history}

## 현재 질문
{user_text}"""
    else:
        return user_text

