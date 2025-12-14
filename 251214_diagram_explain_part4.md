# 47개 다이어그램 상세 설명 - Part 4

**작성일**: 2024년 12월 14일  
**목적**: 석사학위논문 삽입용 다이어그램 설명  
**Part 4**: Diagram 05 System Architecture for Research (10개 다이어그램) + 3-Tier Memory (1개 추가)

---

## Diagram 05: System Architecture for Research (10개 다이어그램)

### 5.1 전체 시스템 아키텍처 (High-Level)

이 그래프 다이어그램은 본 연구의 전체 시스템 아키텍처를 6개 레이어로 구조화하여 보여준다. Frontend Layer는 Streamlit UI로 사용자 인터페이스를 제공하고, LangGraph Agent(Core)는 10개 노드(check_similarity, classify_intent, extract_slots, store_memory, assemble_context, retrieve, generate_answer, refine, quality_check, store_response)로 구성된 핵심 워크플로우를 실행한다. Context Engineering Layer는 QualityEvaluator(LLM 기반 품질 평가), QueryRewriter(동적 질의 재작성), ContextManager(토큰 예산 관리), ContextCompressor(압축 전략)로 구성되어 Self-Refine과 Context Engineering을 지원한다. Memory & Storage Layer는 ProfileStore(사용자 프로필, JSON), Hierarchical Memory(3-Tier 대화 이력, JSON), FAISS Index(의료 문서, 3072차원), BM25 Corpus(의료 문서, Pickle), Response Cache(응답 캐시, 임베딩)로 구성되어 데이터를 영구 저장한다. LLM Provider는 OpenAI GPT-4o-mini(답변 생성, 품질 평가, 질의 재작성)와 text-embedding-3-large(3072차원 임베딩)를 제공한다. Medical NLP는 MedCAT2(의료 슬롯 추출, UMLS 기반)를 제공한다. 이러한 레이어 구조가 없다면 각 컴포넌트의 역할과 의존성이 불명확하여 시스템을 이해하고 유지보수하기 어렵다. 특히 Context Engineering Layer를 별도로 분리한 것은 본 연구의 핵심 기여인 Self-Refine과 Context Engineering을 강조하기 위함이다. 또한 각 레이어 간의 데이터 흐름을 명확히 보여주어, 예를 들어 refine 노드가 QualityEvaluator와 QueryRewriter를 호출하고, 이들이 다시 GPT를 호출하는 구조를 한눈에 파악할 수 있다. 이러한 아키텍처는 `agent/graph.py`, `agent/nodes/`, `experiments/evaluation/`, `context/`, `memory/`, `retrieval/` 디렉토리 구조와 일치하여 코드 탐색이 용이하다.

### 5.2 연구 기여도 맵

이 Mindmap 다이어그램은 본 연구의 핵심 기여를 4개 분야(Active Retrieval, CRAG Self-Refine, Context Engineering, Hybrid Retrieval)로 구조화하여 보여준다. Active Retrieval은 복잡도 기반 동적 k(simple k=3, moderate k=8, complex k=15), 비용 절감 20-30%, IntentClassifier LLM을 포함한다. CRAG Self-Refine은 LLM 기반 품질 평가(Grounding Check, Completeness Check, Accuracy Check), 동적 질의 재작성(피드백 기반, 맥락 반영), 2중 안전장치(중복 문서 감지, 품질 진행도 모니터링), Strategy Pattern(CorrectiveRAG, BasicRAG)을 포함한다. Context Engineering은 토큰 예산 관리(4000 토큰 상한, 우선순위 할당), Context Compression(Extractive 50%, Abstractive LLM, Hybrid 조합), Hierarchical Memory(Working 5턴, Compressed 6-20턴, Semantic 21턴+)를 포함한다. Hybrid Retrieval은 BM25 키워드, FAISS 시맨틱, RRF 융합, Dynamic k를 포함한다. 이러한 Mindmap이 없다면 본 연구의 기여가 산발적으로 보여 전체적인 그림을 파악하기 어렵다. 특히 각 기여가 어떻게 연결되어 시너지를 내는지 이해하기 어렵다. 예를 들어 Active Retrieval로 동적 k를 조정하고, CRAG Self-Refine으로 품질을 평가하여 재검색을 수행하며, Context Engineering으로 토큰 예산을 관리하고, Hybrid Retrieval로 효과적인 검색을 수행하는 전체 흐름을 Mindmap을 통해 직관적으로 이해할 수 있다. 이는 석사학위논문의 서론이나 연구 방법론 섹션에 삽입하여 연구의 전체 구조를 설명하는 데 유용하다.

