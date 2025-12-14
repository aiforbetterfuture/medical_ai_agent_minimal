# 0-10번 Bat 파일 순차 실행 체크리스트

## 개요

0번부터 10번까지의 bat 파일들이 유기적으로 연계되어 순차적으로 실행될 때 에러가 발생하지 않는지 체크합니다.

---

## 📋 파일 목록 및 역할

| 번호 | 파일명 | 역할 | 의존성 |
|------|--------|------|--------|
| 0 | `0_setup_env.bat` | 가상환경 생성 및 패키지 설치 | 없음 |
| 1 | `1_check_keys.bat` | API 키 확인 | 0번 (가상환경) |
| 2 | `2_run_api.bat` | API 서버 실행 (미구현) | - |
| 3 | `3_run_ui.bat` | Streamlit UI 실행 | 0번 (가상환경) |
| 4 | `4_run_all.bat` | Streamlit UI 실행 (새 창) | 0번 (가상환경) |
| 5 | `5_run_multiturn_test.bat` | 멀티턴 실험 메뉴 | 0번 (가상환경) |
| 6 | `6_check_data_integrity.bat` | 데이터 무결성 검사 | 0번, 1번 |
| 7 | `7_test_single_turn.bat` | 단일 턴 테스트 | 0번, 1번, 6번 |
| 8 | `8_test_multi_turn_single_patient.bat` | 멀티턴 단일 환자 테스트 | 0번, 1번, 6번, 7번 |
| 9 | `9_run_full_experiment.bat` | 전체 실험 실행 | 0번, 1번, 6번, 7번, 8번 |
| 10 | `10_analyze_results.bat` | 결과 분석 | 9번 (실험 완료) |
| 11 | `11_test_memory_verification.bat` | 메모리 검증 (선택적) | 9번 (실험 완료) |

---

## 🔍 순차 실행 체크리스트

### ✅ 0번: 0_setup_env.bat

**역할**: 가상환경 생성 및 패키지 설치

**체크 항목**:
- [x] Python 설치 확인
- [x] 가상환경 생성 (.venv)
- [x] pip 업그레이드
- [x] requirements.txt 설치
- [x] spaCy, MedCAT 설치
- [x] matplotlib 설치
- [x] RAGAS 설치
- [x] spaCy 모델 다운로드
- [x] python-dotenv 확인
- [x] .env 파일 확인 (경고만)
- [x] MEDCAT2_MODEL_PATH 설정

**잠재적 에러**:
- ❌ Python이 설치되지 않음 → 명확한 에러 메시지 있음
- ⚠️ pip 설치 실패 → 경고만 출력하고 계속 진행 (개선 필요)
- ⚠️ RAGAS 설치 실패 → 경고만 출력하고 계속 진행 (개선 필요)

**개선 사항**:
- pip 설치 실패 시 exit /b 1로 종료하도록 수정 권장
- RAGAS 설치 실패 시 재시도 로직 추가 권장

---

### ✅ 1번: 1_check_keys.bat

**역할**: API 키 확인

**체크 항목**:
- [x] 가상환경 확인 (없으면 시스템 Python 사용)
- [x] check_api_keys.py 실행

**잠재적 에러**:
- ⚠️ 가상환경이 없어도 시스템 Python으로 진행 (경고만)
- ❌ .env 파일이 없으면 check_api_keys.py에서 에러 발생 가능

**개선 사항**:
- 가상환경이 없으면 명확한 에러 메시지와 함께 종료하도록 수정 권장
- .env 파일 존재 여부를 먼저 확인하도록 수정 권장

---

### ⚠️ 2번: 2_run_api.bat

**역할**: API 서버 실행 (미구현)

**상태**: 경고만 출력하고 종료 (exit /b 0)

**의존성**: 없음 (실험 파이프라인과 무관)

---

### ✅ 3번: 3_run_ui.bat

**역할**: Streamlit UI 실행

**체크 항목**:
- [x] 가상환경 확인 (없으면 에러)
- [x] python-dotenv 확인 및 설치
- [x] .env 파일 확인 (경고만)
- [x] Streamlit 실행

**잠재적 에러**:
- ❌ 가상환경이 없으면 명확한 에러 메시지와 함께 종료
- ⚠️ python-dotenv 설치 실패 시 에러 처리 있음
- ⚠️ .env 파일이 없어도 경고만 출력하고 계속 진행

**개선 사항**:
- .env 파일이 없으면 종료하도록 수정 권장 (API 키 필요)

---

### ✅ 4번: 4_run_all.bat

**역할**: Streamlit UI 실행 (새 창)

**체크 항목**: 3번과 동일

**의존성**: 0번 (가상환경)

---

### ✅ 5번: 5_run_multiturn_test.bat

**역할**: 멀티턴 실험 메뉴

**체크 항목**:
- [x] 메뉴 표시
- [x] 선택에 따라 6, 7, 8, 9, 10번 호출
- [x] 에러 발생 시 중단 (errorlevel 체크)

