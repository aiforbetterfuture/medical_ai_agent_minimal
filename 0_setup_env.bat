@echo off
setlocal

REM Change to the folder where this BAT file is located
cd /d %~dp0

REM Set PYTHONPATH for local imports
set PYTHONPATH=%CD%

REM Prefer Python 3.10 if available
set "PY_CMD=python"
py -3.10 -c "import sys" >nul 2>&1
if %errorlevel%==0 (
  set "PY_CMD=py -3.10"
  echo [0_setup_env] Using Python: py -3.10
) else (
  echo [0_setup_env] py -3.10 not found, using default python
)

echo [0_setup_env] Creating virtual environment ...
if not exist .venv (
  %PY_CMD% -m venv .venv
  if errorlevel 1 (
    echo [0_setup_env] Failed to create venv.
    pause
    exit /b 1
  )
)

REM Activate venv
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
) else (
  echo [0_setup_env] Failed to activate venv.
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

echo [0_setup_env] Installing spaCy and MedCAT ...
python -m pip install --upgrade "spacy>=3.1,<3.2"
python -m pip install --upgrade "medcat[spacy]"
python -m pip install --upgrade medcat2
python -m pip install --upgrade peft

echo [0_setup_env] Downloading spaCy model ...
python -m spacy download en_core_web_md

echo [0_setup_env] Verifying installations ...
python -c "import medcat; print('medcat:', medcat.__version__)"
python -c "import spacy; print('spacy:', spacy.__version__)"
python -c "import spacy; spacy.load('en_core_web_md'); print('spaCy model OK')"

echo [0_setup_env] Verifying python-dotenv ...
python -c "import dotenv" 2>nul
if errorlevel 1 (
  echo [0_setup_env] Installing python-dotenv ...
  python -m pip install python-dotenv
)

echo.
echo [0_setup_env] Checking .env file ...
if not exist .env (
  echo [0_setup_env] WARNING: .env file not found.
  echo [0_setup_env] Create .env with your API keys.
) else (
  echo [0_setup_env] .env file found.
)

echo [0_setup_env] Checking MedCAT2 model path ...
set "DEFAULT_MODEL=%CD%\medcat2\mc_modelpack_snomed_int_16_mar_2022_25be3857ba34bdd5.zip"
if not defined MEDCAT2_MODEL_PATH (
  if exist "%DEFAULT_MODEL%" (
    echo [0_setup_env] Setting MEDCAT2_MODEL_PATH ...
    setx MEDCAT2_MODEL_PATH "%DEFAULT_MODEL%"
  ) else (
    echo [0_setup_env] Model pack not found at default location.
  )
) else (
  echo [0_setup_env] MEDCAT2_MODEL_PATH already set.
)

echo.
echo [0_setup_env] Setup complete!
echo [0_setup_env] Run: streamlit run app.py
pause
