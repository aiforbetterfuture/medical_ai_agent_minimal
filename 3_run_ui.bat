@echo off
setlocal
REM Pin working directory to the folder of this BAT file:
cd /d %~dp0
REM Ensure local packages (rag/, agent/, etc.) are importable:
set PYTHONPATH=%CD%

REM Check if virtual environment exists
if not exist .venv\Scripts\python.exe (
  echo [3_run_ui] ERROR: Virtual environment not found.
  echo [3_run_ui] Please run 0_setup_env.bat first to create the virtual environment.
  pause
  exit /b 1
)

REM Verify python-dotenv is installed in virtual environment
echo [3_run_ui] Checking python-dotenv installation...
.venv\Scripts\python.exe -c "import dotenv" 2>nul
if errorlevel 1 (
  echo [3_run_ui] WARNING: python-dotenv not found in virtual environment.
  echo [3_run_ui] Installing python-dotenv...
  .venv\Scripts\python.exe -m pip install --quiet --upgrade python-dotenv
  if errorlevel 1 (
    echo [3_run_ui] ERROR: Failed to install python-dotenv.
    echo [3_run_ui] Attempting to install from requirements.txt...
    .venv\Scripts\python.exe -m pip install --quiet --upgrade -r requirements.txt
    if errorlevel 1 (
      echo [3_run_ui] ERROR: Failed to install from requirements.txt.
      echo [3_run_ui] Please check your internet connection and try again.
      pause
      exit /b 1
    )
  )
  echo [3_run_ui] Verifying python-dotenv installation...
  .venv\Scripts\python.exe -c "import dotenv; print('[3_run_ui] python-dotenv version:', dotenv.__version__)" 2>nul
  if errorlevel 1 (
    echo [3_run_ui] ERROR: python-dotenv installation verification failed.
    pause
    exit /b 1
  )
  echo [3_run_ui] python-dotenv installed and verified successfully.
)

REM Load .env file if it exists (python-dotenv will handle this, but we check)
if exist .env (
  echo [3_run_ui] .env file found. Environment variables will be loaded.
) else (
  echo [3_run_ui] WARNING: .env file not found. LLM API keys may not be configured.
)

REM Set Streamlit configuration
set STREAMLIT_PORT=8501

echo [3_run_ui] Starting Medical AI Agent Streamlit UI...
echo [3_run_ui] UI will be available at http://localhost:%STREAMLIT_PORT%
echo [3_run_ui] Using Python: .venv\Scripts\python.exe
echo.
echo [3_run_ui] Press Ctrl+C to stop the server.
echo.

REM Run Streamlit using virtual environment's Python directly
REM This ensures we use the correct Python interpreter with all dependencies
.venv\Scripts\python.exe -m streamlit run app.py --server.port %STREAMLIT_PORT% --server.headless true
