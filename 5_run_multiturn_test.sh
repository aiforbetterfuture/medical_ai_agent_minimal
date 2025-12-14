#!/bin/bash
# ============================================================================
# 멀티턴 실험 실행 스크립트 (Linux/Mac)
# - 80명 Synthea 환자 x 5턴 x 2모드(LLM, AI Agent)
# - 총 800회 API 호출 예상
# - 예상 소요 시간: 2-4시간 (API 속도에 따라 변동)
# ============================================================================

set -e  # 오류 발생 시 중단

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"

echo "============================================================================"
echo "멀티턴 실험 실행"
echo "============================================================================"
echo ""
echo "[경고] 이 실험은 다음을 수행합니다:"
echo "  - 80명 환자 x 5턴 x 2모드 = 800회 API 호출"
echo "  - 예상 비용: \$5-15 (모델 및 토큰 사용량에 따라)"
echo "  - 예상 시간: 2-4시간"
echo ""
read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "실행 취소됨"
    exit 0
fi

# 1. 환경 확인
echo ""
echo "[1/5] 환경 확인 중..."
echo "============================================================================"

if [ ! -f ".venv/bin/python" ]; then
    echo "[오류] 가상환경을 찾을 수 없습니다."
    echo "먼저 python -m venv .venv를 실행하세요."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "[오류] .env 파일을 찾을 수 없습니다."
    echo "API 키를 설정하세요."
    exit 1
fi

# 2. 데이터 확인
echo ""
echo "[2/5] 데이터 확인 중..."
echo "============================================================================"

if [ ! -f "data/patients/patient_list_80.json" ]; then
    echo "[오류] 환자 리스트를 찾을 수 없습니다: data/patients/patient_list_80.json"
    echo "scripts/generate_synthea_profiles.py를 실행하세요."
    exit 1
fi

if [ ! -f "experiments/question_bank/question_bank_5x15.v1.json" ]; then
    echo "[오류] 질문 뱅크를 찾을 수 없습니다."
    exit 1
fi

echo "[확인] 환자 리스트: data/patients/patient_list_80.json"
echo "[확인] 질문 뱅크: experiments/question_bank/question_bank_5x15.v1.json"

# 3. 실험 실행
echo ""
echo "[3/5] 멀티턴 실험 실행 중..."
echo "============================================================================"
echo ""
echo "실행 시작: $(date)"
echo "로그 위치: runs/2025-12-13_primary_v1/"
echo ""

.venv/bin/python experiments/run_multiturn_experiment_v2.py \
    --config experiments/config.yaml \
    --max-patients 80 \
    --max-turns 5

if [ $? -ne 0 ]; then
    echo ""
    echo "[오류] 실험 실행 중 오류가 발생했습니다."
    echo "로그를 확인하세요: runs/2025-12-13_primary_v1/events.jsonl"
    exit 1
fi

echo ""
echo "실행 완료: $(date)"

# 4. 결과 검증
echo ""
echo "[4/5] 결과 검증 중..."
echo "============================================================================"

RUN_DIR="runs/2025-12-13_primary_v1"

if [ ! -f "$RUN_DIR/events.jsonl" ]; then
    echo "[오류] 결과 파일을 찾을 수 없습니다: $RUN_DIR/events.jsonl"
    exit 1
fi

echo "[확인] 이벤트 로그: $RUN_DIR/events.jsonl"

# 데이터 무결성 검증
echo ""
echo "데이터 무결성 검증 중..."
.venv/bin/python scripts/validate_run.py --run_dir "$RUN_DIR"

if [ $? -ne 0 ]; then
    echo "[경고] 데이터 무결성 검증 실패"
    echo "결과 분석 시 주의가 필요합니다."
fi

# 페어링 공정성 검증
echo ""
echo "페어링 공정성 검증 중..."
.venv/bin/python scripts/check_fairness.py --events_path "$RUN_DIR/events.jsonl"

if [ $? -ne 0 ]; then
    echo "[경고] 페어링 공정성 검증 실패"
    echo "Paired t-test 결과가 유효하지 않을 수 있습니다."
fi

# 5. 결과 분석
echo ""
echo "[5/5] 결과 분석 중..."
echo "============================================================================"

# Summary 생성
echo ""
echo "Summary 생성 중..."
.venv/bin/python scripts/summarize_run.py \
    --run_dir "$RUN_DIR" \
    --metrics faithfulness,answer_relevance,context_precision,context_recall,context_relevancy \
    --pretty

if [ $? -ne 0 ]; then
    echo "[오류] Summary 생성 실패"
    exit 1
fi

echo "[확인] Summary: $RUN_DIR/summary.json"

# 테이블 생성
echo ""
echo "CSV 테이블 생성 중..."
.venv/bin/python scripts/make_paper_tables.py \
    --summary_json "$RUN_DIR/summary.json" \
    --output_dir "$RUN_DIR/tables"

if [ $? -ne 0 ]; then
    echo "[경고] 테이블 생성 실패"
else
    echo "[확인] 테이블: $RUN_DIR/tables/"
fi

# 그림 생성
echo ""
echo "그림 생성 중..."
.venv/bin/python scripts/make_paper_figures.py \
    --summary_json "$RUN_DIR/summary.json" \
    --output_dir "$RUN_DIR/figures"

if [ $? -ne 0 ]; then
    echo "[경고] 그림 생성 실패 (matplotlib 필요)"
else
    echo "[확인] 그림: $RUN_DIR/figures/"
fi

# LaTeX 테이블 생성
echo ""
echo "LaTeX 테이블 생성 중..."
.venv/bin/python scripts/make_latex_tables.py \
    --csv_dir "$RUN_DIR/tables" \
    --output_dir "$RUN_DIR/latex"

if [ $? -ne 0 ]; then
    echo "[경고] LaTeX 테이블 생성 실패"
else
    echo "[확인] LaTeX: $RUN_DIR/latex/"
fi

# 완료
echo ""
echo "============================================================================"
echo "멀티턴 실험 완료!"
echo "============================================================================"
echo ""
echo "결과 위치: $RUN_DIR"
echo ""
echo "생성된 파일:"
echo "  - events.jsonl          : 턴별 실행 로그"
echo "  - summary.json          : 통계 요약"
echo "  - tables/*.csv          : CSV 테이블"
echo "  - figures/*.png/pdf     : 그림 (PNG/PDF)"
echo "  - latex/*.tex           : LaTeX 테이블"
echo ""
echo "다음 단계:"
echo "  1. summary.json 확인"
echo "  2. tables/overall_comparison.csv 확인"
echo "  3. figures/ 폴더의 그림 확인"
echo ""

