# Perplexity 평가지표 통합 완료 보고서

## ✅ 완료된 작업

### 1. Perplexity 계산 함수 추가

**파일**: `experiments/evaluation/ragas_metrics.py`

다음 함수들이 추가되었습니다:

1. **`calculate_perplexity()`**: 기본 Perplexity 계산 함수
   - 근사 방법 사용 (답변 길이와 복잡도 기반)
   - PersonaChat 논문 범위(10-40)를 고려한 휴리스틱
   - 추가 API 호출 없이 빠르게 계산 가능

2. **`calculate_perplexity_with_logprobs()`**: 정확한 Perplexity 계산 함수
   - OpenAI logprobs 사용 (추가 API 호출 필요)
   - PersonaChat 논문 방식: `PPL = exp(-1/N * Σ log P(w_i))`
   - 현재는 근사 방법으로 폴백

3. **`calculate_ragas_metrics_safe()` 확장**:
   - `include_perplexity` 파라미터 추가
   - `conversation_history` 파라미터 추가 (Perplexity 계산용)
   - RAGAS 메트릭과 함께 Perplexity 자동 계산

---

### 2. 실험 러너 통합

**파일**: `experiments/run_multiturn_experiment_v2.py`

#### Agent 모드
- RAGAS 메트릭 계산 시 Perplexity 자동 포함
- `conversation_history` 전달하여 컨텍스트 반영

#### LLM 모드
- RAGAS 메트릭 계산 시 Perplexity 자동 포함
- 검색된 문서가 없어도 Perplexity는 계산 가능

---

### 3. 스키마 업데이트

**파일**: `experiments/schemas/events_record.schema.json`

`metrics` 필드에 `perplexity` 추가:
```json
{
  "metrics": {
    "perplexity": {"type": ["number", "null"], "description": "Perplexity (next-token prediction uncertainty), lower is better"}
  }
}
```

---

### 4. 설정 파일 업데이트

**파일**: `experiments/config.yaml`

`evaluation.per_turn_metrics`에 `perplexity` 추가:
```yaml
evaluation:
  per_turn_metrics: ["faithfulness", "answer_relevance", "perplexity", "judge_total_score"]
```

---

## 📊 Perplexity 계산 방식

### 현재 구현 (근사 방법)

**수식**: 휴리스틱 기반 근사
```
complexity_score = answer_chars / answer_length
approximate_ppl = 15.0 + (complexity_score - 4.0) * 3.0
```

**특징**:
- ✅ 추가 API 호출 없음 (빠름, 비용 없음)
- ✅ 실험 진행 중단 없음
- ⚠️ 정확도는 논문 방식보다 낮음

**범위**: PersonaChat 논문 범위(10-40)를 고려
- 일반론적 답변: 낮은 perplexity (10-20)
- 개인화된 답변: 높은 perplexity (20-40)

---

### 향후 개선 방안 (정확한 계산)

**정확한 방법**: 답변 생성 시 logprobs 함께 받기

```python
# 답변 생성 시 logprobs 요청
response = client.chat.completions.create(
    model=model,
    messages=messages,
    logprobs=True,  # 토큰별 확률 요청
    top_logprobs=1
)

# Perplexity 계산
token_logprobs = [t.logprob for t in response.choices[0].logprobs.content]
avg_log_prob = np.mean(token_logprobs)
perplexity = np.exp(-avg_log_prob)
```

**장점**:
- ✅ PersonaChat 논문과 동일한 방식
- ✅ 정확한 계산

**단점**:
- ⚠️ 추가 API 호출 필요 (비용 발생)
- ⚠️ 답변 생성 시점에 logprobs를 받아야 함

---

## 🎯 사용 방법

### 자동 계산 (현재 구현)

다음 멀티턴 테스트 실행 시:
- 각 턴마다 자동으로 Perplexity 계산
- `events.jsonl`에 `metrics.perplexity` 필드로 저장
- `summary.json`에 통계 분석 결과 포함

### 결과 확인

```python
import json

# events.jsonl에서 확인
with open('runs/2025-12-13_primary_v1/events.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        event = json.loads(line)
        if event.get('metrics', {}).get('perplexity'):
            print(f"Perplexity: {event['metrics']['perplexity']}")
```

---

## 📝 참고사항

### Perplexity 해석

- **낮은 값 (10-20)**: 예측하기 쉬운 일반론적 답변
- **높은 값 (20-40)**: 개인화된 정보가 많아 예측이 어려운 답변
- **PersonaChat 논문**: 낮을수록 좋음 (더 일관된 답변)

### 현재 구현의 한계

1. **근사 방법 사용**: 실제 logprobs를 사용하지 않음
2. **정확도 제한**: 논문 방식보다 정확도가 낮을 수 있음
3. **향후 개선**: 답변 생성 시 logprobs를 함께 받는 방식으로 개선 권장

---

## ✅ 통합 완료

- ✅ Perplexity 계산 함수 추가
- ✅ 실험 러너에 통합
- ✅ 스키마 업데이트
- ✅ 설정 파일 업데이트
- ✅ 자동 계산 활성화

다음 실험 실행 시 Perplexity가 자동으로 계산되어 저장됩니다! 🎉