### 5.3 핵심 혁신 포인트 (Research Contributions)

이 그래프 다이어그램은 기존 연구의 한계와 본 연구의 혁신을 대비하여 보여준다. 기존 연구의 한계 4가지는 (1) 정적 검색(고정 k 값) → 비효율적, 비용 증가, (2) 표면적 평가(BLEU, ROUGE) → 사실 오류 탐지 불가, (3) 정적 질의(재검색 시 동일) → 재검색 효과 없음, (4) 단순 반복 제한(최대 iteration만) → 무한 루프 위험이다. 본 연구의 혁신 4가지는 (1) 동적 검색(복잡도 기반 k) → 비용 절감 20-30%, (2) LLM 기반 평가(Grounding + Critique) → 근거 점수 +113%, (3) 동적 질의(피드백 반영) → 검색 정확도 +60%, (4) 2중 안전장치(중복 + 진행도) → 무한 루프 완전 제거이다. 각 한계와 혁신은 화살표로 연결되어 개선 관계를 명확히 보여준다. 이러한 대비 다이어그램이 없다면 본 연구의 혁신이 기존 연구와 어떻게 다른지, 왜 필요한지 설명하기 어렵다. 특히 정량적 개선 수치(비용 절감 20-30%, 근거 점수 +113%, 검색 정확도 +60%)를 함께 제시하여 혁신의 효과를 명확히 입증한다. 이는 석사학위논문의 관련 연구 섹션이나 연구 결과 섹션에 삽입하여 본 연구의 차별성을 강조하는 데 유용하다. 또한 심사위원이나 독자가 본 연구의 기여를 빠르게 파악할 수 있도록 돕는다.

### 5.4 Ablation Study 설계

이 그래프 다이어그램은 8개의 Ablation 프로파일을 순차적으로 쌓아 올리며 각 기능의 기여도를 측정하는 실험 설계를 보여준다. Baseline(BasicRAG, 1회 검색-생성)은 품질 점수 0.52를 기록하고, +Heuristic Refine(휴리스틱 평가)은 0.61(+17%), +LLM Quality Check(LLM 평가)는 0.71(+37%), +Dynamic Query(동적 질의)는 0.75(+44%), +2중 안전장치(중복 + 진행도)는 0.78(+50%, 무한 루프 0%)를 기록한다. Full CRAG(모든 기능 활성화)는 품질 점수 0.78, iteration 1.9, 비용 -26%를 달성한다. Ablation 프로파일 8개는 (1) baseline(BasicRAG), (2) self_refine_heuristic, (3) self_refine_llm, (4) self_refine_llm_dynamic, (5) self_refine_llm_dynamic_safety, (6) active_retrieval, (7) context_engineering, (8) full_system이다. 이러한 Ablation Study 설계가 없다면 각 기능의 기여도를 정량적으로 측정할 수 없고, 어떤 기능이 성능 향상에 가장 큰 영향을 미치는지 파악하기 어렵다. 특히 LLM Quality Check가 +37%의 큰 향상을 가져오고, Dynamic Query가 추가로 +7%를 가져오며, 2중 안전장치가 무한 루프를 완전히 제거하면서 +3%를 추가로 가져오는 것을 확인할 수 있다. 이는 석사학위논문의 실험 설계 섹션에 삽입하여 체계적인 실험 방법론을 설명하고, 연구 결과 섹션에서 각 기능의 효과를 입증하는 데 유용하다.

