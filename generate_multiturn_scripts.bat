@echo off
chcp 65001 >nul
echo ========================================
echo 멀티턴 스크립트 자동 생성
echo ========================================
echo.

python experiments/generate_multiturn_scripts_from_fhir.py ^
    --profile_cards_dir "data/patients/profile_cards" ^
    --out "data/multiturn_scripts/scripts_5turn.jsonl" ^
    --max_patients 80 ^
    --seed 42

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 스크립트 생성 완료!
    echo 📁 출력 파일: data/multiturn_scripts/scripts_5turn.jsonl
) else (
    echo.
    echo ❌ 스크립트 생성 실패
    exit /b 1
)

pause

