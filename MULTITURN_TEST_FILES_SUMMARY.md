# 멀티턴 테스트 파일 구조 요약

## 개요

멀티턴 실험을 단계별로 실행하기 위해 기존의 `5_run_multiturn_test.bat`를 세분화하여 6개의 독립적인 배치 파일로 분리했습니다.

---

## 파일 목록

### Windows 배치 파일

| 번호 | 파일명 | 목적 | 소요 시간 | API 비용 |
|------|--------|------|-----------|----------|
| 5 | `5_run_multiturn_test.bat` | 메뉴 (전체 통합) | - | - |
| 6 | `6_check_data_integrity.bat` | 데이터 무결성 검사 | 10-20초 | $0 |
| 7 | `7_test_single_turn.bat` | 단일 턴 테스트 (1명×1턴×2모드) | 1-2분 | $0.01-0.02 |
| 8 | `8_test_multi_turn_single_patient.bat` | 멀티턴 단일 환자 (1명×5턴×2모드) | 5-10분 | $0.10-0.20 |
| 9 | `9_run_full_experiment.bat` | 전체 실험 (78명×5턴×2모드) | 8-12시간 | $15-25 |
| 10 | `10_analyze_results.bat` | 결과 분석 및 시각화 | 1-2분 | $0 |

### Linux/Mac 쉘 스크립트

| 번호 | 파일명 | 비고 |
|------|--------|------|
| 6 | `6_check_data_integrity.sh` | Linux/Mac용 |
| 7 | `7_test_single_turn.sh` | (향후 작성 예정) |
| 8 | `8_test_multi_turn_single_patient.sh` | (향후 작성 예정) |
| 9 | `9_run_full_experiment.sh` | (향후 작성 예정) |
| 10 | `10_analyze_results.sh` | (향후 작성 예정) |

---

## 각 파일의 역할

### 5_run_multiturn_test.bat (메뉴)

**역할:** 사용자에게 단계별 실행 옵션을 제공하는 메뉴 인터페이스

**기능:**
- 6-10번 파일 중 하나를 선택하여 실행
- 전체 자동 실행 옵션 (A)
- 각 단계의 설명 및 예상 소요 시간 표시

**사용법:**
```bash
5_run_multiturn_test.bat
# 메뉴에서 원하는 단계 선택 (6/7/8/9/10/A/Q)
```

**선택 옵션:**
- `6`: 데이터 무결성 검사
- `7`: 단일 턴 테스트
- `8`: 멀티턴 단일 환자 테스트
- `9`: 전체 실험 실행
- `10`: 결과 분석
- `A`: 전체 자동 실행 (6→7→8→9→10)
- `Q`: 종료

---

### 6_check_data_integrity.bat (데이터 검사)

**역할:** 실험에 필요한 모든 데이터 파일과 설정이 올바르게 준비되었는지 확인

**검사 항목:**
1. 가상환경 존재 확인
2. `.env` 파일 존재 확인
3. 환자 리스트 확인 (`data/patients/patient_list_80.json`)
4. 프로파일 카드 확인 (최소 70개 권장)
5. 질문 뱅크 확인 (`experiments/question_bank/question_bank_5x15.v1.json`)
6. 코퍼스 파일 확인 (BM25 인덱스)
7. FAISS 인덱스 확인 (벡터 검색)
8. 설정 파일 확인 및 내용 검증

**출력 예시:**
```
[확인] 환자 수: 80명
[확인] 범위: SYN_0001 ~ SYN_0080
[확인] 프로파일 카드: 78개
[확인] 질문 수: 75개
[확인] LLM Provider: openai
[확인] LLM Model: gpt-4o-mini
```

**에러 처리:**
- 필수 파일이 없으면 즉시 중단
- 경고 사항은 표시하지만 계속 진행

---

### 7_test_single_turn.bat (단일 턴 테스트)

**역할:** 전체 파이프라인이 정상 작동하는지 최소 규모로 테스트

**실행 규모:**
- 환자 수: 1명
- 턴 수: 1턴
- 모드: 2개 (LLM + Agent)
- 총 API 호출: 2회

**검증 항목:**
- API 연결 (OpenAI)
- 코퍼스 로딩
- FAISS 인덱스 로딩
- MedCAT 모델 로딩
- LLM 모드 실행
- AI Agent 모드 실행
- 결과 저장 (`events.jsonl`)

**실행 명령:**
```python
python experiments/run_multiturn_experiment_v2.py \
    --config experiments/config.yaml \
    --max-patients 1 \
    --max-turns 1
```

**성공 시 출력:**
```
[성공] 단일 턴 테스트 완료!
[확인] 이벤트 수: 2개 (예상: 2개 - LLM + Agent)
```

---

### 8_test_multi_turn_single_patient.bat (멀티턴 단일 환자)

**역할:** 멀티턴 대화 흐름과 컨텍스트 관리가 정상 작동하는지 확인

