"""
Context-aware Query Rewriter (동적 질의 재작성)

- 이전 답변과 품질 피드백을 반영하여 질의를 재작성
- 부족한 정보를 키워드로 추출하여 질의에 추가
- 사용자 맥락(프로필, 대화 이력)을 동적으로 반영
"""

from typing import Dict, Any, List, Optional
from core.llm_client import LLMClient


class QueryRewriter:
    """Context-aware 질의 재작성기"""

    def __init__(self, llm_client: LLMClient):
        """
        Args:
            llm_client: LLM 클라이언트 인스턴스
        """
        self.llm_client = llm_client

    def rewrite(
        self,
        original_query: str,
        quality_feedback: Dict[str, Any],
        previous_answer: str = "",
        profile_summary: str = "",
        slot_out: Optional[Dict[str, Any]] = None,
        iteration_count: int = 0
    ) -> str:
        """
        품질 피드백 기반 질의 재작성

        Args:
            original_query: 원본 사용자 질문
            quality_feedback: 품질 평가 결과 (missing_info, improvement_suggestions 포함)
            previous_answer: 이전 생성 답변
            profile_summary: 사용자 프로필 요약
            slot_out: 추출된 슬롯 정보
            iteration_count: 현재 iteration 횟수

        Returns:
            재작성된 질의 문자열
        """
        # 부족한 정보 추출
        missing_info = quality_feedback.get('missing_info', [])
        improvement_suggestions = quality_feedback.get('improvement_suggestions', [])

        # 간단한 휴리스틱 기반 재작성
        if not missing_info and not improvement_suggestions:
            # 피드백이 없으면 원본 질의 반환 (프로필 정보만 추가)
            return self._enhance_with_profile(original_query, profile_summary, slot_out)

        # LLM 기반 재작성 (더 정교한 질의 생성)
        try:
            rewritten_query = self._llm_based_rewrite(
                original_query=original_query,
                missing_info=missing_info,
                improvement_suggestions=improvement_suggestions,
                previous_answer=previous_answer,
                profile_summary=profile_summary,
                slot_out=slot_out,
                iteration_count=iteration_count
            )
            return rewritten_query
        except Exception as e:
            print(f"[ERROR] LLM 기반 질의 재작성 실패: {e}")
            import traceback
            traceback.print_exc()

            # 폴백: 휴리스틱 기반 재작성
            return self._fallback_rewrite(
                original_query, missing_info, profile_summary, slot_out
            )

    def _llm_based_rewrite(
        self,
        original_query: str,
        missing_info: List[str],
        improvement_suggestions: List[str],
        previous_answer: str,
        profile_summary: str,
        slot_out: Optional[Dict[str, Any]],
        iteration_count: int
    ) -> str:
        """LLM 기반 질의 재작성"""
        # 재작성 프롬프트 생성
        rewrite_prompt = self._build_rewrite_prompt(
            original_query=original_query,
            missing_info=missing_info,
            improvement_suggestions=improvement_suggestions,
            previous_answer=previous_answer,
            profile_summary=profile_summary,
            slot_out=slot_out,
            iteration_count=iteration_count
        )

        # LLM에게 재작성 요청
        rewritten_query = self.llm_client.generate(
            prompt=rewrite_prompt,
            system_prompt=self._get_system_prompt(),
            temperature=0.5,  # 적당한 창의성
            max_tokens=300
        )

        # 정제 (불필요한 설명 제거)
        rewritten_query = rewritten_query.strip()

        # "재작성된 질의:" 같은 프리픽스 제거
        for prefix in ["재작성된 질의:", "Rewritten Query:", "질의:"]:
            if rewritten_query.startswith(prefix):
                rewritten_query = rewritten_query[len(prefix):].strip()

        return rewritten_query

    def _build_rewrite_prompt(
        self,
        original_query: str,
        missing_info: List[str],
        improvement_suggestions: List[str],
        previous_answer: str,
        profile_summary: str,
        slot_out: Optional[Dict[str, Any]],
        iteration_count: int
    ) -> str:
        """재작성 프롬프트 생성"""
        prompt_parts = [
            "다음 의료 질의를 더 효과적인 검색을 위해 재작성해주세요.\n",
            f"**원본 질의:**\n{original_query}\n"
        ]

        if previous_answer:
            # 이전 답변은 너무 길 수 있으므로 요약
            answer_preview = previous_answer[:200] + "..." if len(previous_answer) > 200 else previous_answer
            prompt_parts.append(f"\n**이전 답변 (일부):**\n{answer_preview}\n")

        if missing_info:
            prompt_parts.append(
                f"\n**부족한 정보:**\n"
                f"{', '.join(missing_info)}\n"
            )

        if improvement_suggestions:
            prompt_parts.append(
                f"\n**개선 제안:**\n"
                f"{', '.join(improvement_suggestions)}\n"
            )

        if profile_summary:
            prompt_parts.append(f"\n**사용자 프로필:**\n{profile_summary}\n")

        if slot_out:
            # 슬롯 정보 추가 (간단히)
            demographics = slot_out.get('demographics', {})
            conditions = slot_out.get('conditions', [])
            medications = slot_out.get('medications', [])

            context_info = []
            if demographics.get('age'):
                context_info.append(f"나이: {demographics['age']}")
            if demographics.get('gender'):
                context_info.append(f"성별: {demographics['gender']}")
            if conditions:
                condition_names = [c.get('name', '') for c in conditions if c.get('name')]
                if condition_names:
                    context_info.append(f"질환: {', '.join(condition_names)}")
            if medications:
                med_names = [m.get('name', '') for m in medications if m.get('name')]
                if med_names:
                    context_info.append(f"복용 약물: {', '.join(med_names)}")

            if context_info:
                prompt_parts.append(f"\n**추출된 컨텍스트:**\n{' | '.join(context_info)}\n")

        prompt_parts.append(f"\n**현재 반복 횟수:** {iteration_count + 1}\n")

        prompt_parts.append("""
다음 원칙에 따라 질의를 재작성하세요:

1. **부족한 정보를 질의에 명시적으로 포함**: 예) "부작용", "대체 치료법" 등
2. **사용자 맥락 반영**: 프로필 정보와 슬롯 정보를 자연스럽게 통합
3. **검색 효율성 향상**: 구체적이고 명확한 키워드 사용
4. **간결함 유지**: 불필요한 설명 제거, 핵심만 포함

**재작성된 질의만 반환하고 다른 설명은 생략하세요.**
""")

        return "".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 의료 정보 검색을 위한 질의 재작성 전문가입니다.