**잠재적 에러**:
- ❌ 호출된 bat 파일에서 에러 발생 시 중단됨 (올바름)

**의존성**: 0번 (가상환경)

---

### ✅ 6번: 6_check_data_integrity.bat

**역할**: 데이터 무결성 검사

**체크 항목**:
- [x] 가상환경 확인
- [x] .env 파일 확인
- [x] 환자 리스트 확인 (data\patients\patient_list_80.json)
- [x] 프로파일 카드 확인 (data\patients\profile_cards\SYN_*.json)
- [x] 질문 뱅크 확인 (experiments\question_bank\question_bank_5x15.v1.json)
- [x] 코퍼스 파일 확인 (선택적, 경고만)
- [x] FAISS 인덱스 확인 (선택적, 경고만)
- [x] 설정 파일 확인 (experiments\config.yaml, config\model_config.yaml, config\agent_config.yaml)

**잠재적 에러**:
- ❌ 필수 파일이 없으면 명확한 에러 메시지와 함께 종료
- ⚠️ 코퍼스/인덱스가 없어도 경고만 출력하고 계속 진행 (검색 기능 제한)

**의존성**: 0번 (가상환경), 1번 (API 키)

---

### ✅ 7번: 7_test_single_turn.bat

**역할**: 단일 턴 테스트 (1명 x 1턴 x 2모드)

**체크 항목**:
- [x] 멀티턴 스크립트 확인 및 생성 (없으면 생성 시도)
- [x] run_multiturn_experiment_v2.py 실행
- [x] 에러 발생 시 명확한 안내 메시지
- [x] 결과 확인 (events.jsonl)

**잠재적 에러**:
- ⚠️ 멀티턴 스크립트 생성 실패 시 질문 뱅크 모드로 계속 진행 (경고만)
- ❌ run_multiturn_experiment_v2.py 실행 실패 시 종료
- ⚠️ events.jsonl이 없으면 결과 확인 스킵 (에러 아님)

**의존성**: 0번, 1번, 6번

**개선 사항**:
- 멀티턴 스크립트 생성 실패 시 명확한 경고 메시지 추가 권장

---

### ✅ 8번: 8_test_multi_turn_single_patient.bat

**역할**: 멀티턴 단일 환자 테스트 (1명 x 5턴 x 2모드)

**체크 항목**: 7번과 동일

**잠재적 에러**: 7번과 동일

**의존성**: 0번, 1번, 6번, 7번 (권장)

---

### ✅ 9번: 9_run_full_experiment.bat

**역할**: 전체 실험 실행 (78명 x 5턴 x 2모드)

**체크 항목**:
- [x] API 키 확인
- [x] 데이터 파일 확인
- [x] 멀티턴 스크립트 확인 및 생성
- [x] 질문 뱅크 확인 (선택적)
- [x] 디스크 공간 확인
- [x] 설정 확인
- [x] run_multiturn_experiment_v2.py 실행
- [x] 결과 확인

**잠재적 에러**:
- ❌ API 키 확인 실패 시 종료
- ❌ 데이터 파일 없으면 종료
- ⚠️ 멀티턴 스크립트 생성 실패 시 질문 뱅크 모드로 계속 진행
- ❌ run_multiturn_experiment_v2.py 실행 실패 시 종료

**의존성**: 0번, 1번, 6번, 7번, 8번 (권장)

---

### ✅ 10번: 10_analyze_results.bat

**역할**: 결과 분석

**체크 항목**:
- [x] events.jsonl 파일 확인
- [x] run_paper_pipeline.py 실행
- [x] 결과 파일 확인

**잠재적 에러**:
- ❌ events.jsonl이 없으면 명확한 에러 메시지와 함께 종료
- ❌ run_paper_pipeline.py 실행 실패 시 종료

**의존성**: 9번 (실험 완료)

**개선 사항**:
- run_paper_pipeline.py가 없으면 명확한 에러 메시지 추가 권장

---

### ✅ 11번: 11_test_memory_verification.bat

**역할**: 메모리 검증 (선택적)

**체크 항목**:
- [x] events.jsonl 파일 확인
- [x] test_memory_verification.py 실행

**잠재적 에러**:
- ❌ events.jsonl이 없으면 명확한 에러 메시지와 함께 종료
- ❌ test_memory_verification.py 실행 실패 시 종료

**의존성**: 9번 (실험 완료)

---

## 🚨 발견된 문제점 및 개선 사항

### 1. 0_setup_env.bat - pip 설치 실패 시 경고만 출력

**문제**: pip 설치 실패 시 경고만 출력하고 계속 진행

**개선**:
```bat
"%PYTHON_EXE%" -m pip install -r requirements.txt
if not %errorlevel% equ 0 (
  echo ERROR: Failed to install requirements.
  echo Please check your internet connection and try again.
  pause
  exit /b 1
)
```

