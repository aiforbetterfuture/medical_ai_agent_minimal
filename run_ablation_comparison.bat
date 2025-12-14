@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo 다중 프로파일 비교 실험
echo ========================================
echo.

REM 가상환경 확인 및 활성화
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] 가상환경을 찾을 수 없습니다. 전역 Python 사용
)

echo.
echo 비교할 프로파일:
echo   1. baseline
echo   2. self_refine_heuristic
echo   3. self_refine_llm_quality
echo   4. self_refine_dynamic_query
echo   5. full_context_engineering
echo.
echo [시작] 프로파일 비교 실험 시작...
echo.

REM Python 스크립트 실행
python experiments\run_ablation_comparison.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 실행 실패 (Error Code: %ERRORLEVEL%)
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [완료] 비교 결과가 저장되었습니다.
echo ========================================
echo.
echo 결과 확인:
echo   - JSON: runs\ablation_comparison\comparison_*.json
echo   - CSV:  runs\ablation_comparison\summary_*.csv
echo.
echo 결과 분석:
echo   run_analyze_results.bat
echo.

pause