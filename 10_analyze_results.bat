@echo off
setlocal
REM ============================================================================
REM 10. 결과 분석 (통합 파이프라인)
REM - 모든 평가 지표 포함 (RAGAS + 멀티턴 컨텍스트 지표)
REM - 데이터 검증, 통계 분석, 표/그래프/LaTeX 생성
REM ============================================================================

chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo [10] 실험 결과 분석 (통합 파이프라인)
echo ============================================================================
echo.

set RUN_DIR=runs\2025-12-13_primary_v1

REM 결과 디렉토리 확인
if not exist %RUN_DIR%\events.jsonl (
    echo [ERROR] Experiment results not found: %RUN_DIR%\events.jsonl
    echo.
    echo Please run the experiment first:
    echo   9_run_full_experiment.bat
    echo.
    pause
    exit /b 1
)

REM run_paper_pipeline.py 존재 여부 확인
if not exist scripts\run_paper_pipeline.py (
    echo [오류] scripts\run_paper_pipeline.py를 찾을 수 없습니다.
    echo.
    echo 이 파일이 없으면 결과 분석을 수행할 수 없습니다.
    echo.
    pause
    exit /b 1
)

REM 통합 파이프라인 실행
echo [INFO] Running integrated analysis pipeline...
echo [INFO] This will perform:
echo   - Data validation
echo   - Fairness check
echo   - Statistical analysis (RAGAS metrics)
echo   - Multiturn context metrics (CUS, UR, CCR)
echo   - Table generation (CSV)
echo   - Figure generation (PNG/PDF)
echo   - LaTeX table generation
echo.

.venv\Scripts\python.exe scripts\run_paper_pipeline.py --run_dir %RUN_DIR%

if errorlevel 1 (
    echo.
    echo [ERROR] Analysis pipeline failed
    pause
    exit /b 1
)

REM 완료
echo.
echo ============================================================================
echo [COMPLETE] Result analysis finished!
echo ============================================================================
echo.
echo Generated files:
echo ----------------------------------------------------------------------------
echo   paper_assets\summary.json      : 통계 요약 (모든 지표 포함)
echo   paper_assets\tables\*.csv      : CSV 표
echo   paper_assets\figures\*.png     : 그래프 (PNG)
echo   paper_assets\figures\*.pdf     : 그래프 (PDF)
echo   paper_assets\latex\*.tex       : LaTeX 테이블
echo.
echo Output location: %RUN_DIR%\paper_assets\
echo.
echo Next steps for paper writing:
echo ----------------------------------------------------------------------------
echo 1. Review summary.json
echo    - Check overall statistics
echo    - Check per-turn analysis
echo    - Check efficiency metrics
echo    - Check multiturn context metrics (CUS, UR, CCR)
echo.
echo 2. Insert CSV tables into paper
echo    - paper_assets\tables\overall_comparison.csv
echo    - paper_assets\tables\per_turn_comparison.csv
echo    - paper_assets\tables\efficiency_metrics.csv
echo.
echo 3. Insert figures into paper
echo    - paper_assets\figures\overall_comparison.png
echo    - paper_assets\figures\per_turn_trends.png
echo    - paper_assets\figures\efficiency_comparison.png
echo    - paper_assets\figures\effect_sizes.png
echo.
echo 4. Use LaTeX tables (if using LaTeX)
echo    - paper_assets\latex\*.tex
echo.
pause
