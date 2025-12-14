# 멀티턴 스크립트 자동 생성 가이드

## 개요

기존 질문 뱅크 방식 대신, Synthea 프로필 카드에서 자동으로 5턴 멀티턴 질문 스크립트를 생성하는 새로운 방식입니다.

## 주요 특징

1. **자동 슬롯 추출**: Synthea 프로필 카드에서 환자 정보를 자동으로 추출
2. **개인화된 질문**: 각 환자마다 고유한 5턴 질문 생성
3. **맥락 의존 설계**: 3·4턴 질문은 의도적으로 맥락이 필요하지만 질문에는 드러나지 않게 설계
4. **평가 준비**: 슬롯 정보를 로그에 포함하여 평가 가능

## 사용 방법

### 1. 멀티턴 스크립트 생성

```bash
# 방법 1: Python 스크립트 직접 실행
python experiments/generate_multiturn_scripts_from_fhir.py \
    --profile_cards_dir "data/patients/profile_cards" \
    --out "data/multiturn_scripts/scripts_5turn.jsonl" \
    --max_patients 80 \
    --seed 42

# 방법 2: Windows 배치 파일 사용
generate_multiturn_scripts.bat
```

### 2. 실험 설정에서 멀티턴 스크립트 모드 활성화

`experiments/config.yaml` 파일에서 다음 설정을 추가/수정:

```yaml
multiturn_scripts:
  enabled: true  # true면 자동 생성 스크립트 사용, false면 기존 question_bank 사용
  scripts_path: "data/multiturn_scripts/scripts_5turn.jsonl"
  slot_builder_config_dir: "config/synthea"
```

### 3. 실험 실행

기존과 동일하게 실험을 실행하면 됩니다:

```bash
python experiments/run_multiturn_experiment_v2.py --config experiments/config.yaml
```

또는

```bash
9_run_full_experiment.bat
```

## 질문 생성 규칙

### Turn 1: 인구통계 + 주요 질환 + 증상 (필수 명시)
- 나이, 성별, primary condition, chief symptom을 명시적으로 포함

### Turn 2: 약물 + 검사/바이탈 + 시술 (명시)
- 복용 약물, 검사 결과, 바이탈, 주요 시술을 명시

### Turn 3: 운동 (의도적으로 맥락 비명시)
- 질환/수치/약을 질문에 재언급하지 않음
- Agent는 Turn 1, 2의 정보를 메모리에서 끌어와야 함

### Turn 4: 식단 (의도적으로 맥락 비명시)
- 질환/수치/약을 질문에 재언급하지 않음
- Agent는 Turn 1, 2의 정보를 메모리에서 끌어와야 함

### Turn 5: 통합 4주 플랜
- 앞 4턴의 정보를 종합하여 실행 계획 제시

## 슬롯 추출 규칙

### Primary Condition 선택
- `config/synthea/condition_priority.yaml`의 우선순위 기반
- Active 상태의 만성질환 우선
- 심혈관/신장/당뇨 계열이 우선순위 높음

### 증상 생성
- `config/synthea/symptom_map.yaml`의 매핑 규칙 기반
- Primary condition에 따라 적절한 증상 자동 생성

### 검사 결과 선택
- Primary condition과 연관된 검사 우선 선택
- 최신 측정치만 사용 (중복 제거)

## 출력 형식

생성된 스크립트는 JSONL 형식으로 저장됩니다:

```json
{
  "patient_id": "SYN_0001",
  "slots": {
    "age": 67,
    "sex": "남성",
    "primary_condition": "Type 2 Diabetes Mellitus",
    "comorbidities": ["Hypertension", "Hyperlipidemia"],
    "key_meds": ["Metformin", "Lisinopril"],
    "key_vitals": {"bp_systolic": "131mmHg", "bp_diastolic": "74mmHg"},
    "key_labs": {"hba1c": "6.24%", "glucose": "118mg/dL"},
    "major_procedures": [],
    "chief_symptom": "피로"
  },
  "turns": [
    {
      "turn_id": 1,
      "question": "67세 남성인데 Type 2 Diabetes Mellitus이(가) 있고, 최근 피로가 심해졌어요. 무엇부터 점검해야 하나요?"
    },
    ...
  ]
}
```

## 평가

이벤트 로그에 `slots_truth` 필드가 포함되어 다음 평가 지표 계산에 사용됩니다:

- **CUS (Context Utilization Score)**: 맥락 재사용 점수
- **SFS (Slot Factuality Score)**: 슬롯 사실성 점수
- **CSP (Contraindication/Safety Penalty)**: 금기/안전 감점
- **MCS (Multi-turn Consistency Score)**: 멀티턴 일관성 점수
- **ASS (Actionability/Specificity Score)**: 실행 가능성 점수

## 주의사항

1. **스크립트 생성 후 실험 실행**: 실험 전에 반드시 스크립트를 생성해야 합니다
2. **설정 파일 확인**: `config.yaml`에서 `multiturn_scripts.enabled`가 `true`인지 확인하세요
3. **기존 질문 뱅크와 호환**: `enabled: false`로 설정하면 기존 질문 뱅크 방식을 사용합니다