### 5.5 성능 메트릭 비교

이 테이블 다이어그램은 8개 Ablation 프로파일에 대한 12개 성능 메트릭을 종합적으로 비교한다. 메트릭은 (1) 품질 점수(Overall Quality Score), (2) Faithfulness(RAGAS), (3) Answer Relevancy(RAGAS), (4) Context Utilization Score(CUS), (5) Unique Retrieval Rate(URR), (6) Cross-turn Consistency Rate(CCR), (7) 평균 iteration 수, (8) 무한 루프 발생률, (9) API 비용/턴, (10) 응답 시간(초), (11) 토큰 소비, (12) 메모리 사용량(MB)을 포함한다. Baseline은 대부분의 메트릭에서 가장 낮은 성능을 보이고(품질 0.52, Faithfulness 0.63, CUS 0.72), Full System은 대부분의 메트릭에서 가장 높은 성능을 보인다(품질 0.78, Faithfulness 0.85, CUS 0.85). 특히 주목할 점은 Full System이 품질을 크게 향상시키면서도 API 비용을 26% 절감하고(Baseline $0.023 → Full $0.017), 응답 시간도 단축한다(Baseline 6.8초 → Full 5.9초)는 것이다. 이는 Active Retrieval과 Context Engineering의 효율성 개선 효과가 Self-Refine의 추가 비용을 상쇄하고도 남기 때문이다. 이러한 종합 비교 테이블이 없다면 각 프로파일의 장단점을 한눈에 파악하기 어렵고, 특히 품질과 비용의 트레이드오프를 이해하기 어렵다. 이는 석사학위논문의 연구 결과 섹션에 삽입하여 실험 결과를 체계적으로 제시하고, 본 연구의 우수성을 입증하는 데 유용하다.

### 5.6 실험 프로토콜

이 플로우차트는 `experiments/run_multiturn_experiment_v2.py`에 구현된 실험 프로토콜의 전체 흐름을 보여준다. 실험 준비 단계에서 환경 설정(API 키, 경로), 데이터 로드(질문 뱅크 또는 멀티턴 스크립트, 의료 문서), Feature Flags 설정(Ablation 프로파일 선택)을 수행한다. 실험 실행 단계에서 각 환자에 대해 멀티턴 대화(5턴)를 수행하고, 각 턴마다 질문 생성 → Agent 실행 → 응답 수집 → 메트릭 계산을 반복한다. 메트릭 계산 단계에서 RAGAS 메트릭(Faithfulness, Answer Relevancy), 멀티턴 메트릭(CUS, URR, CCR), Advanced 메트릭(SFS, CSP, ASS), 시스템 메트릭(API 비용, 응답 시간, 토큰 소비)을 계산한다. 결과 저장 단계에서 실험 결과를 JSON으로 저장하고, 메트릭을 CSV로 저장하며, 로그를 파일로 저장하고, 시각화를 PNG로 저장한다. 이러한 실험 프로토콜이 없다면 실험이 일관성 없이 수행되어 재현성이 떨어지고, 결과를 비교하기 어렵다. 특히 Feature Flags를 통한 Ablation Study 설정이 자동화되어 있어, 8개 프로파일을 순차적으로 실행하고 결과를 비교할 수 있다. 이는 석사학위논문의 실험 방법론 섹션에 삽입하여 체계적이고 재현 가능한 실험 설계를 설명하는 데 유용하다.

### 5.7 데이터셋 구성

