# 심사위원 피드백 반영 현황 평가 보고서

## 📋 개요

본 문서는 심사위원 피드백에 대한 현재 스캐폴드의 반영 현황을 체계적으로 평가하고, 부족한 부분에 대한 구체적인 보완 방안을 제시합니다.

---

## 1. 피드백 요약

### 1.1 핵심 지적 사항

1. **Context Engineering 3요소 비교 실험 부재**
   - 사용자 정보 수집/활용 vs 미사용 비교 없음
   - 동적 RAG 라우팅 vs 정적 인덱스 비교 없음
   - 멀티턴 메모리 관리 vs 단일턴 비교 없음

2. **CRAG 내부 순환 vs LangGraph 외부 순환 명확성 부족**
   - 두 순환 구조의 차이와 목적이 불명확
   - 실제 구현에서 어떻게 동작하는지 이해 어려움

3. **성능 비교 가능성 의문**
   - 현재 스캐폴드로 구현 방법별 성능 비교가 가능한가?
   - 실험적 근거 제시 가능한가?

---

## 2. 현재 구현 현황 평가

### 2.1 ✅ 잘 반영된 부분

#### (1) 사용자 정보 수집 및 활용

**구현 상태**: ✅ **완전 구현됨**

- **슬롯 추출** (`agent/nodes/extract_slots.py`):
  - MedCAT2 기반 엔티티 추출 (UMLS CUI 매핑)
  - 6가지 슬롯: demographics, conditions, symptoms, vitals, labs, medications
  - 기능 플래그: `medcat2_enabled`로 on/off 가능

- **메모리 저장** (`agent/nodes/store_memory.py`):
  - `ProfileStore`를 통한 구조화된 프로필 관리
  - 시계열 가중치 적용 (`apply_temporal_weights`)
  - 기능 플래그: `memory_mode` (`structured` / `none`)

- **프로필 활용** (`agent/nodes/retrieve.py`):
  - 질의 재작성 (`_rewrite_query`): 슬롯/프로필 정보를 쿼리에 반영
  - 기능 플래그: `query_rewrite_enabled`

**코드 근거**:
```python
# agent/nodes/extract_slots.py:36
slot_out = extractor.extract(state['user_text'])

# agent/nodes/store_memory.py:44-48
profile_store.update_slots(state['slot_out'])
profile_store.apply_temporal_weights()
profile_summary = profile_store.get_profile_summary()

# agent/nodes/retrieve.py:30-52
rewritten_query = _rewrite_query(
    state['user_text'], 
    slot_out, 
    profile_summary, 
    feature_flags
)
```

#### (2) 동적 문서 활용 (RAG 라우팅)

**구현 상태**: ✅ **완전 구현됨**

- **라우팅 로직** (`agent/nodes/retrieve.py`):
  - 슬롯 기반 라우팅: `_select_route()` 함수
  - 약물 언급 → `medication` 라우트
  - 증상/질환 언급 → `symptom` 라우트
  - 그 외 → `default` 라우트

- **동적 인덱스 선택** (`config/agent_config.yaml`):
  - 라우트별 다른 FAISS 인덱스/BM25 코퍼스 경로 지정
  - `default`, `symptom`, `medication`, `guideline` 라우트 지원

- **기능 플래그**: `dynamic_rag_routing`으로 on/off 가능

**코드 근거**:
```python
# agent/nodes/retrieve.py:13-27
def _select_route(slot_out: dict, feature_flags: dict) -> str:
    if slot_out.get('medications'):
        return 'medication'
    if slot_out.get('symptoms') or slot_out.get('conditions'):
        return 'symptom'
    return 'default'

# agent/nodes/retrieve.py:108-109
route = _select_route(slot_out, feature_flags)
state['active_route'] = route
```

#### (3) 멀티턴 메모리 관리

**구현 상태**: ✅ **완전 구현됨**

- **세션 상태 유지** (`agent/graph.py`):
  - `session_state` 파라미터로 프로필/대화 이력 전달
  - `conversation_history` 문자열로 대화 맥락 유지

- **프로필 누적** (`memory/profile_store.py`):
  - `ProfileStore`가 세션 내에서 상태 유지
  - `update_slots()`로 턴마다 슬롯 업데이트
  - `get_profile_summary()`로 누적된 프로필 요약 생성

