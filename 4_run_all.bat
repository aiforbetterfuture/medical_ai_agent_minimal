@echo off
setlocal
REM Pin working directory to the folder of this BAT file:
cd /d %~dp0
REM Ensure local packages (rag/, agent/, etc.) are importable:
set PYTHONPATH=%CD%

REM Check if virtual environment exists
if not exist .venv\Scripts\activate.bat (
  echo [4_run_all] ERROR: Virtual environment not found.
  echo [4_run_all] Please run 0_setup_env.bat first to create the virtual environment.
  pause
  exit /b 1
)

REM Check for .env file
if not exist .env (
  echo [4_run_all] WARNING: .env file not found. LLM API keys may not be configured.
  echo [4_run_all] Continuing anyway...
) else (
  echo [4_run_all] .env file found. Environment variables will be loaded.
)

REM Set ports
set STREAMLIT_PORT=8501

echo [4_run_all] ========================================
echo [4_run_all] Starting Medical AI Agent Streamlit UI
echo [4_run_all] ========================================
echo.

REM Verify python-dotenv is installed in virtual environment (for Streamlit UI)
echo [4_run_all] Checking python-dotenv installation for Streamlit UI...
.venv\Scripts\python.exe -c "import dotenv" 2>nul
if errorlevel 1 (
  echo [4_run_all] WARNING: python-dotenv not found in virtual environment.
  echo [4_run_all] Installing python-dotenv...
  .venv\Scripts\python.exe -m pip install --quiet --upgrade python-dotenv
  if errorlevel 1 (
    echo [4_run_all] ERROR: Failed to install python-dotenv.
    echo [4_run_all] Attempting to install from requirements.txt...
    .venv\Scripts\python.exe -m pip install --quiet --upgrade -r requirements.txt
    if errorlevel 1 (
      echo [4_run_all] ERROR: Failed to install from requirements.txt.
      echo [4_run_all] Please check your internet connection and try again.
      pause
      exit /b 1
    )
  )
  echo [4_run_all] Verifying python-dotenv installation...
  .venv\Scripts\python.exe -c "import dotenv; print('[4_run_all] python-dotenv version:', dotenv.__version__)" 2>nul
  if errorlevel 1 (
    echo [4_run_all] ERROR: python-dotenv installation verification failed.
    pause
    exit /b 1
  )
  echo [4_run_all] python-dotenv installed and verified successfully.
)

REM Launch Streamlit UI in a new window
echo [4_run_all] Launching Streamlit UI (port %STREAMLIT_PORT%)...
echo [4_run_all] Using Python: .venv\Scripts\python.exe

REM Create a temporary batch file for Streamlit UI window to handle python-dotenv check
set TEMP_BAT=%TEMP%\streamlit_ui_%RANDOM%.bat
(
  echo @echo off
  echo cd /d %CD%
  echo set PYTHONPATH=%CD%
  echo call .venv\Scripts\activate.bat
  echo echo [4_run_all] Checking python-dotenv in new window...
  echo .venv\Scripts\python.exe -c "import dotenv" 2^>nul
  echo if errorlevel 1 ^(
  echo   echo [4_run_all] Installing python-dotenv in new window...
  echo   .venv\Scripts\python.exe -m pip install --upgrade python-dotenv
  echo   if errorlevel 1 ^(
  echo     echo [4_run_all] ERROR: pip install failed. Trying requirements.txt...
  echo     .venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
  echo     if errorlevel 1 ^(
  echo       echo [4_run_all] ERROR: All installation attempts failed.
  echo       pause
  echo       exit /b 1
  echo     ^)
  echo   ^)
  echo   echo [4_run_all] Verifying installation...
  echo   .venv\Scripts\python.exe -c "import dotenv" 2^>nul
  echo   if errorlevel 1 ^(
  echo     echo [4_run_all] ERROR: Verification failed after installation.
  echo     pause
  echo     exit /b 1
  echo   ^)
  echo   echo [4_run_all] python-dotenv verified successfully.
  echo ^)
  echo .venv\Scripts\python.exe -m streamlit run app.py --server.port %STREAMLIT_PORT% --server.headless true
) > "%TEMP_BAT%"

start "MedicalAgent UI" cmd /k "%TEMP_BAT%"

echo.
echo [4_run_all] ========================================
echo [4_run_all] Streamlit UI started!
echo [4_run_all] ========================================
echo [4_run_all] UI: http://localhost:%STREAMLIT_PORT%
echo.
echo [4_run_all] The UI is running in a separate window.
echo [4_run_all] Close that window to stop the service.
echo.
pause
