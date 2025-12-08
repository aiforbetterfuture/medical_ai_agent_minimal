@echo off
setlocal
REM Pin working directory to the folder of this BAT file:
cd /d %~dp0
REM Ensure local packages (rag/, agent/, etc.) are importable:
set PYTHONPATH=%CD%

echo [0_setup_env] Creating virtual environment (.venv) ...
if not exist .venv (
  python -m venv .venv
  if errorlevel 1 (
    echo [0_setup_env] Failed to create venv. Check Python installation.
    pause
    exit /b 1
  )
)

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
) else (
  echo [0_setup_env] Failed to activate venv. Check Python installation.
  pause
  exit /b 1
)

echo [0_setup_env] Upgrading pip ...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [0_setup_env] Failed to upgrade pip.
  pause
  exit /b 1
)

echo [0_setup_env] Installing requirements ...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [0_setup_env] Failed to install requirements.
  pause
  exit /b 1
)

REM Verify critical packages are installed
echo [0_setup_env] Verifying critical packages...
python -c "import dotenv" 2>nul
if errorlevel 1 (
  echo [0_setup_env] WARNING: python-dotenv not found, installing...
  python -m pip install --quiet --upgrade python-dotenv
  if errorlevel 1 (
    echo [0_setup_env] ERROR: Failed to install python-dotenv.
    echo [0_setup_env] Attempting to reinstall from requirements.txt...
    python -m pip install --quiet --upgrade -r requirements.txt
    if errorlevel 1 (
      echo [0_setup_env] ERROR: Failed to install from requirements.txt.
      pause
      exit /b 1
    )
  )
  echo [0_setup_env] Verifying python-dotenv installation...
  python -c "import dotenv; print('[0_setup_env] python-dotenv version:', dotenv.__version__)" 2>nul
  if errorlevel 1 (
    echo [0_setup_env] ERROR: python-dotenv installation verification failed.
    pause
    exit /b 1
  )
)
echo [0_setup_env] Critical packages verified.

echo.
echo [0_setup_env] Checking for .env file...
if not exist .env (
  echo [0_setup_env] WARNING: .env file not found.
  echo [0_setup_env] Please create .env file with your LLM API keys:
  echo [0_setup_env]   OPENAI_API_KEY=your_key_here
  echo [0_setup_env]   GOOGLE_API_KEY=your_key_here  (optional, for Gemini)
  echo [0_setup_env]   GEMINI_API_KEY=your_key_here  (optional, for Gemini)
  echo [0_setup_env]   ANTHROPIC_API_KEY=your_key_here  (optional, for Claude)
) else (
  echo [0_setup_env] .env file found.
)

echo.
echo [0_setup_env] Setup complete!
echo [0_setup_env] Next steps:
echo [0_setup_env]   1. Ensure .env file is configured with API keys
echo [0_setup_env]   2. Run 3_run_ui.bat to start the Streamlit UI
echo [0_setup_env]   3. Or run 4_run_all.bat to start the UI
pause
