@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo Basic RAG vs Corrective RAG 비교 실험
echo ========================================
echo.
echo 실험 설정:
echo   - 환자: Synthea 80명 중 1명 랜덤 선택
echo   - 턴 수: 5턴 멀티턴 대화
echo   - 모드: AI Agent
echo   - 비교: Basic RAG vs Corrective RAG
echo.
echo ========================================
echo.

REM 가상환경 활성화
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] 가상환경을 찾을 수 없습니다. 전역 Python 사용
)

echo.
echo [실행] 실험 시작...
echo.

REM Python 스크립트 실행
python experiments\run_basic_vs_crag_single_patient.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 실행 실패 (Error Code: %ERRORLEVEL%)
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [완료] 실험 완료!
echo ========================================
echo.
echo 결과 확인:
echo   - JSON: runs\basic_vs_crag\*.json
echo.

pause