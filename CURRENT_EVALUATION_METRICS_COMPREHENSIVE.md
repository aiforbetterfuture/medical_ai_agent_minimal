# 스캐폴드 평가지표 상세 정리

## 📋 개요

현재 스캐폴드에 구현된 모든 평가지표를 카테고리별로 정리한 문서입니다.

---

## 1. RAGAS (Retrieval-Augmented Generation Assessment) 지표

### 1.1 Faithfulness (신뢰성)

**파일**: `experiments/evaluation/ragas_metrics.py`

**정의**: 생성된 답변이 검색된 근거 문서(contexts)와 얼마나 일치하는지 측정

**범위**: 0.0 ~ 1.0 (높을수록 좋음)

**계산 방법**:
- RAGAS 라이브러리의 `faithfulness` 메트릭 사용
- LLM 기반 평가: 답변의 주장이 contexts에서 뒷받침되는지 확인
- Hallucination(환각) 감지: 근거 없이 생성된 정보를 탐지

**사용 모델**: GPT-4o-mini (RAGAS 내부 사용)

**설정**:
```python
from ragas.metrics import faithfulness
metrics = [faithfulness]
```

**출력 형식**:
```json
{
  "faithfulness": 0.85
}
```

**의미**:
- **0.9 이상**: 답변이 근거 문서와 매우 잘 일치
- **0.7-0.9**: 대체로 일치하나 일부 주장이 근거 부족
- **0.5-0.7**: 상당 부분 근거 없음
- **0.5 미만**: 심각한 환각 또는 근거 부족

---

### 1.2 Answer Relevance (답변 관련성)

**파일**: `experiments/evaluation/ragas_metrics.py`

**정의**: 생성된 답변이 사용자 질문과 얼마나 관련이 있는지 측정

**범위**: 0.0 ~ 1.0 (높을수록 좋음)

**계산 방법**:
- RAGAS 라이브러리의 `answer_relevancy` 메트릭 사용
- LLM 기반 평가: 답변이 질문을 적절히 다루는지 확인
- 질문-답변 관련성 측정

**사용 모델**: GPT-4o-mini (RAGAS 내부 사용)

**설정**:
```python
from ragas.metrics import answer_relevancy
metrics = [answer_relevancy]
```

**출력 형식**:
```json
{
  "answer_relevance": 0.78  # answer_relevancy -> answer_relevance로 변환됨
}
```

**의미**:
- **0.9 이상**: 답변이 질문을 완벽하게 다룸
- **0.7-0.9**: 답변이 질문과 관련 있으나 일부 누락
- **0.5-0.7**: 답변이 질문과 부분적으로만 관련
- **0.5 미만**: 답변이 질문과 무관하거나 완전히 다른 주제

---

### 1.3 Perplexity (혼란도)

**파일**: `experiments/evaluation/ragas_metrics.py` (`calculate_perplexity` 함수)

**정의**: 다음 단어 예측 불확실성 측정 (답변의 자연스러움/일관성)

**범위**: 10.0 ~ 40.0 (낮을수록 좋음, 일반론적 답변은 낮음)

**계산 방법**:
- PersonaChat 논문 방식 근사:
  ```
  PPL = exp(-1/N * Σ log P(w_i | w_1, ..., w_{i-1}))
  ```
- 현재는 휴리스틱 기반 근사:
  - 답변 길이와 복잡도 기반
  - 실제 OpenAI logprobs를 사용하려면 추가 API 호출 필요

**공식**:
```python
complexity_score = answer_chars / max(answer_length, 1)
approximate_ppl = 15.0 + (complexity_score - 4.0) * 3.0
```

**출력 형식**:
```json
{
  "perplexity": 18.5
}
```

**의미**:
- **10-20**: 일반론적 답변 (낮은 perplexity)
- **20-30**: 개인화된 답변 (중간 perplexity)
- **30-40**: 매우 구체적/개인화된 답변 (높은 perplexity)

**참고**: 
- LLM 모드는 일반론적 답변으로 낮은 perplexity
- AI Agent 모드는 개인화된 답변으로 높은 perplexity 예상
- **주의**: 현재는 근사 방법이므로 정확도 제한적

