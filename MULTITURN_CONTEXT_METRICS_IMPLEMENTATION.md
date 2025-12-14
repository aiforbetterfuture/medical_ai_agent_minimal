# 멀티턴 컨텍스트 평가 지표 구현 완료 보고서

## 📋 구현 완료 항목

### ✅ 1. 질문은행 메타데이터 매핑
- **파일**: `experiments/evaluation/question_bank_mapper.py`
- **기능**: `required_fields` → `required_slots` 변환, `update_key` 추출
- **상태**: 완료

### ✅ 2. 멀티턴 컨텍스트 평가 지표 계산 함수
- **파일**: `experiments/evaluation/multiturn_context_metrics.py`
- **구현된 지표**:
  - **CUS (Context Utilization Score)**: required_slots를 답변에서 사용했는가?
  - **UR (Update Responsiveness)**: 새로 들어온 update_key가 답변에 반영되었는가?
  - **CCR (Context Contradiction Rate)**: 이전 턴 정보와 모순되는가? (룰 기반)
- **상태**: 완료

### ✅ 3. JSONL 로더 및 레코드 빌더
- **파일**: 
  - `experiments/evaluation/io/jsonl.py`: JSONL I/O 유틸리티
  - `experiments/evaluation/build_records.py`: events.jsonl에서 평가 레코드 빌드
- **상태**: 완료

### ✅ 4. events.jsonl 로깅 보완
- **파일**: `experiments/run_multiturn_experiment_v2.py`
- **추가된 필드**:
  - `metadata.slots_state`: 현재 슬롯 상태
  - `metadata.turn_updates`: 이번 턴에 새로 추가된 업데이트
  - `metadata.retrieved_docs`: 검색된 문서 요약 (최대 10개)
- **상태**: 완료

### ✅ 5. 평가 파이프라인 스크립트
- **파일**: `scripts/evaluate_metrics_from_run.py`
- **기능**:
  - events.jsonl에서 레코드 빌드
  - CUS, UR, CCR 지표 계산
  - 모드별/턴별 집계
  - Paired comparison (Agent - LLM) 분석
- **상태**: 완료

---

## 🚀 사용 방법

### 1. 실험 실행 (기존과 동일)
```bash
python experiments/run_multiturn_experiment_v2.py --config experiments/config.yaml
```

실험 실행 시 자동으로 `events.jsonl`에 다음 필드가 추가됩니다:
- `metadata.slots_state`
- `metadata.turn_updates`
- `metadata.retrieved_docs`

### 2. 평가 지표 계산
```bash
python scripts/evaluate_metrics_from_run.py --run_dir runs/2025-12-13_primary_v1
```

**출력 파일**:
- `runs/<run_id>/eval/metrics_per_record.jsonl`: 레코드별 메트릭
- `runs/<run_id>/eval/metrics_summary.json`: 집계 요약

**출력 예시**:
```json
{
  "by_mode": {
    "llm": {
      "CUS": 0.65,
      "UR": 0.45,
      "CCR_rule_obvious": 0.10
    },
    "agent": {
      "CUS": 0.82,
      "UR": 0.78,
      "CCR_rule_obvious": 0.05
    }
  },
  "paired_agent_minus_llm_mean": {
    "CUS": 0.17,
    "UR": 0.33,
    "CCR_rule_obvious": -0.05
  }
}
```

---

## 📊 지표 설명

### CUS (Context Utilization Score)
- **의미**: 질문이 요구하는 `required_slots`를 답변이 실제로 반영했는가?
- **범위**: 0.0 ~ 1.0 (높을수록 좋음)
- **계산**: `사용한 required_slots 개수 / 전체 required_slots 개수`

### UR (Update Responsiveness)
- **의미**: 새로 들어온 수치/증상 변화가 답변에서 우선 반영되었는가?
- **범위**: 0.0 ~ 1.0 (높을수록 좋음)
- **계산**: `반영된 업데이트 개수 / 전체 업데이트 개수`

### CCR (Context Contradiction Rate)
- **의미**: 이전 턴 정보와 모순되는가?
- **범위**: 0.0 또는 1.0 (낮을수록 좋음, 0=모순 없음, 1=모순 있음)
- **계산**: 룰 기반 (명백한 모순만 체크)

---

## 🔧 기술적 세부사항

### 슬롯 상태 추출
- `ProfileStore`에서 슬롯 상태를 추출하여 `slots_state` 딕셔너리로 변환
- 구조: `{"demographics": {...}, "conditions": [...], "medications": [...], ...}`

### 턴 업데이트 계산
- 이전 턴 슬롯 상태와 현재 턴 슬롯 상태를 비교
- 새로 추가된 labs, vitals, symptoms, medications를 `turn_updates`로 추출

### 질문은행 메타데이터 매핑
- `required_fields` (예: `["AGE", "SEX_KO", "COND1_KO"]`)를 `required_slots` (예: `["demographics.age", "demographics.gender", "conditions"]`)로 변환
- Turn 3의 경우 `update_key`를 `"labs"` 또는 `"vitals"`로 설정

---

## ⚠️ 주의사항

1. **LLM Judge 미구현**: 현재는 룰 기반 CCR만 구현됨. 의학적 모순 판정을 위해서는 LLM Judge 추가 필요
2. **슬롯 매핑 정확도**: 답변 텍스트에서 슬롯 값 추출의 정확도는 한계가 있을 수 있음 (동의어, 변형 표현 처리 필요)
3. **update_key 추출**: 현재는 카테고리 레벨(`"labs"`, `"vitals"`)만 지원. 구체적인 항목(`"labs.hba1c"`)은 질문 텍스트에서 추출 필요

---

## 📝 다음 단계 (선택적)

1. **LLM Judge 통합**: CCR의 의학적 모순 판정을 위한 LLM Judge 추가
2. **슬롯 매핑 개선**: 동의어 사전, 정규식 패턴 확장
3. **구체적 update_key 추출**: 질문 텍스트에서 실제 lab/vital 이름 추출
4. **기존 분석 파이프라인 통합**: `summary.json`에 멀티턴 컨텍스트 지표 추가

---

**작성일**: 2025-12-13  
**버전**: 1.0

