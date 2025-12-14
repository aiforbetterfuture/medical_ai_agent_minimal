# 7번, 8번 배치 파일에 RAGAS 평가지표 계산 추가 완료

## 변경 사항

### 7_test_single_turn.bat
1. **안내 메시지 추가**: RAGAS 평가지표 계산이 포함된다는 안내 추가
2. **결과 확인 로직 추가**: RAGAS 메트릭이 정상적으로 계산되었는지 확인하는 스크립트 추가

### 8_test_multi_turn_single_patient.bat
1. **안내 메시지 추가**: RAGAS 평가지표 계산이 포함된다는 안내 추가
2. **결과 확인 로직 추가**: RAGAS 메트릭이 정상적으로 계산되었는지 확인하는 스크립트 추가

## RAGAS 계산 동작 방식

### 공통 스크립트 사용
- 7번, 8번, 9번 배치 파일 모두 `experiments\run_multiturn_experiment_v2.py`를 호출합니다.
- 이 스크립트에는 이미 RAGAS 계산 코드가 포함되어 있습니다.

### RAGAS 계산 조건
```python
if HAS_RAGAS_EVAL and self.config.get('evaluation', {}).get('per_turn_metrics'):
    # RAGAS 메트릭 계산
    ragas_metrics = calculate_ragas_metrics_safe(...)
```

### 설정 파일 확인
- `experiments/config.yaml`의 `evaluation.per_turn_metrics`에 다음이 포함되어 있습니다:
  - `faithfulness`
  - `answer_relevance`
  - `perplexity`
  - `judge_total_score`

## 추가된 기능

### 1. 안내 메시지
- 테스트 시작 전에 RAGAS 평가지표 계산이 포함된다는 안내 표시
- 사용자가 RAGAS 계산 여부를 명확히 알 수 있음

### 2. 결과 확인
- 테스트 완료 후 RAGAS 메트릭이 정상적으로 계산되었는지 확인
- 계산된 메트릭 종류를 표시
- 계산 실패 시 경고 메시지 표시

## 사용 방법

### 7번 파일 실행
```batch
7_test_single_turn.bat
```
- 실행 시 RAGAS 계산 안내 메시지 표시
- 완료 후 RAGAS 메트릭 확인 결과 표시

### 8번 파일 실행
```batch
8_test_multi_turn_single_patient.bat
```
- 실행 시 RAGAS 계산 안내 메시지 표시
- 완료 후 RAGAS 메트릭 확인 결과 표시

## 기대 효과

1. **사전 테스트 가능**: 7번, 8번 파일에서 RAGAS 계산이 정상 작동하는지 사전 확인 가능
2. **시간/토큰 절약**: 9번 파일 실행 전에 RAGAS 계산 문제를 발견하여 불필요한 실행 방지
3. **명확한 피드백**: RAGAS 계산 결과를 즉시 확인하여 문제를 조기에 발견

## 참고사항

- RAGAS 계산은 `experiments/evaluation/ragas_metrics.py`에서 수행됩니다.
- 계산 실패 시에도 실험은 계속 진행됩니다 (graceful degradation).
- 계산된 메트릭은 `events.jsonl`의 `metrics` 필드에 저장됩니다.