---

## 2. 멀티턴 컨텍스트 지표

### 2.1 CUS (Context Utilization Score) - 맥락 활용 점수

**파일**: `experiments/evaluation/multiturn_context_metrics.py` (`compute_cus` 함수)

**정의**: 질문이 요구하는 `required_slots` 중 답변이 실제로 반영했는지 측정

**범위**: 0.0 ~ 1.0 (높을수록 좋음)

**계산 방법**:
```python
CUS = (사용한 슬롯 개수) / (전체 요구 슬롯 개수)
```

**입력**:
- `answer`: 생성된 답변 텍스트
- `required_slots`: 질문이 요구하는 슬롯 리스트 (예: `["age", "sex", "conditions", "medications", "labs.hba1c"]`)
- `patient_profile`: 환자 프로필 (ground truth)
- `slots_state`: 현재 슬롯 상태 (ProfileStore에서 추출)

**슬롯 사용 판정 방법**:
- **나이**: 정확한 숫자 매칭 또는 "65세", "65 살", "65-year" 패턴
- **성별**: "male/female/남성/여성" 등 키워드 매칭
- **질환/약물**: 리스트의 어떤 요소라도 답변에 나타나면 사용된 것으로 간주
- **검사 결과**: 숫자 값이 답변에 포함되면 사용된 것으로 간주
- **동의어 지원**: `slot_synonyms.py` 모듈 사용 (가능한 경우)

**출력 형식**:
```json
{
  "metric": "CUS",
  "score": 0.75,
  "hits": 3,
  "total": 4,
  "used_detail": {
    "age": {"value": 67, "used": true},
    "sex": {"value": "남성", "used": true},
    "conditions": {"value": ["당뇨병"], "used": true},
    "labs.hba1c": {"value": 6.24, "used": false}
  }
}
```

**의미**:
- **0.8 이상**: 대부분의 요구 슬롯을 활용
- **0.6-0.8**: 절반 이상 활용
- **0.4-0.6**: 일부만 활용
- **0.4 미만**: 거의 활용하지 않음

**특징**:
- Turn 3, 4에서 특히 중요 (의도적으로 맥락이 비명시적)
- LLM 모드는 낮은 CUS 예상 (맥락 재사용 어려움)
- AI Agent 모드는 높은 CUS 예상 (ProfileStore 활용)

---

### 2.2 UR (Update Responsiveness) - 업데이트 반응성

**파일**: `experiments/evaluation/multiturn_context_metrics.py` (`compute_ur` 함수)

**정의**: 특정 턴에 새로 입력된 `update_key`가 답변에 우선 반영되었는지 측정

**범위**: 0.0 또는 1.0 (반영되었으면 1.0, 아니면 0.0)

**계산 방법**:
- `update_key`가 있는 경우에만 평가 (예: Turn 3의 "labs", "vitals")
- 이번 턴에 새로 들어온 정보(`turn_updates`)가 답변에 반영되었는지 확인

**입력**:
- `answer`: 생성된 답변 텍스트
- `update_key`: 질문은행에서 정의한 업데이트 키 (예: `"labs"`, `"vitals"`, `"medications"`)
- `turn_updates`: 이번 턴에 새로 들어온 정보 (slots_state에서 추출)
- `question_text`: 질문 텍스트 (선택적)

**카테고리별 처리**:
- `update_key`가 "labs", "vitals", "medications", "symptoms"인 경우:
  - 해당 카테고리 내의 모든 업데이트가 답변에 반영되었는지 확인
  - 반영된 항목 비율로 점수 계산 (0.0 ~ 1.0)
- 중첩된 경로 (예: "labs.hba1c")인 경우:
  - 해당 값이 답변에 나타나면 1.0, 아니면 0.0

**출력 형식**:
```json
{
  "metric": "UR",
  "applicable": true,
  "score": 1.0,
  "update_key": "labs",
  "update_value": {"hba1c": {"value": 6.24, "unit": "%"}},
  "reflected": true,
  "reflected_items": ["hba1c"],
  "total_items": 1
}
```

