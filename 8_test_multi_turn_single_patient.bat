@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo [8] 멀티턴 단일 환자 테스트 (1명 x 5턴 x 2모드)
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
echo   - 멀티턴 대화 흐름
echo   - 컨텍스트 누적 및 관리
echo   - 질문 선택 로직
echo   - 메모리 관리
echo   - RAGAS 평가지표 계산
echo   - 전체 파이프라인 안정성
echo.
echo 예상 소요 시간: 약 5-10분
echo 예상 API 비용: 약 $0.10-0.20
echo.
pause

REM Python 스크립트 실행
echo.
echo [실행] 멀티턴 테스트 시작...
echo ============================================================================
echo.

.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py --config experiments\config.yaml --max-patients 1 --max-turns 5
set EXIT_CODE=!errorlevel!

echo.
echo [디버그] Python 종료 코드: !EXIT_CODE!
echo.

if not !EXIT_CODE! equ 0 (
    echo.
    echo ============================================================================
    echo [실패] 멀티턴 테스트 실패
    echo ============================================================================
    echo.
    echo Python 스크립트 종료 코드: !EXIT_CODE!
    echo.
    echo 오류 원인을 확인하세요:
    echo   1. 로그 확인: runs\2025-12-13_primary_v1\events.jsonl
    echo   2. 에러 메시지 확인 (위 출력 참조)
    echo   3. API 크레딧 확인
    echo.
    pause
    exit /b 1
)

REM 결과 확인
echo.
echo ============================================================================
echo [성공] 멀티턴 테스트 완료!
echo ============================================================================
echo.

set RUN_DIR=runs\2025-12-13_primary_v1

if exist %RUN_DIR%\events.jsonl (
    echo [결과 파일 확인]
    echo ----------------------------------------------------------------------------
    
    REM 이벤트 수 확인
    for /f %%i in ('powershell -Command "(Get-Content %RUN_DIR%\events.jsonl | Measure-Object -Line).Lines"') do set EVENT_COUNT=%%i
    echo [확인] 이벤트 수: !EVENT_COUNT!개 (예상: 10개 - 5턴 x 2모드)
    
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
echo 멀티턴 테스트가 성공했습니다!
echo.
echo 이제 전체 실험을 실행할 준비가 되었습니다:
echo   9_run_full_experiment.bat - 전체 실험 (78명 x 5턴)
echo.
echo 주의사항:
echo   - 전체 실험은 약 8-12시간 소요됩니다
echo   - API 비용은 약 $15-25 예상됩니다
echo   - 실행 중 중단하지 마세요
echo.
pause
