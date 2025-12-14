@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo [7] 단일 턴 테스트 (1명 x 1턴 x 2모드)
echo ============================================================================
echo.

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

if not exist experiments\config.yaml (
    echo [오류] experiments\config.yaml를 찾을 수 없습니다.
    pause
    exit /b 1
)

echo 이 테스트는 다음을 검증합니다:
echo   - API 연결 (OpenAI)
echo   - 코퍼스 로딩
echo   - FAISS 인덱스 로딩
echo   - MedCAT 모델 로딩
echo   - LLM 모드 실행
echo   - AI Agent 모드 실행
echo   - RAGAS 평가지표 계산
echo   - 결과 저장
echo.
pause

REM Python 스크립트 실행
echo.
echo [실행] 단일 턴 테스트 시작...
echo ============================================================================
echo.

.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py --config experiments\config.yaml --max-patients 1 --max-turns 1
set EXIT_CODE=!errorlevel!

echo.
echo [디버그] Python 종료 코드: !EXIT_CODE!
echo.

if not !EXIT_CODE! equ 0 (
    echo.
    echo ============================================================================
    echo [실패] 단일 턴 테스트 실패
    echo ============================================================================
    echo.
    echo Python 스크립트 종료 코드: !EXIT_CODE!
    echo.
    echo 오류 원인을 확인하세요:
    echo   1. API 키 확인: 1_check_keys.bat
    echo   2. 로그 확인: runs\2025-12-13_primary_v1\events.jsonl
    echo   3. 데이터 확인: 6_check_data_integrity.bat
    echo.
    pause
    exit /b 1
)

REM 결과 확인
echo.
echo ============================================================================
echo [성공] 단일 턴 테스트 완료!
echo ============================================================================
echo.

set RUN_DIR=runs\2025-12-13_primary_v1

if exist %RUN_DIR%\events.jsonl (
    echo [결과 파일 확인]
    echo ----------------------------------------------------------------------------
    
    REM 이벤트 수 확인
    for /f %%i in ('powershell -Command "(Get-Content %RUN_DIR%\events.jsonl | Measure-Object -Line).Lines"') do set EVENT_COUNT=%%i
    echo [확인] 이벤트 수: !EVENT_COUNT!개 (예상: 2개 - LLM + Agent)
    
    REM 평가지표 확인
    if exist check_events_metrics.py (
        echo.
        echo [평가지표 확인]
        echo ----------------------------------------------------------------------------
        .venv\Scripts\python.exe check_events_metrics.py %RUN_DIR%
    )
)

echo.
echo ============================================================================
echo 다음 단계
echo ============================================================================
echo.
echo 단일 턴 테스트가 성공했습니다!
echo.
echo 다음 중 하나를 선택하세요:
echo   1. 8_test_multi_turn_single_patient.bat  - 1명 x 5턴 테스트
echo   2. 9_run_full_experiment.bat             - 전체 실험 (78명 x 5턴)
echo.
pause
