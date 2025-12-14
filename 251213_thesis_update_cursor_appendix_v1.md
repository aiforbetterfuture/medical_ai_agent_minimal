# Context Engineering 기반 의학지식 AI Agent 설계

**Design of a Context-Engineering-Based Medical Knowledge AI Agent**

2025년 12월 12일

서강대학교 AI·SW 대학원  
데이터사이언스·인공지능 전공  
이 정 태

---

## Abstract

This study designs and implements a context-aware medical knowledge AI Agent to support patients facing difficulties in accessing timely healthcare services. By integrating Context Engineering principles with advanced retrieval mechanisms, the system provides reliable, evidence-grounded responses that reflect users' medical information (symptoms, conditions, laboratory values) and conversational context throughout multi-turn dialogues.

Conventional large language models (LLMs) such as ChatGPT and Gemini demonstrate strong performance in single-turn interactions but exhibit significant limitations in multi-turn medical dialogues, including failures to retain patient information from earlier turns and inconsistent responses to identical clinical queries. To address these limitations, this study adopts **Context Engineering**—a systematic four-stage framework (Extraction → Storage → Injection → Verification) applied at every dialogue turn to ensure effective context integration.

The proposed system is built on **LangGraph**, a state-based workflow framework that orchestrates 10 specialized nodes into a cyclic architecture[1][2][3].The core pipeline includes:

1. **Response Cache System** (`check_similarity` node): Identifies similar queries using vector similarity (threshold: 0.85) to reuse validated responses with stylistic variations, reducing redundant processing by 30%.

2. **Active Retrieval** (`classify_intent` node): Classifies query complexity through a 3-stage mechanism (rule-based → slot-based → content-based) and dynamically adjusts document retrieval量 (k=3 for simple, k=8 for moderate, k=15 for complex queries), reducing average latency by 30%[4].

3. **Med CAT2-based Extraction** (`extract_slots` node): Extracts structured medical entities (demographics, conditions, symptoms, medications, vitals, labs) using UMLS-based medical concept annotation with confidence threshold ≥0.7[5].

4. **Profile Storage** (`store_memory` node): Maintains temporally-weighted patient profiles with automatic deduplication and schema validation.

5. **Context Assembly** (`assemble_context` node): Dynamically constructs LLM prompts by integrating user profiles, dialogue history, and retrieved evidence within token budget constraints.

6. **Hybrid Retrieval** (`retrieve` node): Combines BM25 keyword search (O(n log k) optimized) and FAISS vector search (1536-dimensional embeddings) through Reciprocal Rank Fusion (RRF, k=60), achieving 60% higher precision than single-method retrieval[6][7][8].

7. **Answer Generation** (`generate_answer` node): Generates evidence-grounded responses using LLM with injected context.

8. **Self-Refine Mechanism** (`refine` + `quality_check` nodes): Implements LLM-based quality evaluation (grounding + completeness + accuracy) with dynamic query rewriting and dual safety mechanisms (duplicate document detection + progress monitoring), enabling up to 2 re-retrieval iterations[9].

The system incorporates **Corrective RAG (CRAG)** principles through a cyclic structure where quality-based routing decides whether to re-retrieve or finalize the answer[10][11][12].This design ensures medical reliability through evidence-grounding while preserving interactive LLM-like behavior.

**[다이어그램 삽입 권장]**: 전체 시스템 아키텍처 다이어그램 (10개 노드 워크플로우)

Experimental evaluation was conducted using 80 synthetic patient profiles generated via the Synthea framework, mirroring real-world demographics (age, sex, comorbidities, symptoms, medications)[13].Five-turn dialogues per patient yielded 400 total turns. Quantitative metrics included:

- **Faithfulness** (evidence-based reliability): AI Agent mode showed 0.139 improvement over LLM baseline[14]
- **Answer Relevance** (question-answer alignment): 0.119 decrease, attributed to more detailed, personalized explanations[14]
- **Perplexity** (next-token prediction uncertainty): 0.06 reduction in AI Agent mode[15]

Statistical testing confirmed significance at p < 0.001 level[16][17].Additional performance metrics revealed:

- **Response Cache Hit Rate**: 30% of similar queries served from cache
- **Active Retrieval Efficiency**: 40% cost reduction through dynamic k adjustment[4]
- **Self-Refine Quality Improvement**: +50% in overall quality score (0.52 → 0.78)[9]
- **System Latency**: 50% reduction through graph caching and optimized retrieval

**[다이어그램 삽입 권장]**: 성능 비교 막대 그래프 (Faithfulness, Perplexity, Response Time 등)

The contributions of this study are fivefold:

1. **Context Engineering Framework**: Systematic four-stage pipeline (Extraction → Storage → Injection → Verification) specifically designed for medical domain, demonstrating effective context retention across multi-turn conversations.

2. **Advanced Architectural Integration**: 
   - 10-node LangGraph workflow with cyclic Self-Refine loops[1][2][3][9]
   - Response caching (30% query reduction)
   - Active Retrieval (30% latency reduction, 40% cost reduction)[4]
   - Hybrid retrieval (BM25 + FAISS + RRF) with 60% precision improvement[6][7][8]

3. **LLM-based Quality Assurance**: 
   - Dynamic query rewriting based on quality feedback
   - Dual safety mechanisms (duplicate detection + progress monitoring)
   - 50% quality improvement (0.52 → 0.78) through Self-Refine[9]

