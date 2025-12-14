# 평가 지표 개선 완료 보고서

## 개요

ChatGPT 제안을 기반으로 평가 지표 구현을 개선했습니다.

---

## 구현 완료 사항

### 1. ✅ ASS (Actionability/Specificity Score) 추가

**파일**: `experiments/evaluation/advanced_metrics.py`

**구현 내용**:
- **Turn 3 (운동)**: frequency, intensity, duration, stop_criteria 체크
- **Turn 4 (식단)**: 규칙 개수(3개 이상), 모니터링 지표, 추적/재검 체크
- **수학적 공식**: `ASS = (발견된 요소 수) / (요구 요소 수)`

**패턴 매칭**:
- 운동: `주 N회`, `중강도`, `N분`, `흉통`, `호흡곤란` 등
- 식단: 줄바꿈 기반 규칙 개수, `혈압`, `혈당`, `재검` 등

**통합**: `run_multiturn_experiment_v2.py`에 자동 계산 추가

---

### 2. ✅ SFS "환자-사실 주장" 판정 로직 개선

**파일**: `experiments/evaluation/advanced_metrics.py` (`_is_asserted` 함수)

**개선 내용**:
- **CLAIM_CUES 패턴 추가**: "현재", "당신", "검사결과", "수치가", "복용 중", "진단", "병력", "이미", "확인됨"
- **예시 패턴 강화**: "예를 들어", "일반적으로", "보통", "가능한 약물" 등
- **윈도우 기반 판정**: 엔티티 주변 50자 윈도우에서 패턴 검색

**효과**:
- 오탐(false positive) 감소
- "예시로 든 약물"과 "환자 복용 약물" 구분 정확도 향상

---

### 3. ✅ 후처리 모듈 추가

**파일**: `experiments/evaluation/post_hoc_evaluator.py`

**기능**:
- `events.jsonl`을 읽어서 평가 지표 재계산
- 에이전트 로직과 완전히 분리 (무결성 보장)
- CLI 지원: `python -m experiments.evaluation.post_hoc_evaluator --events ... --output ...`

**사용 예시**:
```bash
python -m experiments.evaluation.post_hoc_evaluator \
    --events runs/2025-12-14_experiment/events.jsonl \
    --output runs/2025-12-14_experiment/scores.jsonl \
    --config_dir config/eval
```

**장점**:
- 실험 후 별도 평가 실행 가능
- 기존 실험 결과 재평가 가능
- 에이전트 로직 변경 없이 평가 로직만 수정 가능

---

## 스키마 업데이트

**파일**: `experiments/schemas/events_record.schema.json`

**추가된 필드**:
```json
{
  "ASS": {
    "type": ["number", "null"],
    "description": "Actionability/Specificity Score (0.0~1.0), higher is better"
  }
}
```

---

## ChatGPT 제안 vs 현재 구현 비교

### ✅ 구현 완료

| 항목 | ChatGPT 제안 | 현재 구현 | 상태 |
|------|-------------|----------|------|
| **ASS 지표** | ✅ Turn 3/4 실행 가능성 측정 | ✅ 구현 완료 | ✅ 완료 |
| **SFS 판정 개선** | ✅ CLAIM_CUES 패턴 | ✅ 구현 완료 | ✅ 완료 |
| **후처리 모듈** | ✅ events.jsonl 읽기 | ✅ 구현 완료 | ✅ 완료 |

### ⚠️ 선택적 개선 (현재 구현으로 충분)

| 항목 | ChatGPT 제안 | 현재 구현 | 판단 |
|------|-------------|----------|------|
| **모듈 구조** | `evaluation/mt_eval/` 분리 | 단일 파일 | ✅ 현재 구조 유지 (관리 용이) |
| **FHIR 파서** | 독립 파서 | `synthea_slot_builder.py` 재사용 | ✅ 기존 구현 활용 (중복 방지) |

---

## 개선 효과

### 1. 평가 정확도 향상

- **ASS 추가**: 실행 가능한 답변과 일반론적 답변 구분 가능
- **SFS 개선**: 오탐 감소로 환각 감지 정확도 향상

### 2. 무결성 보장

- **후처리 모듈**: 에이전트 로직과 완전 분리
- **재평가 가능**: 기존 실험 결과 재계산 가능

### 3. 확장성

- **모듈화**: 평가 로직 독립적 수정 가능
- **CLI 지원**: 자동화 스크립트에 쉽게 통합

---

## 사용 방법

### 실시간 평가 (기존 방식)

멀티턴 실험 실행 시 자동으로 계산되어 `events.jsonl`에 저장됩니다.

```bash
python experiments/run_multiturn_experiment_v2.py
```

### 후처리 평가 (새로운 방식)

실험 후 별도로 평가 지표를 재계산합니다.

```bash
python -m experiments.evaluation.post_hoc_evaluator \
    --events runs/2025-12-14_experiment/events.jsonl \
    --output runs/2025-12-14_experiment/scores.jsonl
```

---

## 결과 확인

### events.jsonl에서 확인

```json
{
  "metrics": {
    "SFS": 0.90,
    "CSP": 0.1,
    "CUS_improved": 0.85,
    "ASS": 0.75
  }
}
```

### 후처리 결과 확인

```json
{
  "patient_id": "SYN_0001",
  "mode": "agent",
  "turn_id": 3,
  "metrics": {
    "SFS": 0.90,
    "CSP": 0.1,
    "CUS_improved": 0.85,
    "ASS": 0.75
  },
  "details": {
    "ASS": {
      "metric": "ASS",
      "score": 0.75,
      "elements_found": {
        "frequency": true,
        "intensity": true,
        "duration": true,
        "stop_criteria": false
      }
    }
  }
}
```

---

## 향후 개선 가능 사항

### 1. LLM Judge 옵션 (선택적)

SFS의 애매한 케이스를 LLM Judge로 2차 판정:
- 현재: 룰 기반만
- 개선: LLM Judge 옵션 추가 (비용 고려)

### 2. 모듈 구조 리팩토링 (선택적)

필요시 `evaluation/mt_eval/` 구조로 분리:
- 현재: 단일 파일 (관리 용이)
- 개선: 모듈 분리 (확장성 높음)

---

## 결론

### ✅ 완료된 개선

1. **ASS 지표 추가** - 실행 가능성 측정
2. **SFS 판정 로직 개선** - 오탐 감소
3. **후처리 모듈 추가** - 무결성 보장

### ✅ 현재 구현의 장점

- 실시간 계산 + 후처리 옵션 (하이브리드)
- 기존 인프라 재사용 (중복 방지)
- 단일 파일 구조 (관리 용이)

### 📊 평가 지표 완성도

- **SFS**: ✅ 완료 (개선됨)
- **CSP**: ✅ 완료
- **CUS_improved**: ✅ 완료
- **ASS**: ✅ 완료 (새로 추가)

**모든 필수 평가 지표가 구현 완료되었습니다.**

---

**최종 업데이트**: 2025-12-14
**구현 완료**: ✅

