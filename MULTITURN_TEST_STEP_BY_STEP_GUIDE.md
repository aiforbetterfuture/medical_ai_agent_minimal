# 멀티턴 테스트 단계별 실행 가이드

## 개요

멀티턴 실험을 단계별로 실행하여 에러를 조기에 발견하고 안정적으로 실험을 수행하기 위한 가이드입니다.

## 왜 단계별 실행이 필요한가?

### 기존 방식의 문제점
- **한 번에 모든 것을 실행**: 80명 × 5턴 × 2모드 = 800회 API 호출을 한 번에 실행
- **에러 발견 지연**: 실험 중간에 에러가 발생해도 어디서 문제가 생겼는지 파악하기 어려움
- **시간과 비용 낭비**: 설정 오류나 데이터 문제로 인해 몇 시간 실행 후 실패
- **디버깅 어려움**: 로그가 너무 길어서 문제 원인을 찾기 힘듦

### 단계별 실행의 장점
- **조기 에러 발견**: 각 단계에서 문제를 즉시 확인
- **점진적 검증**: 작은 규모부터 시작하여 전체로 확장
- **시간 절약**: 문제가 있으면 1-2분 내에 발견
- **비용 절감**: 설정 오류로 인한 불필요한 API 호출 방지
- **명확한 디버깅**: 어느 단계에서 문제가 생겼는지 명확히 파악

---

## 실행 단계

### 0단계: 환경 설정 (사전 준비)

```bash
# Windows
0_setup_env.bat
1_check_keys.bat

# Linux/Mac
./0_setup_env.sh
./1_check_keys.sh
```

**확인 사항:**
- ✅ 가상환경 생성 완료
- ✅ 패키지 설치 완료
- ✅ API 키 확인 완료
- ✅ MedCAT 모델 로드 확인

---

### 6단계: 데이터 무결성 검사

**목적:** 실험에 필요한 모든 데이터 파일이 올바르게 준비되었는지 확인

```bash
# Windows
6_check_data_integrity.bat

# Linux/Mac
./6_check_data_integrity.sh
```

**검사 항목:**
1. 환자 리스트 (80명)
2. 프로파일 카드 (최소 70개 권장)
3. 질문 뱅크 (75개 질문)
4. 코퍼스 파일 (BM25 검색용)
5. FAISS 인덱스 (벡터 검색용)
6. 설정 파일 (experiments/config.yaml, config/model_config.yaml 등)

**예상 소요 시간:** 10-20초

**성공 시 출력:**
```
[확인] 환자 수: 80명
[확인] 프로파일 카드: 78개
[확인] 질문 수: 75개
[확인] LLM Provider: openai
[확인] LLM Model: gpt-4o-mini
```

**실패 시 조치:**
- 환자 리스트 없음 → `python scripts/generate_synthea_profiles.py` 실행
- 질문 뱅크 없음 → 프로젝트 파일 확인
- 설정 파일 없음 → 프로젝트 구조 확인

---

### 7단계: 단일 턴 테스트

**목적:** 전체 파이프라인이 정상 작동하는지 최소 규모로 테스트

**규모:** 1명 × 1턴 × 2모드 = 2회 API 호출

```bash
# Windows
7_test_single_turn.bat

# Linux/Mac
./7_test_single_turn.sh
```

**검증 항목:**
- ✅ API 연결 (OpenAI)
- ✅ 코퍼스 로딩
- ✅ FAISS 인덱스 로딩
- ✅ MedCAT 모델 로딩
- ✅ LLM 모드 실행
- ✅ AI Agent 모드 실행
- ✅ 결과 저장 (events.jsonl)

**예상 소요 시간:** 1-2분

**예상 API 비용:** $0.01-0.02

**성공 시 출력:**
```
[성공] 단일 턴 테스트 완료!
[확인] 이벤트 수: 2개 (예상: 2개 - LLM + Agent)
```

**실패 시 조치:**
- API 키 오류 → `1_check_keys.bat` 재실행, .env 파일 확인
- 코퍼스 로딩 실패 → 데이터 파일 확인
- MedCAT 오류 → 모델 경로 확인
- 검색 실패 → 로그에서 구체적인 에러 메시지 확인

---

### 8단계: 멀티턴 단일 환자 테스트

**목적:** 멀티턴 대화 흐름과 컨텍스트 관리가 정상 작동하는지 확인

**규모:** 1명 × 5턴 × 2모드 = 10회 API 호출

```bash
# Windows
8_test_multi_turn_single_patient.bat

# Linux/Mac
./8_test_multi_turn_single_patient.sh
```

**검증 항목:**
- ✅ 멀티턴 대화 흐름
- ✅ 컨텍스트 누적 및 관리
- ✅ 질문 선택 로직 (SHA256 해시 기반)
- ✅ 메모리 관리
- ✅ 전체 파이프라인 안정성

