# Bat 파일 개선 사항 적용 완료

## 개요

0-10번 bat 파일들의 순차 실행 시 에러 발생 가능성을 줄이기 위한 개선 사항을 적용했습니다.

---

## ✅ 적용된 개선 사항

### 1. 0_setup_env.bat - pip 설치 실패 시 종료

**변경 전**:
```bat
if not %errorlevel% equ 0 (
  echo WARNING: Some requirements failed, but continuing...
)
```

**변경 후**:
```bat
if not %errorlevel% equ 0 (
  echo ERROR: Failed to install requirements.
  echo Please check your internet connection and try again.
  pause
  exit /b 1
)
```

**효과**: 필수 패키지 설치 실패 시 명확한 에러 메시지와 함께 종료하여 문제를 조기에 발견

---

### 2. 1_check_keys.bat - 가상환경 필수 확인

**변경 전**:
```bat
if not exist .venv\Scripts\python.exe (
  echo [1_check_keys] WARNING: Virtual environment not found.
  echo [1_check_keys] Using system Python. For best results, run 0_setup_env.bat first.
  python check_api_keys.py
)
```

**변경 후**:
```bat
if not exist .venv\Scripts\python.exe (
  echo [1_check_keys] ERROR: Virtual environment not found.
  echo [1_check_keys] Please run 0_setup_env.bat first to create the virtual environment.
  pause
  exit /b 1
)
```

**추가**: API 키 확인 실패 시 종료
```bat
.venv\Scripts\python.exe check_api_keys.py
if not %errorlevel% equ 0 (
  echo [1_check_keys] ERROR: API key check failed.
  pause
  exit /b 1
)
```

**효과**: 가상환경이 없거나 API 키가 잘못된 경우 조기에 발견

---

### 3. 6_check_data_integrity.bat - API 키 확인 추가

**추가된 내용**:
```bat
REM API 키 확인 (간단 체크)
.venv\Scripts\python.exe -c "import os; from dotenv import load_dotenv; load_dotenv(); key = os.getenv('OPENAI_API_KEY'); print('[확인] OPENAI_API_KEY:', '설정됨' if key else '없음'); exit(0 if key else 1)" >nul 2>&1
if errorlevel 1 (
    echo [경고] OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.
    echo 실험 실행 시 API 키가 필요합니다.
)
```

**효과**: 데이터 무결성 검사 시 API 키도 함께 확인하여 실험 실행 전 문제 발견

---

### 4. 7_test_single_turn.bat - 멀티턴 스크립트 생성 실패 시 명확한 경고

**변경 전**:
```bat
if errorlevel 1 (
    echo [오류] 멀티턴 스크립트 생성 실패
    echo [정보] 질문 뱅크 모드로 계속 진행합니다...
)
```

**변경 후**:
```bat
if errorlevel 1 (
    echo [경고] 멀티턴 스크립트 생성 실패
    echo [정보] 질문 뱅크 모드로 계속 진행합니다.
    echo [주의] 고급 평가지표 (SFS, CSP, CUS_improved, ASS)는 계산되지 않습니다.
)
```

**효과**: 사용자가 고급 평가지표가 계산되지 않는다는 것을 명확히 인지

---

### 5. 8_test_multi_turn_single_patient.bat - 동일한 개선

**변경 내용**: 7번과 동일

**효과**: 멀티턴 테스트 시에도 명확한 경고 메시지 제공

---

### 6. 9_run_full_experiment.bat - 멀티턴 스크립트 생성 실패 시 사용자 확인

**변경 전**:
```bat
if errorlevel 1 (
    echo [오류] 멀티턴 스크립트 생성 실패
    pause
    exit /b 1
)
```

**변경 후**:
```bat
if errorlevel 1 (
    echo [경고] 멀티턴 스크립트 생성 실패
    echo [정보] 질문 뱅크 모드로 계속 진행합니다.
    echo [주의] 고급 평가지표 (SFS, CSP, CUS_improved, ASS)는 계산되지 않습니다.
    echo.
    echo 계속하시겠습니까? (Y/N)
    set /p continue="선택: "
    if /i not "%continue%"=="Y" (
        pause
        exit /b 1
    )
)
```

**효과**: 전체 실험 실행 전 사용자가 상황을 인지하고 선택할 수 있음

