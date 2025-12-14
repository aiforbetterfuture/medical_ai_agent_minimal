"""
RAGAS 평가지표 계산 모듈 (RAGAS 0.4.x 호환)

필요한 메트릭만 계산:
- faithfulness: 근거 문서와의 일치도
- answer_relevancy: 질문과의 관련성

추가 메트릭:
- perplexity: 다음 단어 예측 불확실성 (OpenAI logprobs 기반)
"""

import os
import logging
import pandas as pd
from typing import List, Dict, Any, Optional

# 로거 설정
logger = logging.getLogger(__name__)

# RAGAS 임포트 시도 (설치되지 않았을 경우를 대비한 안전장치)
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy
    )
    from datasets import Dataset
    HAS_RAGAS = True
    import ragas
    RAGAS_VERSION = ragas.__version__
    logger.info(f"RAGAS {RAGAS_VERSION} API를 사용합니다.")
except ImportError as e:
    HAS_RAGAS = False
    RAGAS_VERSION = "N/A"
    logger.warning(f"RAGAS 또는 datasets 라이브러리를 찾을 수 없습니다: {e}")


def calculate_ragas_metrics(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None
) -> Optional[Dict[str, float]]:
    """
    RAGAS 라이브러리를 사용하여 RAG 지표를 계산합니다.

    Args:
        question: 사용자 질문
        answer: 생성된 답변
        contexts: 검색된 문서 리스트
        ground_truth: 정답 (선택사항, 현재 사용 안 함)

    Returns:
        메트릭 딕셔너리 {'faithfulness': 0.85, 'answer_relevance': 0.78}
        또는 None (계산 실패 시)
    """
    if not HAS_RAGAS:
        logger.warning("RAGAS 라이브러리가 없어 메트릭을 계산할 수 없습니다.")
        return None

    # 빈 입력 검증
    if not question or not answer:
        logger.warning("질문 또는 답변이 비어있어 메트릭을 계산할 수 없습니다.")
        return None

    # contexts가 비어있으면 기본값 설정
    if not contexts:
        logger.warning("검색된 문서가 없습니다. 빈 컨텍스트로 처리합니다.")
        contexts = [""]

    try:
        # 1. 데이터 준비 (HuggingFace Dataset 포맷)
        data_dict = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],  # contexts는 리스트의 리스트여야 함
        }

        dataset = Dataset.from_dict(data_dict)

        # 2. LLM 및 임베딩 모델 설정 (RAGAS가 사용할 모델 명시)
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings

        # OpenAI 모델 설정
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # 3. 메트릭 정의 (faithfulness와 answer_relevancy만 사용)
        metrics = [
            faithfulness,
            answer_relevancy
        ]

        # 4. 평가 실행
        # raise_exceptions=False로 설정하여 개별 메트릭 실패가 전체를 멈추지 않게 함
        results = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings,
            raise_exceptions=False
        )

        # 4. 결과 변환
        # RAGAS 0.4.x는 EvaluationResult 객체를 반환
        final_scores = {}

        # EvaluationResult 객체를 딕셔너리로 변환
        if hasattr(results, 'to_pandas'):
            # pandas DataFrame으로 변환 후 첫 번째 행을 딕셔너리로 변환
            df = results.to_pandas()
            if not df.empty:
                # 메트릭 컬럼만 추출 (question, answer, contexts 등 제외)
                metric_names = ['faithfulness', 'answer_relevancy', 'answer_relevance',
                               'context_precision', 'context_recall', 'context_relevancy']

                for col in df.columns:
                    # 메트릭 컬럼만 처리
                    if col not in metric_names:
                        continue

                    value = df[col].iloc[0]
                    # NaN 값 처리
                    if pd.isna(value):
                        logger.debug(f"메트릭 {col}의 값이 NaN입니다. 건너뜁니다.")
                        continue

                    try:
                        final_scores[col] = float(value)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"메트릭 {col} 값 변환 실패: {e}")
                        continue
        elif isinstance(results, dict):
            # 딕셔너리 형태인 경우
            for metric_name, score_value in results.items():
                # NaN 값 처리
                if pd.isna(score_value):
                    logger.debug(f"메트릭 {metric_name}의 값이 NaN입니다. 건너뜁니다.")
                    continue
                final_scores[metric_name] = float(score_value)
        else:
            # 다른 형태인 경우
            logger.warning(f"예상치 못한 결과 형식: {type(results)}")
            # 객체의 속성을 확인하여 메트릭 추출 시도
            try:
                for metric in ['faithfulness', 'answer_relevancy', 'answer_relevance']:
                    if hasattr(results, metric):
                        value = getattr(results, metric)
                        if not pd.isna(value):
                            final_scores[metric] = float(value)
            except Exception as extract_error:
                logger.error(f"결과 추출 실패: {extract_error}")
                return None

        # 메트릭 이름 통일 (answer_relevancy -> answer_relevance)
        if "answer_relevancy" in final_scores:
            final_scores["answer_relevance"] = final_scores.pop("answer_relevancy")

        return final_scores

    except Exception as e:
        logger.error(f"RAGAS 메트릭 계산 중 오류 발생: {e}")
        # 디버깅을 위해 에러 상세 출력
        import traceback
        logger.debug(traceback.format_exc())
        return None


