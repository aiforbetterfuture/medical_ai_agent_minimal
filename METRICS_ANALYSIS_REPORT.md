# 평가지표 분석 보고서

## 🔍 현재 상황 요약

**결론**: RAGAS 평가지표(Faithfulness, Answer Relevance 등)가 **설정은 되어 있으나 실제로 계산/저장되지 않았습니다**.

---

## 📋 설정 파일 분석

### 1. `experiments/config.yaml`

```yaml
evaluation:
  per_turn_metrics: ["faithfulness", "answer_relevance", "judge_total_score"]
  multiturn_metrics: ["context_utilization", "context_contradiction", "update_responsiveness"]
  export_summary_json: true
  export_summary_path: "runs/{run_id}/summary.json"
```

**상태**: ✅ 설정은 되어 있음

---

### 2. `experiments/schemas/events_record.schema.json`

```json
{
  "metrics": {
    "type": ["object", "null"],
    "description": "Evaluation metrics (if computed)",
    "properties": {
      "faithfulness": {"type": ["number", "null"]},
      "answer_relevance": {"type": ["number", "null"]},
      "context_precision": {"type": ["number", "null"]},
      "context_recall": {"type": ["number", "null"]},
      "context_relevancy": {"type": ["number", "null"]}
    }
  }
}
```

**상태**: ✅ 스키마는 정의되어 있음

---

## ❌ 문제점 분석

### 1. 실험 러너에서 평가지표 계산/저장 로직 부재

**파일**: `experiments/run_multiturn_experiment_v2.py`

**문제**:
- `_log_event()` 메서드에서 `metrics` 필드를 생성하지 않음
- RAGAS 라이브러리 호출 코드가 없음
- 평가지표 계산 함수가 호출되지 않음

**현재 코드 구조**:
```python
def _log_event(self, ...):
    event = {
        "schema_version": "events_record.v1",
        "run_id": self.run_id,
        "mode": mode,
        "patient_id": patient_id,
        "turn_id": turn_id,
        "question": {...},
        "answer": {...},
        "usage": {...},
        "timing_ms": {...},
        "metadata": {...},
        # ❌ "metrics": {...} 필드가 없음!
    }
```

---

### 2. 평가지표 계산 모듈 부재

**확인 결과**:
- `experiments/evaluation/multiturn_metrics.py`: 멀티턴 특화 지표만 계산 (Context Utilization, Context Contradiction 등)
- RAGAS 메트릭 계산 코드가 없음
- `ragas` 라이브러리 import/사용 코드가 없음

---

### 3. events.jsonl에 metrics 필드 없음

**확인 결과**:
```bash
python -c "import json; f=open('runs/2025-12-13_primary_v1/events.jsonl','r',encoding='utf-8'); line=f.readline(); data=json.loads(line); print('metrics' in data); print(data.get('metrics', 'NOT FOUND'))"
# 출력: False, NOT FOUND
```

**상태**: ❌ `events.jsonl`에 `metrics` 필드가 전혀 없음

---

### 4. summarize_run.py는 metrics를 읽으려 하지만 데이터가 없음

**파일**: `scripts/summarize_run.py`

**코드**:
```python
DEFAULT_MAIN_METRICS = [
    "faithfulness",
    "answer_relevance",
    "judge_total",
    "grounding",
    "completeness",
    "accuracy",
]

def collect_metric_values(records: Dict[Key, Dict[str, Any]], mode: str, metric: str) -> List[float]:
    vals: List[float] = []
    for k, rec in records.items():
        if k.mode != mode:
            continue
        v = extract_metric_value(rec, metric)  # events.jsonl에서 metrics 필드 읽기 시도
        if v is None:
            continue  # ❌ metrics 필드가 없어서 항상 None 반환
        vals.append(v)
    return vals  # ❌ 빈 리스트 반환
```

**상태**: ✅ 코드는 올바르게 작성되어 있으나, 데이터가 없어서 빈 결과만 반환

---

## 📊 현재 사용 가능한 지표

### 1. 효율성 지표 (✅ 사용 가능)

- **비용**: `usage.estimated_cost_usd`
- **응답 시간**: `timing_ms.total`
- **캐시 히트율**: `metadata.cache_hit` (Agent 모드만)

**위치**: `runs/2025-12-13_primary_v1/paper_assets/summary.json` → `efficiency` 섹션

---

### 2. 멀티턴 특화 지표 (⚠️ 별도 계산 필요)

**파일**: `experiments/evaluation/multiturn_metrics.py`

**지표**:
- `context_utilization`: 이전 턴 정보 활용도
- `context_contradiction`: 이전 정보와의 모순도
- `update_responsiveness`: 새 정보 반영도

**상태**: ⚠️ 코드는 있으나 실험 러너에서 호출되지 않음

---

### 3. RAGAS 평가지표 (❌ 계산되지 않음)

**필요한 지표**:
- `faithfulness`: 근거 문서와의 일치도
- `answer_relevance`: 질문과의 관련성
- `context_precision`: 컨텍스트 정밀도
- `context_recall`: 컨텍스트 재현율
- `context_relevancy`: 컨텍스트 관련성

**상태**: ❌ 계산/저장 로직이 전혀 없음

---