**예상 소요 시간:** 5-10분

**예상 API 비용:** $0.10-0.20

**성공 시 출력:**
```
[성공] 멀티턴 테스트 완료!
[확인] 이벤트 수: 10개 (예상: 10개 - 5턴 x 2모드)
Turn 1 (llm): 9738ms
Turn 2 (llm): 10257ms
...
```

**실패 시 조치:**
- 중간에 멈춤 → API 크레딧 확인, 네트워크 확인
- 컨텍스트 오류 → 메모리 관리 로직 확인
- 질문 선택 오류 → 질문 뱅크 구조 확인

---

### 9단계: 전체 실험 실행

**목적:** 전체 규모의 멀티턴 실험 수행

**규모:** 78명 × 5턴 × 2모드 = 780회 API 호출

```bash
# Windows
9_run_full_experiment.bat

# Linux/Mac
./9_run_full_experiment.sh
```

**예상 소요 시간:** 8-12시간

**예상 API 비용:** $15-25 (OpenAI GPT-4o-mini 기준)

**주의사항:**
1. ⚠️ 컴퓨터를 끄거나 절전 모드로 전환하지 마세요
2. ⚠️ 네트워크 연결이 안정적인지 확인하세요
3. ⚠️ API 크레딧이 충분한지 확인하세요 (최소 $30 권장)
4. ⚠️ 실행 중 에러 발생 시 즉시 중단됩니다
5. ⚠️ 중간에 중단하면 처음부터 다시 실행해야 합니다

**실행 전 최종 확인:**
- API 키 유효성
- 데이터 파일 존재
- 디스크 공간 (최소 1GB)

**성공 시 출력:**
```
[성공] 실험 완료!
[확인] 이벤트 수: 780개
[확인] 파일 크기: XX.XX MB
```

**실패 시 조치:**
- API 쿼터 초과 → OpenAI 대시보드에서 크레딧 추가
- 네트워크 오류 → 네트워크 연결 확인 후 재실행
- 메모리 부족 → 다른 프로그램 종료 후 재실행

---

### 10단계: 결과 분석

**목적:** 실험 결과를 검증하고 통계 분석 수행

```bash
# Windows
10_analyze_results.bat

# Linux/Mac
./10_analyze_results.sh
```

**수행 작업:**
1. **데이터 검증** (`validate_run.py`)
   - 파일 존재 확인
   - 필드 타입 확인
   - 페어링 완전성 확인

2. **공정성 검증** (`check_fairness.py`)
   - LLM과 Agent 모드 간 정확한 페어링 확인
   - Paired t-test 유효성 검증

3. **통계 분석** (`summarize_run.py`)
   - 전체 통계 계산
   - 턴별 분석
   - Paired t-test, Cohen's d 계산

4. **표 생성** (`make_paper_tables.py`)
   - CSV 표 생성 (main_results.csv, by_turn.csv, efficiency.csv)

5. **그래프 생성** (`make_paper_figures.py`)
   - PNG 그래프 생성 (latency_comparison.png, by_turn.png)

**예상 소요 시간:** 1-2분

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

**성공 시 출력:**
```
[완료] 결과 분석 완료!
총 이벤트 수: 780
LLM 평균 응답시간: 9500ms
Agent 평균 응답시간: 12000ms
p-value: 0.000123
Cohen d: 0.456
```

---

## 전체 자동 실행

모든 단계를 자동으로 실행하려면:

```bash
# Windows
5_run_multiturn_test.bat
# 메뉴에서 'A' 선택

# Linux/Mac
./5_run_multiturn_test.sh
# 메뉴에서 'A' 선택
```

**자동 실행 순서:**
1. 6_check_data_integrity
2. 7_test_single_turn
3. 8_test_multi_turn_single_patient
4. 9_run_full_experiment (사용자 확인 후)
5. 10_analyze_results

**장점:**
- 한 번의 명령으로 전체 파이프라인 실행
- 각 단계에서 에러 발생 시 즉시 중단
- 테스트 단계(6-8)를 통과한 후에만 전체 실험 실행

**단점:**
- 전체 소요 시간이 길어짐 (테스트 포함)
- 중간에 개입할 수 없음

---

## 권장 워크플로우

### 첫 실행 시 (권장)
```
0_setup_env.bat → 1_check_keys.bat → 
6_check_data_integrity.bat → 
7_test_single_turn.bat → 
8_test_multi_turn_single_patient.bat → 
9_run_full_experiment.bat → 
10_analyze_results.bat
```

### 재실행 시 (데이터/설정 변경 없음)
```
9_run_full_experiment.bat → 10_analyze_results.bat
```

### 설정 변경 후
```
6_check_data_integrity.bat → 
7_test_single_turn.bat → 
9_run_full_experiment.bat → 
10_analyze_results.bat
```