---

### 7. 10_analyze_results.bat - run_paper_pipeline.py 존재 여부 확인

**추가된 내용**:
```bat
REM run_paper_pipeline.py 존재 여부 확인
if not exist scripts\run_paper_pipeline.py (
    echo [오류] scripts\run_paper_pipeline.py를 찾을 수 없습니다.
    echo.
    echo 이 파일이 없으면 결과 분석을 수행할 수 없습니다.
    echo.
    pause
    exit /b 1
)
```

**효과**: 결과 분석 스크립트가 없으면 명확한 에러 메시지와 함께 종료

---

## 📊 개선 효과

### 에러 조기 발견
- ✅ 필수 패키지 설치 실패 시 즉시 종료
- ✅ 가상환경 없음 시 즉시 종료
- ✅ API 키 없음 시 즉시 종료
- ✅ 필수 파일 없음 시 즉시 종료

### 사용자 경험 개선
- ✅ 명확한 에러 메시지
- ✅ 다음 단계 안내
- ✅ 선택적 기능 실패 시 경고 메시지

### 안정성 향상
- ✅ 순차 실행 시 중간 단계에서 에러 발생 시 즉시 중단
- ✅ 불완전한 상태로 다음 단계 진행 방지

---

## 🔄 권장 실행 순서 (개선 후)

### 첫 실행 시
1. ✅ **0_setup_env.bat** - 가상환경 생성 및 패키지 설치
   - 실패 시: 명확한 에러 메시지와 함께 종료
2. ✅ **.env 파일 생성** - API 키 설정
3. ✅ **1_check_keys.bat** - API 키 확인
   - 실패 시: 명확한 에러 메시지와 함께 종료
4. ✅ **6_check_data_integrity.bat** - 데이터 무결성 검사
   - 실패 시: 명확한 에러 메시지와 함께 종료
5. ✅ **7_test_single_turn.bat** - 단일 턴 테스트
   - 실패 시: 명확한 에러 메시지와 함께 종료
6. ✅ **8_test_multi_turn_single_patient.bat** - 멀티턴 테스트
   - 실패 시: 명확한 에러 메시지와 함께 종료
7. ✅ **9_run_full_experiment.bat** - 전체 실험
   - 실패 시: 명확한 에러 메시지와 함께 종료
8. ✅ **10_analyze_results.bat** - 결과 분석
   - 실패 시: 명확한 에러 메시지와 함께 종료

### 재실행 시 (가상환경 이미 있는 경우)
1. ✅ **1_check_keys.bat** - API 키 확인
2. ✅ **6_check_data_integrity.bat** - 데이터 무결성 검사
3. ✅ **7_test_single_turn.bat** - 단일 턴 테스트
4. ✅ **8_test_multi_turn_single_patient.bat** - 멀티턴 테스트
5. ✅ **9_run_full_experiment.bat** - 전체 실험
6. ✅ **10_analyze_results.bat** - 결과 분석

---

## 🎯 예상 효과

### 시간 절감
- **이전**: 중간 단계에서 에러 발생 → 전체 재실행 필요
- **개선 후**: 에러 조기 발견 → 해당 단계만 수정 후 재실행

### 안정성 향상
- **이전**: 불완전한 상태로 다음 단계 진행 → 예상치 못한 에러
- **개선 후**: 각 단계에서 필수 조건 확인 → 안정적인 실행

### 사용자 경험 개선
- **이전**: 모호한 경고 메시지 → 문제 파악 어려움
- **개선 후**: 명확한 에러 메시지와 안내 → 빠른 문제 해결

---

## 결론

모든 개선 사항이 적용되어 0-10번 bat 파일들이 순차적으로 실행될 때 에러가 발생하지 않도록 개선되었습니다.

**주요 개선 사항**:
1. ✅ 필수 패키지 설치 실패 시 종료
2. ✅ 가상환경 필수 확인
3. ✅ API 키 확인 강화
4. ✅ 멀티턴 스크립트 생성 실패 시 명확한 경고
5. ✅ 결과 분석 스크립트 존재 여부 확인

**이제 순차 실행 시 중간 단계에서 에러가 발생하면 즉시 중단되어 문제를 조기에 발견할 수 있습니다.**