**실행 규모:**
- 환자 수: 1명
- 턴 수: 5턴
- 모드: 2개 (LLM + Agent)
- 총 API 호출: 10회

**검증 항목:**
- 멀티턴 대화 흐름
- 컨텍스트 누적 및 관리
- 질문 선택 로직 (SHA256 해시 기반)
- 메모리 관리
- 전체 파이프라인 안정성

**실행 명령:**
```python
python experiments/run_multiturn_experiment_v2.py \
    --config experiments/config.yaml \
    --max-patients 1 \
    --max-turns 5
```

**성공 시 출력:**
```
[성공] 멀티턴 테스트 완료!
[확인] 이벤트 수: 10개 (예상: 10개 - 5턴 x 2모드)
Turn 1 (llm): 9738ms
Turn 2 (llm): 10257ms
...
```

---

### 9_run_full_experiment.bat (전체 실험)

**역할:** 전체 규모의 멀티턴 실험 수행

**실행 규모:**
- 환자 수: 78명 (프로파일 카드 보유 환자)
- 턴 수: 5턴
- 모드: 2개 (LLM + Agent)
- 총 API 호출: 780회

**실행 전 확인:**
1. API 키 유효성 (`check_api_keys.py`)
2. 데이터 파일 존재
3. 디스크 공간 (최소 1GB)

**실행 명령:**
```python
python experiments/run_multiturn_experiment_v2.py \
    --config experiments/config.yaml
```

**주의사항:**
- ⚠️ 컴퓨터를 끄거나 절전 모드로 전환하지 마세요
- ⚠️ 네트워크 연결이 안정적인지 확인하세요
- ⚠️ API 크레딧이 충분한지 확인하세요 (최소 $30 권장)
- ⚠️ 실행 중 에러 발생 시 즉시 중단됩니다
- ⚠️ 중간에 중단하면 처음부터 다시 실행해야 합니다

**성공 시 출력:**
```
[성공] 실험 완료!
[확인] 이벤트 수: 780개
[확인] 파일 크기: XX.XX MB
```

---

### 10_analyze_results.bat (결과 분석)

**역할:** 실험 결과를 검증하고 통계 분석 수행

**수행 작업:**

1. **데이터 검증** (`scripts/validate_run.py`)
   - 파일 존재 확인
   - 필드 타입 확인
   - 페어링 완전성 확인

2. **공정성 검증** (`scripts/check_fairness.py`)
   - LLM과 Agent 모드 간 정확한 페어링 확인
   - Paired t-test 유효성 검증

3. **통계 분석** (`scripts/summarize_run.py`)
   - 전체 통계 계산
   - 턴별 분석
   - Paired t-test, Cohen's d 계산

4. **표 생성** (`scripts/make_paper_tables.py`)
   - CSV 표 생성

5. **그래프 생성** (`scripts/make_paper_figures.py`)
   - PNG 그래프 생성

**생성되는 파일:**
```
runs/2025-12-13_primary_v1/
├── events.jsonl              # 원본 실험 로그
├── resolved_config.json      # 설정 스냅샷
├── summary.json              # 통계 요약
├── tables/
│   ├── main_results.csv      # 주요 결과 표
│   ├── by_turn.csv           # 턴별 분석 표
│   └── efficiency.csv        # 효율성 지표 표
└── figures/
    ├── latency_comparison.png  # 응답 시간 비교 그래프
    └── by_turn.png             # 턴별 분석 그래프
```

---

## 실행 흐름도

### 권장 실행 순서 (첫 실행)

```
0_setup_env.bat
      ↓
1_check_keys.bat
      ↓
6_check_data_integrity.bat
      ↓
7_test_single_turn.bat
      ↓
8_test_multi_turn_single_patient.bat
      ↓
9_run_full_experiment.bat
      ↓
10_analyze_results.bat
```

### 재실행 시 (데이터/설정 변경 없음)

```
9_run_full_experiment.bat
      ↓
10_analyze_results.bat
```

### 설정 변경 후

```
6_check_data_integrity.bat
      ↓
7_test_single_turn.bat
      ↓
9_run_full_experiment.bat
      ↓
10_analyze_results.bat
```

---

## 에러 처리 전략

### 각 단계의 에러 처리

1. **6단계 (데이터 검사)**
   - 필수 파일 없음 → 즉시 중단 (`exit /b 1`)
   - 경고 사항 → 표시하지만 계속 진행

2. **7단계 (단일 턴 테스트)**
   - API 오류 → 즉시 중단, 원인 안내
   - 로딩 오류 → 즉시 중단, 파일 확인 안내

3. **8단계 (멀티턴 단일 환자)**
   - 중간 오류 → 즉시 중단, 로그 확인 안내
   - 컨텍스트 오류 → 즉시 중단, 메모리 관리 확인

