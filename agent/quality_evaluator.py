"""
LLM 기반 품질 평가자 (Context Engineering 기반)

- Grounding Check: 답변이 검색 문서에 근거하는지 확인
- Completeness Check: 사용자 질문에 완전히 답했는지 확인
- Accuracy Check: 의학적으로 정확한지 확인
- Missing Info Identification: 부족한 정보 식별 및 피드백 생성
"""

import json
from typing import Dict, Any, List, Optional
from core.llm_client import LLMClient


class QualityEvaluator:
    """LLM 기반 품질 평가자"""

    def __init__(self, llm_client: LLMClient):
        """
        Args:
            llm_client: LLM 클라이언트 인스턴스
        """
        self.llm_client = llm_client

    def evaluate(
        self,
        user_query: str,
        answer: str,
        retrieved_docs: List[Dict[str, Any]],
        profile_summary: str = "",
        previous_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        답변 품질을 종합 평가

        Args:
            user_query: 사용자 질문
            answer: 생성된 답변
            retrieved_docs: 검색된 문서 리스트
            profile_summary: 사용자 프로필 요약
            previous_feedback: 이전 iteration의 피드백 (선택적)

        Returns:
            {
                'overall_score': float,  # 전체 품질 점수 (0-1)
                'grounding_score': float,  # 근거 점수
                'completeness_score': float,  # 완전성 점수
                'accuracy_score': float,  # 정확성 점수
                'missing_info': List[str],  # 부족한 정보 리스트
                'improvement_suggestions': List[str],  # 개선 제안
                'needs_retrieval': bool,  # 재검색 필요 여부
                'reason': str  # 평가 사유
            }
        """
        # 문서 컨텍스트 포맷팅
        docs_text = self._format_docs(retrieved_docs)

        # 평가 프롬프트 생성
        evaluation_prompt = self._build_evaluation_prompt(
            user_query=user_query,
            answer=answer,
            docs_text=docs_text,
            profile_summary=profile_summary,
            previous_feedback=previous_feedback
        )

        # LLM에게 평가 요청
        try:
            evaluation_result = self.llm_client.generate(
                prompt=evaluation_prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.3,  # 일관된 평가를 위해 낮은 temperature
                max_tokens=800
            )

            # JSON 파싱
            feedback = self._parse_evaluation_result(evaluation_result)

            # 전체 점수 계산 (가중 평균)
            overall_score = (
                feedback['grounding_score'] * 0.4 +
                feedback['completeness_score'] * 0.4 +
                feedback['accuracy_score'] * 0.2
            )
            feedback['overall_score'] = overall_score

            return feedback

        except Exception as e:
            print(f"[ERROR] 품질 평가 실패: {e}")
            import traceback
            traceback.print_exc()

            # 폴백: 간단한 휴리스틱 평가
            return self._fallback_evaluation(user_query, answer, retrieved_docs)

    def _format_docs(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """검색 문서를 텍스트로 포맷팅"""
        if not retrieved_docs:
            return "[검색된 문서 없음]"

        formatted = []
        for i, doc in enumerate(retrieved_docs[:5], 1):  # 상위 5개만
            text = doc.get('text', '')[:500]  # 토큰 절약을 위해 500자로 제한
            formatted.append(f"[문서 {i}]\n{text}")

        return "\n\n".join(formatted)

    def _build_evaluation_prompt(
        self,
        user_query: str,
        answer: str,
        docs_text: str,
        profile_summary: str,
        previous_feedback: Optional[Dict[str, Any]]
    ) -> str:
        """평가 프롬프트 생성"""
        prompt_parts = [
            "다음 의료 AI 답변의 품질을 평가해주세요.\n",
            f"**사용자 질문:**\n{user_query}\n",
            f"\n**생성된 답변:**\n{answer}\n",
            f"\n**검색된 근거 문서:**\n{docs_text}\n"
        ]

        if profile_summary:
            prompt_parts.append(f"\n**사용자 프로필:**\n{profile_summary}\n")

        if previous_feedback:
            missing_info = previous_feedback.get('missing_info', [])
            if missing_info:
                prompt_parts.append(
                    f"\n**이전 iteration에서 식별된 부족 정보:**\n"
                    f"{', '.join(missing_info)}\n"
                )

        prompt_parts.append("""
다음 기준으로 평가하고, JSON 형식으로 결과를 반환하세요:

1. **Grounding (근거성)**: 답변이 검색 문서에 근거하는가? (0.0-1.0)
2. **Completeness (완전성)**: 사용자 질문에 완전히 답했는가? (0.0-1.0)
3. **Accuracy (정확성)**: 의학적으로 정확하고 안전한가? (0.0-1.0)
4. **Missing Info (부족 정보)**: 답변에 부족한 정보가 있다면 나열
5. **Improvement Suggestions (개선 제안)**: 답변 개선을 위한 구체적 제안
6. **Needs Retrieval (재검색 필요)**: 추가 검색이 필요한가? (true/false)
7. **Reason (평가 사유)**: 전반적인 평가 이유

**출력 형식 (JSON):**
```json
{
  "grounding_score": 0.8,
  "completeness_score": 0.7,
  "accuracy_score": 0.9,
  "missing_info": ["약물 부작용 정보", "대체 치료법"],
  "improvement_suggestions": ["부작용을 더 상세히 설명", "대체 치료법 추가"],
  "needs_retrieval": true,
  "reason": "답변은 대체로 정확하나 부작용 정보가 부족함"
}
```

JSON만 반환하고 다른 설명은 생략하세요.
""")

        return "".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 의료 AI 답변의 품질을 평가하는 전문가입니다.
답변의 근거성, 완전성, 정확성을 엄격하게 평가하고, 부족한 정보를 식별하며, 개선 방안을 제시합니다.
항상 JSON 형식으로만 응답하세요."""

    def _parse_evaluation_result(self, result: str) -> Dict[str, Any]:
        """LLM 평가 결과 파싱"""
        # JSON 블록 추출
        result = result.strip()

        # 코드 블록 제거
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]

        # JSON 파싱
        try:
            feedback = json.loads(result)
        except json.JSONDecodeError as e:
            print(f"[WARNING] JSON 파싱 실패: {e}")
            print(f"원본 결과: {result}")
            # 폴백: 기본 구조 반환
            feedback = {
                'grounding_score': 0.5,
                'completeness_score': 0.5,
                'accuracy_score': 0.5,
                'missing_info': [],
                'improvement_suggestions': [],
                'needs_retrieval': False,
                'reason': 'JSON 파싱 실패로 기본값 사용'
            }

        # 필수 필드 확인 및 기본값 설정
        feedback.setdefault('grounding_score', 0.5)
        feedback.setdefault('completeness_score', 0.5)
        feedback.setdefault('accuracy_score', 0.5)
        feedback.setdefault('missing_info', [])
        feedback.setdefault('improvement_suggestions', [])
        feedback.setdefault('needs_retrieval', False)
        feedback.setdefault('reason', '')

        # 점수 범위 검증 (0-1)
        for key in ['grounding_score', 'completeness_score', 'accuracy_score']:
            feedback[key] = max(0.0, min(1.0, float(feedback[key])))

        return feedback

    def _fallback_evaluation(
        self,
        user_query: str,
        answer: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """폴백: 간단한 휴리스틱 평가"""
        print("[INFO] LLM 평가 실패, 폴백 휴리스틱 사용")

        # 답변 길이 점수
        length_score = min(len(answer) / 500, 1.0)

        # 근거 문서 존재 여부
        evidence_score = 1.0 if len(retrieved_docs) > 0 else 0.0

        # 전체 점수
        overall_score = (length_score * 0.5 + evidence_score * 0.5)

        return {
            'overall_score': overall_score,
            'grounding_score': evidence_score,
            'completeness_score': length_score,
            'accuracy_score': 0.7,  # 기본값
            'missing_info': [],
            'improvement_suggestions': [],
            'needs_retrieval': overall_score < 0.5,
            'reason': '폴백 휴리스틱 평가 (LLM 평가 실패)'
        }