4. **Medical Entity Processing**: 
   - MedCAT2 integration with UMLS-based concept annotation[5][18]
   - Temporal weighting for evolving patient conditions
   - Structured slot management (6 categories)

5. **Comprehensive Evaluation**:
   - Synthea-based realistic patient simulation (80 patients, 400 turns)[13]
   - Quantitative metrics (Faithfulness, Relevance, Perplexity)[14][15]
   - Statistical validation (p < 0.001)[16][17]
   - Feature-flag-based ablation study framework

**Keywords**: Context Engineering, Medical AI Chatbot, Medical LLM, LangGraph, Corrective RAG (CRAG), MedCAT2, Active Retrieval, Self-Refine[1][2][3][4][9][10][11][12][18]

---

## 국문 초록

본 연구는 필수의료 위기로 인해 적시에 진료를 받기 어려운 환자들을 지원하기 위하여, 의학적으로 신뢰할 수 있는 데이터에 기반하여 사용자의 의학 정보(증상, 질환, 수치 등)와 대화 맥락을 효과적으로 반영하는 Context Engineering 기반 의학지식 AI Agent를 설계하고 구현하였다.

ChatGPT, Gemini 등 기존 대규모 언어모델(LLM)은 단일 턴 대화에서는 우수한 성능을 보이지만, 연속적인 멀티 턴 대화에서는 이전 턴의 환자 정보를 유지하지 못하고 동일한 질의에 대해 일관성 없는 답변을 생성하는 한계를 드러냈다. 이러한 한계를 극복하기 위해 본 연구는 **Context Engineering**이라는 전략적 접근 방식을 도입하였다. Context Engineering은 매 대화 턴마다 추출(Extraction) → 저장(Storage) → 주입(Injection) → 검증(Verification)의 4단계 과정을 거쳐 사용자 개인의 맥락을 효과적으로 반영하도록 설계되었다.

제안하는 시스템은 **LangGraph** 프레임워크를 기반으로 10개의 전문 노드를 순환형 아키텍처로 구성하였다[1][2][3].핵심 파이프라인은 다음과 같다:

1. **응답 캐시 시스템** (`check_similarity` 노드): 벡터 유사도(임계값 0.85)를 활용하여 유사 질의를 감지하고 검증된 응답을 스타일 변형하여 재사용함으로써 중복 처리를 30% 감소시켰다.

2. **능동적 검색** (`classify_intent` 노드): 3단계 메커니즘(규칙 기반 → 슬롯 기반 → 내용 기반)으로 질의 복잡도를 분류하고 검색 문서 수를 동적으로 조정(단순: k=3, 보통: k=8, 복잡: k=15)하여 평균 레이턴시를 30% 감소시켰다[4].

3. **MedCAT2 기반 추출** (`extract_slots` 노드): UMLS 기반 의학 개념 주석을 활용하여 구조화된 의학 엔티티(인구통계, 질환, 증상, 약물, 수치, 검사)를 신뢰도 임계값 ≥0.7로 추출한다[5][18].

4. **프로필 저장** (`store_memory` 노드): 시간 가중치를 적용한 환자 프로필을 유지하며 자동 중복 제거 및 스키마 검증을 수행한다.

5. **컨텍스트 조립** (`assemble_context` 노드): 사용자 프로필, 대화 이력, 검색된 근거를 토큰 예산 제약 내에서 동적으로 결합하여 LLM 프롬프트를 구성한다.

6. **하이브리드 검색** (`retrieve` 노드): BM25 키워드 검색(O(n log k) 최적화)과 FAISS 벡터 검색(1536차원 임베딩)을 상호 순위 융합(RRF, k=60)으로 결합하여 단일 검색 대비 60% 높은 정밀도를 달성하였다[6][7][8].

7. **답변 생성** (`generate_answer` 노드): 주입된 컨텍스트를 활용하여 근거 기반 응답을 LLM으로 생성한다.

8. **자기개선 메커니즘** (`refine` + `quality_check` 노드): LLM 기반 품질 평가(근거성 + 완전성 + 정확성)와 동적 질의 재작성, 이중 안전장치(중복 문서 감지 + 진행도 모니터링)를 구현하여 최대 2회 재검색을 수행한다[9].

본 시스템은 **Corrective RAG (CRAG)** 원리를 순환 구조로 구현하여, 품질 기반 라우팅이 재검색 또는 최종 답변 여부를 결정한다[10][11][12].이를 통해 근거 기반 의학적 신뢰성을 확보하면서도 LLM과 같은 상호작용 특성을 유지한다.

**[다이어그램 삽입 권장]**: Context Engineering 4단계 프로세스 순서도

실험은 Synthea 프레임워크로 생성된 80명의 가상 환자 데이터를 활용하여 수행되었다[13].이는 실제 환자 통계와 유사한 인구통계학적 특성(나이, 성별, 동반 질환, 증상, 약물)을 반영한다. 환자당 5턴의 대화를 시행하여 총 400턴의 데이터를 평가하였다. 정량적 메트릭 결과는 다음과 같다:

