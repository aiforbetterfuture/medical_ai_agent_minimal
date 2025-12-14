# 9번 Bat 파일 실행 시 자동 계산/저장 데이터 종합 가이드

## 📋 개요

`9_run_full_experiment.bat` 실행 시 자동으로 계산되고 저장되는 모든 지표, 메모리 변화, 데이터를 정리하고, 이것들이 어떤 의미 있는 연구 결과를 낼 수 있는지 설명합니다.

**실험 규모**: 78명 환자 × 5턴 × 2모드 (LLM + Agent) = **780개 이벤트**

---

## 🎯 Part 1: 자동 계산되는 평가지표 (11개)

### 1.1 RAGAS 기반 지표 (3개) - 모든 턴, 모든 모드

| 지표 | 범위 | 계산 조건 | 저장 위치 | 연구 활용 |
|------|------|----------|----------|----------|
| **Faithfulness** | 0.0~1.0 | `evaluation.per_turn_metrics` 포함 | `events.jsonl[].metrics.faithfulness` | 근거 기반 답변 품질, Hallucination 측정 |
| **Answer Relevance** | 0.0~1.0 | `evaluation.per_turn_metrics` 포함 | `events.jsonl[].metrics.answer_relevance` | 질문-답변 관련성 평가 |
| **Perplexity** | 낮을수록 좋음 | `evaluation.per_turn_metrics` 포함 | `events.jsonl[].metrics.perplexity` | 언어 모델의 확신도 측정 |

**자동 계산**: ✅ 각 턴의 답변 생성 직후 자동 계산

**연구 결과 예시**:
> "Agent 모드의 평균 Faithfulness 점수 (M=0.88, SD=0.10)는 LLM 모드 (M=0.72, SD=0.15)보다 유의미하게 높았다 (t(778)=28.5, p<0.001)."

---

### 1.2 멀티턴 컨텍스트 지표 (3개) - 모든 턴, 모든 모드

| 지표 | 범위 | 계산 조건 | 저장 위치 | 연구 활용 |
|------|------|----------|----------|----------|
| **CUS** | 0.0~1.0 | `evaluation.multiturn_metrics` 포함 | `events.jsonl[].metrics.CUS` | 이전 턴 정보 활용 정도 |
| **UR** | 0.0~1.0 | `evaluation.multiturn_metrics` 포함, update_key 있을 때 | `events.jsonl[].metrics.UR` | 새 정보 반영 정도 |
| **CCR** | 0.0~1.0 (낮을수록 좋음) | `evaluation.multiturn_metrics` 포함 | `events.jsonl[].metrics.CCR` | 모순 없는 답변 생성 능력 |

**자동 계산**: ✅ 각 턴의 답변 생성 직후 자동 계산

**연구 결과 예시**:
> "Agent 모드는 평균 CUS 점수 0.82로 LLM 모드(0.45)보다 82% 높은 컨텍스트 활용도를 보였다."

---

### 1.3 고급 평가 지표 (4개) - 멀티턴 스크립트 모드, Agent 모드만

| 지표 | 범위 | 계산 조건 | 저장 위치 | 연구 활용 |
|------|------|----------|----------|----------|
| **SFS** | 0.0~1.0 | `slots_truth` 있을 때 | `events.jsonl[].metrics.SFS` | 환자 정보 기반 사실성, Hallucination 측정 |
| **CSP** | 0.0~1.0 (낮을수록 좋음) | `slots_truth` 있을 때 | `events.jsonl[].metrics.CSP` | 의학적 금기 위반 빈도, 안전성 평가 |
| **CUS_improved** | 0.0~1.0 | `slots_truth` 있을 때 | `events.jsonl[].metrics.CUS_improved` | slots_truth 기반 개선된 컨텍스트 활용 |
| **ASS** | 0.0~1.0 | `slots_truth` 있을 때 | `events.jsonl[].metrics.ASS` | 구체적이고 실행 가능한 권고 포함 정도 |

**자동 계산 조건**:
- 멀티턴 스크립트 모드 (`multiturn_scripts.enabled: true`)
- `slots_truth`가 있는 경우
- Agent 모드에서만

**연구 결과 예시**:
> "Agent 모드는 평균 SFS 점수 0.90으로 환자 정보 기반 사실성이 높았고, CSP 점수 0.10으로 안전성 위반이 적었다."

---

## 🧠 Part 2: 계층형 메모리 시스템 (Agent 모드만)

### 2.1 Working Memory (Tier 1) - 자동 저장

**저장 시점**: 각 턴마다 자동 저장

**저장 내용**:
- 최근 5턴의 원본 대화 (user_query, agent_response)
- 추출된 슬롯 정보 (extracted_slots)
- 턴 ID, 타임스탬프, 중요도 점수

