# 코드 효율화 및 개선 사항 분석

## 📋 개요

전체 스캐폴드 코드베이스를 검토하여 발견한 비효율적 코드, 아키텍처 문제, 성능 개선 가능 사항을 정리했습니다.

---

## 🔴 심각한 문제 (즉시 수정 권장)

### 1. 그래프 재사용 없음 - 성능 저하

**위치**: `agent/graph.py:89`

**문제**:
```python
def run_agent(user_text: str, mode: str = 'ai_agent') -> str:
    # ...
    app = build_agent_graph()  # 매번 그래프 빌드!
    final_state = app.invoke(initial_state)
```

**영향**: 
- 매 요청마다 그래프 재빌드 (불필요한 오버헤드)
- 초기화 시간 증가

**수정 방안**:
```python
# 그래프를 모듈 레벨에서 캐싱
_agent_graph_cache = None

def get_agent_graph():
    global _agent_graph_cache
    if _agent_graph_cache is None:
        _agent_graph_cache = build_agent_graph()
    return _agent_graph_cache

def run_agent(user_text: str, mode: str = 'ai_agent') -> str:
    # ...
    app = get_agent_graph()  # 재사용
    final_state = app.invoke(initial_state)
```

---

### 2. 상태에 객체 저장 - 직렬화 문제

**위치**: 여러 노드에서 `state['slot_extractor']`, `state['llm_client']` 등 저장

**문제**:
- LangGraph는 상태를 직렬화할 수 있어야 함
- Python 객체는 직렬화되지 않음
- 멀티프로세싱/분산 환경에서 문제 발생 가능

**영향**:
- 상태 저장/복원 실패
- 분산 실행 불가

**수정 방안**:
- 전역 싱글톤 또는 모듈 레벨 캐시 사용
- 또는 별도의 컨텍스트 관리자 도입

---

### 3. 설정 파일 매번 로드 - I/O 오버헤드

**위치**: `core/config.py`의 모든 함수

**문제**:
```python
def get_llm_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if config is None:
        config = load_config()  # 매번 파일 읽기!
```

**영향**:
- 매 노드 실행마다 YAML 파일 읽기
- 불필요한 디스크 I/O

**수정 방안**:
```python
# 모듈 레벨 캐싱
_config_cache = None
_llm_config_cache = None
_retrieval_config_cache = None

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    global _config_cache
    if _config_cache is None:
        # 파일 로드
        _config_cache = ...
    return _config_cache
```

---

## 🟡 중간 문제 (성능 개선)

### 4. BM25 검색 비효율 - 전체 점수 계산

**위치**: `retrieval/hybrid_retriever.py:90`

**문제**:
```python
scores = self.bm25_index.get_scores(query_tokens)  # 전체 문서 점수 계산
top_indices = sorted(range(len(scores)), ...)[:k]  # 전체 정렬 후 k개만 선택
```

**영향**:
- 대용량 코퍼스에서 O(n log n) 정렬
- 불필요한 메모리 사용

**수정 방안**:
```python
# heapq를 사용한 상위 k개만 선택
import heapq

def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
    # ...
    query_tokens = tokenize_ko_en(query)
    scores = self.bm25_index.get_scores(query_tokens)
    
    # 상위 k개만 선택 (O(n log k))
    top_indices = heapq.nlargest(k, range(len(scores)), key=lambda i: scores[i])
    
    results = []
    for rank, idx in enumerate(top_indices, start=1):
        # ...
```

**성능 개선**: O(n log n) → O(n log k), 메모리 사용량 감소

---

### 5. ProfileStore의 비효율적 검색

**위치**: `memory/profile_store.py:144-149`

**문제**:
```python
sbp = next((v for v in reversed(self.ltm.vitals) if str(v.name).upper() == "SBP"), None)
dbp = next((v for v in reversed(self.ltm.vitals) if str(v.name).upper() == "DBP"), None)
```

**영향**:
- 리스트 전체 순회 (O(n))
- 매번 문자열 변환 및 비교

**수정 방안**:
```python
def get_profile_summary(self) -> str:
    # ...
    # 딕셔너리로 인덱싱 (한 번만 순회)
    vitals_dict = {}
    for v in reversed(self.ltm.vitals):
        name_upper = str(v.name).upper()
        if name_upper not in vitals_dict:
            vitals_dict[name_upper] = v
    
    sbp = vitals_dict.get("SBP")
    dbp = vitals_dict.get("DBP")
    
    # labs도 동일하게 처리
    labs_dict = {}
    for l in reversed(self.ltm.labs):
        name_upper = str(l.name).upper()
        if name_upper not in labs_dict:
            labs_dict[name_upper] = l
    
    a1c = labs_dict.get("A1C")
    fpg = labs_dict.get("FPG")
```

---

### 6. 코드 중복 - 모드 체크 반복

**위치**: 모든 노드에서 `state.get('mode') == 'llm'` 체크

**문제**:
- 동일한 로직 반복
- 유지보수 어려움

**수정 방안**:
```python
# core/utils.py
def is_llm_mode(state: AgentState) -> bool:
    """LLM 모드 여부 확인"""
    return state.get('mode') == 'llm'

# 각 노드에서
if is_llm_mode(state):
    return state  # 또는 적절한 처리
```

---

### 7. LLM 클라이언트 초기화 중복

**위치**: `retrieve_node`, `generate_answer_node`

**문제**:
- 동일한 초기화 로직 중복
- 상태에 저장 (직렬화 문제)

