@echo off
setlocal
REM Pin working directory to the folder of this BAT file:
cd /d %~dp0
REM Ensure local packages are importable:
set PYTHONPATH=%CD%

echo [1_check_keys] Checking API keys in .env file...
echo.

REM Check if virtual environment exists
if not exist .venv\Scripts\python.exe (
  echo [1_check_keys] WARNING: Virtual environment not found.
  echo [1_check_keys] Using system Python. For best results, run 0_setup_env.bat first.
  python check_api_keys.py
) else (
  echo [1_check_keys] Using virtual environment Python...
  .venv\Scripts\python.exe check_api_keys.py
)

echo.
pause