**저장 위치**: 
- 메모리: `session_state['hierarchical_memory'].working_memory` (deque, maxlen=5)
- 통계: `events.jsonl[].metadata.hierarchical_memory_stats.working_memory_size`
- 검증 결과: `events.jsonl[].memory_verification.tier1_working_memory` (선택적)

**연구 결과 활용**:
- ✅ **원본 보존 검증**: 최근 5턴이 모두 원본 형태로 저장되는지 확인
- ✅ **메모리 효율성**: 최근 5턴만 유지하여 메모리 사용량 최적화
- ✅ **컨텍스트 접근성**: 즉시 접근 가능한 최근 대화 정보

---

### 2.2 Compressed Memory (Tier 2) - 자동 압축

**저장 시점**: 5턴 도달 시 자동 압축 (LLM 요약)

**저장 내용**:
- 5턴 대화의 의학적 요약 (200 토큰 이내)
- 핵심 의료 정보 (conditions, medications, symptoms, vitals)
- 턴 범위, 중요도 점수, 타임스탬프

**저장 위치**:
- 메모리: `session_state['hierarchical_memory'].compressing_memory` (List[CompressedMemory])
- 통계: `events.jsonl[].metadata.hierarchical_memory_stats.compressed_memory_count`
- 검증 결과: `events.jsonl[].memory_verification.tier2_compressed_memory` (선택적)

**연구 결과 활용**:
- ✅ **압축 효율성**: 원본 5턴 → 요약 200 토큰 (압축률 측정)
- ✅ **의학 정보 보존**: 압축 후에도 핵심 의료 정보 보존 여부 확인
- ✅ **토큰 절감 효과**: 압축 메모리 사용 시 토큰 사용량 감소 측정

---

### 2.3 Semantic Memory (Tier 3) - 자동 업데이트

**저장 시점**: 5턴 도달 시 자동 업데이트

**저장 내용**:
- 만성 질환 (2회 이상 언급 또는 만성 키워드 포함)
- 만성 약물 (2회 이상 언급)
- 알레르기 (1회 언급도 저장)
- 건강 패턴 (평균 혈압, 증상 빈도 등)

**저장 위치**:
- 메모리: `session_state['hierarchical_memory'].semantic_memory` (SemanticMemory 객체)
- 통계: `events.jsonl[].metadata.hierarchical_memory_stats.chronic_conditions_count` 등
- 검증 결과: `events.jsonl[].memory_verification.tier3_semantic_memory` (선택적)

**연구 결과 활용**:
- ✅ **장기 정보 추출**: 만성 질환/약물이 자동으로 식별되는지 확인
- ✅ **의학적 정확성**: 예상된 만성 질환이 모두 저장되는지 검증
- ✅ **정보 지속성**: 다음 세션에서도 장기 정보가 유지되는지 확인

---

## 🔍 Part 3: 메모리 검증 결과 (선택적, Agent 모드만)

**자동 계산 조건**: `evaluation.memory_verification_enabled: true`

**저장 위치**: 
- `events.jsonl[].memory_verification` (각 이벤트)
- `runs/{run_id}/memory_verification.json` (실험 완료 후 요약)

**검증 항목**:
- Tier 1: 최근 5턴 원본 저장 확인
- Tier 2: 5턴 도달 시 압축 트리거 및 요약 품질 확인
- Tier 3: 만성질환/알레르기 저장 확인

---

## 💾 Part 4: 세션 상태 관리 (Agent 모드만)

### 4.1 ProfileStore (프로필 저장소)

**자동 업데이트 시점**: 각 턴마다

**저장 내용**:
- 인구통계학적 정보 (age, sex, height, weight, BMI)
- 질환 (conditions)
- 증상 (symptoms)
- 약물 (medications)
- 바이탈 (vitals: BP, HR, RR 등)
- 검사 수치 (labs: HbA1c, glucose, LDL 등)

**저장 위치**: 
- 메모리: `session_state['profile_store']` (ProfileStore 객체)
- 이벤트: `events.jsonl[].metadata.slots_state` (슬롯 상태 추출)

---

### 4.2 슬롯 상태 (slots_state)

**자동 추출 시점**: 각 턴마다

**저장 위치**: `events.jsonl[].metadata.slots_state`

**연구 결과 활용**:
- ✅ **정보 누적 패턴**: 턴이 진행될수록 슬롯이 어떻게 증가하는지 분석
- ✅ **업데이트 빈도**: 각 턴에서 새로운 정보가 얼마나 추가되는지 측정
- ✅ **컨텍스트 풍부도**: Agent 모드가 더 많은 슬롯을 활용하는지 비교

---

### 4.3 슬롯 진실값 (slots_truth)

**자동 로드 시점**: 멀티턴 스크립트 모드일 때

