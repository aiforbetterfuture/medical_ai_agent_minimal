"""
노드 6: Self-Refine (Context Engineering 기반 강화 버전)

- LLM 기반 품질 평가 (Grounding + Self-Critique)
- 동적 질의 재작성 (이전 답변 + 피드백 반영)
- Iteration별 이력 추적 (품질 점수, 문서 해시 등)
"""

import hashlib
from agent.state import AgentState
from core.utils import is_llm_mode
from agent.quality_evaluator import QualityEvaluator
from agent.query_rewriter import QueryRewriter
from core.llm_client import get_llm_client
from core.config import get_llm_config


def refine_node(state: AgentState) -> AgentState:
    """
    Self-Refine 노드 (강화 버전)

    생성된 답변의 품질을 검증하고, 필요 시 재검색을 위한 개선된 질의를 생성합니다.
    LLM 모드에서는 품질 검증을 건너뛰고 바로 통과시킵니다.
    """
    print("[Node] refine (Enhanced with Context Engineering)")

    feature_flags = state.get('feature_flags', {})
    self_refine_enabled = feature_flags.get('self_refine_enabled', True)
    llm_based_quality_check = feature_flags.get('llm_based_quality_check', True)
    dynamic_query_rewrite = feature_flags.get('dynamic_query_rewrite', True)

    # LLM 모드 또는 셀프 리파인 비활성화: 품질 검증 건너뛰기
    if is_llm_mode(state) or not self_refine_enabled:
        return {
            **state,
            'quality_score': 1.0,
            'needs_retrieval': False
        }

    answer = state.get('answer', '')
    retrieved_docs = state.get('retrieved_docs', [])
    profile_summary = state.get('profile_summary', '')
    iteration_count = state.get('iteration_count', 0)

    # === 품질 평가 ===
    if llm_based_quality_check:
        # LLM 기반 품질 평가 (Grounding + Self-Critique)
        quality_feedback = _llm_based_evaluation(
            state=state,
            answer=answer,
            retrieved_docs=retrieved_docs,
            profile_summary=profile_summary
        )
        quality_score = quality_feedback.get('overall_score', 0.5)
        needs_retrieval_by_quality = quality_feedback.get('needs_retrieval', False)
    else:
        # 기존 휴리스틱 평가 (폴백)
        quality_feedback = _heuristic_evaluation(
            answer=answer,
            retrieved_docs=retrieved_docs,
            profile_summary=profile_summary
        )
        quality_score = quality_feedback.get('overall_score', 0.5)
        needs_retrieval_by_quality = quality_score < feature_flags.get('quality_threshold', 0.5)

    print(f"[Refine] 품질 점수: {quality_score:.2f} (Iteration: {iteration_count + 1})")

    # === 재검색 필요 여부 결정 ===
    max_iter = feature_flags.get('max_refine_iterations', 2)
    threshold = feature_flags.get('quality_threshold', 0.5)

    needs_retrieval = (
        needs_retrieval_by_quality and
        quality_score < threshold and
        iteration_count < max_iter
    )

    # === 이력 추적 (Ablation 연구용) ===
    quality_score_history = state.get('quality_score_history') or []
    quality_score_history.append(quality_score)

    # === 동적 질의 재작성 (재검색이 필요한 경우) ===
    new_query = state.get('user_text', '')
    query_rewrite_history = state.get('query_rewrite_history') or []

    if needs_retrieval and dynamic_query_rewrite:
        # Query Rewriter 사용
        new_query = _rewrite_query(
            state=state,
            quality_feedback=quality_feedback,
            answer=answer
        )
        query_rewrite_history.append(new_query)
        print(f"[Refine] 질의 재작성 완료: {new_query[:100]}...")
    else:
        # 재검색 불필요 또는 동적 재작성 비활성화
        query_rewrite_history.append(new_query)

    # === Iteration 로그 (분석용) ===
    refine_iteration_logs = state.get('refine_iteration_logs') or []
    refine_iteration_logs.append({
        'iteration': iteration_count + 1,
        'quality_score': quality_score,
        'quality_feedback': quality_feedback,
        'needs_retrieval': needs_retrieval,
        'rewritten_query': new_query,
        'num_docs': len(retrieved_docs)
    })

    return {
        **state,
        'quality_score': quality_score,
        'quality_feedback': quality_feedback,
        'needs_retrieval': needs_retrieval,
        'query_for_retrieval': new_query,  # 재작성된 질의로 검색
        'quality_score_history': quality_score_history,
        'query_rewrite_history': query_rewrite_history,
        'refine_iteration_logs': refine_iteration_logs
    }


