# 멀티턴 실험 실행 가이드

80명 Synthea 환자에 대한 전체 멀티턴 테스트 실행 가이드입니다.

## 📋 실험 개요

- **환자 수**: 80명 (Synthea 생성 가상 환자)
- **턴 수**: 5턴 (환자당)
- **모드**: 2가지 (LLM, AI Agent)
- **총 API 호출**: 800회 (80 × 5 × 2)
- **예상 시간**: 2-4시간
- **예상 비용**: $5-15 (모델 및 토큰 사용량에 따라)

## 🚀 빠른 시작

### Windows (PowerShell/CMD)

```cmd
5_run_multiturn_test.bat
```

### Linux/Mac (Bash)

```bash
chmod +x 5_run_multiturn_test.sh
./5_run_multiturn_test.sh
```

## 📝 사전 준비사항

### 1. 환경 설정

```cmd
# 1. 가상환경 생성 및 패키지 설치
0_setup_env.bat

# 2. API 키 확인
1_check_keys.bat
```

### 2. .env 파일 설정

`.env` 파일에 다음 API 키를 설정하세요:

```env
# 필수: OpenAI 또는 Google API 키 중 하나 이상
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# 선택: MedCAT 모델 경로 (자동 설정됨)
MEDCAT2_MODEL_PATH=C:\...\medcat2\mc_modelpack_snomed_int_16_mar_2022_25be3857ba34bdd5.zip
```

### 3. 데이터 준비

#### 환자 데이터 생성 (Synthea 사용 시)

```cmd
python scripts\generate_synthea_profiles.py
```

이 스크립트는 다음을 생성합니다:
- `data/patients/patient_list_80.json`: 80명 환자 리스트
- `data/patients/profile_cards/SYN_*.json`: 환자별 프로파일 카드

#### 질문 뱅크 확인

`experiments/question_bank/question_bank_5x15.v1.json`이 존재하는지 확인하세요.
- 5턴 × 15개 paraphrase = 75개 질문

## 🎯 실행 방법

### 방법 1: 배치 파일 사용 (권장)

```cmd
5_run_multiturn_test.bat
```

이 배치 파일은 다음을 자동으로 수행합니다:
1. 환경 확인 (가상환경, .env, 데이터)
2. 멀티턴 실험 실행 (80명 × 5턴 × 2모드)
3. 결과 검증 (데이터 무결성, 페어링 공정성)
4. 결과 분석 (summary, tables, figures, latex)

### 방법 2: 수동 실행

#### Step 1: 실험 실행

```cmd
.venv\Scripts\python.exe experiments\run_multiturn_experiment_v2.py ^
    --config experiments\config.yaml ^
    --max-patients 80 ^
    --max-turns 5
```

#### Step 2: 결과 검증

```cmd
# 데이터 무결성 검증
.venv\Scripts\python.exe scripts\validate_run.py ^
    --run_dir runs\2025-12-13_primary_v1

# 페어링 공정성 검증
.venv\Scripts\python.exe scripts\check_fairness.py ^
    --events_path runs\2025-12-13_primary_v1\events.jsonl
```

#### Step 3: 결과 분석

```cmd
# Summary 생성
.venv\Scripts\python.exe scripts\summarize_run.py ^
    --run_dir runs\2025-12-13_primary_v1 ^
    --metrics faithfulness,answer_relevance,context_precision,context_recall ^
    --pretty

# CSV 테이블 생성
.venv\Scripts\python.exe scripts\make_paper_tables.py ^
    --summary_json runs\2025-12-13_primary_v1\summary.json ^
    --output_dir runs\2025-12-13_primary_v1\tables

# 그림 생성 (matplotlib 필요)
.venv\Scripts\python.exe scripts\make_paper_figures.py ^
    --summary_json runs\2025-12-13_primary_v1\summary.json ^
    --output_dir runs\2025-12-13_primary_v1\figures

# LaTeX 테이블 생성
.venv\Scripts\python.exe scripts\make_latex_tables.py ^
    --csv_dir runs\2025-12-13_primary_v1\tables ^
    --output_dir runs\2025-12-13_primary_v1\latex
```

## 📊 결과 파일

실험 완료 후 `runs/2025-12-13_primary_v1/` 디렉토리에 다음 파일이 생성됩니다:

```
runs/2025-12-13_primary_v1/
├── run_manifest.json          # 실험 메타데이터
├── events.jsonl                # 턴별 실행 로그 (800줄)
├── summary.json                # 통계 요약
├── tables/
│   ├── overall_comparison.csv      # 전체 비교 (LLM vs Agent)
│   ├── per_turn_comparison.csv     # 턴별 비교
│   ├── efficiency_metrics.csv      # 효율성 지표
│   └── ablation_comparison.csv     # Ablation 비교 (있는 경우)
├── figures/
│   ├── overall_comparison.png/pdf  # 전체 비교 차트
│   ├── per_turn_trends.png/pdf     # 턴별 트렌드
│   ├── efficiency_comparison.png/pdf  # 효율성 비교
│   └── effect_sizes.png/pdf        # 효과 크기 (Cohen's d)
└── latex/
    ├── overall_comparison.tex      # LaTeX 테이블
    ├── per_turn_comparison.tex
    ├── efficiency_metrics.tex
    └── ablation_comparison.tex
```

