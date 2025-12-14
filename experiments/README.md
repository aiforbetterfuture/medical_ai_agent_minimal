# 멀티턴 실험 가이드

80명 Synthea 환자 × 5턴 멀티턴 대화를 통한 LLM vs AI Agent 성능 비교 실험

## 개요

이 실험은 ChatGPT의 권고사항을 기반으로 다음과 같은 설계 원칙을 따릅니다:

1. **재현가능성**: 질문은 반정형화(semi-structured)되어 있으며, deterministic 선택 규칙 사용
2. **객관성**: 동일 환자, 동일 질문 시퀀스로 LLM/Agent 모드를 paired comparison
3. **멀티턴 특화 평가**: Context Utilization, Context Contradiction, Update Responsiveness 등

## 디렉토리 구조

```
experiments/
├── config.yaml                      # 실험 설정 (재현가능성 보장)
├── question_bank/
│   └── question_bank_5x15.v1.json  # 5턴 × 15개 paraphrase 질문 (총 75개)
├── run_multiturn_experiment.py      # 메인 실행 스크립트
├── evaluation/
│   └── multiturn_metrics.py         # 멀티턴 지표 계산
└── logging/                         # 실험 결과 저장

data/patients/
├── patient_list_80.json             # 80명 환자 리스트
└── profile_cards/
    ├── SYN_0001.json                # 환자 프로파일 카드
    └── ...

runs/
└── 2025-12-13_primary_v1/           # 실험 결과
    ├── run_manifest.json            # 실행 메타데이터
    ├── events.jsonl                 # 턴별 결과 로그
    └── node_trace.jsonl             # Agent 노드 추적 (선택)
```

## 실험 설정

### config.yaml 주요 파라미터

```yaml
run:
  run_id: "2025-12-13_primary_v1"

reproducibility:
  global_seed: 42
  deterministic_question_selection: true
  question_selection_rule: "sha256(patient_id + ':' + turn_id) % 15"

modes:
  run_order: ["llm", "agent"]  # Paired comparison

llm:
  model: "gpt-4o-mini"
  temperature: 0.2

agent:
  model: "gpt-4o-mini"
  temperature: 0.2
  feature_flags:
    active_retrieval_enabled: true
    self_refine_enabled: true
    llm_judge_enabled: true
```

## 5턴 설계

각 턴은 특정 능력을 테스트하도록 설계되었습니다:

| 턴 | 목적 | 테스트하는 능력 |
|----|------|----------------|
| Turn 1 | Profile Ingestion | 슬롯 추출 (환자 정보 파악) |
| Turn 2 | Implicit Follow-up | 메모리/컨텍스트 주의 (이전 정보 활용) |
| Turn 3 | New Evidence Update | 업데이트 반영 (새 바이탈/검사 결과) |
| Turn 4 | Near-duplicate + Minor Addition | 캐시/재사용성 + 미세 정보 처리 |
| Turn 5 | Personalized Plan & Safety Net | 종합 판단 및 안전망 제시 |

## 실행 방법

### 1. 환경 준비

```bash
# 필요한 패키지 설치
pip install -r requirements.txt

# API 키 설정 (.env 파일에 OPENAI_API_KEY 설정)
```

### 2. 환자 프로파일 생성 (Synthea 데이터 활용 시)

```bash
# Synthea FHIR 파일이 있는 경우
python scripts/generate_synthea_profiles.py

# 없는 경우 샘플 프로파일이 자동 생성됩니다
```

### 3. 실험 실행

#### 전체 실험 (80명 × 5턴)

```bash
python experiments/run_multiturn_experiment.py \
  --config experiments/config.yaml
```

#### 테스트 실행 (일부 환자만)

```bash
python experiments/run_multiturn_experiment.py \
  --config experiments/config.yaml \
  --max-patients 5 \
  --max-turns 3
```

### 4. 결과 분석

#### Paper-Ready 분석 파이프라인 (권장)

One-click 명령으로 논문에 필요한 모든 자료를 생성합니다:

```bash
# 전체 파이프라인 실행 (검증, 통계, 테이블, 그래프, LaTeX)
python scripts/run_paper_pipeline.py \
  --run_dir runs/2025-12-13_primary_v1 \
  --output_dir runs/2025-12-13_primary_v1/paper_assets
```

