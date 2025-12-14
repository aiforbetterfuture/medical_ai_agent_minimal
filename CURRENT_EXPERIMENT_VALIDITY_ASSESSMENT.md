# 현재 실행 중인 실험 유효도 평가

## ⚠️ 현재 상황

**78번째 환자까지 진행 중인 멀티턴 실험**에서 Synthea 환자 데이터의 플레이스홀더가 비어있는 것으로 확인되었습니다.

## 🔍 문제 원인 분석

### 1. 실행 시점 문제

현재 실행 중인 실험은 **수정 전 코드**로 시작되었을 가능성이 높습니다:

- **수정 전**: `_fill_placeholders()` 함수가 잘못된 데이터 구조를 가정
  ```python
  # 잘못된 코드 (이전)
  age = profile_card.get('age')  # ❌ 최상위에 없음
  conditions = profile_card.get('conditions')  # ❌ 최상위에 없음
  ```

- **수정 후**: 올바른 중첩 구조에서 데이터 추출
  ```python
  # 올바른 코드 (현재)
  demographics = profile_card.get('demographics', {})
  age = demographics.get('age_years', '?')
  clinical = profile_card.get('clinical_summary', {})
  conditions = clinical.get('conditions', [])
  ```

### 2. Python 모듈 캐싱 문제

Python은 모듈을 한 번만 로드하고 메모리에 캐시합니다. 따라서:
- 실험이 시작된 후 코드를 수정해도 **이미 로드된 모듈은 이전 버전을 사용**합니다
- 실험을 중단하고 다시 시작해야 수정된 코드가 적용됩니다

## 📊 유효도 평가

### 현재 실험의 유효도: ⚠️ **낮음**

**이유**:
1. ❌ 플레이스홀더가 비어있어 질문이 제대로 생성되지 않음
   - 예: "저는 {AGE}세 {SEX_KO}이고 {COND1_KO}이(가) 있어요..."
   - 실제 환자 데이터가 반영되지 않음

2. ❌ 답변 품질에 부정적 영향
   - 빈 슬롯으로 질문이 생성되면 AI가 맥락을 파악하기 어려움
   - 개인화된 답변 생성 불가능

3. ❌ 실험 결과의 신뢰도 저하
   - 멀티턴 대화의 핵심인 "개인화된 컨텍스트 유지" 테스트 불가능
   - RAGAS 메트릭 (Faithfulness, Answer Relevance 등)이 부정확할 수 있음

### 권장 사항

#### 옵션 1: 현재 실험 중단 및 재시작 (권장) ✅

**장점**:
- 수정된 코드로 올바른 실험 수행 가능
- 유효한 결과 확보

**단점**:
- 78명까지 진행한 작업 손실
- 시간 재투자 필요

**실행 방법**:
```bash
# 1. 현재 실험 중단 (Ctrl+C)
# 2. 수정된 코드 확인
# 3. 실험 재시작
9_run_full_experiment.bat
```

#### 옵션 2: 현재 실험 완료 후 재실험

**장점**:
- 현재 실험 완료 (데이터 수집 목적)
- 이후 재실험으로 비교 가능

**단점**:
- 현재 실험 결과는 유효도가 낮음
- 시간 낭비 가능성

## 🔧 추가된 디버깅 기능

수정된 코드에 **디버깅 로그**를 추가했습니다:

```python
# 플레이스홀더가 남아있는지 확인
remaining_placeholders = [p for p in ['{AGE}', '{SEX_KO}', ...] if p in question_text]
if remaining_placeholders:
    logger.warning(f"⚠️ 플레이스홀더가 채워지지 않았습니다: {remaining_placeholders}")
    logger.warning(f"   원본 템플릿: {original_template[:150]}")
    logger.warning(f"   채워진 질문: {question_text[:150]}")
    logger.warning(f"   프로필 카드 키: {list(profile_card.keys())}")
```

**다음 실험부터는**:
- 플레이스홀더가 비어있으면 경고 메시지 출력
- 원인 파악이 쉬워짐

## 📋 확인 방법

### 현재 실험 결과 확인

실험 결과 파일에서 질문 필드를 확인:

```bash
# events.jsonl 파일 확인
python -c "
import json
with open('runs/2025-12-13_primary_v1/events.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        event = json.loads(line)
        if '{' in event.get('question', '') and '}' in event.get('question', ''):
            print(f\"환자: {event.get('patient_id')}, 턴: {event.get('turn_id')}\")
            print(f\"질문: {event.get('question')[:200]}\")
            print()
"
```

**예상 결과**:
- 플레이스홀더가 비어있으면: `"저는 {AGE}세 {SEX_KO}이고..."`
- 플레이스홀더가 채워지면: `"저는 67세 남성이고..."`

## ✅ 최종 권장사항

### 1. 현재 실험 중단 및 재시작 (강력 권장)

**이유**:
- 현재 실험 결과는 유효도가 낮아 분석 가치가 제한적
- 수정된 코드로 올바른 실험 수행 필요
- 시간 투자 대비 결과 품질이 중요

**실행 순서**:
1. 현재 실험 중단 (Ctrl+C)
2. 수정된 코드 확인 (`experiments/run_multiturn_experiment_v2.py`)
3. 실험 재시작: `9_run_full_experiment.bat`

### 2. 재시작 전 확인사항

- ✅ `experiments/run_multiturn_experiment_v2.py`의 `_fill_placeholders()` 함수가 수정되었는지 확인
- ✅ 디버깅 로그가 추가되었는지 확인
- ✅ 프로필 카드 파일이 올바른 구조인지 확인 (`data/patients/profile_cards/SYN_0001.json`)

### 3. 재시작 후 모니터링

실험 시작 후 첫 몇 환자의 로그를 확인:

```bash
# 실험 실행 중 로그 확인
# 플레이스홀더 경고가 없어야 함
```

**정상 출력 예시**:
```
Turn 1:
  질문: 저는 67세 남성이고 당뇨병이(가) 있어요...
  (플레이스홀더 경고 없음)
```

**비정상 출력 예시**:
```
⚠️ 플레이스홀더가 채워지지 않았습니다: ['{AGE}', '{SEX_KO}']
   원본 템플릿: 저는 {AGE}세 {SEX_KO}이고...
   채워진 질문: 저는 {AGE}세 {SEX_KO}이고...
```

## 📝 결론

**현재 실행 중인 실험(78번째 환자까지)의 유효도는 낮습니다.**

**권장 조치**:
1. ✅ 현재 실험 중단
2. ✅ 수정된 코드로 재시작
3. ✅ 디버깅 로그로 문제 모니터링

이렇게 하면 **유효한 실험 결과**를 확보할 수 있습니다.

