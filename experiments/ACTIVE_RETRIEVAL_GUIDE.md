# Active Retrieval 실험 가이드

## 개요

Active Retrieval은 쿼리의 의도를 분석하여 검색 필요성을 판단하고, 복잡도에 따라 동적으로 검색 문서 수(k)를 조정하는 시스템입니다.

**핵심 목표**:
- 불필요한 검색 스킵으로 레이턴시 감소
- 토큰 비용 절감
- 답변 품질 유지 또는 향상

---

## 시스템 아키텍처

### 1. 워크플로우

```
User Query
    ↓
[check_similarity] - 캐시 확인
    ↓ (miss)
[classify_intent] - 의도 분류 ← NEW!
    ↓
검색 필요?
    ├─ No  → [assemble_context] → [generate_answer] (검색 스킵)
    └─ Yes → [extract_slots] → ... → [retrieve] (정상 플로우)
```

### 2. 의도 분류 로직

**Stage 1: Rule-based Filtering**
- 인사 감지: "안녕", "hello" 등
- 단순 응답: "네", "감사합니다" 등
- → 검색 불필요 (k=0)

**Stage 2: Slot-based Analysis**
- 의료 엔티티 존재 여부 확인
- 복잡도 추정:
  - **simple**: 1개 개념, 20자 이하 → k=3
  - **moderate**: 2-3개 개념, 50자 이하 → k=8
  - **complex**: 4개 이상 개념, 50자 초과 → k=15

**Stage 3: Query Content Analysis**
- 사실 기반 질문 패턴: "무엇", "어떻게", "?"
- Follow-up 질문: "그거", "그건"
- → 쿼리 길이 기반 복잡도 판단

### 3. 안전장치

- **Feature Flag**: `active_retrieval_enabled` (기본값: `False`)
- **Fallback**: 분류 실패 시 기존 로직 사용
- **Budget Constraint**: dynamic_k도 토큰 예산 제약 적용
- **Error Handling**: 모든 단계에 try-except

---

## 사용 방법

### A. 활성화/비활성화

#### 방법 1: 코드에서 직접 설정

```python
from agent.graph import run_agent

# Active Retrieval ON
answer = run_agent(
    user_text="정상 혈압 범위는?",
    mode='ai_agent',
    feature_overrides={'active_retrieval_enabled': True}
)

# Active Retrieval OFF (기본값)
answer = run_agent(
    user_text="정상 혈압 범위는?",
    mode='ai_agent',
    feature_overrides={'active_retrieval_enabled': False}
)
```

#### 방법 2: Config 파일 수정

`config/agent_config.yaml` (또는 해당 설정 파일):

```yaml
features:
  active_retrieval_enabled: true  # 활성화
  default_k: 8
  simple_query_k: 3
  moderate_query_k: 8
  complex_query_k: 15
```

---

## Ablation Study (A/B 테스트)

### 1. 베이스라인 실험 (Active Retrieval OFF)

```bash
python experiments/test_active_retrieval.py \
  --mode baseline \
  --name "baseline_20241212" \
  --output experiments/ablation
```

### 2. 처리 실험 (Active Retrieval ON)

```bash
python experiments/test_active_retrieval.py \
  --mode treatment \
  --name "treatment_20241212" \
  --output experiments/ablation
```

### 3. 비교 분석

```bash
python experiments/test_active_retrieval.py \
  --mode compare \
  --baseline experiments/ablation/baseline_20241212_*.json \
  --treatment experiments/ablation/treatment_20241212_*.json \
  --output experiments/ablation
```

**출력 예시**:
```
==============================================================
ABLATION STUDY COMPARISON
==============================================================
Baseline:  baseline_20241212 (n=10)
Treatment: treatment_20241212 (n=10)
--------------------------------------------------------------
avg_latency_ms:
  Baseline:  2000.0000
  Treatment: 1400.0000
  Change:    -30.00%

avg_cost_usd:
  Baseline:  0.0010
  Treatment: 0.0006
  Change:    -40.00%

avg_quality_score:
  Baseline:  0.7500
  Treatment: 0.7600
  Change:    +1.33%

Statistical Significance: ✓ (p=0.0123)
==============================================================
```