def _llm_based_evaluation(
    state: AgentState,
    answer: str,
    retrieved_docs: list,
    profile_summary: str
) -> dict:
    """LLM 기반 품질 평가"""
    print("[Refine] LLM 기반 품질 평가 수행 중...")

    # LLM 클라이언트 초기화 (캐싱)
    if 'llm_client' not in state:
        llm_config = get_llm_config()
        llm_client = get_llm_client(
            provider=llm_config.get('provider', 'openai'),
            model=llm_config.get('model', 'gpt-4o-mini'),
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 1000)
        )
        state['llm_client'] = llm_client
    else:
        llm_client = state['llm_client']

    # Quality Evaluator 초기화 (캐싱)
    if 'quality_evaluator' not in state:
        evaluator = QualityEvaluator(llm_client=llm_client)
        state['quality_evaluator'] = evaluator
    else:
        evaluator = state['quality_evaluator']

    # 이전 피드백 가져오기 (반복 개선)
    previous_feedback = state.get('quality_feedback')

    # 평가 실행
    try:
        quality_feedback = evaluator.evaluate(
            user_query=state.get('user_text', ''),
            answer=answer,
            retrieved_docs=retrieved_docs,
            profile_summary=profile_summary,
            previous_feedback=previous_feedback
        )
    except Exception as e:
        print(f"[ERROR] LLM 평가 실패, 휴리스틱으로 폴백: {e}")
        quality_feedback = _heuristic_evaluation(answer, retrieved_docs, profile_summary)

    return quality_feedback


def _heuristic_evaluation(
    answer: str,
    retrieved_docs: list,
    profile_summary: str
) -> dict:
    """기존 휴리스틱 평가 (폴백)"""
    # 간단한 품질 평가
    # 1. 답변 길이 체크
    length_score = min(len(answer) / 500, 1.0)  # 500자 이상이면 1.0

    # 2. 근거 문서 존재 여부
    evidence_score = 1.0 if len(retrieved_docs) > 0 else 0.0

    # 3. 개인화 정보 포함 여부
    personalization_score = 1.0 if profile_summary else 0.0

    # 전체 품질 점수 (가중 평균)
    overall_score = (
        length_score * 0.3 +
        evidence_score * 0.4 +
        personalization_score * 0.3
    )

    return {
        'overall_score': overall_score,
        'grounding_score': evidence_score,
        'completeness_score': length_score,
        'accuracy_score': 0.7,  # 기본값
        'missing_info': [],
        'improvement_suggestions': [],
        'needs_retrieval': overall_score < 0.5,
        'reason': '휴리스틱 평가 (폴백)'
    }


def _rewrite_query(
    state: AgentState,
    quality_feedback: dict,
    answer: str
) -> str:
    """동적 질의 재작성"""
    print("[Refine] 동적 질의 재작성 수행 중...")

    # LLM 클라이언트 가져오기
    llm_client = state.get('llm_client')
    if not llm_client:
        llm_config = get_llm_config()
        llm_client = get_llm_client(
            provider=llm_config.get('provider', 'openai'),
            model=llm_config.get('model', 'gpt-4o-mini'),
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 1000)
        )
        state['llm_client'] = llm_client

    # Query Rewriter 초기화 (캐싱)
    if 'query_rewriter' not in state:
        rewriter = QueryRewriter(llm_client=llm_client)
        state['query_rewriter'] = rewriter
    else:
        rewriter = state['query_rewriter']

    # 재작성 실행
    try:
        rewritten_query = rewriter.rewrite(
            original_query=state.get('user_text', ''),
            quality_feedback=quality_feedback,
            previous_answer=answer,
            profile_summary=state.get('profile_summary', ''),
            slot_out=state.get('slot_out', {}),
            iteration_count=state.get('iteration_count', 0)
        )
    except Exception as e:
        print(f"[ERROR] 질의 재작성 실패, 원본 질의 사용: {e}")
        rewritten_query = state.get('user_text', '')

    return rewritten_query


def _compute_doc_hashes(retrieved_docs: list) -> list:
    """문서 해시 계산 (중복 검색 방지용)"""
    doc_hashes = []
    for doc in retrieved_docs:
        doc_text = doc.get('text', '')
        doc_hash = hashlib.md5(doc_text.encode('utf-8')).hexdigest()
        doc_hashes.append(doc_hash)
    return doc_hashes
