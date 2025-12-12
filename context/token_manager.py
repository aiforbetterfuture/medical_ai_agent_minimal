"""
토큰 예산 배분기 (간단한 근사치 버전)

- 실제 서비스에서는 tiktoken 등 실제 토크나이저로 교체 가능
- 최대 컨텍스트 길이 내에서 쿼리/프로필/최근 대화/검색 근거 예산을 분배
"""

from dataclasses import dataclass


@dataclass
class TokenPlan:
    max_total: int
    for_query: int
    for_profile: int
    for_recent: int
    for_longterm: int
    for_docs: int


class TokenManager:
    """LLM 컨텍스트 내 토큰 예산 배분"""

    def __init__(self, max_total_tokens: int = 4000):
        self.max_total = max_total_tokens

    def count_tokens(self, text: str) -> int:
        """
        토큰 수 근사치
        - 가벼운 근사치: 단어 수 * 1.3
        - 필요 시 tiktoken 등으로 교체
        """
        if not text:
            return 0
        return int(len(text.split()) * 1.3)

    def make_plan(
        self,
        *,
        current_query: str,
        profile_summary: str = "",
        longterm_summary: str = "",
        reserved_for_docs: int = 900,
        reserved_for_system: int = 400,
    ) -> TokenPlan:
        """쿼리/프로필/최근 대화/장기 요약/검색 근거 예산 분배"""
        q = self.count_tokens(current_query)
        p = self.count_tokens(profile_summary)
        l = self.count_tokens(longterm_summary)

        # 검색 근거와 시스템 프롬프트용 예산을 미리 확보
        available = max(1000, self.max_total - reserved_for_docs - reserved_for_system)

        base = q + p + l
        remaining = max(0, available - base)

        # 남은 예산 중 60%를 최근 대화에 할당
        recent = int(remaining * 0.6)

        return TokenPlan(
            max_total=self.max_total,
            for_query=q,
            for_profile=p,
            for_recent=recent,
            for_longterm=l,
            for_docs=reserved_for_docs,
        )