### 4. 커스텀 쿼리 세트 사용

`queries.txt` 파일 생성:
```
안녕하세요
정상 혈압 범위는?
65세 남성, 혈압 140/90인데 위험한가요?
```

실행:
```bash
python experiments/test_active_retrieval.py \
  --mode baseline \
  --queries queries.txt
```

---

## 메트릭 수집

### 수집되는 메트릭

**쿼리별 메트릭** (QueryMetrics):
- `needs_retrieval`: 검색 필요 여부
- `dynamic_k`: 동적으로 결정된 k 값
- `query_complexity`: simple/moderate/complex
- `classification_time_ms`: 분류 소요 시간
- `retrieval_executed`: 실제 검색 실행 여부
- `num_docs_retrieved`: 검색된 문서 수
- `total_latency_ms`: 전체 레이턴시
- `estimated_cost_usd`: 추정 비용
- `quality_score`: 답변 품질 점수

**집계 통계** (Aggregate Stats):
- `avg_latency_ms`, `p95_latency_ms`, `p99_latency_ms`
- `avg_cost_usd`, `total_cost_usd`
- `avg_quality_score`, `median_quality_score`
- `retrieval_skip_rate`: 검색 스킵 비율
- `complexity_distribution`: 복잡도 분포
- `avg_iterations`: 평균 Self-Refine 반복 횟수

### 메트릭 데이터 접근

```python
from agent.metrics.ablation_metrics import AblationMetrics

# 저장된 결과 로드
metrics = AblationMetrics.load_results("experiments/ablation/baseline_*.json")

# 통계 계산
stats = metrics.calculate_statistics()

print(f"Average Latency: {stats['avg_latency_ms']:.2f}ms")
print(f"Skip Rate: {stats['retrieval_skip_rate']*100:.1f}%")

# 개별 쿼리 메트릭 접근
for qm in metrics.query_metrics:
    print(f"{qm.query_text}: {qm.total_latency_ms:.2f}ms, complexity={qm.query_complexity}")
```

---

## 성능 튜닝

### k 값 조정

복잡도별 k 값을 조정하여 최적화:

```python
feature_overrides = {
    'active_retrieval_enabled': True,
    'simple_query_k': 2,      # 더 공격적으로 줄이기
    'moderate_query_k': 5,    # 기본값 8에서 5로
    'complex_query_k': 12,    # 기본값 15에서 12로
}
```

### 분류 임계값 조정

`classify_intent.py` 수정:

```python
def _is_greeting(self, query: str) -> bool:
    # 더 엄격한 임계값
    return any(pattern in query_lower for pattern in greeting_patterns) and len(query) < 20
```

### 복잡도 추정 알고리즘 개선

```python
def _estimate_complexity(self, slot_out, query):
    # LLM 기반 복잡도 추정으로 업그레이드
    complexity_prompt = f"다음 의료 질문의 복잡도를 simple/moderate/complex로 분류하세요: {query}"
    complexity = self.llm.classify(complexity_prompt)
    return complexity
```

---

## 예상 효과

### 정량적 효과

| 메트릭 | 베이스라인 | Active Retrieval | 개선률 |
|--------|-----------|-----------------|--------|
| 평균 레이턴시 | 2.0s | 1.4s | -30% |
| P95 레이턴시 | 3.5s | 2.3s | -34% |
| 평균 비용 | $0.0010 | $0.0006 | -40% |
| 검색 스킵률 | 0% | 30% | +30% |
| 답변 품질 | 0.75 | 0.76 | +1.3% |

### 정성적 효과

- **사용자 경험**: 간단한 질문에 즉시 응답
- **비용 효율**: 불필요한 API 호출 감소
- **시스템 부하**: 검색 엔진 부담 경감
- **확장성**: 더 많은 사용자 처리 가능

---

## 문제 해결

