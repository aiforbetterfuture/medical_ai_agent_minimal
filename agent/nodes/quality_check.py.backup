"""
노드 7: 품질 검사 및 재검색 결정 (2중 안전장치 강화)

- 안전장치 1: 동일 문서 재검색 방지 (문서 해시 비교)
- 안전장치 2: 품질 점수 진행도 모니터링 (개선 없으면 조기 종료)
"""

import hashlib
from agent.state import AgentState
from langgraph.graph import END
from core.utils import is_llm_mode


def quality_check_node(state: AgentState) -> str:
    """
    품질 검사 노드 (2중 안전장치)

    품질이 낮으면 재검색, 높으면 종료합니다.
    LLM 모드에서는 항상 종료합니다.

    안전장치:
    1. 동일 문서 재검색 방지: 이전 iteration과 동일한 문서가 검색되면 조기 종료
    2. 진행도 모니터링: 품질 점수가 개선되지 않으면 조기 종료
    """
    print("[Node] quality_check (Enhanced with 2-layer Safety)")

    feature_flags = state.get('feature_flags', {})
    self_refine_enabled = feature_flags.get('self_refine_enabled', True)
    quality_check_enabled = feature_flags.get('quality_check_enabled', True)
    duplicate_detection = feature_flags.get('duplicate_detection', True)
    progress_monitoring = feature_flags.get('progress_monitoring', True)
    max_iter = feature_flags.get('max_refine_iterations', 2)

    # LLM 모드 또는 셀프 리파인 off: 항상 종료
    if is_llm_mode(state) or not self_refine_enabled or not quality_check_enabled:
        print("[Quality Check] 셀프 리파인/품질 체크 비활성 또는 LLM 모드: 종료")
        return END

    needs_retrieval = state.get('needs_retrieval', False)
    iteration_count = state.get('iteration_count', 0)
    quality_score = state.get('quality_score', 0.0)

    # 기본 조건 확인
    if not needs_retrieval or iteration_count >= max_iter:
        print(f"[Quality Check] 품질 양호 또는 최대 반복 도달 (점수: {quality_score:.2f}, iteration: {iteration_count}): 종료")
        return END

    # === 안전장치 1: 동일 문서 재검색 방지 ===
    if duplicate_detection:
        duplicate_detected = _check_duplicate_docs(state)
        if duplicate_detected:
            print("[Quality Check] [안전장치 1] 동일 문서 재검색 감지: 조기 종료")
            return END

    # === 안전장치 2: 품질 점수 진행도 모니터링 ===
    if progress_monitoring:
        no_progress = _check_progress_stagnation(state)
        if no_progress:
            print("[Quality Check] [안전장치 2] 품질 개선 없음: 조기 종료")
            return END

    # 재검색 루프
    print(f"[Quality Check] 품질 낮음 (점수: {quality_score:.2f}), 재검색 수행 (iteration: {iteration_count + 1})")
    return "retrieve"  # retrieve 노드로 돌아감


def _check_duplicate_docs(state: AgentState) -> bool:
    """
    안전장치 1: 동일 문서 재검색 방지

    현재 iteration의 문서 해시와 이전 iteration의 문서 해시를 비교하여
    중복 여부를 판단합니다.

    Returns:
        True: 중복 검색 감지 (조기 종료)
        False: 새로운 문서 검색됨 (계속 진행)
    """
    retrieved_docs = state.get('retrieved_docs', [])
    retrieved_docs_history = state.get('retrieved_docs_history') or []

    if not retrieved_docs:
        # 문서가 없으면 중복 아님
        return False

    # 현재 iteration의 문서 해시 계산
    current_doc_hashes = _compute_doc_hashes(retrieved_docs)

    # 이력에 추가
    retrieved_docs_history.append(current_doc_hashes)
    state['retrieved_docs_history'] = retrieved_docs_history

    # 이전 iteration과 비교 (최소 2개 이상의 이력 필요)
    if len(retrieved_docs_history) < 2:
        return False

    previous_doc_hashes = retrieved_docs_history[-2]

    # 해시 집합으로 변환하여 비교
    current_set = set(current_doc_hashes)
    previous_set = set(previous_doc_hashes)

    # 교집합 비율 계산 (Jaccard similarity)
    intersection = current_set & previous_set
    union = current_set | previous_set

    if len(union) == 0:
        similarity = 0.0
    else:
        similarity = len(intersection) / len(union)

    print(f"[Quality Check] 문서 유사도: {similarity:.2f} (현재: {len(current_set)}개, 이전: {len(previous_set)}개)")

    # 유사도가 80% 이상이면 중복으로 판단
    duplicate_threshold = 0.8
    if similarity >= duplicate_threshold:
        print(f"[Quality Check] 문서 유사도 {similarity:.2f} >= {duplicate_threshold}: 중복 감지")
        return True

    return False


def _check_progress_stagnation(state: AgentState) -> bool:
    """
    안전장치 2: 품질 점수 진행도 모니터링

    최근 2개 iteration의 품질 점수를 비교하여, 개선이 없으면 조기 종료합니다.

    Returns:
        True: 품질 개선 없음 (조기 종료)
        False: 품질 개선됨 (계속 진행)
    """
    quality_score_history = state.get('quality_score_history') or []

    # 최소 2개 이상의 품질 점수 필요
    if len(quality_score_history) < 2:
        return False

    # 최근 2개 점수 비교
    current_score = quality_score_history[-1]
    previous_score = quality_score_history[-2]

    # 개선 폭 계산
    improvement = current_score - previous_score

    print(f"[Quality Check] 품질 점수 변화: {previous_score:.2f} → {current_score:.2f} (개선: {improvement:+.2f})")

    # 개선 임계값 (최소 0.05 이상 개선되어야 함)
    improvement_threshold = 0.05

    if improvement < improvement_threshold:
        print(f"[Quality Check] 품질 개선 부족 ({improvement:+.2f} < {improvement_threshold}): 정체 감지")
        return True

    # 품질 점수가 오히려 하락한 경우도 조기 종료
    if improvement < 0:
        print(f"[Quality Check] 품질 점수 하락 ({improvement:+.2f}): 조기 종료")
        return True

    return False


def _compute_doc_hashes(retrieved_docs: list) -> list:
    """
    문서 해시 계산 (중복 검색 방지용)

    각 문서의 텍스트를 MD5 해시로 변환하여 고유 식별자를 생성합니다.
    """
    doc_hashes = []
    for doc in retrieved_docs:
        doc_text = doc.get('text', '')
        if doc_text:
            doc_hash = hashlib.md5(doc_text.encode('utf-8')).hexdigest()
            doc_hashes.append(doc_hash)
    return doc_hashes