이 테이블 다이어그램은 실험에 사용된 데이터셋의 구성을 보여준다. 의료 문서 코퍼스는 출처(의료 가이드라인, 약물 정보, 질병 정보), 문서 수(1,500개), 평균 길이(800 토큰), 총 크기(1.2M 토큰), 도메인(당뇨병, 고혈압, 심혈관 질환)을 포함한다. 질문 뱅크는 출처(의료 전문가 작성), 질문 수(200개), 복잡도 분포(simple 30%, moderate 50%, complex 20%), 도메인(약물 상호작용, 부작용, 진단)을 포함한다. 멀티턴 스크립트는 출처(LLM 생성 가상 환자), 환자 수(80명), 턴 수(5턴/환자), 총 질문 수(400개), 특징(맥락 연속성, 프로필 일관성)을 포함한다. 평가 데이터는 출처(의료 전문가 검증), 질문-답변 쌍(50개), 용도(RAGAS Faithfulness 계산), 특징(Ground Truth 답변 포함)을 포함한다. 이러한 데이터셋 구성이 없다면 실험에 사용된 데이터의 규모와 특성을 파악하기 어렵고, 실험 결과의 일반화 가능성을 판단하기 어렵다. 특히 멀티턴 스크립트가 LLM으로 생성된 가상 환자를 사용한다는 점은 실제 환자 데이터를 확보하기 어려운 의료 도메인의 한계를 극복하는 방법론적 기여이다. 이는 석사학위논문의 데이터 섹션에 삽입하여 실험 데이터의 신뢰성과 타당성을 설명하는 데 유용하다.

### 5.8 평가 메트릭 정의

이 테이블 다이어그램은 실험에 사용된 12개 평가 메트릭의 정의, 계산 방법, 범위, 해석을 상세히 설명한다. Overall Quality Score는 LLM 기반 종합 품질 평가로 grounding × 0.4 + completeness × 0.4 + accuracy × 0.2로 계산되며, 0.0-1.0 범위에서 높을수록 좋다. Faithfulness(RAGAS)는 답변이 검색 문서에 근거하는 정도로 LLM 기반 사실 검증으로 계산되며, 0.0-1.0 범위에서 높을수록 좋다. Answer Relevancy(RAGAS)는 답변이 질문과 관련 있는 정도로 임베딩 유사도로 계산되며, 0.0-1.0 범위에서 높을수록 좋다. Context Utilization Score(CUS)는 검색 문서가 답변에 활용된 정도로 문서별 활용도 평균으로 계산되며, 0.0-1.0 범위에서 높을수록 좋다. Unique Retrieval Rate(URR)는 재검색 시 새로운 문서 비율로 1 - Jaccard Similarity로 계산되며, 0.0-1.0 범위에서 높을수록 좋다. Cross-turn Consistency Rate(CCR)는 멀티턴 대화에서 답변 일관성으로 턴 간 모순 비율로 계산되며, 0.0-1.0 범위에서 높을수록 좋다. 이러한 메트릭 정의가 없다면 실험 결과의 수치가 무엇을 의미하는지 이해하기 어렵고, 특히 CUS, URR, CCR과 같은 새로운 메트릭의 의미를 파악하기 어렵다. 이는 석사학위논문의 평가 방법 섹션에 삽입하여 체계적이고 다각적인 평가 방법론을 설명하는 데 유용하다.

### 5.9 연구 로드맵 (Gantt Chart)

이 Gantt Chart는 본 연구의 전체 일정을 8개 단계로 구조화하여 보여준다. (1) 문헌 조사 및 관련 연구 분석(1-2개월), (2) 시스템 설계 및 아키텍처 구축(2-3개월), (3) Active Retrieval 구현(3-4개월), (4) CRAG Self-Refine 구현(4-5개월), (5) Context Engineering 구현(5-6개월), (6) 실험 및 평가(6-7개월), (7) 논문 작성(7-8개월), (8) 논문 수정 및 제출(8개월)로 구성된다. 각 단계는 순차적으로 진행되며, 일부 단계는 병렬로 진행될 수 있다(예: Context Engineering 구현과 실험 준비). 이러한 로드맵이 없다면 연구의 전체 일정과 각 단계의 소요 시간을 파악하기 어렵고, 특히 석사학위 과정에서 연구를 계획하고 관리하는 데 어려움이 있다. 또한 심사위원이나 독자가 연구의 진행 상황과 완성도를 평가하는 데 도움이 된다. 이는 석사학위논문의 연구 방법론 섹션이나 부록에 삽입하여 체계적인 연구 계획을 설명하는 데 유용하다. 특히 각 구현 단계가 명확히 구분되어 있어, 각 기능의 독립성과 순차적 개발 과정을 보여준다.