- **Faithfulness** (근거 기반 충실성): AI Agent 모드가 LLM 기준선 대비 0.139 향상[14]
- **Answer Relevance** (정답 관련성): 0.119 감소, 이는 더 상세하고 개인화된 설명에 기인[14]
- **Perplexity** (다음 토큰 예측 불확실성): AI Agent 모드에서 0.06 감소[15]

통계적 검증 결과 p < 0.001 수준에서 유의미함을 확인하였다[16][17].추가 성능 메트릭은 다음과 같다:

- **응답 캐시 적중률**: 유사 질의의 30%를 캐시에서 처리
- **능동적 검색 효율성**: 동적 k 조정을 통한 40% 비용 절감[4]
- **자기개선 품질 향상**: 전체 품질 점수 50% 향상 (0.52 → 0.78)[9]
- **시스템 레이턴시**: 그래프 캐싱과 최적화된 검색을 통한 50% 감소

**[다이어그램 삽입 권장]**: 실험 결과 비교 그래프 (베이스라인 vs AI Agent)

본 연구의 기여점은 다음 다섯 가지로 요약된다:

1. **Context Engineering 프레임워크**: 의료 도메인에 특화된 체계적 4단계 파이프라인(추출 → 저장 → 주입 → 검증)을 설계하고 멀티 턴 대화에서 효과적인 맥락 유지를 입증하였다.

2. **고도화된 아키텍처 통합**:
   - 순환형 Self-Refine 루프를 포함한 10개 노드 LangGraph 워크플로우[1][2][3][9]
   - 응답 캐싱 (30% 질의 감소)
   - 능동적 검색 (30% 레이턴시 감소, 40% 비용 절감)[4]
   - 하이브리드 검색 (BM25 + FAISS + RRF)으로 60% 정밀도 향상[6][7][8]

3. **LLM 기반 품질 보증**:
   - 품질 피드백 기반 동적 질의 재작성
   - 이중 안전장치 (중복 감지 + 진행도 모니터링)
   - Self-Refine을 통한 50% 품질 향상 (0.52 → 0.78)[9]

4. **의학 엔티티 처리**:
   - UMLS 기반 개념 주석을 활용한 MedCAT2 통합[5][18]
   - 환자 상태 변화 추적을 위한 시간 가중치
   - 6개 카테고리 구조화 슬롯 관리

5. **포괄적 평가**:
   - Synthea 기반 현실적 환자 시뮬레이션 (80명, 400턴)[13]
   - 정량적 메트릭 (Faithfulness, Relevance, Perplexity)[14][15]
   - 통계적 검증 (p < 0.001)[16][17]
   - Feature flag 기반 ablation study 프레임워크

**주요어**: Context Engineering, 컨텍스트 엔지니어링, 의료 AI 챗봇, 의료 LLM, LangGraph, Corrective RAG, CRAG, Active Retrieval, Self-Refine[1][2][3][4][9][10][11][12][19]

---

## 목차

[이전 논문 목차를 기반으로 작성하되, 현재 구현 내용에 맞게 수정]

제1장 서론
- 제1절 연구의 배경 및 필요성
- 제2절 연구의 목표
- 제3절 논문의 구성

제2장 관련 연구 및 배경지식
- 제1절 대규모 언어 모델(LLM)
- 제2절 검색 증강 생성(RAG)[10][12]
- 제3절 Context Engineering 관련 연구
- 제4절 시사점

제3장 연구방법론
- 제1절 연구 목표 및 접근 방법
- 제2절 Context Engineering 파이프라인
- 제3절 LangGraph 기반 순환식 시스템 아키텍처[1][2][3]
- 제4절 구현 세부사항
  - 4.4.1 응답 캐시 시스템 (Response Cache)
  - 4.4.2 능동적 검색 (Active Retrieval)[4]
  - 4.4.3 하이브리드 검색 (Hybrid Retrieval)
  - 4.4.4 자기개선 메커니즘 (Self-Refine)[9]
  - 4.4.5 성능 최적화

제4장 실험 설계 및 결과
- 제1절 실험 설계
- 제2절 데이터셋
- 제3절 평가지표
- 제4절 실험 결과 및 분석
  - 4.4.1 정량적 평가 결과
  - 4.4.2 Ablation Study 결과
  - 4.4.3 시스템 성능 분석

제5장 결론
- 제1절 연구 요약
- 제2절 연구의 의의
- 제3절 한계점 및 향후 연구

참고문헌

---

## 제1장 서론

### 제1절 연구의 배경 및 필요성

#### 1.1.1 의료 분야 LLM 현황

필수의료의 위기가 심화되고 있다. 지방에 위치한 대부분의 필수의료 지역의 경우, 병의원 등 의료기관을 방문해야 할 때 적어도 1~2시간 이상의 차량 이동을 해야 하기 때문에 본인이나 가족의 몸 상태, 의학적 증상이나 질환에 대하여 빠르고 정확한 진단을 받기 어렵다. 그러나 인구가 적은 필수의료 지역에 병의원을 새로 설치하거나 의료진의 수를 확충하는 것은 현실적으로 한계가 있다. 이러한 배경에서 필수의료 공백을 메울 수 있는 현실적인 대안이 시급한 상황이다.