생성되는 파일:
- `summary.json`: 통계 분석 결과 (paired t-test, Cohen's d, 95% CI 등)
- `tables/`: CSV 테이블 (overall_comparison, per_turn, efficiency)
- `figures/`: PNG/PDF 그래프 (bar charts, line plots, effect sizes)
- `latex/`: LaTeX 테이블 (.tex 파일, 논문에 바로 삽입 가능)

#### 개별 분석 스크립트

단계별로 실행하려면:

```bash
# 1. Fairness 검증 (paired comparison 유효성)
python scripts/check_fairness.py \
  --events_path runs/2025-12-13_primary_v1/events.jsonl

# 2. 데이터 무결성 검증
python scripts/validate_run.py \
  --run_dir runs/2025-12-13_primary_v1

# 3. 통계 분석 (summary.json 생성)
python scripts/summarize_run.py \
  --events_path runs/2025-12-13_primary_v1/events.jsonl \
  --output_json runs/2025-12-13_primary_v1/summary.json

# 4. CSV 테이블 생성
python scripts/make_paper_tables.py \
  --summary_json runs/2025-12-13_primary_v1/summary.json \
  --output_dir runs/2025-12-13_primary_v1/tables

# 5. 그래프 생성 (matplotlib 필요)
python scripts/make_paper_figures.py \
  --summary_json runs/2025-12-13_primary_v1/summary.json \
  --output_dir runs/2025-12-13_primary_v1/figures

# 6. LaTeX 테이블 변환
python scripts/make_latex_tables.py \
  --csv_dir runs/2025-12-13_primary_v1/tables \
  --output_dir runs/2025-12-13_primary_v1/latex
```

#### 멀티턴 특화 지표 (선택적)

```bash
# 멀티턴 지표 계산
python experiments/evaluation/multiturn_metrics.py \
  runs/2025-12-13_primary_v1/events.jsonl \
  data/patients/profile_cards/

# 결과 출력:
# - Context Utilization Score (CUS)
# - Context Contradiction Rate (CCR)
# - Update Responsiveness (UR)
```

## 출력 파일 형식

### resolved_config.json (재현성 보장용 설정 스냅샷)

```json
{
  "schema_version": "resolved_config.v1",
  "run_id": "2025-12-13_primary_v1",
  "created_at_utc": "2025-12-13T00:00:30Z",
  "git_info": {
    "branch": "main",
    "commit_hash": "a1b2c3d4",
    "is_dirty": false
  },
  "config": {
    "llm": {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "max_tokens": 2048
    },
    "features": {
      "active_retrieval_enabled": true,
      "context_compression_enabled": false,
      "hierarchical_memory_enabled": true,
      "self_refine_enabled": true
    }
  },
  "experiment_params": {
    "max_patients": 80,
    "max_turns": 5
  }
}
```

### events.jsonl (한 줄 = 한 턴)

```json
{
  "schema_version": "events_record.v1",
  "run_id": "2025-12-13_primary_v1",
  "mode": "agent",
  "patient_id": "SYN_0001",
  "turn_id": 1,
  "question": {
    "question_id": "T1_Q03",
    "text": "기저질환이 당뇨병이고 현재 메트포르민 복용 중입니다..."
  },
  "answer": "제공된 근거 문서 기준으로...",
  "timestamp_utc": "2025-12-13T00:01:05Z",
  "usage": {
    "input_tokens": 1180,
    "output_tokens": 520,
    "estimated_cost_usd": 0.00023
  },
  "timing_ms": {
    "total": 1940,
    "llm_call": 1820,
    "context_assembly": 85,
    "retrieval": 35
  },
  "metadata": {
    "cache_hit": false,
    "quality_score": 0.82,
    "iteration_count": 0,
    "retrieved_docs_count": 8,
    "dynamic_k": 8,
    "query_complexity": "moderate"
  }
}
```

### summary.json (통계 분석 결과)

```json
{
  "schema_version": "summary.v1",
  "run_id": "2025-12-13_primary_v1",
  "created_at_utc": "2025-12-13T02:30:00Z",
  "paired_comparison": {
    "faithfulness": {
      "llm_mean": 0.78,
      "llm_std": 0.12,
      "agent_mean": 0.86,
      "agent_std": 0.09,
      "delta_mean": 0.08,
      "cohens_d": 0.75,
      "ci95_lower": 0.05,
      "ci95_upper": 0.11,
      "p_value": 0.001,
      "n_pairs": 400
    }
  },
  "per_turn_breakdown": {
    "turn_1": {
      "llm": {"faithfulness": {"mean": 0.80, "std": 0.11}},
      "agent": {"faithfulness": {"mean": 0.87, "std": 0.08}}
    }
  },
  "efficiency_comparison": {
    "cost_per_turn_llm": 0.00023,
    "cost_per_turn_agent": 0.00031,
    "latency_mean_llm": 1820.5,
    "latency_mean_agent": 2150.3
  }
}
```

### run_manifest.json (실험 메타데이터)

```json
{
  "schema_version": "run_manifest.v1",
  "run_id": "2025-12-13_primary_v1",
  "created_at_utc": "2025-12-13T00:00:30Z",
  "config": {...},
  "data": {
    "patient_count": 80,
    "question_bank_version": "question_bank_5x15.v1"
  }
}
```

## 평가 지표

### 1. 표준 RAG 지표
- **Faithfulness**: 근거 문서에 대한 충실도 (0.0-1.0)
- **Answer Relevance**: 질문과 답변의 관련성 (0.0-1.0)
- **Context Precision**: 검색된 문서의 정밀도 (0.0-1.0)
- **Context Recall**: 검색된 문서의 재현율 (0.0-1.0)
- **Context Relevancy**: 검색된 문서의 관련성 (0.0-1.0)

### 2. 통계적 비교 지표
- **Paired t-test**: LLM vs AI Agent의 통계적 유의성 검정
- **Cohen's d**: 효과 크기 (Effect Size)
  - Small: |d| < 0.5
  - Medium: 0.5 ≤ |d| < 0.8
  - Large: |d| ≥ 0.8
- **95% Confidence Interval**: 평균 차이의 95% 신뢰구간
- **p-value**: 유의 확률 (p < 0.05: 통계적으로 유의)

### 3. 효율성 지표
- **Cost per Turn**: 턴당 평균 비용 (USD)
- **Latency**: 응답 지연시간 (ms)
- **Cache Hit Rate**: 캐시 히트율 (0.0-1.0)
- **Token Usage**: 입력/출력 토큰 사용량

### 4. 멀티턴 특화 지표 (선택적)
- **Context Utilization Score (CUS)**: Turn 2에서 이전 턴 정보 활용도
- **Context Contradiction Rate (CCR)**: 이전 정보와 모순되는 조언 비율
- **Update Responsiveness (UR)**: Turn 3에서 새 정보 반영도

## 질문 뱅크 구조

### 5턴 × 15개 Paraphrase = 75개 질문

각 턴마다 15개의 다른 표현(paraphrase)이 있으며, 동일한 스키마를 따릅니다.

예시 (Turn 1):
- `T1_Q01`: "저는 {AGE}세 {SEX_KO}이고 {COND1_KO}이(가) 있어요..."
- `T1_Q02`: "{AGE}세 {SEX_KO}입니다. 기저질환은 {COND1_KO}이고..."
- ... (총 15개)

### Deterministic 선택 규칙

```python
# SHA256 해시를 사용한 재현가능한 질문 선택
selection_key = f"{patient_id}:{turn_id}"
hash_digest = hashlib.sha256(selection_key.encode()).hexdigest()
index = int(hash_digest, 16) % 15
```

## 결과 요약

실험 완료 후 다음 명령으로 요약 통계를 확인할 수 있습니다:

```bash
# events.jsonl 기반 집계
python -c "
import json
events = [json.loads(line) for line in open('runs/2025-12-13_primary_v1/events.jsonl')]
print(f'Total turns: {len(events)}')
print(f'LLM turns: {sum(1 for e in events if e[\"mode\"]==\"llm\")}')
print(f'Agent turns: {sum(1 for e in events if e[\"mode\"]==\"agent\")}')
"
```

## 문제 해결

### Q1: 프로파일 카드가 부족한 경우

```bash
# 샘플 프로파일 재생성
python scripts/generate_synthea_profiles.py
```

### Q2: Agent 그래프 오류

```bash
# Agent 그래프 테스트
python -c "from agent.graph import create_agent_graph; create_agent_graph()"
```

### Q3: API 호출 실패

- `.env` 파일에 `OPENAI_API_KEY` 설정 확인
- API 할당량/잔액 확인

## 재현성 보장 (Reproducibility)

본 실험 인프라는 석사학위 논문 연구의 재현성을 최우선으로 설계되었습니다.

### 재현성 체크리스트

1. **Deterministic Question Selection**
   - SHA256 해시 기반 질문 선택
   - 동일한 patient_id + turn_id → 동일한 질문

2. **Configuration Snapshot**
   - `resolved_config.json`에 모든 설정 스냅샷 저장
   - Git commit hash, feature flags, model parameters 포함

3. **Paired Comparison Validation**
   - `check_fairness.py`로 완벽한 pairing 검증
   - LLM과 Agent 모드가 정확히 같은 (patient, turn, question) 실행

4. **Statistical Rigor**
   - Paired t-test (정확한 대응표본 검정)
   - Cohen's d (효과 크기)
   - 95% Confidence Interval

5. **Data Integrity**
   - `validate_run.py`로 데이터 무결성 검증
   - Required fields, type checking, pairing completeness

### 재현 방법

다른 연구자가 본 실험을 재현하려면:

```bash
# 1. 동일한 코드 버전 체크아웃
git checkout <commit_hash>  # resolved_config.json에서 확인

# 2. 동일한 설정으로 실험 실행
python experiments/run_multiturn_experiment_v2.py \
  --config experiments/config.yaml \
  --max-patients 80 \
  --max-turns 5

# 3. 결과 검증
python scripts/check_fairness.py --events_path runs/<run_id>/events.jsonl
python scripts/validate_run.py --run_dir runs/<run_id>

# 4. 통계 분석
python scripts/summarize_run.py \
  --events_path runs/<run_id>/events.jsonl \
  --output_json runs/<run_id>/summary.json
```

### JSON Schema 검증

모든 출력 파일은 JSON Schema로 검증 가능합니다:

```bash
# Schema 파일 위치
ls experiments/schemas/
# - resolved_config.schema.json
# - events_record.schema.json
# - summary.schema.json
```

## 참고 자료

- ChatGPT 권고안: `chatgpt_80명 멀티턴 테스트 실행 방안.txt`
- 원본 스캐폴드: `agent/`, `experiments/`
- Synthea 공식 문서: https://github.com/synthetichealth/synthea
- Paper Pipeline Scripts: `scripts/run_paper_pipeline.py`

## 라이선스

MIT License