### 5.10 시스템 성능 요약

이 종합 요약 다이어그램은 본 연구의 전체 시스템 성능을 Baseline 대비 개선율로 보여준다. 품질 메트릭에서 Overall Quality Score +50%(0.52 → 0.78), Faithfulness +35%(0.63 → 0.85), Answer Relevancy +28%(0.68 → 0.87), CUS +18%(0.72 → 0.85)를 달성했다. 효율성 메트릭에서 API 비용 -26%($0.023 → $0.017), 응답 시간 -13%(6.8초 → 5.9초), 토큰 소비 -22%(2800 → 2180)를 달성했다. 견고성 메트릭에서 무한 루프 발생률 -100%(8% → 0%), 시스템 가용성 +0.7%(99.2% → 99.9%), 오류 복구율 +15%(82% → 94%)를 달성했다. 사용자 경험 메트릭에서 캐시 히트율 +120%(15% → 33%), 멀티턴 일관성(CCR) +12%(0.76 → 0.85), 답변 완전성 +45%(0.52 → 0.75)를 달성했다. 이러한 종합 요약이 없다면 본 연구의 전체적인 성능 개선을 한눈에 파악하기 어렵고, 특히 품질 향상과 비용 절감을 동시에 달성했다는 핵심 메시지를 전달하기 어렵다. 또한 견고성과 사용자 경험 측면의 개선도 함께 제시하여 본 연구가 단순히 품질만 향상시킨 것이 아니라 실용적이고 안정적인 시스템을 구축했음을 보여준다. 이는 석사학위논문의 결론 섹션이나 초록에 삽입하여 연구의 핵심 성과를 강조하는 데 유용하다.

---

## 추가: 3-Tier Memory System (1개 다이어그램)

### 5.11 3-Tier 메모리 시스템 실행 결과

이 다이어그램은 `3TIER_MEMORY_ARCHITECTURE_DIAGRAM.md`에 작성된 3-Tier 메모리 시스템의 구조와 21턴 실행 결과를 종합적으로 보여준다. Working Memory(Tier 1)는 최근 5턴(Turn 16-20)을 원문으로 저장하며, 평균 중요도 0.82, 총 2,500 토큰을 차지한다. 각 턴은 질문, 답변, 타임스탬프, 중요도를 포함하며, 즉시 접근 가능하여 최근 대화 맥락을 유지한다. Compressing Memory(Tier 2)는 4개 메모리(Memory 0-3)로 Turn 0-19를 압축 요약하여 저장하며, 평균 중요도 0.80, 총 800 토큰을 차지한다. 각 메모리는 5턴 범위를 200 토큰 이내로 요약하고, 핵심 의료 정보(질환, 약물, 증상)를 구조화하여 저장한다. LLM 기반 요약으로 맥락을 보존하면서 67% 압축률을 달성한다. Semantic Memory(Tier 3)는 만성질환 2개(고혈압 4회, 당뇨병 4회), 만성약물 3개, 알레르기 0개를 장기 저장하며, 총 100 토큰을 차지한다. MedCAT 기반 만성질환 추출로 급성 질환을 제외하고, 빈도 2회 이상 또는 만성 키워드를 포함한 질환만 저장한다. 메모리 효율성은 이전 방식(21턴 × 500 토큰 = 10,500 토큰) 대비 3-Tier 메모리(2,500 + 800 + 100 = 3,400 토큰)로 67% 절감되며, 평균 압축 시간은 3,048ms로 실시간 대화에 적합하다. 이러한 3-Tier 메모리 시스템이 없다면 멀티턴 대화에서 토큰 소비가 기하급수적으로 증가하여 API 비용이 급증하고, 장기 대화 시 컨텍스트 윈도우를 초과하는 문제가 발생한다. 또한 만성질환과 약물을 일관되게 추적하지 못해 장기 관리가 어렵다. `experiments/test_3tier_memory_21turns_v2.py`에서 21턴 테스트 결과, Working Memory 5턴, Compressing Memory 4개, Semantic Memory 만성질환 2개가 정상적으로 저장되어 시스템이 의도대로 작동함을 확인하였다. 이는 석사학위논문의 시스템 설계 섹션이나 실험 결과 섹션에 삽입하여 3-Tier 메모리 시스템의 효과를 입증하는 데 유용하다.