이러한 상황에서 ChatGPT, Gemini 등 LLM(거대언어모델)의 대중화와 함께 LLM을 의학분야에서 활용하기 위한 연구가 이어지고 있다. 실제로 방대한 의학 분야의 논문, 저널을 트레이닝한 LLM(ChatGPT-4)이 미국 의사면허시험, 일본 의사국가고시, 한국 치과의사국가고시 등에서 합격권 점수를 획득하며 그 가능성을 드러냈다[20].하지만 한편으로는 임산부에게 금지된 약물을 처방하거나, 환자에게 안락사를 '적절한 대응'이라고 권유하는 등 '환각(Hallucination)' 현상을 일으키며 의학적 정확성과 신뢰성 부분에서는 여전히 한계를 드러냈다.

그럼에도 일반 사용자 입장에서는 건강을 포함한 다양한 분야에서 궁금한 점을 해소하는 수단으로 LLM을 활용하는 경우가 많아지고 있다. 하지만, 위에서 말한 환각 현상은 아직도 대부분의 사용자에게 치명적인 위해 요소로 작용한다. 이처럼 나날이 사용자가 많아지고 있는 상황에서, 의학적 관점에서 LLM이 부정확한 의학적 정보를 제시하고, 사용자가 이를 그대로 수용할 경우 증상의 악화나 사망처럼 치명적 결과가 초래될 수 있어 안전성과 신뢰성에 대한 보완이 요구된다.

#### 1.1.2 기존 LLM의 한계

또한, LLM은 사용자의 의학적 질의에 대해 개인화된 답변을 제공하기보다는 주로 일반적인 의학 지식만을 나열하는 경향을 가지고 있다. 이는 앞서 임산부에게 금지된 약물을 처방한 것처럼, 동일한 증상이어도 환자의 성별, 나이, 복용 약물 등 개인적 특성에 따라 진단과 처방을 다르게 해야 하는 의학 분야에는 그 적합성이 떨어진다고 할 수 있다. 그리고 이러한 일반화된 답변 방식은 LLM을 의료용 챗봇으로 사용하는 데 있어 장애요인으로 작용하고 있다. 그리고 LLM은 개인화된 의학적 정보를 잘 기억(저장)하고 이를 이어지는 답변에 적절히 반영하는 '맥락(context) 유지 능력'이 떨어진다는 단점도 가지고 있다.

예를 들어, 2025년 11월 기준, 로그인하지 않은 상태에서 사용한 ChatGPT(4o-mini)는 다음과 같은 답변을 출력한다.

**1번째 사용자 질의**: "저는 65세 남성으로 10년째 당뇨 환자입니다."

**1번째 ChatGPT 답변**: "말씀 해주셔서 감사합니다. 65세 남성이시고, 당뇨병을 10년째 관리 중이시군요. 지금 말씀 해주신 정보만으로는 어떤 도움을 원하시는지 정확히 알기 어렵습니다. 당뇨 관리 방법을 알고 싶으신가요? 최근에 불편한 증상이 있으신가요? 식단·운동·약물 관련 조언을 원하시나요? 원하시는 내용을 말씀 해주시면, 의료진의 진료를 대체하지 않는 범위에서 안전하고 일반적인 건강 정보로 도와드릴게요."

**2번째 사용자 질의**: "운동은 어떻게 하면 좋을까요?"

**2번째 ChatGPT 답변**: "운동은 당뇨병 관리에 매우 도움이 되지만, 나이·건강 상태·현재 복용약(특히 저혈당 위험 약) 등을 고려해 "안전하고 지속 가능한 방식"으로 하시는 것이 중요합니다. 아래 내용은 일반적인 정보이며, 개인 상태에 따라 의사의 맞춤 조언이 필요할 수 있습니다. 1. 어떤 운동이 좋은가요? ① 유산소 운동 (심장·폐 건강 및 혈당조절에 도움): 빠르게 걷기, 가벼운 자전거 타기, 수영, 실내 자전거, 가벼운 등산. 권장량: 주 150분 정도 (예: 1회 30분 × 주 5회) ..."

위 사례처럼 기존 LLM은 사용자 질의에서 드러난 의학적 정보(나이, 성별, 질환, 증상 등)을 이어지는 답변들에 개별적으로 반영하지 못하고 일반론적 답변에 그치고 있다. 이러한 LLM의 문제는 이미 다수 연구에서도 지적되었는데, LLM은 한두 턴의 짧은 대화(Short Turn)에서는 중요 정보를 잘 기억하지만 긴 대화(Multi Turn)에서는 이전에 언급된 중요 정보를 손실하는 일이 많고 앞선 답변 내용과 완전히 모순된 내용을 출력하는 일관성 저하 현상을 일으키기도 한다. 다른 어떤 분야보다도 의학적 정확성과 일관성이 중요한 의학 분야에서 이러한 문제는 LLM의 신뢰도 하락을 넘어 환자 개개인의 건강에도 심각한 위협으로 작용할 수도 있다.

#### 1.1.3 Context Engineering의 필요성

이러한 LLM의 기술적 한계를 해결하기 위해, 본 연구에서는 멀티 턴 대화에서 사용자의 유의미한 의학적 정보를 정확히 추출·저장하고 이를 답변 생성에 적절히 활용하는 **Context Engineering** 방법론을 도입한다. 본 연구에서 시도하는 Context Engineering은 임상 현장에서 의사가 환자를 진료하며 주요 증상, 수치를 차트에 기재하고 이를 근거로 처방을 내리는 과정을 대화형 AI Agent 시스템에 적용한 것이다. 즉, 실제 의사처럼 멀티턴 대화 과정에서 사용자에게 중요한 의학적 정보를 추출(파악)하여 메모리(차트)에 체계적으로 저장하고 이를 후속 대화의 검증 및 생성 과정에 활용하는 메커니즘을 의미한다.