---

### 2. 1_check_keys.bat - 가상환경 없을 때 경고만 출력

**문제**: 가상환경이 없어도 시스템 Python으로 진행

**개선**:
```bat
if not exist .venv\Scripts\python.exe (
  echo [오류] 가상환경을 찾을 수 없습니다.
  echo 먼저 0_setup_env.bat를 실행하세요.
  pause
  exit /b 1
)
```

---

### 3. 7, 8, 9번 - 멀티턴 스크립트 생성 실패 시 경고만 출력

**문제**: 멀티턴 스크립트 생성 실패 시 질문 뱅크 모드로 계속 진행 (경고만)

**개선**: 명확한 경고 메시지 추가
```bat
if errorlevel 1 (
    echo [경고] 멀티턴 스크립트 생성 실패
    echo [정보] 질문 뱅크 모드로 계속 진행합니다.
    echo [주의] 고급 평가지표 (SFS, CSP, CUS_improved, ASS)는 계산되지 않습니다.
    pause
)
```

---

### 4. 10번 - run_paper_pipeline.py 존재 여부 확인 없음

**문제**: run_paper_pipeline.py가 없으면 명확한 에러 메시지 없음

**개선**:
```bat
if not exist scripts\run_paper_pipeline.py (
    echo [오류] scripts\run_paper_pipeline.py를 찾을 수 없습니다.
    pause
    exit /b 1
)
```

---

### 5. 공통 - .env 파일 확인 로직 일관성 부족

**문제**: 일부 파일은 .env 파일이 없어도 경고만 출력하고 계속 진행

**개선**: 실험 실행 파일(7, 8, 9번)은 .env 파일이 필수이므로 확인 후 없으면 종료하도록 수정 권장

---

## ✅ 권장 실행 순서

### 최소 실행 순서 (필수)
1. **0_setup_env.bat** - 가상환경 및 패키지 설치
2. **1_check_keys.bat** - API 키 확인
3. **6_check_data_integrity.bat** - 데이터 무결성 검사
4. **7_test_single_turn.bat** - 단일 턴 테스트
5. **8_test_multi_turn_single_patient.bat** - 멀티턴 테스트
6. **9_run_full_experiment.bat** - 전체 실험
7. **10_analyze_results.bat** - 결과 분석

### 선택적 실행
- **11_test_memory_verification.bat** - 메모리 검증 (9번 완료 후)

---

## 🔧 수정 권장 사항 요약

1. **0_setup_env.bat**: pip 설치 실패 시 종료하도록 수정
2. **1_check_keys.bat**: 가상환경 없으면 종료하도록 수정
3. **7, 8, 9번**: 멀티턴 스크립트 생성 실패 시 명확한 경고 메시지 추가
4. **10번**: run_paper_pipeline.py 존재 여부 확인 추가
5. **공통**: .env 파일 확인 로직 일관성 개선

---

## 📝 체크리스트 실행 가이드

### 첫 실행 시
1. ✅ 0_setup_env.bat 실행 (가상환경 생성)
2. ✅ .env 파일 생성 (API 키 설정)
3. ✅ 1_check_keys.bat 실행 (API 키 확인)
4. ✅ 6_check_data_integrity.bat 실행 (데이터 확인)
5. ✅ 7_test_single_turn.bat 실행 (단일 턴 테스트)
6. ✅ 8_test_multi_turn_single_patient.bat 실행 (멀티턴 테스트)
7. ✅ 9_run_full_experiment.bat 실행 (전체 실험)
8. ✅ 10_analyze_results.bat 실행 (결과 분석)

### 재실행 시 (가상환경 이미 있는 경우)
1. ✅ 1_check_keys.bat 실행 (API 키 확인)
2. ✅ 6_check_data_integrity.bat 실행 (데이터 확인)
3. ✅ 7_test_single_turn.bat 실행 (단일 턴 테스트)
4. ✅ 8_test_multi_turn_single_patient.bat 실행 (멀티턴 테스트)
5. ✅ 9_run_full_experiment.bat 실행 (전체 실험)
6. ✅ 10_analyze_results.bat 실행 (결과 분석)

---

## 결론

대부분의 bat 파일은 에러 처리가 잘 되어 있으나, 일부 개선 사항이 있습니다:

1. ✅ **에러 처리**: 대부분의 파일에서 에러 발생 시 명확한 메시지와 함께 종료
2. ⚠️ **경고 처리**: 일부 파일에서 경고만 출력하고 계속 진행 (개선 필요)
3. ✅ **의존성 체크**: 대부분의 파일에서 필수 의존성 확인
4. ⚠️ **일관성**: .env 파일 확인 로직의 일관성 개선 필요

**전체적으로 순차 실행 시 에러가 발생하지 않도록 잘 설계되어 있으나, 위의 개선 사항을 적용하면 더욱 안정적입니다.**