**의미**:
- **1.0**: 새로 들어온 정보가 답변에 반영됨
- **0.0**: 새로 들어온 정보가 답변에 반영되지 않음
- **applicable: false**: 해당 턴에 update_key가 없음

**특징**:
- Turn 3에서 특히 중요 (새로운 검사 결과/바이탈 반영)
- LLM 모드는 낮은 UR 예상 (이전 턴 정보 기억 어려움)
- AI Agent 모드는 높은 UR 예상 (ProfileStore에 자동 저장)

---

### 2.3 CCR (Context Contradiction Rate) - 맥락 모순률

**파일**: `experiments/evaluation/multiturn_context_metrics.py` (`ccr_rule_checks` 함수)

**정의**: 답변이 이전 턴까지 축적된 환자 정보(슬롯)와 모순되는지 측정

**범위**: 0.0 (모순 없음) 또는 1.0 (모순 있음)

**계산 방법**:
- 룰 기반 체크 (명백한 모순만 탐지)
- LLM Judge 지원 (의학적 모순 판정, 선택적)

**입력**:
- `answer`: 생성된 답변 텍스트
- `slots_state`: 현재 슬롯 상태 (이전 턴까지 축적된 정보)

**룰 기반 체크 항목**:

1. **성별 모순**:
   - 남성인데 임신 언급 → 모순
   - 여성인데 전립선 언급 → 모순

2. **질환 모순**:
   - 당뇨가 있는데 "당뇨가 아니다"라고 부정 → 모순

3. **약물 모순**:
   - 메트포르민 복용 중인데 "메트포르민을 복용하지 않는다"고 부정 → 모순

**출력 형식**:
```json
{
  "metric": "CCR_rule_obvious",
  "has_contradiction": false,
  "contradictions": [],
  "score": 0.0
}
```

또는 모순이 있는 경우:
```json
{
  "metric": "CCR_rule_obvious",
  "has_contradiction": true,
  "contradictions": ["sex: male but pregnancy mentioned"],
  "score": 1.0
}
```

**LLM Judge 지원**:
- `experiments/evaluation/llm_judge_ccr.py`의 `ccr_llm_judge` 함수
- 의학적 모순 판정 (예: CKD 환자에게 고단백 권장)
- 하이브리드 방식: 룰 기반 먼저 체크, 필요시 LLM Judge 호출

**의미**:
- **0.0**: 모순 없음 (좋음)
- **1.0**: 모순 있음 (나쁨)

**특징**:
- 안전성 측정에 중요
- LLM 모드는 높은 CCR 예상 (이전 정보 기억 어려움)
- AI Agent 모드는 낮은 CCR 예상 (ProfileStore로 일관성 유지)

---

## 3. LLM Judge 지표

### 3.1 Judge Total Score (종합 판정 점수)

**파일**: `experiments/evaluation/llm_judge_ccr.py` (참고)

**정의**: LLM Judge를 통한 종합 품질 평가

**범위**: 0.0 ~ 1.0 (높을수록 좋음)

**계산 방법**:
- LLM 기반 평가 (설정 파일 참조)
- `config.yaml`의 `quality.llm_judge` 설정 사용:
  ```yaml
  quality:
    llm_judge:
      enabled: true
      judge_model: "gpt-4o-mini"
      temperature: 0.2
      weights:
        grounding: 0.4
        completeness: 0.4
        accuracy: 0.2
      thresholds:
        pass_score: 0.60
  ```

**가중치**:
- **grounding (0.4)**: 근거 문서와의 일치도
- **completeness (0.4)**: 답변의 완성도
- **accuracy (0.2)**: 답변의 정확성

**출력 형식**:
```json
{
  "judge_total_score": 0.75
}
```

**의미**:
- **0.8 이상**: 매우 우수한 답변
- **0.6-0.8**: 양호한 답변
- **0.4-0.6**: 보통 답변
- **0.4 미만**: 부족한 답변

**참고**: 
- 현재 설정에서는 `judge_total_score`가 `per_turn_metrics`에 포함되어 있으나, 실제 계산 여부는 코드 확인 필요

---