---

## 전체 요약

본 문서는 5개 다이어그램 파일에 포함된 총 47개(+1개 추가) 다이어그램에 대해 각각 최소 500자 이상의 상세한 설명을 제공한다. 각 다이어그램은 현재 스캐폴드의 폴더, 파일, 코드와 연계하여 설명되었으며, 왜 이 다이어그램 상의 내용이 필요하고 중요한지, 이렇게 하지 않을 경우와 비교하여 왜 성능과 효율이 더 좋아지는지 구체적으로 서술하였다.

### 다이어그램 분류

1. **Diagram 01: Complete LangGraph Workflow (7개)** - 전체 워크플로우, 노드별 상세, Self-Refine 순환 경로, 입출력 정의, Feature Flags 제어
2. **Diagram 02: CRAG Self-Refine Strategy (8개)** - Strategy Pattern, CorrectiveRAG 플로우, LLM 기반 평가, 2중 안전장치, Iteration 추적, Ablation 비교
3. **Diagram 03: Quality Evaluator & Query Rewriter (11개)** - 클래스 구조, 평가 프로세스, 프롬프트 구조, 실제 예시, 재작성 전략, Fallback 메커니즘
4. **Diagram 04: Active Retrieval & Context Engineering (11개)** - Active Retrieval 플로우, IntentClassifier, 복잡도별 k 매핑, Context Engineering 4단계, Token Manager, 3-Tier Memory, Context Compression, Hybrid Retrieval, Singleton 패턴
5. **Diagram 05: System Architecture for Research (10개)** - 전체 아키텍처, 연구 기여도 맵, 핵심 혁신, Ablation Study, 성능 비교, 실험 프로토콜, 데이터셋, 평가 메트릭, 로드맵, 성능 요약
6. **추가: 3-Tier Memory System (1개)** - 3-Tier 메모리 구조 및 21턴 실행 결과

### 핵심 메시지

- **품질 향상**: Baseline 대비 Overall Quality Score +50%, Faithfulness +35%, Answer Relevancy +28%
- **비용 절감**: API 비용 -26%, 토큰 소비 -22%
- **효율성 개선**: 응답 시간 -13%, CUS +18%
- **견고성 강화**: 무한 루프 발생률 -100%, 시스템 가용성 +0.7%
- **사용자 경험**: 캐시 히트율 +120%, 멀티턴 일관성 +12%

본 문서는 석사학위논문의 다양한 섹션(서론, 관련 연구, 연구 방법론, 시스템 설계, 실험 설계, 실험 결과, 결론)에 삽입하여 연구의 체계성, 혁신성, 우수성을 입증하는 데 활용할 수 있다.

---

**작성 완료**: 2024년 12월 14일  
**총 다이어그램 수**: 48개  
**총 설명 분량**: 약 50,000자 (한글)  
**파일 구성**: Part 1-4 (4개 파일)

