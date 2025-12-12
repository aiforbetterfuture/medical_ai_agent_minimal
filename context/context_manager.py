"""
ContextManager: 계층형 컨텍스트를 토큰 예산 내에서 조합

본 스켈레톤은 기존 스캐폴드 무결성을 해치지 않는 최소 추가 설계입니다.
- 외부 저장소(session_repo, longterm_repo)가 없을 때도 동작하도록 선택적 의존성으로 처리
- conversation_history 문자열을 최근 대화 컨텍스트로 가볍게 잘라 사용
- profile_summary는 state에 있는 값을 그대로 활용
"""

from typing import Optional

from .token_manager import TokenManager


class ContextManager:
    def __init__(
        self,
        token_manager: TokenManager,
        session_repo=None,  # 선택적: 세션 메시지 저장소
        longterm_repo=None,  # 선택적: 장기 요약 저장소
    ):
        self.token_manager = token_manager
        self.session_repo = session_repo
        self.longterm_repo = longterm_repo

    def build_context(
        self,
        *,
        user_id: str = "anonymous",
        session_id: str = "session-default",
        current_query: str,
        conversation_history: Optional[str] = None,
        profile_summary: Optional[str] = None,
        longterm_summary: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> dict:
        """
        컨텍스트 조립 결과를 반환합니다.

        Returns:
            {
              "session_context": str,
              "profile_context": str,
              "longterm_context": str,
              "context_prompt": str,
              "token_plan": Dict[str, Any],
            }
        """
        # 외부 저장소가 없으면 state에서 전달된 값 사용
        profile_text = profile_summary or ""
        longterm_text = longterm_summary or ""

        # 토큰 플랜 계산
        plan = self.token_manager.make_plan(
            current_query=current_query,
            profile_summary=profile_text,
            longterm_summary=longterm_text,
            reserved_for_docs=900,
            reserved_for_system=400,
        )

        # 최근 대화 컨텍스트를 토큰 예산 내로 자르기
        session_context = self._clip_text(
            conversation_history or "",
            max_tokens=plan.for_recent,
        )

        # 최종 컨텍스트 프롬프트 구성
        context_prompt = self._assemble_prompt(
            profile_text,
            longterm_text,
            session_context,
        )

        return {
            "session_context": session_context,
            "profile_context": profile_text,
            "longterm_context": longterm_text,
            "context_prompt": context_prompt,
            "token_plan": plan.__dict__,
        }

    # 내부 유틸
    def _clip_text(self, text: str, max_tokens: int) -> str:
        """간단한 토큰 예산 내 자르기 (단어 단위)"""
        if not text or max_tokens <= 0:
            return ""
        tokens = text.split()
        # 근사치: 토큰 수는 단어 수로 간주
        clipped = tokens[-max_tokens:]
        return " ".join(clipped)

    def _assemble_prompt(
        self,
        profile_text: str,
        longterm_text: str,
        session_context: str,
    ) -> str:
        parts = []
        if profile_text:
            parts.append("【환자 프로필】\n" + profile_text)
        if longterm_text:
            parts.append("【장기 요약】\n" + longterm_text)
        if session_context:
            parts.append("【최근 대화】\n" + session_context)
        return "\n\n".join(parts)