## 📈 결과 확인

### 1. Summary 확인

```cmd
# JSON 뷰어로 확인
notepad runs\2025-12-13_primary_v1\summary.json

# 또는 Python으로 확인
python -c "import json; print(json.dumps(json.load(open('runs/2025-12-13_primary_v1/summary.json')), indent=2))"
```

### 2. CSV 테이블 확인

```cmd
# Excel로 열기
start runs\2025-12-13_primary_v1\tables\overall_comparison.csv
```

### 3. 그림 확인

```cmd
# 탐색기로 열기
explorer runs\2025-12-13_primary_v1\figures
```

## 🔍 주요 평가 지표

### 1. 전체 비교 (Overall Comparison)

- **Faithfulness**: 근거 충실도 (0-1)
- **Answer Relevance**: 답변 관련성 (0-1)
- **Context Precision**: 컨텍스트 정밀도 (0-1)
- **Context Recall**: 컨텍스트 재현율 (0-1)
- **Context Relevancy**: 컨텍스트 관련성 (0-1)

### 2. 통계 분석

- **Δ (Agent - LLM)**: 평균 차이
- **Cohen's d**: 효과 크기
- **95% CI**: 95% 신뢰구간
- **p-value**: 통계적 유의성
- **Sig.**: 유의성 표시 (*** p<0.001, ** p<0.01, * p<0.05)

### 3. 효율성 지표

- **Cost per turn**: 턴당 비용 ($)
- **Latency**: 응답 시간 (초)
- **Cache hit rate**: 캐시 적중률 (%)
- **Token usage**: 토큰 사용량

## ⚠️ 주의사항

### 1. API 비용

- 800회 API 호출 예상
- GPT-4o-mini 기준: $5-10
- Gemini 기준: $3-8
- 실제 비용은 토큰 사용량에 따라 변동

### 2. 실행 시간

- 평균 응답 시간: 3-5초/턴
- 총 예상 시간: 2-4시간
- 네트워크 상태에 따라 변동

### 3. 오류 처리

실험 중 오류 발생 시:

```cmd
# 로그 확인
type runs\2025-12-13_primary_v1\events.jsonl | findstr "error"

# 마지막 100줄 확인
powershell "Get-Content runs\2025-12-13_primary_v1\events.jsonl -Tail 100"
```

### 4. 중단 및 재개

실험이 중단된 경우:
- `events.jsonl`에 기록된 턴까지는 유효
- 재실행 시 처음부터 다시 시작 (중복 방지 로직 없음)
- 부분 결과 분석 가능

## 🐛 문제 해결

### Q1: "OPENAI_API_KEY가 설정되지 않았습니다"

```cmd
# .env 파일 확인
type .env

# API 키 설정
echo OPENAI_API_KEY=sk-... >> .env
```

### Q2: "환자 리스트를 찾을 수 없습니다"

```cmd
# 환자 데이터 생성
python scripts\generate_synthea_profiles.py
```

### Q3: "질문 뱅크를 찾을 수 없습니다"

```cmd
# 질문 뱅크 확인
dir experiments\question_bank\question_bank_5x15.v1.json
```

질문 뱅크가 없는 경우, 프로젝트 저장소에서 다운로드하거나 직접 생성해야 합니다.

### Q4: "데이터 무결성 검증 실패"

```cmd
# 상세 로그 확인
.venv\Scripts\python.exe scripts\validate_run.py ^
    --run_dir runs\2025-12-13_primary_v1 ^
    --verbose
```

### Q5: "페어링 공정성 검증 실패"

LLM과 Agent 모드의 환자/턴/질문이 일치하지 않는 경우입니다.
- 실험 재실행 권장
- 또는 부분 결과만 분석

## 📚 추가 자료

- **실험 설정**: `experiments/config.yaml`
- **질문 뱅크**: `experiments/question_bank/question_bank_5x15.v1.json`
- **환자 리스트**: `data/patients/patient_list_80.json`
- **README**: `experiments/README.md`

## 🤝 지원

문제가 발생하면 다음을 확인하세요:
1. 로그 파일: `runs/2025-12-13_primary_v1/events.jsonl`
2. 실험 설정: `experiments/config.yaml`
3. API 키 상태: `1_check_keys.bat`

---

**마지막 업데이트**: 2025-12-13