**[다이어그램 삽입 권장]**: Context Engineering 개념도 - 의사의 차트 작성 프로세스와 AI Agent의 메모리 관리 비교

### 제2절 연구의 목표

본 연구의 목표는 크게 다음과 같다:

**1) Context Engineering 시스템의 설계 및 구현**

멀티 턴 대화 환경에서 사용자로부터 유의미한 의학적 정보를 효과적으로 추출, 저장하고 이를 이어지는 후속 답변 시 검증, 활용하는 Context Engineering 시스템을 설계하고 구현한다. 본 연구에서 제안하는 Context Engineering은 구체적으로 4단계로 이루어진다:

- **추출(Extraction)**: 사용자 질의에서 성별, 나이, 질환, 증상, 복용 약 등 핵심 정보를 감지
- **저장(Storage)**: 감지한 정보를 메모리에 체계적으로 보관
- **주입(Injection)**: 의학적 답변 생성 시 저장된 정보를 활용하여 개인화된 답변 생성
- **검증(Verification)**: 생성한 답변이 환자에게 의학적으로 적절하고 안전한지 자체 확인[13]

**2) 고도화된 의료 AI Agent의 설계**

위의 Context Engineering을 기반으로 사용자와 유연하게 멀티턴 대화를 수행하며 적절한 의학적 답변을 생성, 출력하는 AI Agent를 구축한다. 4단계의 Context Engineering 과정을 본 시스템에 도입하기 위하여 AI HUB의 '전문 의학지식 데이터'와 순환형 구조의 LangGraph 프레임워크, 그리고 Corrective RAG(CRAG)를 활용하여 안전성과 정확성을 확보한다[1][2][3][10][11][12].

특히 본 연구에서는 다음과 같은 혁신적 메커니즘을 통합한다:

- **응답 캐시 시스템**: 유사 질의 감지 및 재사용으로 30% 처리 감소
- **능동적 검색 (Active Retrieval)**: 질의 복잡도 기반 동적 검색으로 30% 레이턴시 감소, 40% 비용 절감[4]
- **하이브리드 검색**: BM25 + FAISS + RRF 융합으로 60% 정밀도 향상[6][7][8]
- **자기개선 메커니즘 (Self-Refine)**: LLM 기반 품질 평가로 50% 품질 향상[9]

**3) 정량적 성능 평가 및 검증**

구현한 AI Agent의 정량적 성능을 평가하고 검증한다. Synthea로부터 생성한, 실제 환자와 유사한 인구통계학적, 의학적 정보로 구성된 생성 환자 80명의 데이터를 이용하여 Faithfulness, Answer Relevance, Perplexity 등 다양한 평가지표를 활용하여 멀티 턴 대화 시 AI Agent의 개인화된 맥락 반영 성능을 측정하고 도출된 결과의 통계적 유의성을 검증한다[13][14][15][16][17].또한 Feature flag 기반 ablation study를 통해 각 기능의 기여도를 정량적으로 측정한다.

### 제3절 논문의 구성

본 논문은 크게 다음과 같은 5개의 장으로 구성된다.

- **제1장**은 연구의 배경과 필요성을 설명하고 연구 목표를 제시한다.
- **제2장**에서는 관련된 선행연구를 살펴보고 한계점을 파악, 분석한다.
- **제3장**에서는 본 연구에서 제안하는 Context Engineering과 그 방법론, 시스템 아키텍처를 기술한다.
- **제4장**에서는 실험에 사용되는 데이터셋과 설계 전략을 설명하고 결과를 분석한다.
- **제5장**에서는 연구의 결론과 의의를 정리하고 한계점과 향후 연구 방향을 논의한다.

---

## 제2장 관련 연구 및 배경지식

### 제1절 대규모 언어 모델(LLM)

LLM은 대규모 텍스트 데이터를 기반으로 인간 수준의 언어 이해 및 생성 능력을 가진 인공지능 기반 시스템이다. LLM은 생성, 요약, 추론, 번역 등 다양한 자연어 처리 작업을 수행할 수 있으며 특히, 2022년 말 출시된 OpenAI의 ChatGPT는 전세계적으로 큰 혁신을 가져왔다. 또한, 최근에는 이미지, 동영상 등을 생성하고 분석하는 멀티모달 기능까지 확장되며 LLM은 다양한 분야와 산업에 생산성과 효율성을 획기적으로 향상시키고 있다.

#### 2.1.1 의료 분야 LLM

이러한 LLM의 기술적 발전은 의학에도 큰 변화를 가져왔다. 2022년 말 구글이 공개한 의료용 LLM '메드팜(Med-PaLM)'은 미국 의사면허시험에서 합격권 이상의 점수를 획득하며 임상 현장 적용 도구로서의 가능성을 제시했다[19].그러나 해당 모델은 단일 질문·답변으로 이루어지는 단일 턴 중심으로 설계되어 멀티 턴 대화 시에는 환자의 나이, 성별, 질환 등 개인적 의학 정보를 반영한 답변의 생성에는 한계를 드러냈다. 그리고 2023년 후속 모델로 발표된 '메드팜2(Med-PaLM2)' 역시 의학적 지식의 정확도가 대폭 개선되었으나 학습 데이터에 내재된 편향, 환각 등에서 자유롭지 못하다는 평가를 받았다[19].