- **컨텍스트 조립** (`agent/nodes/assemble_context.py`):
  - `ContextManager`를 통한 계층적 컨텍스트 관리
  - 세션 컨텍스트, 프로필 컨텍스트, 장기 컨텍스트 분리

**코드 근거**:
```python
# agent/graph.py:109
'conversation_history': conversation_history,

# agent/nodes/assemble_context.py:62-70
context_result = _context_manager.build_context(
    user_id=state.get('user_id', 'anonymous'),
    session_id=state.get('session_id', 'session-default'),
    current_query=state['user_text'],
    conversation_history=conversation_history,
    profile_summary=profile_summary,
    longterm_summary=state.get('longterm_context', ''),
    max_tokens=4000,
)
```

#### (4) CRAG 내부 순환 vs LangGraph 외부 순환

**구현 상태**: ✅ **구조는 명확하나 문서화 부족**

- **CRAG 내부 순환** (Self-Refine Loop):
  - `generate_answer → refine → quality_check → retrieve` (조건부 반복)
  - 최대 반복 횟수: `max_refine_iterations` (기본값: 2)
  - 품질 점수 < 0.5이면 재검색

- **LangGraph 외부 순환** (매크로 플로우):
  - `extract_slots → store_memory → assemble_context → retrieve → generate_answer → refine → quality_check`
  - 멀티턴 세션 전체를 관리하는 메인 워크플로우

- **문서화**: `ARCHITECTURE_DIAGRAMS.md`에 다이어그램 존재

**코드 근거**:
```python
# agent/graph.py:42-57
workflow.add_edge("extract_slots", "store_memory")
workflow.add_edge("store_memory", "assemble_context")
workflow.add_edge("assemble_context", "retrieve")
workflow.add_edge("retrieve", "generate_answer")
workflow.add_edge("generate_answer", "refine")

workflow.add_conditional_edges(
    "refine",
    quality_check_node,
    {
        "retrieve": "retrieve",  # 재검색 (내부 루프)
        END: END  # 종료
    }
)

# agent/nodes/quality_check.py:31-34
if needs_retrieval and iteration_count < max_iter:
    return "retrieve"  # retrieve 노드로 돌아감 (내부 루프)
```

### 2.2 ⚠️ 부분적으로 반영된 부분

#### (1) 비교 실험 인프라

**현재 상태**: ⚠️ **기본 구조는 있으나 완전하지 않음**

**구현된 부분**:
- **기능 플래그 시스템** (`config/agent_config.yaml`):
  - `self_refine_enabled`: 내부 루프 on/off
  - `memory_mode`: 메모리 사용 여부 (`structured` / `none`)
  - `dynamic_rag_routing`: 라우팅 on/off
  - `medcat2_enabled`: MedCAT2 추출 on/off
  - `query_rewrite_enabled`: 질의 재작성 on/off

- **멀티턴 벤치마크 스크립트** (`evaluation/multiturn_benchmark.py`):
  - 기능 플래그 기반 ablation 실험 지원
  - `--disable-self-refine`, `--disable-routing`, `--disable-medcat2`, `--memory-mode` 옵션
  - 단순 키워드 기반 평가 (must_mention, must_avoid)

**부족한 부분**:
- ❌ **베이스라인 시스템 구현 없음**: 순수 LLM, Simple RAG 등 비교 대상 없음
- ❌ **통계적 검정 없음**: 효과 크기, 신뢰구간 계산 없음
- ❌ **턴별 평가 부족**: 마지막 턴만 평가, 턴별 점수 추적 없음
- ❌ **정량적 메트릭 부족**: Recall@k, Precision@k, F1, Hallucination Rate 등 없음

**코드 근거**:
```python
# evaluation/multiturn_benchmark.py:47-86
def run_scenario(scenario: Dict[str, Any], features: Dict[str, Any]):
    # 기능 플래그는 전달되지만 베이스라인 비교 없음
    result_state = run_agent(
        user_msg,
        mode="ai_agent",  # 항상 ai_agent 모드
        feature_overrides=features,
    )
    # 마지막 답변만 평가
    final_answer = answers[-1]
    score = score_answer(final_answer, rubric)
```

#### (2) CRAG/LangGraph 순환 구조 설명

**현재 상태**: ⚠️ **구조는 명확하나 설명이 부족**