## 🔧 해결 방안

### 옵션 1: 실험 러너에 RAGAS 평가 통합 (권장)

**필요한 작업**:

1. **RAGAS 라이브러리 설치**
   ```bash
   pip install ragas
   ```

2. **평가지표 계산 함수 추가**
   ```python
   # experiments/evaluation/ragas_metrics.py (새 파일)
   from ragas import evaluate
   from ragas.metrics import (
       faithfulness,
       answer_relevance,
       context_precision,
       context_recall,
       context_relevancy
   )
   from datasets import Dataset
   
   def calculate_ragas_metrics(
       question: str,
       answer: str,
       contexts: List[str],  # 검색된 문서들
       ground_truth: Optional[str] = None
   ) -> Dict[str, float]:
       """RAGAS 메트릭 계산"""
       dataset = Dataset.from_dict({
           "question": [question],
           "answer": [answer],
           "contexts": [contexts],
           "ground_truth": [ground_truth] if ground_truth else [None]
       })
       
       result = evaluate(
           dataset,
           metrics=[
               faithfulness,
               answer_relevance,
               context_precision,
               context_recall,
               context_relevancy
           ]
       )
       
       return {
           "faithfulness": result["faithfulness"][0],
           "answer_relevance": result["answer_relevance"][0],
           "context_precision": result["context_precision"][0],
           "context_recall": result["context_recall"][0],
           "context_relevancy": result["context_relevancy"][0]
       }
   ```

3. **실험 러너에 통합**
   ```python
   # experiments/run_multiturn_experiment_v2.py
   from experiments.evaluation.ragas_metrics import calculate_ragas_metrics
   
   def _log_event(self, ..., retrieved_docs: List[Dict] = None):
       # ... 기존 코드 ...
       
       # RAGAS 메트릭 계산
       metrics = None
       if self.config.get('evaluation', {}).get('per_turn_metrics'):
           contexts = [doc.get('text', '') for doc in (retrieved_docs or [])]
           try:
               metrics = calculate_ragas_metrics(
                   question=question_text,
                   answer=answer_text,
                   contexts=contexts
               )
           except Exception as e:
               logger.warning(f"RAGAS 메트릭 계산 실패: {e}")
       
       event = {
           # ... 기존 필드들 ...
           "metrics": metrics  # ✅ 추가
       }
   ```

---

### 옵션 2: 사후 평가 스크립트 작성

**필요한 작업**:

1. **사후 평가 스크립트 작성**
   ```python
   # scripts/evaluate_ragas_metrics.py (새 파일)
   import json
   from experiments.evaluation.ragas_metrics import calculate_ragas_metrics
   
   def evaluate_existing_events(events_jsonl_path: str, output_path: str):
       """기존 events.jsonl에 RAGAS 메트릭 추가"""
       events = []
       with open(events_jsonl_path, 'r', encoding='utf-8') as f:
           for line in f:
               events.append(json.loads(line))
       
       # 각 이벤트에 대해 RAGAS 메트릭 계산
       for event in events:
           # 검색된 문서 가져오기 (retrieval_snapshot 또는 node_trace에서)
           contexts = get_retrieved_contexts(event)
           
           metrics = calculate_ragas_metrics(
               question=event['question']['text'],
               answer=event['answer']['text'],
               contexts=contexts
           )
           
           event['metrics'] = metrics
       
       # 업데이트된 events.jsonl 저장
       with open(output_path, 'w', encoding='utf-8') as f:
           for event in events:
               f.write(json.dumps(event, ensure_ascii=False) + '\n')
   ```

2. **실행**
   ```bash
   python scripts/evaluate_ragas_metrics.py \
     --events_path runs/2025-12-13_primary_v1/events.jsonl \
     --output_path runs/2025-12-13_primary_v1/events_with_metrics.jsonl
   ```

**단점**: 검색된 문서(`contexts`) 정보가 `events.jsonl`에 없으면 계산 불가

---

## 📝 요약

### 현재 상태

| 항목 | 상태 | 설명 |
|------|------|------|
| 설정 파일 | ✅ | `config.yaml`에 평가지표 설정됨 |
| 스키마 정의 | ✅ | `events_record.schema.json`에 metrics 필드 정의됨 |
| 계산 로직 | ❌ | RAGAS 메트릭 계산 코드 없음 |
| 저장 로직 | ❌ | `_log_event()`에서 metrics 필드 저장 안 함 |
| 데이터 존재 | ❌ | `events.jsonl`에 metrics 필드 없음 |
| 분석 스크립트 | ✅ | `summarize_run.py`는 metrics를 읽을 준비됨 |

### 핵심 문제

**RAGAS 평가지표가 설정은 되어 있으나, 실제로 계산하고 저장하는 코드가 실험 러너에 통합되지 않았습니다.**

### 해결 필요 사항

1. ✅ RAGAS 라이브러리 설치
2. ✅ RAGAS 메트릭 계산 함수 작성
3. ✅ 실험 러너에 통합 (각 턴마다 메트릭 계산 후 저장)
4. ✅ 검색된 문서(`contexts`) 정보를 이벤트에 포함

---

이 보고서를 바탕으로 RAGAS 평가지표 계산 기능을 추가하시겠습니까?