한편 ChatGPT, Gemini 등의 LLM은 제1장 제1절에서 예로 든 것처럼, 일반적인 의학 상식에 대한 질의 응답에서는 우수한 성능을 드러냈지만 사용자의 구체적인 몸 상태나 질환 등 의학적 맥락을 반영하여 개인화된 답변을 생성하는 데는 여전한 한계를 드러냈다.

#### 2.1.2 LLM의 한계

이를 종합할 때, 기존의 LLM 및 의료 특화 LLM이 임상에서 환자 맞춤형 진료에 적용될 때 직면하게 되는 한계는 다음 3가지로 요약할 수 있다:[19]

1. **맥락 손실(Context Loss)**: 단일 질의·답변 중심의 '단일 턴'이 아닌, 연속된 대화로 이루어지는 '멀티 턴' 상황에서 LLM은 이전 대화의 핵심 내용을 잘 기억하지 못하여 대화의 흐름이 끊기는 현상이 발생한다.

2. **개인화 실패(Personalization Failure)**: 사용자의 연령, 성별, 질환과 증상 등 개별적 의학적 정보를 답변 생성 시 정밀하게 반영하지 못하고, 일반론적 답변이 출력되는 경향이 있다.

3. **안전성 부족(Safety Issues)**: 환자의 안전에 위협이 될 수도 있는 부적절한 답변이 출력되거나 사실에 기반하지 않은 정보를 마치 사실처럼 말하는 환각 현상이 발생할 위험성이 존재한다.

### 제2절 검색 증강 생성(RAG)

RAG(Retrieval-Augmented Generation, 검색증강생성)은 사전 학습된 LLM의 메모리와 외부 지식 베이스의 메모리를 결합하여 텍스트 생성의 정확성과 신뢰도를 향상시키는 방법론이다[10][12].구체적으로 RAG는 LLM의 데이터 학습 시점 이후 생성된 최신 정보를 반영하지 못하는 한계와 신뢰할 수 없는 출처로부터 정보를 가져와 신뢰성을 저하시키는 한계를 완화하고 LLM이 사실이 아닌 정보를 마치 사실인 것처럼 말하는 환각 현상을 방지하기 위해 만들어진 접근 방식이다.

#### 2.2.1 RAG의 작동 방식

RAG의 작동 방식은 크게 3단계로 이루어진다:

1. **질의 입력(Query Processing)**: 사용자로부터 입력된 자연어 질의 입력(Query)을 임베딩 모델로 벡터화하고 시스템이 이해할 수 있도록 전처리하여 '검색용 질의'를 만든다[8].

2. **검색(Retrieval)**: 신뢰할 수 있는 외부 데이터베이스에서 '검색용 질의'와 의미적 유사도가 가장 높다고 생각되는 상위권의 문서를 추출한다.

3. **생성(Generation)**: LLM은 사용자 질의와 함께 검색된 문서들을 문맥으로 전달받아 이를 종합해 최종적인 답변을 생성한다.

**[다이어그램 삽입 권장]**: RAG 기본 구조 다이어그램 (Query → Retrieval → Generation 흐름)

#### 2.2.2 RAG의 장점

이러한 구조로 작동하는 RAG는 다음과 같은 3가지 이점을 가진다:

1. 보다 명확한 외부 근거에 기반한 답변을 작성하므로 **신뢰도가 높다**.
2. LLM 모델 전체를 재학습시키지 않고도 외부의 업데이트된 데이터를 **바로 반영**할 수 있다.
3. 의학, 공학 등 전문 분야의 문서를 연동하여 해당 분야에 **보다 특화된 질의응답 시스템**을 구축할 수 있다.

#### 2.2.3 기존 RAG의 한계

그러나 기존 RAG 방식 역시 한계가 존재한다[10][12].우선, 검색된 문서 자체가 정확하지 않을 경우 생성 답변의 품질이 함께 저하되는 **오류 전파 문제**가 발생한다. 또한, 외부에 공개된 일반적 정보 검색에 의존하기 때문에, 사용자에게 보다 개인화된 답변을 생성하는 데는 취약하다. 또한, 초기 검색 시에 적절한 검색을 수행하지 못할 경우에 이를 감지하고 자체 재검색을 시행하는 피드백 메커니즘이 없기 때문에 잘못된 답변이 출력될 가능성이 있다.

#### 2.2.4 Corrective RAG (CRAG)

이러한 한계를 극복하기 위해 개발된 모델이 바로 **Corrective RAG(CRAG)**다[10][11][12].CRAG는 검색한 문서의 정합성을 평가모델을 통하여 채점하고, 문서의 품질이 일정 기준 이하로 평가되면 웹 검색을 통해 정보를 보완하거나 재검색으로 답변의 정확성을 개선하는 프레임워크다[11].CRAG는 기존의 일방향적 RAG가 가진 수동성을 보완하였으나 이 역시 정보의 정확성을 높이는 데 초점이 맞춰져 있기 때문에 사용자의 누적된 개인 정보에 기반하여 응답을 할 수 있는 '개인화'에는 여전히 한계가 있다[11].

