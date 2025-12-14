# CUS, UR, CCR 평가지표 통합 완료

## 변경 사항

### 1. `experiments/run_multiturn_experiment_v2.py`
- **멀티턴 컨텍스트 메트릭 계산 모듈 import 추가**
  - `compute_cus`, `compute_ur`, `ccr_rule_checks` 함수 import
  - `get_question_metadata` 함수 import
  - `HAS_MULTITURN_METRICS` 플래그 추가

- **`run()` 메서드에 CUS, UR, CCR 계산 로직 추가**
  - 질문 뱅크에서 `required_slots`와 `update_key` 추출
  - 환자 프로필 로드
  - LLM 모드와 Agent 모드 모두 지원
  - 계산된 메트릭을 `events.jsonl`에 저장

### 2. `experiments/schemas/events_record.schema.json`
- **메트릭 스키마에 CUS, UR, CCR 필드 추가**
  - `CUS`: Context Utilization Score (0.0~1.0)
  - `UR`: Update Responsiveness (0.0~1.0)
  - `CCR`: Context Contradiction Rate (0.0~1.0)

## 계산 로직

### CUS (Context Utilization Score)
- **조건**: `required_slots`가 있을 때만 계산
- **LLM 모드**: `patient_profile`만 사용 (slots_state 없음)
- **Agent 모드**: `slots_state` 우선, 없으면 `patient_profile` 사용
- **점수**: 0.0~1.0 (높을수록 좋음)

### UR (Update Responsiveness)
- **조건**: `update_key`가 있을 때만 계산
- **LLM 모드**: `turn_updates`가 없으므로 계산 불가 (None)
- **Agent 모드**: `turn_updates` 사용
- **점수**: 0.0~1.0 (높을수록 좋음)

### CCR (Context Contradiction Rate)
- **조건**: 모든 턴에서 계산
- **LLM 모드**: `slots_state`가 없으므로 빈 딕셔너리 사용 (모순 없음으로 간주)
- **Agent 모드**: `slots_state` 사용
- **점수**: 0.0~1.0 (낮을수록 좋음, 0=모순 없음, 1=모순 있음)

## 스캐폴드 무결성

### ✅ Import 경로 확인
- `experiments.evaluation.multiturn_context_metrics` ✅
- `experiments.evaluation.question_bank_mapper` ✅

### ✅ 함수 시그니처 확인
- `compute_cus(answer, required_slots, patient_profile, slots_state)` ✅
- `compute_ur(answer, update_key, turn_updates, question_text)` ✅
- `ccr_rule_checks(answer, slots_state)` ✅
- `get_question_metadata(question_item, question_text)` ✅

### ✅ 설정 파일 확인
- `experiments/config.yaml`의 `evaluation.multiturn_metrics` ✅
- 설정 값: `["context_utilization", "context_contradiction", "update_responsiveness"]` ✅

### ✅ 스키마 확인
- `experiments/schemas/events_record.schema.json`에 CUS, UR, CCR 필드 추가 ✅

## 적용 범위

### 7번 파일 (`7_test_single_turn.bat`)
- ✅ `experiments\run_multiturn_experiment_v2.py` 호출
- ✅ CUS, UR, CCR 자동 계산

### 8번 파일 (`8_test_multi_turn_single_patient.bat`)
- ✅ `experiments\run_multiturn_experiment_v2.py` 호출
- ✅ CUS, UR, CCR 자동 계산

### 9번 파일 (`9_run_full_experiment.bat`)
- ✅ `experiments\run_multiturn_experiment_v2.py` 호출
- ✅ CUS, UR, CCR 자동 계산

## 에러 처리

### Graceful Degradation
- 모든 메트릭 계산은 `try-except` 블록으로 감싸져 있음
- 계산 실패 시에도 실험은 계속 진행됨
- 에러는 경고 레벨로 로깅됨

### 안전장치
- `HAS_MULTITURN_METRICS` 플래그로 모듈 존재 여부 확인
- 설정 파일의 `multiturn_metrics` 확인
- 각 메트릭 계산마다 개별 `try-except` 블록

## 메트릭 저장 형식

### events.jsonl
```json
{
  "metrics": {
    "faithfulness": 0.85,
    "answer_relevance": 0.78,
    "perplexity": 16.23,
    "CUS": 0.75,
    "UR": 0.80,
    "CCR": 0.0
  }
}
```

### 메트릭 통합 로직
- RAGAS 메트릭과 멀티턴 컨텍스트 메트릭을 하나의 딕셔너리로 통합
- `_detail` 필드는 제외하고 점수만 저장
- 모든 메트릭이 `events.jsonl`의 `metrics` 필드에 저장됨

## 테스트 방법

### 7번 파일 실행
```batch
7_test_single_turn.bat
```
- 실행 후 `events.jsonl`에서 `metrics` 필드 확인
- CUS, UR, CCR 값이 있는지 확인

### 8번 파일 실행
```batch
8_test_multi_turn_single_patient.bat
```
- 실행 후 `events.jsonl`에서 `metrics` 필드 확인
- 턴별로 CUS, UR, CCR 값이 있는지 확인

### 9번 파일 실행
```batch
9_run_full_experiment.bat
```
- 실행 후 `events.jsonl`에서 `metrics` 필드 확인
- 모든 턴에서 CUS, UR, CCR 값이 있는지 확인

## 참고사항

- LLM 모드에서는 `slots_state`와 `turn_updates`가 없으므로:
  - CUS: `patient_profile`만 사용하여 계산
  - UR: 계산 불가 (None)
  - CCR: 빈 딕셔너리 사용 (모순 없음으로 간주)

- Agent 모드에서는 `slots_state`와 `turn_updates`를 사용:
  - CUS: `slots_state` 우선, 없으면 `patient_profile` 사용
  - UR: `turn_updates` 사용
  - CCR: `slots_state` 사용

- 모든 메트릭은 `experiments/evaluation/multiturn_context_metrics.py`에서 계산됩니다.
- 질문 뱅크 메타데이터는 `experiments/evaluation/question_bank_mapper.py`에서 추출됩니다.