---

## 에러 해결 가이드

### API 관련 에러

**증상:** `429 You exceeded your current quota`
- **원인:** API 크레딧 부족
- **해결:** OpenAI 대시보드에서 크레딧 추가

**증상:** `401 Unauthorized`
- **원인:** API 키 오류
- **해결:** `.env` 파일의 `OPENAI_API_KEY` 확인

**증상:** `503 Service Unavailable`
- **원인:** OpenAI 서버 일시적 오류
- **해결:** 잠시 후 재시도

### 데이터 관련 에러

**증상:** `환자 리스트를 찾을 수 없습니다`
- **원인:** `data/patients/patient_list_80.json` 파일 없음
- **해결:** `python scripts/generate_synthea_profiles.py` 실행

**증상:** `질문 뱅크를 찾을 수 없습니다`
- **원인:** `experiments/question_bank/question_bank_5x15.v1.json` 파일 없음
- **해결:** 프로젝트 파일 구조 확인

**증상:** `프로파일 카드가 부족합니다`
- **원인:** 프로파일 카드가 70개 미만
- **해결:** 경고이므로 진행 가능하지만, 가능하면 카드 생성 스크립트 재실행

### 검색 관련 에러

**증상:** `[ERROR] 검색 실패: 'NoneType' object has no attribute 'shape'`
- **원인:** 임베딩 생성 실패
- **해결:** 
  1. 네트워크 연결 확인
  2. 임베딩 모델 로딩 확인
  3. 로그에서 구체적인 에러 확인

**증상:** `코퍼스 파일을 찾을 수 없습니다`
- **원인:** BM25 인덱스 파일 없음
- **해결:** 
  1. `data/corpus/` 디렉토리 확인
  2. 인덱스 생성 스크립트 실행 (프로젝트에 포함되어 있어야 함)

### 인코딩 관련 에러

**증상:** `UnicodeEncodeError: 'cp949' codec can't encode character`
- **원인:** Windows 콘솔 인코딩 문제
- **해결:** 이미 수정됨 (`sys.stdout.reconfigure(encoding='utf-8')`)

---

## 결과 해석

### summary.json 주요 지표

```json
{
  "overall": {
    "total_events": 780,
    "llm_mean_latency_ms": 9500.0,
    "agent_mean_latency_ms": 12000.0,
    "paired_ttest_pvalue": 0.000123,
    "cohens_d": 0.456,
    "ci_95_lower": -2800.0,
    "ci_95_upper": -2200.0
  }
}
```

**해석:**
- `paired_ttest_pvalue < 0.05`: 통계적으로 유의미한 차이
- `cohens_d > 0.5`: 중간 크기의 효과
- `ci_95`: 95% 신뢰구간 (음수 = Agent가 더 느림)

### 논문 작성 시 사용할 표

1. **main_results.csv**: 전체 비교 결과
2. **by_turn.csv**: 턴별 상세 분석
3. **efficiency.csv**: 효율성 지표 (토큰 사용량, 비용 등)

---

## 추가 팁

### 실험 중단 및 재개

현재 구현에서는 중단 후 재개가 지원되지 않습니다. 중단 시 처음부터 다시 실행해야 합니다.

**향후 개선 방향:**
- 체크포인트 저장
- 중단된 지점부터 재개

### 로그 확인

실시간 로그 확인:
```bash
# Windows PowerShell
Get-Content runs\2025-12-13_primary_v1\events.jsonl -Wait -Tail 10

# Linux/Mac
tail -f runs/2025-12-13_primary_v1/events.jsonl
```

### 디스크 공간 관리

실험 결과는 약 100-500MB의 공간을 차지합니다. 오래된 실험 결과는 정기적으로 삭제하세요.

---

## 문의 및 지원

문제가 발생하면:
1. 해당 단계의 로그 확인
2. `error.md`에 에러 메시지 복사
3. 에러 메시지와 함께 문의

---

## 체크리스트

실험 시작 전:
- [ ] 가상환경 설정 완료 (0_setup_env.bat)
- [ ] API 키 확인 완료 (1_check_keys.bat)
- [ ] 데이터 무결성 확인 완료 (6_check_data_integrity.bat)
- [ ] 단일 턴 테스트 성공 (7_test_single_turn.bat)
- [ ] 멀티턴 단일 환자 테스트 성공 (8_test_multi_turn_single_patient.bat)
- [ ] API 크레딧 충분 ($30 이상 권장)
- [ ] 디스크 공간 충분 (1GB 이상)
- [ ] 네트워크 연결 안정적

실험 완료 후:
- [ ] 결과 분석 완료 (10_analyze_results.bat)
- [ ] summary.json 확인
- [ ] CSV 표 확인
- [ ] 그래프 확인
- [ ] 논문에 사용할 자료 준비