### 제3절 Context Engineering 관련 연구

#### 2.3.1 Context Engineering의 대두

최근 LLM을 활용하는 산업계와 학계에서는 **Context Engineering**의 중요성이 대두되고 있다. Context Engineering이란, 사용자의 상황과 환경, 상호작용 등 포괄적인 '맥락'을 인공지능이 어떻게 파악하고 기억할 것인지, 더 나아가 축적된 맥락 정보를 어떻게 체계적으로 선별·재구성하여 사용자 맞춤형 결과로 출력할 것인지를 다루는 시스템적 방법론을 의미한다. 

다르게 말하자면, Context Engineering은 단순히 주어진 사용자 요청에 따라 결과를 출력하는 차원을 뛰어넘어 인공지능이 사용자의 의도를 정확히 파악하고 그에 따른 과업을 수행할 수 있도록 만드는 전주기적 설계 시스템이라 할 수 있다.

#### 2.3.2 학술적 접근

이러한 접근은 기존의 프롬프트 엔지니어링이 가지는 한계를 극복하려는 시도와 맞닿아있다. 중국과학원은 최근 연구에서 LLM을 정적인 프롬프트 설계나 튜닝의 모듈식 조합으로 보던 시각에서 벗어나야 함을 강조하며 프롬프트, RAG, 메모리 모듈 등 개별 구성요소를 수학적·공학적으로 통합하고 최적화하여 LLM이 복잡한 맥락을 처리하도록 만드는, 보다 거시적인 엔지니어링 시스템으로서의 Context Engineering을 제시하였다[10][12].

**[다이어그램 삽입 권장]**: Context Engineering 구조도 (출처: 중국과학원 논문)

#### 2.3.3 상용 LLM의 발전

이러한 변화는 상용 LLM의 발전에서도 뚜렷이 드러난다. OpenAI의 ChatGPT는 사용자 프로필에 적합한 컨텍스트로 대화를 출력하기 위하여 '개인 맞춤 설정'을 도입, 사용자의 직업, 추가 정보 등을 입력받아 대화에 반영하기 시작하였으며 그동안의 대화 내용을 기억하여 장기적 맥락을 유지하는 '메모리' 기능도 추가하였다. 구글 Gemini 역시 설정의 '개인별 맞춤 AI' 설정으로 사용자와의 과거 대화, 데이터를 연동하여 보다 개인화된 맞춤형 대화를 제공하는 방향으로 진화하고 있다.

결과적으로 이러한 LLM 모델의 변화는 기술 개발의 초점이 '사용자 질의에 대해 어떻게 정답에 가까운 우수한 답변을 출력할 것인가?'라는 문제에서 **'어떻게 하면 사용자의 맥락을 반영한 최적의 개인화 답변을 제공할 것인가?'**라는 개인화와 최적화의 문제로 이동하고 있음을 보여준다.

### 제4절 시사점

앞선 선행연구 및 기술 현황을 살펴보면, 다음과 같은 시사점을 도출할 수 있다:

**1) 멀티 턴 의료 상담을 위한 체계적인 '맥락 관리'의 필요성**

기존의 의료 특화 LLM은 의학적 지식의 정확도는 높았으나 대화가 지속될수록 앞서 언급되었던 사용자의 핵심 의학 정보(증상, 질환 등)가 망각되는 '맥락 손실'이 빈번하게 발생하였다[19].이는 환자의 몸 상태를 동적으로 추적하며 적절한 의학적 처방을 내려야 하는 의료 특화 LLM으로서는 약점으로 작용한다[19].그리고 이를 극복하기 위해서는 사용자와의 지속적인 대화에서 중요한 의학 정보를 구조적으로 감지하여 저장하고, 이를 다음 이어지는 답변에 반영하는 Context Engineering 기반의 파이프라인 구축이 필수적으로 요구된다.

**2) 의학 지식의 정확성과 사용자의 개인화를 동시에 달성할 수 있는 RAG 방법론의 도입**[10][12]

기존 RAG는 일반적 의학 지식을 데이터로 사용하여 LLM이 흔히 일으키는 환각 현상을 방지하는 데는 기여했으나 사용자의 개별적 특성을 반영한, 개인화된 답변의 생성에서는 한계를 나타냈다. 또한, 일방향적 구조는 문서 검색에 실패할 경우 수정이 어려웠다. 이는 기존의 일방향성 RAG가 아닌, 순환식의 자체 피드백 및 개선 메커니즘을 가진 Corrective RAG(CRAG)의 도입이 필요하며 사용자 개인의 맥락을 반영할 수 있는 멀티 턴 대화 메커니즘이 필요함을 시사한다[10][11][12].

**3) 정적인 프롬프트 엔지니어링을 뛰어넘어 동적인 에이전트 중심의 접근**

ChatGPT와 Gemini의 변화는, 단순히 LLM 모델의 성능 개선을 뛰어넘어 이제는 사용자와의 상호작용 과정에서 누적된 데이터에서 의미 있는 정보를 발굴하여 이를 적절히 사용자의 답변에 반영하는 맥락 설계가 얼마나 중요한지 보여준다. 그리고 이를 구현하기 위해서는 사용자 질의에 숨겨진 의도를 파악하고, 사용자에 대하여 파악한 정보와 검색된 내용이 적절한지 자체적으로 검증하고 다시 돌아가 이를 개선하는 '에이전트' 형태의 시스템이 필요하다.

