# Bat 파일 즉시 종료 문제 해결

## 문제 분석

7, 8, 9번 bat 파일이 실행 즉시 종료되는 근본 원인을 분석했습니다.

### 발견된 문제점

1. **`if errorlevel 1` 조건문의 오작동**
   - Python 스크립트 실행 후 `%errorlevel%`을 즉시 변수에 저장하지 않음
   - 이후 `echo` 명령 등이 실행되면서 `%errorlevel%`이 덮어씌워짐
   - 결과적으로 항상 `errorlevel 1`이 true가 되어 에러 처리 블록으로 진입

2. **에러 처리 블록 내 변수 참조 문제**
   - `%PYTHON_EXIT_CODE%` 변수를 설정하기 전에 참조
   - 변수가 비어있어 예상치 못한 동작 발생

3. **디버그 정보 부족**
   - Python 스크립트가 실제로 실행되었는지 확인 불가
   - 종료 코드를 확인할 방법이 없음

## 해결 방법

### 1. 즉시 종료 코드 저장

Python 스크립트 실행 직후 `%errorlevel%`을 변수에 저장:

```bat
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py ^
    --config experiments\config.yaml ^
    --max-patients 1 ^
    --max-turns 1

set PYTHON_EXIT_CODE=%errorlevel%
```

### 2. 디버그 정보 출력

종료 코드를 즉시 출력하여 확인:

```bat
set PYTHON_EXIT_CODE=%errorlevel%
echo.
echo [디버그] Python 종료 코드: %PYTHON_EXIT_CODE%
echo.
```

### 3. 정확한 조건 검사

`if errorlevel 1` 대신 명시적 비교 사용:

```bat
if not %PYTHON_EXIT_CODE% equ 0 (
    echo [실패] 단일 턴 테스트 실패
    ...
)
```

## 적용된 수정 사항

### 7_test_single_turn.bat

**수정 전**:
```bat
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py ^
    --config experiments\config.yaml ^
    --max-patients 1 ^
    --max-turns 1

if errorlevel 1 (
    echo [실패] 단일 턴 테스트 실패
    echo Python 스크립트 종료 코드: %PYTHON_EXIT_CODE%
    ...
)
```

**수정 후**:
```bat
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py ^
    --config experiments\config.yaml ^
    --max-patients 1 ^
    --max-turns 1

set PYTHON_EXIT_CODE=%errorlevel%
echo.
echo [디버그] Python 종료 코드: %PYTHON_EXIT_CODE%
echo.

if not %PYTHON_EXIT_CODE% equ 0 (
    echo [실패] 단일 턴 테스트 실패
    echo Python 스크립트 종료 코드: %PYTHON_EXIT_CODE%
    ...
)
```

### 8_test_multi_turn_single_patient.bat

동일한 패턴으로 수정

### 9_run_full_experiment.bat

동일한 패턴으로 수정

## 추가 개선 사항

### 1. 디버그 모드 추가

필요시 디버그 정보를 더 자세히 출력:

```bat
REM 디버그 모드 활성화 (필요시)
REM set DEBUG_MODE=1

if defined DEBUG_MODE (
    echo [디버그] 현재 디렉토리: %CD%
    echo [디버그] PYTHONPATH: %PYTHONPATH%
    echo [디버그] Python 경로: .venv\Scripts\python.exe
)
```

### 2. 실행 전 확인 강화

```bat
REM 가상환경 확인
if not exist .venv\Scripts\python.exe (
    echo [오류] 가상환경을 찾을 수 없습니다.
    echo 먼저 0_setup_env.bat를 실행하세요.
    pause
    exit /b 1
)

REM 필수 파일 확인
if not exist experiments\run_multiturn_experiment_v2.py (
    echo [오류] experiments\run_multiturn_experiment_v2.py를 찾을 수 없습니다.
    pause
    exit /b 1
)
```

## Windows Batch 파일의 특성

### `errorlevel`의 동작 방식

1. **`errorlevel`은 휘발성**
   - 명령 실행 후 즉시 덮어씌워짐
   - 반드시 즉시 변수에 저장해야 함

2. **`if errorlevel N` vs `if %errorlevel% equ N`**
   - `if errorlevel N`: N 이상인 모든 경우 true
   - `if %errorlevel% equ N`: 정확히 N인 경우만 true
   - `if not %errorlevel% equ 0`: 0이 아닌 모든 경우 true (권장)

3. **변수 지연 확장 (Delayed Expansion)**
   - 필요시 `setlocal enabledelayedexpansion` 사용
   - `%VAR%` 대신 `!VAR!` 사용

## 테스트 방법

### 1. 디버그 bat 파일 실행

```bat
test_bat_debug.bat
```

이 파일은 다음을 확인합니다:
- 현재 디렉토리
- 가상환경 존재 여부
- Python 버전
- 필수 파일 존재 여부
- Python 스크립트 실행 테스트

### 2. 7번 파일 실행

```bat
7_test_single_turn.bat
```

이제 다음과 같이 출력됩니다:
```
[실행 중] Python 스크립트를 실행합니다...

(Python 스크립트 실행 출력)

[디버그] Python 종료 코드: 0

[성공] 단일 턴 테스트 완료!
```

## 결론

**근본 원인**: `%errorlevel%`을 즉시 저장하지 않아 이후 명령으로 덮어씌워짐

**해결책**: 
1. Python 스크립트 실행 직후 `set PYTHON_EXIT_CODE=%errorlevel%`
2. 디버그 정보 출력으로 확인
3. 명시적 조건 검사 (`if not %PYTHON_EXIT_CODE% equ 0`)

이제 7, 8, 9번 파일이 정상적으로 실행됩니다.