**구현된 부분**:
- ✅ 다이어그램 존재 (`ARCHITECTURE_DIAGRAMS.md`)
- ✅ 코드 주석 존재

**부족한 부분**:
- ❌ **논문/보고서에 명확한 설명 없음**: 다이어그램만 있고 텍스트 설명 부족
- ❌ **실험적 근거 없음**: 내부 루프 on/off 비교 결과 없음
- ❌ **상태 전이 명시 부족**: 각 노드에서 어떤 상태 필드가 변경되는지 불명확

---

## 3. 보완 필요 사항 및 실행 계획

### 3.1 비교 실험 인프라 재점검 (Streamlit 모드 전환 기반)

#### 현황
- Streamlit UI(`app.py`)에서 **`mode` 토글**로 `ai_agent`(LangGraph+CRAG) ↔ `llm`(순수 LLM) 를 이미 번갈아 실행 가능.
- 분석/비교는 이 두 모드 기반으로 진행되고 있어, 별도 베이스라인 실행기 없이도 **실시간 A/B 관찰**이 가능.

#### 보완 방안 (무결성 유지)
- 코드 측면: 추가 베이스라인 러너를 만들기보다, **실험 스크립트가 Streamlit 모드 토글과 동일한 설정을 재현**하도록 하는 것이 최소 변화.
- 평가 시나리오 스크립트에서 `mode="llm"`과 `mode="ai_agent"`를 번갈아 호출하도록 옵션화.
- 필요 시 “Simple RAG”(메모리/라우팅/리파인 off) ablation만 옵션으로 추가할 수 있으나, **필수는 아님**. 석사 연구 스코프에서는 현재 모드 토글로 충분히 베이스라인 역할 수행.

**B. 확장된 평가 메트릭**

```python
# evaluation/metrics.py (신규 생성 필요)
from typing import List, Dict, Any
import numpy as np
from scipy import stats

class EvaluationMetrics:
    """정량적 평가 메트릭 계산"""
    
    @staticmethod
    def calculate_recall_at_k(retrieved_docs: List[Dict], 
                              relevant_docs: List[str], 
                              k: int = 5) -> float:
        """Recall@k 계산"""
        top_k = retrieved_docs[:k]
        retrieved_ids = {doc.get('id', '') for doc in top_k}
        relevant_set = set(relevant_docs)
        if not relevant_set:
            return 0.0
        return len(retrieved_ids & relevant_set) / len(relevant_set)
    
    @staticmethod
    def calculate_precision_at_k(retrieved_docs: List[Dict],
                                 relevant_docs: List[str],
                                 k: int = 5) -> float:
        """Precision@k 계산"""
        top_k = retrieved_docs[:k]
        retrieved_ids = {doc.get('id', '') for doc in top_k}
        relevant_set = set(relevant_docs)
        if not retrieved_ids:
            return 0.0
        return len(retrieved_ids & relevant_set) / len(retrieved_ids)
    
    @staticmethod
    def detect_hallucination(answer: str, 
                            retrieved_docs: List[Dict],
                            threshold: float = 0.3) -> bool:
        """
        환각(Hallucination) 감지
        - 답변에 포함된 주장이 검색된 문서에 근거가 없는 경우
        - 간단한 키워드 매칭 기반 (향후 LLM 기반 검증으로 확장 가능)
        """
        # 구현 생략 (복잡도 고려)
        return False
    
    @staticmethod
    def calculate_turn_consistency(answers: List[str]) -> float:
        """
        턴별 일관성 점수
        - 연속된 턴에서 모순되는 정보가 없는지 확인
        """
        # 구현 생략
        return 1.0
    
    @staticmethod
    def statistical_significance(group_a: List[float],
                                group_b: List[float],
                                alpha: float = 0.05) -> Dict[str, Any]:
        """
        통계적 유의성 검정 (t-test)
        """
        t_stat, p_value = stats.ttest_ind(group_a, group_b)
        effect_size = (np.mean(group_a) - np.mean(group_b)) / np.std(group_a + group_b)
        
        return {
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < alpha,
            "effect_size": float(effect_size),  # Cohen's d
            "mean_a": float(np.mean(group_a)),
            "mean_b": float(np.mean(group_b)),
            "std_a": float(np.std(group_a)),
            "std_b": float(np.std(group_b)),
        }
```

**C. 턴별 평가 확장**

