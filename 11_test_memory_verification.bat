@echo off
setlocal
REM ============================================================================
REM 11. 계층형 메모리 검증 테스트
REM - 멀티턴 실험 결과를 기반으로 계층형 메모리 시스템 검증
REM - Tier 1: 작업 메모리 (최근 5턴 원본 저장 확인)
REM - Tier 2: 압축 메모리 (5턴 도달 시 의학적 요약 확인)
REM - Tier 3: 의미 메모리 (만성질환/알레르기 저장 확인)
REM ============================================================================

chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo [11] 계층형 메모리 검증 테스트
echo ============================================================================
echo.
echo 이 테스트는 다음을 검증합니다:
echo   - Tier 1 (Working Memory): 최근 5턴 원본 저장 확인
echo   - Tier 2 (Compressed Memory): 5턴 도달 시 의학적 요약 확인
echo   - Tier 3 (Semantic Memory): 만성질환/알레르기 저장 확인
echo.
echo 주의사항:
echo   - 멀티턴 실험이 먼저 실행되어야 합니다 (9_run_full_experiment.bat)
echo   - events.jsonl 파일이 있어야 합니다
echo   - hierarchical_memory_enabled가 true여야 합니다
echo.
pause

REM 이벤트 파일 확인
set EVENTS_FILE=runs\2025-12-13_primary_v1\events.jsonl

if not exist %EVENTS_FILE% (
    echo [오류] 이벤트 파일을 찾을 수 없습니다: %EVENTS_FILE%
    echo.
    echo 먼저 멀티턴 실험을 실행하세요:
    echo   9_run_full_experiment.bat
    echo.
    pause
    exit /b 1
)

REM 메모리 검증 실행
echo.
echo [실행] 메모리 검증 시작...
echo ============================================================================
echo.

.venv\Scripts\python.exe experiments\test_memory_verification.py ^
    --events %EVENTS_FILE% ^
    --output runs\memory_verification_analysis.json

if errorlevel 1 (
    echo.
    echo ============================================================================
    echo [실패] 메모리 검증 실패
    echo ============================================================================
    echo.
    echo 오류 원인을 확인하세요:
    echo   1. events.jsonl 파일 확인
    echo   2. hierarchical_memory_enabled 설정 확인
    echo   3. 로그 확인
    echo.
    pause
    exit /b 1
)

REM 결과 확인
echo.
echo ============================================================================
echo [성공] 메모리 검증 완료!
echo ============================================================================
echo.

if exist runs\memory_verification_analysis.json (
    echo [결과 파일 확인]
    echo ----------------------------------------------------------------------------
    echo 결과 파일: runs\memory_verification_analysis.json
    echo.
    echo 상세 결과를 확인하세요.
)

echo.
pause