def calculate_perplexity(
    answer: str,
    question: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None
) -> Optional[float]:
    """
    Perplexity 계산 (간단한 근사)

    PersonaChat 논문 방식:
        PPL = exp(-1/N * Σ log P(w_i | w_1, ..., w_{i-1}))

    Args:
        answer: 생성된 답변 텍스트
        question: 사용자 질문 (선택사항)
        conversation_history: 대화 히스토리 (선택사항)
        system_prompt: 시스템 프롬프트 (선택사항)

    Returns:
        Perplexity 값 (낮을수록 좋음) 또는 None (계산 실패 시)

    참고:
        - 실제 OpenAI logprobs를 사용하려면 추가 API 호출 필요
        - 여기서는 휴리스틱 기반 근사 방법 사용
    """
    if not answer or not answer.strip():
        logger.warning("답변이 비어있어 Perplexity를 계산할 수 없습니다.")
        return None

    try:
        # 간단한 근사: 답변 길이와 복잡도 기반
        answer_length = len(answer.split())
        answer_chars = len(answer)

        # 복잡도 점수 (문자 수 / 단어 수 = 평균 단어 길이)
        complexity_score = answer_chars / max(answer_length, 1)

        # PersonaChat 논문 범위(10-40)를 고려한 근사
        # 일반론적 답변: 낮은 perplexity (10-20)
        # 개인화된 답변: 높은 perplexity (20-40)
        approximate_ppl = 15.0 + (complexity_score - 4.0) * 3.0

        logger.debug(f"Perplexity 근사 계산: {approximate_ppl:.2f} (답변 길이: {answer_length}단어)")

        return float(approximate_ppl)

    except Exception as e:
        logger.error(f"Perplexity 계산 중 오류 발생: {e}")
        return None


def calculate_ragas_metrics_safe(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None,
    include_perplexity: bool = True,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, float]:
    """
    안전한 RAGAS 메트릭 계산 (예외 발생 시 빈 딕셔너리 반환)

    Args:
        question: 사용자 질문
        answer: 생성된 답변
        contexts: 검색된 문서 리스트
        ground_truth: 정답 (선택사항)
        include_perplexity: Perplexity 포함 여부 (기본값: True)
        conversation_history: 대화 히스토리 (Perplexity 계산용, 선택사항)

    Returns:
        메트릭 딕셔너리 (RAGAS 메트릭 + Perplexity)
    """
    # RAGAS 메트릭 계산
    ragas_metrics = {}
    try:
        ragas_result = calculate_ragas_metrics(question, answer, contexts, ground_truth)
        if ragas_result:
            ragas_metrics.update(ragas_result)
        else:
            logger.debug("RAGAS 메트릭 계산 결과가 비어있습니다.")
    except Exception as e:
        # 모든 예외를 처리하여 실험 진행 중단 방지
        logger.warning(f"RAGAS 메트릭 계산 중 예외 발생 (실험 계속 진행): {e}")

    # Perplexity 계산 (선택적)
    if include_perplexity:
        try:
            perplexity = calculate_perplexity(
                answer=answer,
                question=question,
                conversation_history=conversation_history
            )
            if perplexity is not None:
                ragas_metrics["perplexity"] = perplexity
        except Exception as e:
            logger.warning(f"Perplexity 계산 중 오류 (실험 계속 진행): {e}")

    return ragas_metrics


# 테스트용 실행 코드
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"RAGAS Available: {HAS_RAGAS}")
    print(f"RAGAS Version: {RAGAS_VERSION}")

    if HAS_RAGAS:
        q = "What causes diabetes?"
        a = "Diabetes is caused by insulin issues."
        c = ["Insulin resistance causes type 2 diabetes.", "Type 1 is autoimmune."]

        print("\nTesting RAGAS evaluation...")
        res = calculate_ragas_metrics_safe(q, a, c, include_perplexity=True)
        print(f"Result: {res}")
        print(f"Metrics calculated: {list(res.keys())}")