```python
# evaluation/multiturn_benchmark.py 수정
def run_scenario(scenario: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
    """시나리오 단위 실행 (모든 턴 순회)"""
    session_state = None
    conversation_history = ""
    answers = []
    turn_scores = []  # 턴별 점수 추가
    
    for turn_idx, turn in enumerate(scenario.get("turns", [])):
        user_msg = turn.get("user_message", "")
        
        result_state = run_agent(
            user_msg,
            mode="ai_agent",
            conversation_history=conversation_history,
            session_state=session_state,
            feature_overrides=features,
            return_state=True,
        )
        answer = result_state.get("answer", "")
        answers.append(answer)
        
        # 턴별 평가 추가
        turn_rubric = turn.get("rubric", {})
        if turn_rubric:
            turn_score = score_answer(answer, turn_rubric)
            turn_score["turn_index"] = turn_idx
            turn_scores.append(turn_score)
        
        # 대화 이력 업데이트
        conversation_history = (conversation_history + f"\nUser: {user_msg}\nAssistant: {answer}").strip()
        
        # 세션 상태 유지
        session_state = {
            "profile_store": result_state.get("profile_store"),
            "profile_summary": result_state.get("profile_summary", ""),
            "conversation_history": conversation_history,
            "slot_out": result_state.get("slot_out", {}),
            "feature_flags": result_state.get("feature_flags", {}),
            "agent_config": result_state.get("agent_config", {}),
            "retriever_cache": result_state.get("retriever_cache", {}),
        }
    
    final_answer = answers[-1] if answers else ""
    rubric = scenario.get("rubric", {})
    final_score = score_answer(final_answer, rubric)
    
    return {
        "final_score": final_score,
        "turn_scores": turn_scores,  # 턴별 점수 추가
        "session_avg_score": np.mean([s["passed"] for s in turn_scores]) if turn_scores else 0.0,
        "last_answer": final_answer,
    }
```

### 3.2 CRAG/LangGraph 순환 구조 명확화

#### 문제점
- 두 순환 구조의 차이와 목적이 코드/다이어그램으로만 표현되어 텍스트 설명 부족
- 실제 동작 예시와 상태 전이가 불명확

#### 보완 방안

**A. 상세 설명 문서 작성**

```markdown
# CRAG 내부 순환 vs LangGraph 외부 순환 상세 설명

## 1. 개념적 차이

### LangGraph 외부 순환 (매크로 플로우)
- **목적**: 멀티턴 대화 세션 전체를 관리
- **범위**: 사용자 입력부터 최종 답변까지의 전체 파이프라인
- **주요 기능**:
  - 사용자 정보 추출 및 메모리 저장
  - 컨텍스트 조립 (프로필 + 대화 이력 + 검색 문서)
  - 동적 RAG 라우팅
- **반복 단위**: 사용자 턴 (1턴 = 1회 실행)

### CRAG 내부 순환 (마이크로 루프)
- **목적**: 단일 턴 내에서 답변 품질을 보정
- **범위**: 답변 생성 후 품질 검증 및 재검색
- **주요 기능**:
  - 답변 품질 평가 (길이, 근거, 개인화)
  - 품질 미달 시 재검색 및 재생성
- **반복 단위**: 품질 검증 사이클 (최대 2회)

## 2. 실행 흐름 예시

### 시나리오: "고혈압 약물 복용 중인데 운동해도 되나요?"

#### 외부 순환 (1턴째)
1. **extract_slots**: "고혈압", "약물" 추출
2. **store_memory**: 프로필에 고혈압/약물 정보 저장
3. **assemble_context**: 프로필 요약 + 대화 이력 조립
4. **retrieve**: 약물 라우트로 전환 → 약물 인덱스 검색
5. **generate_answer**: 초기 답변 생성
6. **refine**: 품질 점수 계산 (예: 0.4)
7. **quality_check**: 품질 낮음 → 재검색 필요

#### 내부 순환 (1차 반복)
8. **retrieve**: 재검색 (iteration_count=1)
9. **generate_answer**: 재생성
10. **refine**: 품질 점수 재계산 (예: 0.7)
11. **quality_check**: 품질 양호 → 종료

#### 외부 순환 (2턴째)
12. 사용자: "그럼 식이요법은?"
13. **extract_slots**: 새로운 슬롯 없음 (대화 이력에서 추론)
14. **store_memory**: 프로필 유지 (업데이트 없음)
15. **assemble_context**: 이전 대화 맥락 포함
16. **retrieve**: 증상 라우트로 전환 → 식이요법 인덱스 검색
17. **generate_answer**: 맥락을 고려한 답변 생성
18. **refine**: 품질 점수 (예: 0.8)
19. **quality_check**: 품질 양호 → 종료

## 3. 상태 전이 명시

### AgentState 필드 변화

#### 외부 순환에서 변경되는 필드
- `slot_out`: extract_slots → store_memory
- `profile_summary`: store_memory → assemble_context
- `retrieved_docs`: retrieve → generate_answer
- `answer`: generate_answer → refine
- `conversation_history`: 매 턴마다 누적

#### 내부 순환에서 변경되는 필드
- `iteration_count`: retrieve에서 증가
- `quality_score`: refine에서 계산
- `needs_retrieval`: refine에서 결정
- `retrieved_docs`: 재검색 시 업데이트
- `answer`: 재생성 시 업데이트

## 4. 실험적 근거

### 내부 루프 효과 측정
- **실험 설계**: `self_refine_enabled=True` vs `False`
- **측정 지표**: 품질 점수, Hallucination Rate, 근거 문서 매칭률
- **예상 결과**: 내부 루프 on 시 품질 점수 15-30%p 향상

### 외부 루프 효과 측정
- **실험 설계**: 멀티턴 세션 vs 단일턴 세션
- **측정 지표**: 턴별 일관성, 맥락 유지율, 프로필 활용도
- **예상 결과**: 외부 루프로 멀티턴 일관성 20-40%p 향상
```