## 4. 설정 파일에서 정의된 지표

### 4.1 Per-Turn Metrics (턴별 지표)

**파일**: `experiments/config.yaml`

**설정**:
```yaml
evaluation:
  per_turn_metrics: ["faithfulness", "answer_relevance", "perplexity", "judge_total_score"]
```

**지표 목록**:
1. `faithfulness`: RAGAS Faithfulness
2. `answer_relevance`: RAGAS Answer Relevance
3. `perplexity`: Perplexity
4. `judge_total_score`: LLM Judge 종합 점수

---

### 4.2 Multi-Turn Metrics (멀티턴 지표)

**파일**: `experiments/config.yaml`

**설정**:
```yaml
evaluation:
  multiturn_metrics: ["context_utilization", "context_contradiction", "update_responsiveness"]
```

**지표 목록**:
1. `context_utilization`: CUS (Context Utilization Score)
2. `context_contradiction`: CCR (Context Contradiction Rate)
3. `update_responsiveness`: UR (Update Responsiveness)

---

## 5. 이벤트 로그에 저장되는 지표

### 5.1 저장 형식

**파일**: `runs/{run_id}/events.jsonl`

**스키마**: `experiments/schemas/events_record.schema.json`

**저장 위치**: 각 이벤트의 `metrics` 필드

**예시**:
```json
{
  "schema_version": "events_record.v1",
  "run_id": "2025-12-13_primary_v1",
  "mode": "agent",
  "patient_id": "SYN_0001",
  "turn_id": 3,
  "question": {...},
  "answer": {...},
  "metrics": {
    "faithfulness": 0.85,
    "answer_relevance": 0.78,
    "perplexity": 18.5,
    "CUS": 0.75,
    "UR": 1.0,
    "CCR": 0.0
  },
  "slots_truth": {...}
}
```

---

## 6. 지표 계산 흐름

### 6.1 LLM 모드

```
질문 입력
  ↓
LLM 직접 호출
  ↓
답변 생성
  ↓
평가지표 계산:
  - RAGAS (faithfulness, answer_relevance)
  - Perplexity
  - CUS (patient_profile만 사용, slots_state 없음)
  - UR (turn_updates 없을 수 있음)
  - CCR (slots_state 없음)
  ↓
이벤트 로그 저장
```

### 6.2 AI Agent 모드

```
질문 입력
  ↓
Agent 실행 (LangGraph)
  ↓
답변 생성
  ↓
평가지표 계산:
  - RAGAS (faithfulness, answer_relevance)
  - Perplexity
  - CUS (slots_state 사용 가능)
  - UR (turn_updates 사용 가능)
  - CCR (slots_state 사용 가능)
  ↓
이벤트 로그 저장
```

---

## 7. 지표별 비교 예상

### 7.1 LLM vs AI Agent 모드 예상 차이

| 지표 | LLM 모드 예상 | AI Agent 모드 예상 | 차이 이유 |
|------|--------------|-------------------|---------|
| **faithfulness** | 중간 (0.6-0.8) | 높음 (0.7-0.9) | Agent는 검색 문서 활용 |
| **answer_relevance** | 높음 (0.8-0.9) | 높음 (0.8-0.9) | 둘 다 질문에 관련 있음 |
| **perplexity** | 낮음 (10-20) | 높음 (20-35) | Agent는 개인화된 답변 |
| **CUS** | 낮음 (0.3-0.5) | 높음 (0.7-0.9) | Agent는 맥락 재사용 |
| **UR** | 낮음 (0.0-0.3) | 높음 (0.8-1.0) | Agent는 업데이트 반영 |
| **CCR** | 높음 (0.2-0.5) | 낮음 (0.0-0.1) | Agent는 일관성 유지 |

---

## 8. 구현 상태

### 8.1 완전 구현된 지표

✅ **RAGAS Faithfulness**: 완전 구현
✅ **RAGAS Answer Relevance**: 완전 구현
✅ **Perplexity**: 근사 방법으로 구현 (정확도 제한적)
✅ **CUS**: 완전 구현
✅ **UR**: 완전 구현
✅ **CCR (룰 기반)**: 완전 구현

