# RAGAS 자동 계산 여부 설명

## ❌ RAGAS 라이브러리 설치만으로는 자동 계산되지 않습니다

**중요**: RAGAS 라이브러리를 설치하는 것만으로는 평가지표가 자동으로 계산되지 않습니다.

---

## 🔍 RAGAS 작동 방식

### 1. RAGAS는 라이브러리입니다

RAGAS는 **평가지표를 계산하는 도구**이지, 자동으로 실행되는 서비스가 아닙니다.

### 2. 명시적 호출이 필요합니다

RAGAS를 사용하려면 **코드에서 명시적으로 호출**해야 합니다:

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevance,
    context_precision,
    context_recall,
    context_relevancy
)
from datasets import Dataset

# 1. 데이터 준비
dataset = Dataset.from_dict({
    "question": ["질문 텍스트"],
    "answer": ["답변 텍스트"],
    "contexts": [["검색된 문서 1", "검색된 문서 2", ...]],
    "ground_truth": ["정답 (선택사항)"]
})

# 2. 명시적으로 evaluate() 호출
results = evaluate(
    dataset,
    metrics=[
        faithfulness,
        answer_relevance,
        context_precision,
        context_recall,
        context_relevancy
    ]
)

# 3. 결과 확인
print(results["faithfulness"])  # 예: [0.85]
print(results["answer_relevance"])  # 예: [0.78]
```

---

## 📋 현재 상황

### ✅ 설치 완료 (이제 가능)

`0_setup_env.bat`에 ragas 설치 코드를 추가했습니다:
- `ragas` 라이브러리 설치
- `datasets` 라이브러리 설치 (RAGAS 의존성)

### ❌ 아직 계산되지 않음

**이유**: 실험 러너(`experiments/run_multiturn_experiment_v2.py`)에 RAGAS 호출 코드가 없음

---

## 🔧 자동 계산을 위한 필요 작업

### 옵션 1: 실험 러너에 통합 (권장)

각 턴마다 답변 생성 후 자동으로 RAGAS 메트릭을 계산하도록 실험 러너를 수정:

```python
# experiments/run_multiturn_experiment_v2.py

from experiments.evaluation.ragas_metrics import calculate_ragas_metrics

def _run_agent_mode(self, ...):
    # ... 기존 코드 ...
    
    # 답변 생성 후
    answer_text = final_state.get('final_answer', '')
    retrieved_docs = final_state.get('retrieved_docs', [])
    
    # RAGAS 메트릭 계산
    metrics = None
    if self.config.get('evaluation', {}).get('per_turn_metrics'):
        contexts = [doc.get('text', '') for doc in retrieved_docs]
        try:
            metrics = calculate_ragas_metrics(
                question=question_text,
                answer=answer_text,
                contexts=contexts
            )
        except Exception as e:
            logger.warning(f"RAGAS 메트릭 계산 실패: {e}")
    
    # 이벤트에 metrics 포함
    event = {
        # ... 기존 필드들 ...
        "metrics": metrics  # ✅ 추가
    }
```

### 옵션 2: 사후 평가 스크립트

실험 완료 후 별도 스크립트로 계산:

```bash
python scripts/evaluate_ragas_metrics.py \
  --events_path runs/2025-12-13_primary_v1/events.jsonl \
  --output_path runs/2025-12-13_primary_v1/events_with_metrics.jsonl
```

---

## 📝 요약

| 항목 | 상태 | 설명 |
|------|------|------|
| 라이브러리 설치 | ✅ | `0_setup_env.bat`에 추가됨 |
| 자동 계산 | ❌ | **설치만으로는 자동 계산 안 됨** |
| 명시적 호출 필요 | ✅ | 코드에서 `evaluate()` 호출 필요 |
| 실험 러너 통합 | ❌ | 아직 구현 안 됨 |

---

## 🎯 다음 단계

1. ✅ **완료**: `0_setup_env.bat`에 ragas 설치 추가
2. ⏳ **필요**: RAGAS 메트릭 계산 함수 작성 (`experiments/evaluation/ragas_metrics.py`)
3. ⏳ **필요**: 실험 러너에 통합 (`experiments/run_multiturn_experiment_v2.py`)

**결론**: RAGAS 라이브러리를 설치하는 것만으로는 자동 계산되지 않습니다. 실험 러너에 RAGAS 호출 코드를 추가해야 합니다.