4. **9단계 (전체 실험)**
   - 실행 전 최종 확인 (API 키, 데이터, 디스크)
   - 실행 중 오류 → 즉시 중단, 로그 저장
   - 재개 불가 → 처음부터 재실행 필요

5. **10단계 (결과 분석)**
   - 검증 실패 → 경고 표시, 계속 진행
   - 분석 실패 → 즉시 중단
   - 표/그래프 생성 실패 → 경고 표시, 계속 진행

---

## 장점 및 개선 사항

### 세분화의 장점

1. **조기 에러 발견**
   - 각 단계에서 문제를 즉시 확인
   - 1-2분 내에 설정 오류 발견 가능

2. **점진적 검증**
   - 작은 규모부터 시작 (1턴 → 5턴 → 전체)
   - 각 단계에서 신뢰성 확보

3. **시간 절약**
   - 설정 오류로 인한 8-12시간 낭비 방지
   - 테스트 단계에서 대부분의 문제 발견

4. **비용 절감**
   - 불필요한 API 호출 방지
   - 테스트 비용: $0.11-0.22 vs 전체 비용: $15-25

5. **명확한 디버깅**
   - 어느 단계에서 문제가 생겼는지 명확
   - 로그가 짧아서 분석 용이

### 기존 방식과의 비교

| 항목 | 기존 (통합 실행) | 신규 (단계별 실행) |
|------|------------------|-------------------|
| 에러 발견 시간 | 몇 시간 후 | 1-2분 내 |
| 디버깅 난이도 | 높음 (긴 로그) | 낮음 (짧은 로그) |
| 비용 낭비 | 높음 ($15-25) | 낮음 ($0.11-0.22) |
| 실행 유연성 | 낮음 | 높음 |
| 학습 곡선 | 낮음 | 중간 |

---

## 향후 개선 방향

### 체크포인트 기능

현재는 중단 시 처음부터 재실행해야 하지만, 향후 다음 기능 추가 가능:
- 환자별 체크포인트 저장
- 중단된 지점부터 재개
- 실패한 환자만 재실행

### 병렬 실행

현재는 순차 실행이지만, 향후 다음 최적화 가능:
- 환자별 병렬 처리
- 모드별 병렬 처리 (LLM과 Agent 동시 실행)
- 실행 시간 단축 (8-12시간 → 2-3시간)

### 실시간 모니터링

향후 다음 기능 추가 가능:
- 웹 대시보드로 실시간 진행 상황 확인
- 에러 발생 시 알림
- 예상 완료 시간 표시

---

## 사용 예시

### 시나리오 1: 첫 실행

```bash
# 1. 환경 설정
0_setup_env.bat
1_check_keys.bat

# 2. 데이터 확인
6_check_data_integrity.bat
# → 78개 프로파일 카드 확인

# 3. 단일 턴 테스트
7_test_single_turn.bat
# → 2분 소요, 성공

# 4. 멀티턴 단일 환자 테스트
8_test_multi_turn_single_patient.bat
# → 8분 소요, 성공

# 5. 전체 실험 (밤새 실행)
9_run_full_experiment.bat
# → 10시간 소요, 성공

# 6. 결과 분석
10_analyze_results.bat
# → 1분 소요, 표 및 그래프 생성
```

### 시나리오 2: API 키 오류 발견

```bash
# 1. 단일 턴 테스트
7_test_single_turn.bat
# → 에러: 401 Unauthorized

# 2. API 키 확인
1_check_keys.bat
# → 에러: OPENAI_API_KEY가 유효하지 않습니다

# 3. .env 파일 수정
# OPENAI_API_KEY=sk-...

# 4. 재시도
7_test_single_turn.bat
# → 성공!

# 5. 전체 실험 진행
9_run_full_experiment.bat
```

### 시나리오 3: 설정 변경 후 재실행

```bash
# 1. experiments/config.yaml 수정
# llm.model: gpt-4o-mini → gpt-4o

# 2. 설정 확인
6_check_data_integrity.bat
# → [확인] LLM Model: gpt-4o

# 3. 단일 턴 테스트
7_test_single_turn.bat
# → 성공 (응답 품질 확인)

# 4. 전체 실험
9_run_full_experiment.bat
# → 실행 (비용 더 높음)

# 5. 결과 분석
10_analyze_results.bat
```

---

## 요약

- **5개의 독립적인 배치 파일**로 멀티턴 실험을 단계별로 실행
- **점진적 검증** (1턴 → 5턴 → 전체)으로 에러 조기 발견
- **시간과 비용 절약** (테스트 비용 $0.11-0.22)
- **명확한 디버깅** (각 단계별 짧은 로그)
- **유연한 실행** (개별 실행 또는 전체 자동 실행)

이 구조는 연구의 신뢰성과 재현성을 높이면서도 개발 및 디버깅 효율성을 크게 향상시킵니다.

