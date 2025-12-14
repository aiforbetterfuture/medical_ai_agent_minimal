@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo Ablation 결과 분석
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
echo [분석] 가장 최근 비교 결과 분석 중...
echo.

REM Python 스크립트 실행 (인자 없으면 가장 최근 파일 자동 선택)
python experiments\analyze_ablation_results.py %1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 분석 실패 (Error Code: %ERRORLEVEL%)
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [완료] 분석 완료!
echo ========================================
echo.
echo 차트 확인:
echo   runs\ablation_comparison\charts_*.png
echo.

pause