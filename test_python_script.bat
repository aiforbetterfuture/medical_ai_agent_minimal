@echo off
setlocal
chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo Python 스크립트 실행 테스트
echo ============================================================================
echo.

REM 가상환경 확인
if not exist .venv\Scripts\python.exe (
    echo [오류] 가상환경을 찾을 수 없습니다.
    pause
    exit /b 1
)

echo [1] Python 버전 확인...
.venv\Scripts\python.exe --version
echo.

echo [2] Python 스크립트 존재 확인...
if exist experiments\run_multiturn_experiment_v2.py (
    echo [확인] run_multiturn_experiment_v2.py 존재
) else (
    echo [오류] run_multiturn_experiment_v2.py 없음
    pause
    exit /b 1
)
echo.

echo [3] Python 스크립트 import 테스트...
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'%CD%'); import experiments.run_multiturn_experiment_v2; print('[확인] Import 성공')"
set IMPORT_EXIT=%errorlevel%
echo Import 종료 코드: %IMPORT_EXIT%
echo.

if not %IMPORT_EXIT% equ 0 (
    echo [오류] Import 실패! 상세 에러 확인:
    echo.
    .venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'%CD%'); import experiments.run_multiturn_experiment_v2" 2>&1
    pause
    exit /b 1
)

echo [4] Python 스크립트 help 확인...
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py --help
set HELP_EXIT=%errorlevel%
echo Help 종료 코드: %HELP_EXIT%
echo.

echo [5] 설정 파일 확인...
if exist experiments\config.yaml (
    echo [확인] config.yaml 존재
) else (
    echo [오류] config.yaml 없음
    pause
    exit /b 1
)
echo.

echo [6] 실제 실행 테스트 (--max-patients 1 --max-turns 1)...
echo.
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py ^
    --config experiments\config.yaml ^
    --max-patients 1 ^
    --max-turns 1

set RUN_EXIT=%errorlevel%
echo.
echo 실행 종료 코드: %RUN_EXIT%
echo.

if not %RUN_EXIT% equ 0 (
    echo [오류] 실행 실패!
    pause
    exit /b 1
)

echo ============================================================================
echo [성공] 모든 테스트 통과!
echo ============================================================================
pause