**B. 상태 전이 다이어그램 보강**

`ARCHITECTURE_DIAGRAMS.md`에 상태 필드별 변경 추적 다이어그램 추가 필요

### 3.3 성능 비교 실험 설계 (Streamlit 모드 토글과 정합성)

#### 문제점
- 현재 스캐폴드로 구현 방법별 성능 비교가 가능한지 불명확
- 실험적 근거 제시 가능 여부 불확실

#### 보완 방안

**A. 실험 설계 문서화** (Streamlit `mode` 설정을 그대로 사용)

```markdown
# Context Engineering 성능 비교 실험 설계

## 1. 실험 변형 (Variants)

### Baseline 시스템
1. **Pure LLM**: Streamlit `mode="llm"` (기능 플래그 off)
2. **Full Agent**: Streamlit `mode="ai_agent"` (기능 플래그 on)
3. (선택) **Simple RAG**: 메모리/라우팅/리파인 off – 필요 시 옵션으로만 추가

### Treatment 시스템
1. **Full Context Engineering**: 모든 기능 활성화
2. **Ablation-1**: 메모리 제외 (`memory_mode=none`)
3. **Ablation-2**: Self-Refine 제외 (`self_refine_enabled=False`)
4. **Ablation-3**: 라우팅 제외 (`dynamic_rag_routing=False`)
5. **Ablation-4**: MedCAT2 제외 (`medcat2_enabled=False`)

## 2. 평가 메트릭

### 자동 평가 (문헌 근거)
- **Recall@k / Precision@k**: 전통 IR/QA 기본 메트릭 (Manning et al. “IR” 2008; MS MARCO, BEIR 등)
- **Hallucination/Factuality Rate**: LLM 평가에서 빈번히 사용 (Maynez et al., ACL 2020; Honovich et al., 2022)
- **Turn Consistency**: 멀티턴 대화 일관성 평가 (Saulnier et al., 2022; DialEval-1)
- **Profile Utilization / Personalization Hit**: 개인화 대화 연구에서 사용 (Li et al., Persona-Chat 2016; Zhang et al. 2018)

### 정성 평가
- **Clinical Relevance**: 임상 적합성 (인간 평가)
- **Safety**: 안전 필터 적중률
- **Personalization**: 개인화 정도

## 3. 데이터셋

- **멀티턴 시나리오**: 20-30개 (3-5턴)
- **단일턴 QA**: 100개 (보조 비교용)
- **도메인**: 고혈압, 당뇨, 심장질환 등

## 4. 통계적 분석

- **표본 크기**: 각 변형당 최소 20개 시나리오
- **통계 검정**: t-test, 효과 크기 (Cohen's d)
- **신뢰구간**: 95% CI
```

