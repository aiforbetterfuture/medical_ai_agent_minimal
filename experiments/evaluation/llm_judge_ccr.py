"""
CCR LLM Judge 구현

의학적 모순 판정을 위한 LLM Judge 호출
"""

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# OpenAI 클라이언트 (선택적)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI 패키지가 설치되지 않았습니다. LLM Judge를 사용할 수 없습니다.")


def ccr_llm_judge(
    question: str,
    answer: str,
    slots_state: Dict[str, Any],
    turn_updates: Dict[str, Any],
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> Optional[Dict[str, Any]]:
    """
    CCR LLM Judge 실행
    
    의학적 모순 판정을 위한 LLM Judge 호출
    
    Args:
        question: 사용자 질문
        answer: 생성된 답변
        slots_state: 현재 슬롯 상태
        turn_updates: 이번 턴 업데이트
        model: OpenAI 모델명 (기본값: gpt-4o-mini)
        temperature: Temperature (기본값: 0.0, 재현성 확보)
    
    Returns:
        {
            "has_contradiction": bool,
            "contradiction_items": [
                {
                    "slot": "string",
                    "expected": "string",
                    "answer_fragment": "string",
                    "severity": "low|medium|high"
                }
            ],
            "notes": "string",
            "score": 1.0 (모순 있음) 또는 0.0 (모순 없음)
        } 또는 None (실패 시)
    """
    if not HAS_OPENAI:
        logger.warning("OpenAI 패키지가 없어 LLM Judge를 실행할 수 없습니다.")
        return None
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OPENAI_API_KEY가 설정되지 않아 LLM Judge를 실행할 수 없습니다.")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        
        # 페이로드 구성
        system_prompt = (
            "You are a strict medical consistency evaluator. "
            "Determine whether the answer contradicts the patient's known context. "
            "Return ONLY valid JSON matching the schema."
        )
        
        user_prompt = f"""[QUESTION]
{question}

[ANSWER]
{answer}

[KNOWN_CONTEXT_SLOTS]
{json.dumps(slots_state, ensure_ascii=False, indent=2)}

[TURN_UPDATES]
{json.dumps(turn_updates, ensure_ascii=False, indent=2)}

[JSON_SCHEMA]
{{
  "has_contradiction": "boolean",
  "contradiction_items": [
    {{
      "slot": "string",
      "expected": "string",
      "answer_fragment": "string",
      "severity": "low|medium|high"
    }}
  ],
  "notes": "string"
}}

Output ONLY valid JSON, no other text."""
        
        # LLM 호출
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            response_format={"type": "json_object"},  # JSON 모드 강제
        )
        
        # 응답 파싱
        content = response.choices[0].message.content
        if not content:
            logger.warning("LLM Judge 응답이 비어있습니다.")
            return None
        
        result = json.loads(content)
        
        # 결과 정규화
        has_contradiction = result.get("has_contradiction", False)
        contradiction_items = result.get("contradiction_items", [])
        
        return {
            "has_contradiction": has_contradiction,
            "contradiction_items": contradiction_items,
            "notes": result.get("notes", ""),
            "score": 1.0 if has_contradiction else 0.0,  # CCR은 1=모순 있음
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"LLM Judge 응답 JSON 파싱 실패: {e}")
        logger.error(f"응답 내용: {content[:500] if 'content' in locals() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"LLM Judge 실행 중 오류: {e}", exc_info=True)
        return None


def ccr_hybrid(
    answer: str,
    slots_state: Dict[str, Any],
    question: Optional[str] = None,
    turn_updates: Optional[Dict[str, Any]] = None,
    use_llm_judge: bool = False,
) -> Dict[str, Any]:
    """
    CCR 하이브리드 평가 (룰 기반 + LLM Judge)
    
    룰 기반으로 명백한 모순을 먼저 체크하고,
    필요시 LLM Judge로 의학적 모순을 판정
    
    Args:
        answer: 생성된 답변
        slots_state: 현재 슬롯 상태
        question: 사용자 질문 (LLM Judge용, 선택적)
        turn_updates: 이번 턴 업데이트 (LLM Judge용, 선택적)
        use_llm_judge: LLM Judge 사용 여부 (기본값: False)
    
    Returns:
        {
            "metric": "CCR_hybrid",
            "has_contradiction": bool,
            "contradictions": [모순 항목 리스트],
            "score": 1.0 (모순 있음) 또는 0.0 (모순 없음),
            "method": "rule_only" | "rule+llm_judge"
        }
    """
    from .multiturn_context_metrics import ccr_rule_checks
    
    # 룰 기반 체크
    rule_result = ccr_rule_checks(answer, slots_state)
    
    # 룰 기반에서 모순이 발견되면 즉시 반환
    if rule_result["has_contradiction"]:
        return {
            **rule_result,
            "metric": "CCR_hybrid",
            "method": "rule_only",
        }
    
    # 룰 기반에서 모순이 없고, LLM Judge를 사용하는 경우
    if use_llm_judge and question and turn_updates is not None:
        llm_result = ccr_llm_judge(question, answer, slots_state, turn_updates)
        if llm_result:
            if llm_result["has_contradiction"]:
                return {
                    "metric": "CCR_hybrid",
                    "has_contradiction": True,
                    "contradictions": llm_result["contradiction_items"],
                    "score": 1.0,
                    "method": "rule+llm_judge",
                    "llm_judge_result": llm_result,
                }
            else:
                return {
                    "metric": "CCR_hybrid",
                    "has_contradiction": False,
                    "contradictions": [],
                    "score": 0.0,
                    "method": "rule+llm_judge",
                    "llm_judge_result": llm_result,
                }
    
    # 룰 기반 결과 반환
    return {
        **rule_result,
        "metric": "CCR_hybrid",
        "method": "rule_only",
    }

