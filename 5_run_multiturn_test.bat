@echo off
setlocal
REM ============================================================================
REM 멀티턴 실험 실행 메뉴
REM - 단계별 실행으로 에러 조기 발견
REM - 각 단계별 검증 및 확인
REM ============================================================================

chcp 65001 >nul
cd /d %~dp0

echo ============================================================================
echo 멀티턴 실험 실행 메뉴
echo ============================================================================
echo.
echo 이 스크립트는 멀티턴 실험을 단계별로 안내합니다.
echo 각 단계를 순차적으로 실행하여 에러를 조기에 발견할 수 있습니다.
echo.
echo ============================================================================
echo 실행 단계
echo ============================================================================
echo.
echo [6] 데이터 무결성 검사
echo     "환자 데이터, 질문 뱅크, 코퍼스, 인덱스 확인"
echo     "설정 파일 검증"
echo     "파일: 6_check_data_integrity.bat"
echo.
echo [7] 단일 턴 테스트 (1명 x 1턴 x 2모드)
echo     "전체 파이프라인 검증"
echo     "API 연결 확인"
echo     "예상 시간: 1-2분"
echo     "파일: 7_test_single_turn.bat"
echo.
echo [8] 멀티턴 단일 환자 테스트 (1명 x 5턴 x 2모드)
echo     "멀티턴 대화 흐름 검증"
echo     "컨텍스트 관리 확인"
echo     "예상 시간: 5-10분"
echo     "파일: 8_test_multi_turn_single_patient.bat"
echo.
echo [9] 전체 실험 실행 (78명 x 5턴 x 2모드)
echo     "전체 멀티턴 실험 수행"
echo     "예상 시간: 8-12시간"
echo     "예상 비용: $15-25"
echo     "파일: 9_run_full_experiment.bat"
echo.
echo [10] 결과 분석
echo      "데이터 검증"
echo      "통계 분석"
echo      "표 및 그래프 생성"
echo      "파일: 10_analyze_results.bat"
echo.
echo ============================================================================
echo 권장 실행 순서
echo ============================================================================
echo.
echo 1. 먼저 6_check_data_integrity.bat를 실행하여 데이터를 확인하세요.
echo 2. 그 다음 7_test_single_turn.bat로 단일 턴 테스트를 수행하세요.
echo 3. 문제가 없으면 8_test_multi_turn_single_patient.bat로 멀티턴을 테스트하세요.
echo 4. 모든 테스트가 성공하면 9_run_full_experiment.bat로 전체 실험을 실행하세요.
echo 5. 실험 완료 후 10_analyze_results.bat로 결과를 분석하세요.
echo.
echo ============================================================================
echo 주의사항
echo ============================================================================
echo.
echo 각 단계에서 에러가 발생하면 즉시 중단됩니다.
echo 에러 메시지를 확인하고 문제를 해결한 후 다시 실행하세요.
echo 전체 실험(9번)은 시간이 오래 걸리므로 테스트(7, 8번)를 먼저 수행하세요.
echo.
echo ============================================================================
echo.
echo 어떤 단계를 실행하시겠습니까?
echo.
echo   6 - 데이터 무결성 검사
echo   7 - 단일 턴 테스트
echo   8 - 멀티턴 단일 환자 테스트
echo   9 - 전체 실험 실행
echo   10 - 결과 분석
echo   A - 전체 자동 실행 (6-7-8-9-10)
echo   Q - 종료
echo.
set /p choice="선택 (6/7/8/9/10/A/Q): "

if /i "%choice%"=="6" (
    call 6_check_data_integrity.bat
    goto end
)

if /i "%choice%"=="7" (
    call 7_test_single_turn.bat
    goto end
)

if /i "%choice%"=="8" (
    call 8_test_multi_turn_single_patient.bat
    goto end
)

if /i "%choice%"=="9" (
    call 9_run_full_experiment.bat
    goto end
)

if /i "%choice%"=="10" (
    call 10_analyze_results.bat
    goto end
)

if /i "%choice%"=="A" (
    echo.
    echo ============================================================================
    echo 전체 자동 실행 시작
    echo ============================================================================
    echo.
    
    call 6_check_data_integrity.bat
    if errorlevel 1 goto error
    
    call 7_test_single_turn.bat
    if errorlevel 1 goto error
    
    call 8_test_multi_turn_single_patient.bat
    if errorlevel 1 goto error
    
    echo.
    echo ============================================================================
    echo 테스트 완료! 전체 실험을 시작합니다.
    echo ============================================================================
    pause
    
    call 9_run_full_experiment.bat
    if errorlevel 1 goto error
    
    call 10_analyze_results.bat
    if errorlevel 1 goto error
    
    echo.
    echo ============================================================================
    echo 전체 실행 완료!
    echo ============================================================================
    goto end
)

if /i "%choice%"=="Q" (
    echo 종료합니다.
    goto end
)

echo 잘못된 선택입니다.
pause
goto end

:error
echo.
echo ============================================================================
echo 오류 발생! 실행을 중단합니다.
echo ============================================================================
pause
exit /b 1

:end

