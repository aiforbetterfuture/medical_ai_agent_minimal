@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo 단일 Ablation 테스트 실행
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
echo [실행] Ablation Single Test
echo.

REM Python 스크립트 실행
python experiments\run_ablation_single.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 실행 실패 (Error Code: %ERRORLEVEL%)
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [완료] 결과가 runs\ 디렉토리에 저장되었습니다.
echo ========================================
echo.
echo 결과 확인:
echo   - JSON: runs\ablation_*\results_*.json
echo   - CSV:  runs\ablation_*\results_*.csv
echo.

pause