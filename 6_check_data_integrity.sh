#!/bin/bash
# ============================================================================
# 6. 데이터 무결성 검사
# - 환자 데이터 확인
# - 질문 뱅크 확인
# - 코퍼스 및 인덱스 파일 확인
# - 설정 파일 검증
# ============================================================================

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"

echo "============================================================================"
echo "[6] 데이터 무결성 검사"
echo "============================================================================"
echo ""

# 1. 가상환경 확인
echo "[1/7] 가상환경 확인..."
echo "----------------------------------------------------------------------------"
if [ ! -f ".venv/bin/python" ]; then
    echo "[오류] 가상환경을 찾을 수 없습니다."
    echo "먼저 0_setup_env.sh를 실행하세요."
    exit 1
fi
echo "[확인] 가상환경 존재"

# 2. .env 파일 확인
echo ""
echo "[2/7] .env 파일 확인..."
echo "----------------------------------------------------------------------------"
if [ ! -f ".env" ]; then
    echo "[오류] .env 파일을 찾을 수 없습니다."
    exit 1
fi
echo "[확인] .env 파일 존재"

# 3. 환자 리스트 확인
echo ""
echo "[3/7] 환자 리스트 확인..."
echo "----------------------------------------------------------------------------"
if [ ! -f "data/patients/patient_list_80.json" ]; then
    echo "[오류] 환자 리스트를 찾을 수 없습니다."
    exit 1
fi

.venv/bin/python -c "import json; data = json.load(open('data/patients/patient_list_80.json')); print(f'[확인] 환자 수: {len(data[\"patients\"])}명'); print(f'[확인] 범위: {data[\"patients\"][0][\"patient_id\"]} ~ {data[\"patients\"][-1][\"patient_id\"]}')"

# 4. 프로파일 카드 확인
echo ""
echo "[4/7] 프로파일 카드 확인..."
echo "----------------------------------------------------------------------------"
count=$(ls data/patients/profile_cards/SYN_*.json 2>/dev/null | wc -l)
echo "[확인] 프로파일 카드: ${count}개"
if [ "$count" -lt 70 ]; then
    echo "[경고] 프로파일 카드가 부족합니다 (최소 70개 권장)"
fi

# 5. 질문 뱅크 확인
echo ""
echo "[5/7] 질문 뱅크 확인..."
echo "----------------------------------------------------------------------------"
if [ ! -f "experiments/question_bank/question_bank_5x15.v1.json" ]; then
    echo "[오류] 질문 뱅크를 찾을 수 없습니다."
    exit 1
fi

.venv/bin/python -c "import json; qb = json.load(open('experiments/question_bank/question_bank_5x15.v1.json', encoding='utf-8')); print(f'[확인] 질문 수: {len(qb[\"items\"])}개'); turns = {}; [turns.update({q['turn_id']: turns.get(q['turn_id'], 0) + 1}) for q in qb['items']]; print('[확인] 턴별 분포:', turns)"

# 6. 코퍼스 파일 확인
echo ""
echo "[6/7] 코퍼스 파일 확인..."
echo "----------------------------------------------------------------------------"

CORPUS_FOUND=0

if [ -f "data/corpus/train_source/train_source_data.index.jsonl" ]; then
    echo "[확인] BM25 코퍼스: data/corpus/train_source/train_source_data.index.jsonl"
    CORPUS_FOUND=1
fi

if [ -f "data/corpus/train_qa/train_questions.index.jsonl" ]; then
    echo "[확인] BM25 코퍼스: data/corpus/train_qa/train_questions.index.jsonl"
    CORPUS_FOUND=1
fi

if [ "$CORPUS_FOUND" -eq 0 ]; then
    echo "[경고] 코퍼스 파일을 찾을 수 없습니다."
    echo "검색 기능이 제대로 작동하지 않을 수 있습니다."
fi

# 7. FAISS 인덱스 확인
echo ""
echo "[7/7] FAISS 인덱스 확인..."
echo "----------------------------------------------------------------------------"

INDEX_FOUND=0

if [ -f "data/index/train_source/train_source_data.index.faiss" ]; then
    echo "[확인] FAISS 인덱스: data/index/train_source/train_source_data.index.faiss"
    INDEX_FOUND=1
fi

if [ -f "data/index/train_qa/train_questions.index.faiss" ]; then
    echo "[확인] FAISS 인덱스: data/index/train_qa/train_questions.index.faiss"
    INDEX_FOUND=1
fi

if [ "$INDEX_FOUND" -eq 0 ]; then
    echo "[경고] FAISS 인덱스를 찾을 수 없습니다."
    echo "벡터 검색이 제대로 작동하지 않을 수 있습니다."
fi

# 8. 설정 파일 확인
echo ""
echo "[8/7] 설정 파일 확인..."
echo "----------------------------------------------------------------------------"

if [ ! -f "experiments/config.yaml" ]; then
    echo "[오류] 실험 설정 파일을 찾을 수 없습니다: experiments/config.yaml"
    exit 1
fi
echo "[확인] 실험 설정: experiments/config.yaml"

if [ ! -f "config/model_config.yaml" ]; then
    echo "[오류] 모델 설정 파일을 찾을 수 없습니다: config/model_config.yaml"
    exit 1
fi
echo "[확인] 모델 설정: config/model_config.yaml"

if [ ! -f "config/agent_config.yaml" ]; then
    echo "[오류] 에이전트 설정 파일을 찾을 수 없습니다: config/agent_config.yaml"
    exit 1
fi
echo "[확인] 에이전트 설정: config/agent_config.yaml"

# 9. 설정 파일 내용 검증
echo ""
echo "[설정 내용 검증]"
echo "----------------------------------------------------------------------------"

.venv/bin/python -c "import yaml; config = yaml.safe_load(open('experiments/config.yaml')); print(f'[확인] LLM Provider: {config[\"llm\"][\"provider\"]}'); print(f'[확인] LLM Model: {config[\"llm\"][\"model\"]}'); print(f'[확인] Agent Provider: {config[\"agent\"][\"provider\"]}'); print(f'[확인] Agent Model: {config[\"agent\"][\"model\"]}')"

# 완료
echo ""
echo "============================================================================"
echo "데이터 무결성 검사 완료!"
echo "============================================================================"
echo ""
echo "다음 단계: 7_test_single_turn.sh (단일 턴 테스트)"
echo ""

