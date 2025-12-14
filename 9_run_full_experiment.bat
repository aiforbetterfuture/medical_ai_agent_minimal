@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo [9] 전체 멀티턴 실험 실행
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

echo 실험 규모:
echo   - 환자 수: 78명 (프로파일 카드 보유 환자)
echo   - 턴 수: 5턴/환자
echo   - 모드: 2개 (LLM + AI Agent)
echo   - 총 실행 횟수: 78 x 5 x 2 = 780회
echo.
echo 평가 지표:
echo   - RAGAS: Faithfulness, Answer Relevance, Perplexity
echo   - 멀티턴 컨텍스트: CUS, UR, CCR
echo   - 고급 지표: SFS, CSP, CUS_improved, ASS (멀티턴 스크립트 모드)
echo.
echo 예상 소요 시간: 약 8-12시간
echo 예상 API 비용: 약 $15-25 (OpenAI GPT-4o-mini 기준)
echo.
echo ============================================================================
echo 주의사항
echo ============================================================================
echo.
echo 1. 실행 중 컴퓨터를 끄거나 절전 모드로 전환하지 마세요
echo 2. 네트워크 연결이 안정적인지 확인하세요
echo 3. API 크레딧이 충분한지 확인하세요 (최소 $30 권장)
echo 4. 실행 중 에러 발생 시 즉시 중단됩니다
echo 5. 중간에 중단하면 처음부터 다시 실행해야 합니다
echo.
echo 계속하시겠습니까?
pause

REM 실행 전 최종 확인
echo.
echo [실행 전 최종 확인]
echo ============================================================================
echo.

REM API 키 확인
echo [1/4] API 키 확인...
if exist check_api_keys.py (
    .venv\Scripts\python.exe check_api_keys.py
    if !errorlevel! neq 0 (
        echo [오류] API 키 확인 실패
        pause
        exit /b 1
    )
) else (
    echo [경고] check_api_keys.py 파일이 없습니다. API 키 확인을 건너뜁니다.
)

REM 데이터 확인
echo.
echo [2/4] 데이터 파일 확인...
if not exist data\patients\patient_list_80.json (
    echo [오류] 환자 리스트를 찾을 수 없습니다
    pause
    exit /b 1
)
echo [확인] 데이터 파일 확인 완료

REM 디스크 공간 확인
echo.
echo [3/4] 디스크 공간 확인...
for /f "tokens=3" %%a in ('dir /-c ^| findstr /C:"bytes free"') do set FREE_SPACE=%%a
echo [확인] 디스크 공간 확인 완료

REM 설정 확인
echo.
echo [4/4] 실험 설정 확인...
echo [확인] 설정 파일 확인 완료

REM 실험 시작
echo.
echo ============================================================================
echo [실행] 전체 실험 시작
echo ============================================================================
echo.
echo 시작 시간: %date% %time%
echo.

.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py --config experiments\config.yaml
set EXIT_CODE=!errorlevel!

echo.
echo [디버그] Python 종료 코드: !EXIT_CODE!
echo.

if not !EXIT_CODE! equ 0 (
    echo.
    echo ============================================================================
    echo [실패] 실험 실행 중 오류 발생
    echo ============================================================================
    echo.
    echo 종료 시간: %date% %time%
    echo.
    echo Python 스크립트 종료 코드: !EXIT_CODE!
    echo.
    echo 오류 원인을 확인하세요:
    echo   1. 로그 파일: runs\2025-12-13_primary_v1\events.jsonl
    echo   2. 에러 메시지 (위 출력 참조)
    echo   3. API 크레딧 잔액
    echo.
    echo 오류 해결 후 다시 실행하세요.
    pause
    exit /b 1
)

REM 실험 완료
echo.
echo ============================================================================
echo [성공] 실험 완료!
echo ============================================================================
echo.
echo 종료 시간: %date% %time%
echo.

REM 결과 파일 확인
set RUN_DIR=runs\2025-12-13_primary_v1

echo [결과 파일 확인]
echo ----------------------------------------------------------------------------
if exist %RUN_DIR%\events.jsonl (
    for /f %%i in ('powershell -Command "(Get-Content %RUN_DIR%\events.jsonl | Measure-Object -Line).Lines"') do set EVENT_COUNT=%%i
    echo [확인] 이벤트 수: !EVENT_COUNT!개
    
    for /f %%i in ('powershell -Command "[math]::Round((Get-Item %RUN_DIR%\events.jsonl).Length / 1MB, 2)"') do set FILE_SIZE=%%i
    echo [확인] 파일 크기: !FILE_SIZE! MB
)

if exist %RUN_DIR%\resolved_config.json (
    echo [확인] 설정 스냅샷: %RUN_DIR%\resolved_config.json
)

echo.
echo ============================================================================
echo 다음 단계: 결과 분석
echo ============================================================================
echo.
echo 실험이 성공적으로 완료되었습니다!
echo.
echo 이제 결과를 분석하세요:
echo   10_analyze_results.bat - 통계 분석 및 시각화
echo.
pause