사용자의 원본 질의와 피드백을 바탕으로, 더 효과적인 검색 결과를 얻을 수 있는 질의를 생성합니다.
항상 재작성된 질의만 간결하게 반환하세요."""

    def _fallback_rewrite(
        self,
        original_query: str,
        missing_info: List[str],
        profile_summary: str,
        slot_out: Optional[Dict[str, Any]]
    ) -> str:
        """폴백: 간단한 휴리스틱 재작성"""
        print("[INFO] LLM 재작성 실패, 폴백 휴리스틱 사용")

        parts = [original_query]

        # 부족한 정보를 키워드로 추가
        if missing_info:
            missing_keywords = " ".join(missing_info)
            parts.append(f"추가 정보: {missing_keywords}")

        # 프로필 정보 추가
        if profile_summary:
            parts.append(f"프로필: {profile_summary}")

        # 슬롯 정보 추가
        if slot_out:
            demographics = slot_out.get('demographics', {})
            if demographics.get('age'):
                parts.append(f"나이: {demographics['age']}")
            if demographics.get('gender'):
                parts.append(f"성별: {demographics['gender']}")

        return "\n".join(parts)

    def _enhance_with_profile(
        self,
        original_query: str,
        profile_summary: str,
        slot_out: Optional[Dict[str, Any]]
    ) -> str:
        """프로필 정보만 추가하여 질의 강화 (피드백이 없을 때)"""
        parts = [original_query]

        if profile_summary:
            parts.append(f"프로필: {profile_summary}")

        if slot_out:
            demographics = slot_out.get('demographics', {})
            additions = []

            if demographics.get('age'):
                additions.append(f"나이: {demographics['age']}")
            if demographics.get('gender'):
                additions.append(f"성별: {demographics['gender']}")

            conditions = slot_out.get('conditions', [])
            if conditions:
                condition_names = [c.get('name', '') for c in conditions if c.get('name')]
                if condition_names:
                    additions.append(f"질환: {', '.join(condition_names)}")

            medications = slot_out.get('medications', [])
            if medications:
                med_names = [m.get('name', '') for m in medications if m.get('name')]
                if med_names:
                    additions.append(f"약물: {', '.join(med_names)}")

            if additions:
                parts.append(" | ".join(additions))

        return "\n".join(parts)