**수정 방안**:
```python
# core/llm_client.py에 추가
_llm_client_cache = {}

def get_or_create_llm_client(provider: str = 'openai', **kwargs) -> LLMClient:
    """LLM 클라이언트 캐시 및 재사용"""
    cache_key = f"{provider}_{kwargs.get('model', 'default')}"
    if cache_key not in _llm_client_cache:
        _llm_client_cache[cache_key] = get_llm_client(provider, **kwargs)
    return _llm_client_cache[cache_key]

# 노드에서
llm_client = get_or_create_llm_client(
    provider=embedding_config.get('provider', 'openai')
)
# state에 저장하지 않음
```

---

## 🟢 경미한 문제 (코드 품질)

### 8. 로깅 시스템 없음 - print 사용

**위치**: 모든 노드에서 `print()` 사용

**문제**:
- 프로덕션 환경에서 로그 관리 어려움
- 로그 레벨 제어 불가

**수정 방안**:
```python
# core/logger.py
import logging

logger = logging.getLogger('medical_ai_agent')
logger.setLevel(logging.INFO)

# 노드에서
logger.info("[Node] retrieve")
logger.warning(f"임베딩 생성 실패: {e}")
logger.error(f"답변 생성 실패: {e}")
```

---

### 9. 에러 처리 부족

**위치**: 여러 노드

**문제**:
- 예외 발생 시 기본 메시지만 반환
- 에러 원인 추적 어려움

**수정 방안**:
```python
# 구조화된 에러 처리
class AgentError(Exception):
    """Agent 실행 중 발생하는 에러"""
    pass

class RetrievalError(AgentError):
    """검색 관련 에러"""
    pass

# 노드에서
try:
    # ...
except Exception as e:
    logger.error(f"검색 실패: {e}", exc_info=True)
    raise RetrievalError(f"검색 중 오류 발생: {e}") from e
```

---

### 10. 불필요한 딕셔너리 복사

**위치**: 여러 노드에서 `{**state, ...}` 사용

**문제**:
- 얕은 복사로 충분한데 전체 딕셔너리 복사
- 메모리 사용 증가

**수정 방안**:
```python
# LangGraph는 상태를 자동으로 병합하므로 명시적 복사 불필요
# 단, 수정할 필드만 반환
return {
    'slot_out': slot_out  # 수정된 필드만
}
```

**참고**: LangGraph의 `Annotated` 타입은 자동 병합되므로 전체 복사 불필요

---

### 11. 사용하지 않는 함수

**위치**: `retrieval/rrf_fusion.py:53`

**문제**:
```python
def _calculate_rrf_score(rank: int, k: int = 60) -> float:
    """RRF 점수 계산"""
    return 1.0 / (rank + k)
```

**영향**: 사용되지 않는 코드

**수정 방안**: 삭제 또는 실제 사용

---

### 12. 하드코딩된 값

**위치**: 여러 곳

**문제**:
- 매직 넘버 사용 (예: `k=60`, `quality_score < 0.5`)
- 설정 파일로 관리되지 않음

**수정 방안**:
```python
# config/model_config.yaml에 추가
self_refine:
  quality_threshold: 0.5
  max_iterations: 2
  weights:
    length: 0.3
    evidence: 0.4
    personalization: 0.3

# 코드에서
quality_threshold = config.get('self_refine', {}).get('quality_threshold', 0.5)
```

---

## 📊 성능 개선 예상 효과

| 개선 사항 | 현재 | 개선 후 | 개선율 |
|----------|------|---------|--------|
| 그래프 빌드 | 매번 | 1회 | ~50ms 절약/요청 |
| 설정 로드 | 매번 | 캐싱 | ~10ms 절약/요청 |
| BM25 검색 | O(n log n) | O(n log k) | 대용량에서 10-50% |
| ProfileStore 검색 | O(n) | O(1) | 90%+ 개선 |

---

## 🛠️ 우선순위별 수정 계획

### Phase 1: 즉시 수정 (심각한 문제)
1. ✅ 그래프 재사용 구현
2. ✅ 설정 파일 캐싱
3. ✅ 상태에서 객체 제거 (전역 캐시로 이동)

### Phase 2: 성능 개선 (중간 문제)
4. ✅ BM25 검색 최적화
5. ✅ ProfileStore 검색 최적화
6. ✅ 코드 중복 제거

### Phase 3: 코드 품질 (경미한 문제)
7. ✅ 로깅 시스템 도입
8. ✅ 에러 처리 개선
9. ✅ 하드코딩 값 설정화

---

## 💡 추가 개선 제안

### 13. 비동기 처리 고려

**현재**: 동기 처리로 순차 실행

**개선**: 
- BM25와 FAISS 검색을 병렬 실행
- 임베딩 생성과 검색 준비 병렬화

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def retrieve_node_async(state: AgentState) -> AgentState:
    # BM25와 FAISS를 병렬 실행
    bm25_task = asyncio.to_thread(bm25_retriever.search, query, k)
    faiss_task = asyncio.to_thread(faiss_index.search, query_vector, k)
    
    bm25_results, faiss_results = await asyncio.gather(bm25_task, faiss_task)
    # ...
```

### 14. 메모리 사용 최적화

**문제**: 
- 검색 결과 전체를 메모리에 보관
- 대용량 코퍼스에서 메모리 부족 가능

**개선**:
- 스트리밍 방식으로 결과 처리
- 필요시에만 로드

### 15. 타입 힌팅 강화

**현재**: 일부 타입 힌팅 누락

**개선**:
```python
from typing import TypedDict, List, Dict, Any, Optional

def retrieve_node(state: AgentState) -> AgentState:
    # 명시적 타입 힌팅
    retrieved_docs: List[Dict[str, Any]] = hybrid_retriever.search(...)
    return {
        **state,
        'retrieved_docs': retrieved_docs
    }
```

---

## 📝 수정 코드 예시

주요 개선 사항에 대한 수정 코드는 별도 파일로 제공하겠습니다.

**작성일**: 2025-01-XX  
**버전**: 1.0


