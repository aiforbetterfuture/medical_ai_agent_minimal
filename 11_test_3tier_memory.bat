@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo [11] 3-Tier 메모리 시스템 성능 테스트 (21턴)
echo ============================================================================
echo.

REM 가상환경 확인
if not exist .venv\Scripts\python.exe (
    echo [오류] 가상환경을 찾을 수 없습니다.
    echo 먼저 0_setup_env.bat를 실행하세요.
    pause
    exit /b 1
)

echo 테스트 개요:
echo   - 가상 환자 1명 생성 (LLM 기반)
echo   - AI Agent 모드로 21턴 대화 수행
echo   - 3계층 메모리 상태 추적
echo     * Working Memory (최근 5턴): 원문 저장
echo     * Compressing Memory (6-20턴): 압축 요약
echo     * Semantic Memory (21턴+): 장기 저장
echo   - 평가지표 계산 (RAGAS + 고급 메트릭)
echo   - 메모리 내용 시각화
echo.
echo 예상 소요 시간: 약 15-30분
echo 예상 API 비용: 약 $1-2
echo.
pause

echo.
echo [실행] 3-Tier 메모리 테스트 시작...
echo ============================================================================
echo.

.venv\Scripts\python.exe experiments\test_3tier_memory_21turns_v2.py
set EXIT_CODE=!errorlevel!

echo.
echo [디버그] Python 종료 코드: !EXIT_CODE!
echo.

if not !EXIT_CODE! equ 0 (
    echo.
    echo ============================================================================
    echo [실패] 3-Tier 메모리 테스트 실패
    echo ============================================================================
    echo.
    echo Python 스크립트 종료 코드: !EXIT_CODE!
    echo.
    echo 오류 원인을 확인하세요:
    echo   1. API 키 확인: 1_check_keys.bat
    echo   2. 로그 확인 (위 출력 참조)
    echo   3. 가상환경 확인: .venv\Scripts\python.exe --version
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo [성공] 3-Tier 메모리 테스트 완료!
echo ============================================================================
echo.

REM 결과 파일 확인
set RESULT_DIR=runs\3tier_memory_test

if exist %RESULT_DIR% (
    echo [결과 파일 확인]
    echo ----------------------------------------------------------------------------
    
    REM 최신 결과 파일 찾기
    for /f "delims=" %%i in ('dir /b /o-d %RESULT_DIR%\test_results_*.json 2^>nul') do (
        set LATEST_RESULT=%%i
        goto :found_result
    )
    :found_result
    
    if defined LATEST_RESULT (
        echo [확인] 상세 결과: %RESULT_DIR%\!LATEST_RESULT!
        
        REM 메모리 스냅샷 파일
        set SNAPSHOT_FILE=!LATEST_RESULT:test_results=memory_snapshots!
        if exist %RESULT_DIR%\!SNAPSHOT_FILE! (
            echo [확인] 메모리 스냅샷: %RESULT_DIR%\!SNAPSHOT_FILE!
        )
        
        REM 시각화 파일
        set VIZ_FILE=!LATEST_RESULT:test_results=memory_visualization!
        set VIZ_FILE=!VIZ_FILE:.json=.md!
        if exist %RESULT_DIR%\!VIZ_FILE! (
            echo [확인] 시각화: %RESULT_DIR%\!VIZ_FILE!
            echo.
            echo [메모리 시각화 미리보기]
            echo ----------------------------------------------------------------------------
            powershell -Command "Get-Content '%RESULT_DIR%\!VIZ_FILE!' -Head 30 -Encoding UTF8"
        )
    )
)

echo.
echo ============================================================================
echo 다음 단계
echo ============================================================================
echo.
echo 3-Tier 메모리 테스트가 완료되었습니다!
echo.
echo 결과 확인:
echo   1. 상세 결과: runs\3tier_memory_test\test_results_*.json
echo   2. 메모리 스냅샷: runs\3tier_memory_test\memory_snapshots_*.json
echo   3. 시각화: runs\3tier_memory_test\memory_visualization_*.md
echo.
echo 메모리 계층별 성능 분석:
echo   - Working Memory: 최근 5턴의 원문 저장 상태
echo   - Compressing Memory: 6-20턴의 압축 요약 품질
echo   - Semantic Memory: 21턴 이상의 장기 저장 효과
echo.
pause