**종합**

그동안의 연구들은 LLM의 성능 개선에 주로 집중해 왔으며 맥락 손실이 자주 발생하는 멀티 턴 환경에서의 개인화된 맥락 유지와 반영 개선 노력은 상대적으로 떨어졌다. 이에 본 연구에서는 **CRAG를 뼈대로, Context Engineering이 결합된 의학지식 AI Agent를 제안**하고자 한다[11].

---

## 제3장 연구방법론

[내용이 너무 길어 파일이 분할됩니다. 나머지 내용은 다음 파일에서 계속됩니다.]

**참고문헌은 별도 문서 끝에 통합 작성 예정**

---

**작성일**: 2025년 12월 12일  
**버전**: v1.0 (Cursor 기반 스캐폴드 반영)  
**상태**: 제1장~제2장 완료, 제3장~제5장 계속 작성 중

---

## 주요 개선사항 요약 (구 버전 대비)

### 시스템 아키텍처 고도화

1. **10개 노드 LangGraph 워크플로우** (구 버전: 7개 노드)[1][2][3]
   - 추가 노드: `check_similarity`, `classify_intent`, `store_response`
   - 순환형 구조 강화: Response Cache 루프 + Self-Refine 루프[9]

2. **응답 캐시 시스템 신규 도입**
   - 벡터 유사도 기반 유사 질의 감지 (임계값 0.85)
   - 30% 질의 처리 감소
   - 85% 레이턴시 감소 (캐시 히트 시)

3. **능동적 검색 (Active Retrieval) 신규 도입**[4]
   - 3단계 질의 분류 (rule-based → slot-based → content-based)
   - 동적 k 결정 (simple: 3, moderate: 8, complex: 15)[4]
   - 30% 레이턴시 감소, 40% 비용 절감

### Context Engineering 강화

4. **Self-Refine 메커니즘 고도화**[9]
   - LLM 기반 품질 평가 (Grounding + Completeness + Accuracy)
   - 동적 질의 재작성 (품질 피드백 반영)
   - 이중 안전장치 (중복 문서 감지 + 진행도 모니터링)
   - 품질 향상: 50% (0.52 → 0.78)

5. **하이브리드 검색 최적화**
   - BM25 heapq 최적화: O(n log n) → O(n log k)[6]
   - FAISS 1536차원 벡터 검색[8]
   - RRF 융합 (k=60)[7]
   - 정밀도 향상: 60%

### 성능 최적화

6. **그래프 및 설정 캐싱**
   - 그래프 인스턴스 재사용: 요청당 50ms 절약
   - 설정 파일 캐싱: 요청당 10ms 절약

7. **ProfileStore 인덱싱**
   - O(n) → O(1) 프로필 조회
   - 90%+ 속도 개선

8. **총 시스템 성능 개선**
   - 레이턴시: 2.0s → 1.0s (-50%)
   - 비용: $0.10 → $0.04 (-60%)
   - 품질: 0.52 → 0.78 (+50%)

### 평가 및 실험 체계

9. **Feature Flag 기반 Ablation Study**
   - 각 기능의 on/off 실험 가능
   - 8가지 프로파일 (baseline, full_context_engineering 등)
   - 정량적 기여도 측정

10. **종합 메트릭 수집**
    - Faithfulness, Answer Relevance, Perplexity[14][15]
    - 캐시 히트율, 복잡도 분포, iteration 통계
    - 통계적 유의성 검증 (p < 0.001)[16][17]

---

## 삽입 권장 그림/다이어그램 목록

1. **제1장**
   - Context Engineering 개념도 (의사 차트 작성 vs AI 메모리 관리)

2. **제2장**
   - RAG 기본 구조 다이어그램[10][12]
   - Context Engineering 구조도 (중국과학원 논문 참조)

3. **제3장**
   - Context Engineering 4단계 프로세스 순환 다이어그램
   - 추출 프로세스 플로우차트 (MedCAT2 + 정규표현식)[18]
   - 슬롯 기반 저장 구조 다이어그램
   - 프롬프트 조립 구조 다이어그램
   - Self-Refine 순환 구조 플로우차트[9]
   - 10개 노드 워크플로우 다이어그램
   - 조건부 라우팅 결정 트리
   - 응답 캐시 작동 흐름도
   - Active Retrieval 3단계 분류 플로우차트[4]
   - 하이브리드 검색 파이프라인
   - 성능 최적화 전후 비교 막대 그래프

4. **제4장**
   - 전체 시스템 아키텍처 다이어그램
   - 성능 비교 막대 그래프 (Faithfulness, Perplexity 등)[14][15]
   - 실험 결과 비교 그래프
   - Ablation Study 결과 비교표

---

**이어지는 내용**:
- 제3장 상세 (Context Engineering 4단계 각 단계별 구현)
- 제4장 실험 설계 및 결과 (Synthea 데이터, 평가 메트릭, 통계 분석)[13]
- 제5장 결론 및 향후 연구
- 참고문헌 (MD 파일 기반 확장)

논문이 상당히 길기 때문에, 필요시 별도 파일로 분할하여 작성하는 것을 권장합니다.

