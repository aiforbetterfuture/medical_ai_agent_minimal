@echo off
setlocal

echo ============================================================================
echo BAT 파일 디버그 테스트
echo ============================================================================
echo.

REM 현재 디렉토리 확인
echo [1] 현재 디렉토리: %CD%
echo.

REM 가상환경 확인
echo [2] 가상환경 확인...
if exist .venv\Scripts\python.exe (
    echo [확인] 가상환경 존재: .venv\Scripts\python.exe
) else (
    echo [오류] 가상환경 없음
)
echo.

REM Python 버전 확인
echo [3] Python 버전 확인...
.venv\Scripts\python.exe --version
echo Python 실행 종료 코드: %errorlevel%
echo.

REM 필수 파일 확인
echo [4] 필수 파일 확인...
if exist experiments\run_multiturn_experiment_v2.py (
    echo [확인] run_multiturn_experiment_v2.py 존재
) else (
    echo [오류] run_multiturn_experiment_v2.py 없음
)

if exist experiments\config.yaml (
    echo [확인] config.yaml 존재
) else (
    echo [오류] config.yaml 없음
)
echo.

REM 간단한 Python 스크립트 실행 테스트
echo [5] Python 스크립트 실행 테스트...
.venv\Scripts\python.exe -c "print('Python 실행 성공!')"
echo Python 실행 종료 코드: %errorlevel%
echo.

echo ============================================================================
echo 디버그 테스트 완료
echo ============================================================================
pause

