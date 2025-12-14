@echo off
setlocal
REM ============================================================================
REM 6. 데이터 무결성 검사
REM - 환자 데이터 확인
REM - 질문 뱅크 확인
REM - 코퍼스 및 인덱스 파일 확인
REM - 설정 파일 검증
REM ============================================================================

chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%CD%

echo ============================================================================
echo [6] 데이터 무결성 검사
echo ============================================================================
echo.

REM 1. 가상환경 확인
if not exist .venv\Scripts\python.exe (
    echo [오류] 가상환경을 찾을 수 없습니다.
    echo 먼저 0_setup_env.bat를 실행하세요.
    pause
    exit /b 1
)

REM 2. .env 파일 확인
echo [1/7] .env 파일 확인...
echo ----------------------------------------------------------------------------
if not exist .env (
    echo [오류] .env 파일을 찾을 수 없습니다.
    echo 먼저 .env 파일을 생성하고 API 키를 설정하세요.
    pause
    exit /b 1
)
echo [확인] .env 파일 존재

REM API 키 확인 (간단 체크)
.venv\Scripts\python.exe -c "import os; from dotenv import load_dotenv; load_dotenv(); key = os.getenv('OPENAI_API_KEY'); print('[확인] OPENAI_API_KEY:', '설정됨' if key else '없음'); exit(0 if key else 1)" >nul 2>&1
if errorlevel 1 (
    echo [경고] OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.
    echo 실험 실행 시 API 키가 필요합니다.
)

REM 3. 환자 리스트 확인
echo.
echo [2/7] 환자 리스트 확인...
echo ----------------------------------------------------------------------------
if not exist data\patients\patient_list_80.json (
    echo [오류] 환자 리스트를 찾을 수 없습니다.
    pause
    exit /b 1
)

.venv\Scripts\python.exe -c "import json, sys; sys.stdout.reconfigure(encoding='utf-8'); data = json.load(open('data/patients/patient_list_80.json', encoding='utf-8')); print(f'[확인] 환자 수: {len(data[\"patients\"])}명'); print(f'[확인] 범위: {data[\"patients\"][0][\"patient_id\"]} ~ {data[\"patients\"][-1][\"patient_id\"]}')"

REM 4. 프로파일 카드 확인
echo.
echo [3/7] 프로파일 카드 확인...
echo ----------------------------------------------------------------------------
powershell -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $count = (Get-ChildItem data\patients\profile_cards\SYN_*.json -ErrorAction SilentlyContinue).Count; Write-Host '[확인] 프로파일 카드: '$count'개'; if ($count -lt 70) { Write-Host '[경고] 프로파일 카드가 부족합니다 (최소 70개 권장)' -ForegroundColor Yellow }"

REM 5. 질문 뱅크 확인
echo.
echo [4/7] 질문 뱅크 확인...
echo ----------------------------------------------------------------------------
if not exist experiments\question_bank\question_bank_5x15.v1.json (
    echo [오류] 질문 뱅크를 찾을 수 없습니다.
    pause
    exit /b 1
)

.venv\Scripts\python.exe -c "import json, sys; sys.stdout.reconfigure(encoding='utf-8'); qb = json.load(open('experiments/question_bank/question_bank_5x15.v1.json', encoding='utf-8')); print(f'[확인] 질문 수: {len(qb[\"items\"])}개'); turns = {}; [turns.update({q['turn_id']: turns.get(q['turn_id'], 0) + 1}) for q in qb['items']]; print('[확인] 턴별 분포:', turns)"

REM 6. 코퍼스 파일 확인
echo.
echo [5/7] 코퍼스 파일 확인...
echo ----------------------------------------------------------------------------

set CORPUS_FOUND=0

if exist data\corpus\train_source\train_source_data.index.jsonl (
    echo [확인] BM25 코퍼스: data\corpus\train_source\train_source_data.index.jsonl
    set CORPUS_FOUND=1
)

if exist data\corpus\train_qa\train_questions.index.jsonl (
    echo [확인] BM25 코퍼스: data\corpus\train_qa\train_questions.index.jsonl
    set CORPUS_FOUND=1
)

if %CORPUS_FOUND%==0 (
    echo [경고] 코퍼스 파일을 찾을 수 없습니다.
    echo 검색 기능이 제대로 작동하지 않을 수 있습니다.
)

REM 7. FAISS 인덱스 확인
echo.
echo [6/7] FAISS 인덱스 확인...
echo ----------------------------------------------------------------------------

set INDEX_FOUND=0

if exist data\index\train_source\train_source_data.index.faiss (
    echo [확인] FAISS 인덱스: data\index\train_source\train_source_data.index.faiss
    set INDEX_FOUND=1
)

if exist data\index\train_qa\train_questions.index.faiss (
    echo [확인] FAISS 인덱스: data\index\train_qa\train_questions.index.faiss
    set INDEX_FOUND=1
)

if %INDEX_FOUND%==0 (
    echo [경고] FAISS 인덱스를 찾을 수 없습니다.
    echo 벡터 검색이 제대로 작동하지 않을 수 있습니다.
)

REM 8. 설정 파일 확인
echo.
echo [7/7] 설정 파일 확인...
echo ----------------------------------------------------------------------------

if not exist experiments\config.yaml (
    echo [오류] 실험 설정 파일을 찾을 수 없습니다: experiments\config.yaml
    pause
    exit /b 1
)
echo [확인] 실험 설정: experiments\config.yaml

if not exist config\model_config.yaml (
    echo [오류] 모델 설정 파일을 찾을 수 없습니다: config\model_config.yaml
    pause
    exit /b 1
)
echo [확인] 모델 설정: config\model_config.yaml

if not exist config\agent_config.yaml (
    echo [오류] 에이전트 설정 파일을 찾을 수 없습니다: config\agent_config.yaml
    pause
    exit /b 1
)
echo [확인] 에이전트 설정: config\agent_config.yaml

REM 9. 설정 파일 내용 검증
echo.
echo [설정 내용 검증]
echo ----------------------------------------------------------------------------

.venv\Scripts\python.exe -c "import yaml, sys; sys.stdout.reconfigure(encoding='utf-8'); config = yaml.safe_load(open('experiments/config.yaml', encoding='utf-8')); print(f'[확인] LLM Provider: {config[\"llm\"][\"provider\"]}'); print(f'[확인] LLM Model: {config[\"llm\"][\"model\"]}'); print(f'[확인] Agent Provider: {config[\"agent\"][\"provider\"]}'); print(f'[확인] Agent Model: {config[\"agent\"][\"model\"]}')"

REM 완료
echo.
echo ============================================================================
echo 데이터 무결성 검사 완료!
echo ============================================================================
echo.
echo 다음 단계: 7_test_single_turn.bat (단일 턴 테스트)
echo.
pause