### 8.2 부분 구현된 지표

⚠️ **CCR (LLM Judge)**: 구현되어 있으나 기본적으로 비활성화
⚠️ **Judge Total Score**: 설정에 있으나 실제 계산 여부 확인 필요

### 8.3 미구현 지표 (설정 파일에 언급됨)

❌ **Context Precision**: RAGAS 지표이지만 현재 계산 안 함
❌ **Context Recall**: RAGAS 지표이지만 현재 계산 안 함
❌ **Context Relevancy**: RAGAS 지표이지만 현재 계산 안 함

---

## 9. 새로운 멀티턴 스크립트 모드에서의 지표

### 9.1 추가된 정보

멀티턴 스크립트 모드에서는 다음 정보가 이벤트 로그에 추가됩니다:

```json
{
  "slots_truth": {
    "age": 67,
    "sex": "남성",
    "primary_condition": "Type 2 Diabetes Mellitus",
    "comorbidities": ["Hypertension"],
    "key_meds": ["Metformin"],
    "key_vitals": {"bp_systolic": "131mmHg"},
    "key_labs": {"hba1c": "6.24%"},
    "major_procedures": [],
    "chief_symptom": "피로"
  }
}
```

### 9.2 평가 활용

`slots_truth`를 사용하여 다음 평가 지표 계산 가능:

1. **SFS (Slot Factuality Score)**: 답변이 환자 데이터와 일치하는지
2. **CSP (Contraindication/Safety Penalty)**: 금기/안전 위반 감점
3. **CUS 개선**: `slots_truth`를 ground truth로 사용하여 더 정확한 평가

---

## 10. 참고 파일

- `experiments/evaluation/ragas_metrics.py`: RAGAS 지표 계산
- `experiments/evaluation/multiturn_context_metrics.py`: 멀티턴 컨텍스트 지표 계산
- `experiments/evaluation/multiturn_metrics.py`: 멀티턴 지표 계산 (레거시)
- `experiments/evaluation/llm_judge_ccr.py`: LLM Judge 구현
- `experiments/config.yaml`: 평가 설정
- `experiments/schemas/events_record.schema.json`: 이벤트 스키마
- `config/eval/required_slots_by_turn.yaml`: 턴별 요구 슬롯 정의
- `config/eval/safety_rules.yaml`: 금기/안전 룰 정의

---

## 11. 향후 확장 가능한 지표

### 11.1 제안된 지표 (ChatGPT/Gemini 제안)

1. **SFS (Slot Factuality Score)**: 슬롯 사실성 점수
2. **CSP (Contraindication/Safety Penalty)**: 금기/안전 감점
3. **MCS (Multi-turn Consistency Score)**: 멀티턴 일관성 점수
4. **ASS (Actionability/Specificity Score)**: 실행 가능성 점수

### 11.2 구현 준비 상태

- ✅ 설정 파일 준비: `config/eval/required_slots_by_turn.yaml`
- ✅ 안전 룰 준비: `config/eval/safety_rules.yaml`
- ✅ 슬롯 정보 저장: `slots_truth` 필드
- ⏳ 평가 모듈 구현: 아직 미구현

---

## 12. 요약

### 현재 활성화된 지표

1. **RAGAS Faithfulness** ✅
2. **RAGAS Answer Relevance** ✅
3. **Perplexity** ✅ (근사 방법)
4. **CUS (Context Utilization Score)** ✅
5. **UR (Update Responsiveness)** ✅
6. **CCR (Context Contradiction Rate)** ✅ (룰 기반)

### 설정만 있고 미구현인 지표

1. **Judge Total Score** ⚠️
2. **Context Precision** ❌
3. **Context Recall** ❌
4. **Context Relevancy** ❌

### 향후 확장 가능한 지표

1. **SFS (Slot Factuality Score)** 📋
2. **CSP (Contraindication/Safety Penalty)** 📋
3. **MCS (Multi-turn Consistency Score)** 📋
4. **ASS (Actionability/Specificity Score)** 📋

---

**최종 업데이트**: 2025-12-14
**문서 버전**: 1.0

