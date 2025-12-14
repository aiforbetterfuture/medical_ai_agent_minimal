@echo off
setlocal

cd /d %~dp0
set PYTHONPATH=%~dp0

echo ============================================================================
echo Starting environment setup...
echo ============================================================================

echo.
echo Checking Python installation...

set PY_CMD=
set PYTHON_EXE=

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    python --version
    echo Python found.
    goto create_venv
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    py --version
    echo Python found.
    goto create_venv
)

py -3.10 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py -3.10
    py -3.10 --version
    echo Python 3.10 found.
    goto create_venv
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python3
    python3 --version
    echo Python found.
    goto create_venv
)

echo ERROR: Python not found!
echo Please install Python 3.10 or later.
pause
exit /b 1

:create_venv
echo.
echo Step 1: Creating virtual environment ...
if not exist .venv (
  %PY_CMD% -m venv .venv
  if not %errorlevel% equ 0 (
    echo ERROR: Failed to create venv.
    pause
    exit /b 1
  )
  echo Virtual environment created.
) else (
  echo Virtual environment already exists.
)

echo.
echo Step 2: Activating virtual environment ...
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
  if not %errorlevel% equ 0 (
    echo ERROR: Failed to activate venv.
    pause
    exit /b 1
  )
  echo Virtual environment activated.
  
  if exist .venv\Scripts\python.exe (
    set PYTHON_EXE=.venv\Scripts\python.exe
  ) else (
    set PYTHON_EXE=python
  )
) else (
  echo ERROR: .venv\Scripts\activate.bat not found.
  pause
  exit /b 1
)

echo.
echo Step 3: Upgrading pip ...
"%PYTHON_EXE%" -m pip install --upgrade pip
if not %errorlevel% equ 0 (
  echo WARNING: Failed to upgrade pip, but continuing...
) else (
  echo pip upgraded successfully.
)

echo.
echo Step 4: Installing requirements ...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if not %errorlevel% equ 0 (
  echo ERROR: Failed to install requirements.
  echo Please check your internet connection and try again.
  pause
  exit /b 1
) else (
  echo Requirements installed successfully.
)

echo.
echo Step 5: Installing spaCy and MedCAT ...
"%PYTHON_EXE%" -m pip install --upgrade "spacy>=3.8"
"%PYTHON_EXE%" -m pip install --upgrade "medcat>=2.0"
"%PYTHON_EXE%" -m pip install --upgrade peft
echo spaCy and MedCAT installation completed.

echo.
echo Step 6: Installing matplotlib ...
"%PYTHON_EXE%" -m pip install --upgrade matplotlib
if not %errorlevel% equ 0 (
    echo WARNING: Failed to install matplotlib.
) else (
    echo matplotlib installed successfully.
)

echo.
echo Step 7: Installing ragas and datasets for RAGAS evaluation metrics ...
"%PYTHON_EXE%" -m pip install --upgrade "ragas>=0.1.0" "datasets>=2.14.0"
if not %errorlevel% equ 0 (
    echo WARNING: Failed to install ragas.
    echo You can install later: "%PYTHON_EXE%" -m pip install ragas datasets
) else (
    echo ragas and datasets installed successfully.
    "%PYTHON_EXE%" -c "import ragas; print('RAGAS version:', ragas.__version__)" >nul 2>&1
    if %errorlevel% equ 0 (
        echo RAGAS import test passed.
    ) else (
        echo WARNING: RAGAS import test failed.
    )
)

echo.
echo Step 8: Downloading spaCy model ...
"%PYTHON_EXE%" -m spacy download en_core_web_md
if not %errorlevel% equ 0 (
    echo WARNING: Failed to download spaCy model.
) else (
    echo spaCy model downloaded successfully.
)

echo.
echo Step 9: Verifying installations ...
"%PYTHON_EXE%" -c "import medcat; print('medcat:', medcat.__version__)" 2>nul
"%PYTHON_EXE%" -c "import spacy; print('spacy:', spacy.__version__)" 2>nul
"%PYTHON_EXE%" -c "import spacy; spacy.load('en_core_web_md'); print('spaCy model OK')" 2>nul

"%PYTHON_EXE%" -c "import ragas; print('ragas:', ragas.__version__)" >nul 2>&1
if not %errorlevel% equ 0 (
    echo WARNING: RAGAS verification failed.
    echo Attempting to reinstall RAGAS...
    "%PYTHON_EXE%" -m pip install --upgrade --force-reinstall "ragas>=0.1.0" "datasets>=2.14.0"
    "%PYTHON_EXE%" -c "import ragas; print('ragas:', ragas.__version__)" >nul 2>&1
    if %errorlevel% equ 0 (
        echo RAGAS verification OK after reinstall.
    ) else (
        echo ERROR: RAGAS installation failed.
    )
) else (
    echo RAGAS verification OK.
)

echo.
echo Step 10: Verifying python-dotenv ...
"%PYTHON_EXE%" -c "import dotenv" >nul 2>&1
if not %errorlevel% equ 0 (
  echo Installing python-dotenv ...
  "%PYTHON_EXE%" -m pip install python-dotenv
) else (
  echo python-dotenv already installed.
)

echo.
echo Step 11: Checking .env file ...
if not exist .env (
  echo WARNING: .env file not found.
  echo Create .env with your API keys.
) else (
  echo .env file found.
)

echo.
echo Step 12: Checking MedCAT2 model path ...
set DEFAULT_MODEL=%~dp0medcat2\mc_modelpack_snomed_int_16_mar_2022_25be3857ba34bdd5.zip
if not defined MEDCAT2_MODEL_PATH (
  if exist "%DEFAULT_MODEL%" (
    echo Setting MEDCAT2_MODEL_PATH ...
    setx MEDCAT2_MODEL_PATH "%DEFAULT_MODEL%"
  ) else (
    echo Model pack not found at default location.
  )
) else (
  echo MEDCAT2_MODEL_PATH already set.
)

echo.
echo ============================================================================
echo Setup complete!
echo ============================================================================
echo.
echo Next steps:
echo   - Run: streamlit run app.py
echo   - Or run: 1_check_keys.bat
echo.
pause