**저장 위치**: `events.jsonl[].slots_truth`

**연구 결과 활용**:
- ✅ **정확성 평가**: SFS 계산 시 ground truth와 비교
- ✅ **환각 측정**: 답변에 포함된 정보가 실제 환자 데이터와 일치하는지 확인

---

## 📈 Part 5: 성능 메트릭 (Agent 모드만)

| 메트릭 | 저장 위치 | 연구 활용 |
|--------|----------|----------|
| **quality_score** | `events.jsonl[].metadata.quality_score` | Self-Refine으로 향상된 품질 |
| **iteration_count** | `events.jsonl[].metadata.iteration_count` | 반복 개선 횟수 |
| **retrieved_docs_count** | `events.jsonl[].metadata.retrieved_docs_count` | 검색 효율성 평가 |
| **dynamic_k** | `events.jsonl[].metadata.dynamic_k` | 동적 검색 효과 측정 |
| **query_complexity** | `events.jsonl[].metadata.query_complexity` | 쿼리 복잡도 분석 |
| **hierarchical_memory_stats** | `events.jsonl[].metadata.hierarchical_memory_stats` | 메모리 시스템 통계 |

---

## 💰 Part 6: 비용 및 토큰 사용량

| 메트릭 | 저장 위치 | 연구 활용 |
|--------|----------|----------|
| **input_tokens** | `events.jsonl[].usage.input_tokens` | 입력 토큰 수 |
| **output_tokens** | `events.jsonl[].usage.output_tokens` | 출력 토큰 수 |
| **estimated_cost_usd** | `events.jsonl[].usage.estimated_cost_usd` | 예상 비용 (USD) |

---

## ⏱️ Part 7: 응답 시간

| 메트릭 | 저장 위치 | 연구 활용 |
|--------|----------|----------|
| **total** | `events.jsonl[].timing_ms.total` | 전체 응답 시간 (ms) |
| **llm_call** | `events.jsonl[].timing_ms.llm_call` | LLM 호출 시간 (ms) |
| **retrieval** | `events.jsonl[].timing_ms.retrieval` | 검색 시간 (ms) |
| **context_assembly** | `events.jsonl[].timing_ms.context_assembly` | 컨텍스트 조립 시간 (ms) |

---

## 🎯 Part 8: 핵심 연구 결과 활용 시나리오

### 시나리오 1: 컨텍스트 재사용 능력 증명

**가설**: Agent 모드가 LLM 모드보다 이전 턴 정보를 더 잘 활용한다.

**분석 데이터**:
- `metrics.CUS`: Agent > LLM
- `metrics.CUS_improved`: Agent > LLM
- 턴별 CUS 변화: Agent는 턴이 진행될수록 CUS 증가, LLM은 일정

**논문 표 예시**:

| 턴 | LLM CUS | Agent CUS | 차이 | p-value |
|----|---------|-----------|------|---------|
| 1 | 0.45 | 0.50 | +0.05 | 0.12 |
| 2 | 0.46 | 0.65 | +0.19 | <0.001 |
| 3 | 0.45 | 0.75 | +0.30 | <0.001 |
| 4 | 0.47 | 0.82 | +0.35 | <0.001 |
| 5 | 0.46 | 0.85 | +0.39 | <0.001 |
| **평균** | **0.46** | **0.71** | **+0.25** | **<0.001** |

**논문 문장 예시**:
> "Agent 모드는 평균 CUS 점수 0.71로 LLM 모드(0.46)보다 54% 높은 컨텍스트 활용도를 보였으며, 턴이 진행될수록 그 차이는 더욱 커졌다 (턴 5에서 +0.39, p<0.001)."

---

### 시나리오 2: 안전성 및 정확성 평가

**가설**: Agent 모드가 더 안전하고 정확한 답변을 생성한다.

**분석 데이터**:
- `metrics.SFS`: Agent > LLM (환각 감소)
- `metrics.CSP`: Agent < LLM (안전성 향상)
- `metrics.faithfulness`: Agent > LLM (근거 기반 답변)

**논문 표 예시**:

| 지표 | LLM | Agent | 개선율 | p-value |
|------|-----|-------|--------|---------|
| SFS (사실성) | 0.65 | 0.90 | +38% | <0.001 |
| CSP (안전성 위반) | 0.35 | 0.10 | -71% | <0.001 |
| Faithfulness | 0.72 | 0.88 | +22% | <0.001 |

**논문 문장 예시**:
> "Agent 모드는 평균 SFS 점수 0.90으로 환자 정보 기반 사실성이 높았고, CSP 점수 0.10으로 안전성 위반이 LLM 모드(0.35)보다 71% 적었다."

---

### 시나리오 3: 메모리 시스템 효과 검증