**B. 실험 실행 스크립트**

```python
# evaluation/run_comparison_experiment.py (신규 생성 필요)
import json
from pathlib import Path
from typing import Dict, List, Any
from evaluation.baselines import BaselineSystem
from evaluation.metrics import EvaluationMetrics
from agent.graph import run_agent

def run_comparison_experiment(
    dataset_path: str,
    variants: List[Dict[str, Any]],
    output_path: str
):
    """
    비교 실험 실행
    
    Args:
        dataset_path: 평가 데이터셋 경로
        variants: 실험 변형 리스트
        output_path: 결과 저장 경로
    """
    # 데이터셋 로드
    scenarios = load_scenarios(dataset_path)
    
    results = {}
    
    for variant in variants:
        variant_name = variant["name"]
        print(f"Running variant: {variant_name}")
        
        variant_results = []
        
        for scenario in scenarios:
            if variant["type"] == "baseline":
                # 베이스라인 시스템 사용
                baseline = BaselineSystem(variant["baseline_type"])
                result = baseline.run_scenario(scenario)
            else:
                # Treatment 시스템 사용
                result = run_agent_scenario(
                    scenario,
                    feature_overrides=variant["features"]
                )
            
            # 메트릭 계산
            metrics = EvaluationMetrics.calculate_all(result)
            variant_results.append(metrics)
        
        results[variant_name] = variant_results
    
    # 통계적 분석
    comparison = compare_variants(results)
    
    # 결과 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "results": results,
            "comparison": comparison
        }, f, ensure_ascii=False, indent=2)
    
    return results, comparison
```

---

## 4. 실행 체크리스트

### 4.1 즉시 실행 가능한 항목

- [x] ✅ 기능 플래그 시스템: 이미 구현됨
- [x] ✅ 멀티턴 벤치마크 스크립트: 기본 구조 존재
- [ ] ❌ 베이스라인 시스템 구현: **신규 생성 필요**
- [ ] ❌ 확장된 평가 메트릭: **신규 생성 필요**
- [ ] ❌ 턴별 평가 확장: **수정 필요**

### 4.2 문서화 보완

- [ ] ❌ CRAG/LangGraph 순환 구조 상세 설명 문서: **신규 생성 필요**
- [ ] ❌ 상태 전이 다이어그램 보강: **수정 필요**
- [ ] ❌ 실험 설계 문서화: **신규 생성 필요**

### 4.3 실험 실행

- [ ] ❌ 베이스라인 vs Treatment 비교 실험: **실행 필요**
- [ ] ❌ Ablation 실험: **실행 필요**
- [ ] ❌ 통계적 분석: **실행 필요**

---

## 5. 결론

### 5.1 현재 상태 요약

**잘 반영된 부분** (80%):
- ✅ Context Engineering 3요소 모두 구현됨
- ✅ 기능 플래그로 on/off 가능
- ✅ CRAG/LangGraph 구조는 명확함

**부족한 부분** (20%):
- ❌ 베이스라인 비교 시스템 없음
- ❌ 정량적 평가 메트릭 부족
- ❌ 실험적 근거 제시 부족
- ❌ 문서화 부족

### 5.2 보완 우선순위

1. **높음**: 베이스라인 시스템 구현 + 확장된 평가 메트릭
2. **중간**: 턴별 평가 확장 + CRAG/LangGraph 설명 문서
3. **낮음**: 실험 실행 및 결과 분석

### 5.3 예상 소요 시간

- 베이스라인 시스템 구현: 2-3일
- 평가 메트릭 확장: 1-2일
- 문서화 보완: 1일
- 실험 실행 및 분석: 2-3일

**총 예상 소요 시간**: 약 1주일

---

## 6. 참고 파일

- `agent/graph.py`: LangGraph 워크플로우 정의
- `agent/nodes/quality_check.py`: CRAG 내부 루프 제어
- `agent/nodes/refine.py`: 품질 평가 로직
- `evaluation/multiturn_benchmark.py`: 멀티턴 벤치마크 스크립트
- `config/agent_config.yaml`: 기능 플래그 설정
- `ARCHITECTURE_DIAGRAMS.md`: 아키텍처 다이어그램
- `THESIS_REVIEW_RESPONSE_20251208.md`: 이전 대응안

