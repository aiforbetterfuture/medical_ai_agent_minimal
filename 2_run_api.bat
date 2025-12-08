@echo off
setlocal
REM Pin working directory to the folder of this BAT file:
cd /d %~dp0

echo [2_run_api] ========================================
echo [2_run_api] WARNING: API Server is not implemented
echo [2_run_api] ========================================
echo.
echo [2_run_api] This project currently only supports Streamlit UI.
echo [2_run_api] Please use 3_run_ui.bat to start the Streamlit interface.
echo.
echo [2_run_api] If you need an API server, you can:
echo [2_run_api]   1. Create a FastAPI application
echo [2_run_api]   2. Or use the agent.graph.run_agent() function directly
echo.
pause
exit /b 0