**가설**: 3-Tier 계층형 메모리가 정보 보존과 토큰 절감에 효과적이다.

**분석 데이터**:
- `memory_verification.tier1_working_memory.verified`: 통과율
- `memory_verification.tier2_compressed_memory`: 압축 효율성
- `memory_verification.tier3_semantic_memory`: 장기 정보 저장
- `metadata.hierarchical_memory_stats`: 메모리 통계

**논문 표 예시**:

| Tier | 검증 항목 | 통과율 | 효과 |
|------|----------|--------|------|
| Tier 1 | 최근 5턴 원본 저장 | 95% | 즉시 접근 가능 |
| Tier 2 | 5턴 압축 요약 | 80% | 토큰 80% 절감 |
| Tier 3 | 만성질환 저장 | 87% | 장기 정보 보존 |

**논문 문장 예시**:
> "3-Tier 메모리 시스템은 최근 5턴을 원본으로 보존하면서, 과거 대화를 평균 200 토큰으로 압축하여 토큰 사용량을 80% 절감했다."

---

### 시나리오 4: 개인화 정도 측정

**가설**: Agent 모드가 환자별 정보를 더 잘 반영하여 개인화된 답변을 생성한다.

**분석 데이터**:
- `metrics.ASS`: Agent > LLM
- `metadata.slots_state`: Agent가 더 많은 슬롯 활용
- 턴별 슬롯 누적: Agent는 턴이 진행될수록 슬롯 증가

**논문 표 예시**:

| 턴 | LLM 슬롯 수 | Agent 슬롯 수 | 차이 | p-value |
|----|------------|--------------|------|---------|
| 1 | 3.2 | 4.5 | +1.3 | <0.05 |
| 2 | 3.5 | 6.2 | +2.7 | <0.001 |
| 3 | 3.3 | 7.8 | +4.5 | <0.001 |
| 4 | 3.4 | 8.5 | +5.1 | <0.001 |
| 5 | 3.3 | 9.2 | +5.9 | <0.001 |
| **평균** | **3.3** | **7.2** | **+3.9** | **<0.001** |

**논문 문장 예시**:
> "Agent 모드는 평균 7.2개의 슬롯을 활용하여 개인화된 답변을 생성한 반면, LLM 모드는 3.3개만 활용했다 (p<0.001)."

---

## 📊 Part 9: 자동 생성 파일 목록

### 9.1 events.jsonl

**위치**: `runs/{run_id}/events.jsonl`

**크기**: 약 50-100 MB (780개 이벤트)

**내용**: 모든 이벤트의 완전한 데이터

**데이터 포인트**: 약 23,400개 (780개 이벤트 × 평균 30개 필드)

---

### 9.2 run_manifest.json

**위치**: `runs/{run_id}/run_manifest.json`

**내용**: 실험 설정 스냅샷, Git 정보

---

### 9.3 resolved_config.json

**위치**: `runs/{run_id}/resolved_config.json`

**내용**: 실행 시 해석된 최종 설정

---

### 9.4 memory_verification.json (선택적)

**위치**: `runs/{run_id}/memory_verification.json`

**내용**: 메모리 검증 결과 요약

---

## 🎓 Part 10: 논문 작성 체크리스트

### 실험 설계
- [x] 실험 규모 명시 (78명 × 5턴 × 2모드 = 780회)
- [x] 평가 지표 정의 (11개 지표)
- [x] 비교 기준 명확화 (LLM vs Agent)

### 결과 분석
- [ ] 평가지표 통계 분석 (평균, 표준편차, 검정)
- [ ] 턴별 변화 추이 분석
- [ ] 메모리 시스템 효과 분석
- [ ] 비용-효과 분석

### 논문 작성
- [ ] 결과 표 작성 (3~5개 표)
- [ ] 결과 그래프 작성 (3~5개 그래프)
- [ ] 통계 검정 결과 명시
- [ ] 효과 크기(Effect Size) 계산
- [ ] 사례 분석 (대표 사례 2~3개)

---

## 결론

9번 bat 파일 실행 시 **자동으로 계산되고 저장되는 모든 데이터**가 논문의 연구 결과로 직접 활용 가능합니다.

**핵심 강점**:
1. ✅ **자동화**: 수동 계산 없이 모든 지표 자동 계산
2. ✅ **포괄성**: 11개 평가지표 + 메모리 검증 + 성능 메트릭
3. ✅ **재현성**: 모든 설정과 데이터가 파일로 저장
4. ✅ **확장성**: 780개 이벤트로 충분한 통계적 유의성 확보

**연구 결과로 활용 가능한 주제**:
- 컨텍스트 재사용 능력 비교
- 안전성 및 정확성 평가
- 메모리 시스템 효과 검증
- 개인화 정도 측정
- 비용 및 성능 효율성