### 1. 분류가 제대로 안 됨

**증상**: 인사를 의료 질문으로 오분류

**해결**:
```python
# classify_intent.py 디버깅 로그 추가
print(f"[DEBUG] Query: {query}")
print(f"[DEBUG] is_greeting: {self._is_greeting(query)}")
print(f"[DEBUG] has_medical_info: {self._has_medical_entities(slot_out)}")
```

### 2. 검색이 항상 실행됨

**확인 사항**:
1. Feature flag 활성화 여부:
   ```python
   print(state.get('feature_flags', {}).get('active_retrieval_enabled'))
   ```

2. classification_skipped 확인:
   ```python
   print(state.get('classification_skipped'))  # False여야 함
   ```

3. needs_retrieval 확인:
   ```python
   print(state.get('needs_retrieval'))  # False면 스킵되어야 함
   ```

### 3. 에러 발생 시 fallback 확인

```python
# graph.py의 run_agent에서 최종 상태 확인
final_state = app.invoke(initial_state)
print(f"Classification Error: {final_state.get('classification_error')}")
print(f"Fallback Used: {final_state.get('classification_skipped')}")
```

---

## 고급 사용법

### 1. 실시간 메트릭 모니터링

```python
from agent.nodes.classify_intent import IntentClassifier

# Classifier 메트릭 확인
classifier = state.get('intent_classifier')
if classifier:
    metrics = classifier.get_metrics()
    print(f"Total Queries: {metrics['total_queries']}")
    print(f"Skip Rate: {metrics['skip_rate']*100:.1f}%")
    print(f"Avg Classification Time: {metrics['avg_classification_time_ms']:.2f}ms")
```

### 2. 배치 테스트

```python
import pandas as pd
from agent.graph import run_agent

queries = pd.read_csv("test_queries.csv")
results = []

for _, row in queries.iterrows():
    state = run_agent(
        user_text=row['query'],
        mode='ai_agent',
        feature_overrides={'active_retrieval_enabled': True},
        return_state=True
    )

    results.append({
        'query': row['query'],
        'latency': state.get('classification_time_ms', 0),
        'complexity': state.get('query_complexity'),
        'needs_retrieval': state.get('needs_retrieval')
    })

df = pd.DataFrame(results)
df.to_csv("batch_results.csv", index=False)
```

### 3. HTML 보고서 생성

```python
from agent.metrics.ablation_metrics import generate_ablation_report

# 모든 실험 결과를 HTML로 요약
generate_ablation_report("experiments/ablation")
# → experiments/ablation/ablation_report.html 생성
```

---

## 참고 자료

### 논문 및 이론

- **CRAG (Corrective RAG)**: Active retrieval decision-making
- **Context Engineering Survey**: Query planning and complexity estimation
- **Information Retrieval**: Adaptive k selection

### 코드 구조

```
agent/
├── nodes/
│   ├── classify_intent.py      # 의도 분류 로직
│   ├── retrieve.py              # dynamic_k 지원 추가
│   └── ...
├── metrics/
│   └── ablation_metrics.py      # 메트릭 수집 시스템
└── graph.py                     # 워크플로우 통합

experiments/
├── test_active_retrieval.py     # A/B 테스트 스크립트
├── ACTIVE_RETRIEVAL_GUIDE.md    # 이 문서
└── ablation/                    # 실험 결과 저장소
    ├── baseline_*.json
    ├── treatment_*.json
    ├── comparison_result.json
    └── ablation_report.html
```

---

## 체크리스트

실험 시작 전 확인:

- [ ] Feature flag 설정 확인
- [ ] 테스트 쿼리 준비 (다양한 복잡도 포함)
- [ ] 베이스라인 실험 완료
- [ ] 처리 실험 완료
- [ ] 통계적 유의성 확인 (p < 0.05)
- [ ] 메트릭 저장 확인
- [ ] 비교 보고서 생성

---

**작성일**: 2024-12-12
**버전**: 1.0
**문의**: Active Retrieval 관련 질문은 이슈로 등록해주세요.
