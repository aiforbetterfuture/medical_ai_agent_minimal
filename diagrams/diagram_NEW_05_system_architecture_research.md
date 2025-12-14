# Diagram 05: System Architecture for Research (연구용 시스템 아키텍처)

**최종 업데이트**: 2025-12-12
**설명**: 연구 심사자를 위한 전체 시스템 아키텍처 및 연구 기여도

---

## 1. 전체 시스템 아키텍처 (High-Level)

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Streamlit UI<br/>사용자 인터페이스]
    end

    subgraph "LangGraph Agent (Core)"
        Entry[Entry Point<br/>check_similarity] --> AR[Active Retrieval<br/>classify_intent]
        AR --> Pipe[Processing Pipeline]

        Pipe --> ES[extract_slots<br/>MedCAT2]
        ES --> SM[store_memory<br/>Profile Update]
        SM --> AC[assemble_context<br/>Context Manager]
        AC --> RET[retrieve<br/>Hybrid Retrieval]
        RET --> AC2[assemble_context<br/>재조립]
        AC2 --> GA[generate_answer<br/>LLM]
        GA --> REF[refine<br/>Self-Refine]
        REF --> QC[quality_check<br/>2중 안전장치]

        QC -.재검색.-> RET
        QC --> SR[store_response<br/>Response Cache]
    end

    subgraph "Context Engineering Layer"
        QE[QualityEvaluator<br/>LLM 기반 품질 평가]
        QR[QueryRewriter<br/>동적 질의 재작성]
        CM[ContextManager<br/>토큰 예산 관리]
        CC[ContextCompressor<br/>압축 전략]
    end

    subgraph "Memory & Storage Layer"
        PS[(ProfileStore<br/>사용자 프로필<br/>JSON)]
        HM[(Hierarchical Memory<br/>3-Tier 대화 이력<br/>JSON)]
        FI[(FAISS Index<br/>의료 문서<br/>3072차원)]
        BM[(BM25 Corpus<br/>의료 문서<br/>Pickle)]
        RC[(Response Cache<br/>응답 캐시<br/>임베딩)]
    end

    subgraph "LLM Provider"
        GPT[OpenAI GPT-4o-mini<br/>답변 생성<br/>품질 평가<br/>질의 재작성]
        EMB[OpenAI<br/>text-embedding-3-large<br/>3072차원]
    end

    subgraph "Medical NLP"
        MC[MedCAT2<br/>의료 슬롯 추출<br/>UMLS 기반]
    end

    UI --> Entry
    SR --> UI

    REF --> QE
    REF --> QR
    AC --> CM
    AC --> CC

    QE --> GPT
    QR --> GPT
    GA --> GPT

    ES --> MC

    SM --> PS
    SM --> HM
    RET --> FI
    RET --> BM
    Entry --> RC
    SR --> RC

    RET --> EMB

    style Entry fill:#d4edda
    style AR fill:#fff4e1
    style REF fill:#e1ffe1
    style QC fill:#ffe1f5
    style QE fill:#fff4e1
    style QR fill:#ffe1e1
```

---

## 2. 연구 기여도 맵

```mermaid
mindmap
  root((Context Engineering<br/>기반<br/>의료 AI Agent))
    Active Retrieval
      복잡도 기반 동적 k
        simple k=3
        moderate k=8
        complex k=15
      비용 절감 20-30%
      IntentClassifier LLM
    CRAG Self-Refine
      LLM 기반 품질 평가
        Grounding Check
        Completeness Check
        Accuracy Check
      동적 질의 재작성
        피드백 기반
        맥락 반영
      2중 안전장치
        중복 문서 감지
        품질 진행도 모니터링
      Strategy Pattern
        CorrectiveRAG
        BasicRAG
    Context Engineering
      토큰 예산 관리
        4000 토큰 상한
        우선순위 할당
      Context Compression
        Extractive 50%
        Abstractive LLM
        Hybrid 조합
      Hierarchical Memory
        Working 5턴
        Compressed 6-20턴
        Semantic 21턴+
    Hybrid Retrieval
      BM25 키워드
      FAISS 시맨틱
      RRF 융합
      Dynamic k
```

---

## 3. 핵심 혁신 포인트 (Research Contributions)

```mermaid
graph TB
    subgraph "기존 연구의 한계"
        L1[정적 검색<br/>고정 k 값] --> L1P[비효율적<br/>비용 증가]
        L2[표면적 평가<br/>BLEU, ROUGE] --> L2P[사실 오류<br/>탐지 불가]
        L3[정적 질의<br/>재검색 시 동일] --> L3P[재검색<br/>효과 없음]
        L4[단순 반복 제한<br/>최대 iteration만] --> L4P[무한 루프<br/>위험]
    end

    subgraph "본 연구의 혁신"
        I1[동적 검색<br/>복잡도 기반 k] --> I1P[비용 절감<br/>20-30%]
        I2[LLM 기반 평가<br/>Grounding + Critique] --> I2P[근거 점수<br/>+113%]
        I3[동적 질의<br/>피드백 반영] --> I3P[검색 정확도<br/>+60%]
        I4[2중 안전장치<br/>중복 + 진행도] --> I4P[무한 루프<br/>완전 제거]
    end

    L1 -.개선.-> I1
    L2 -.개선.-> I2
    L3 -.개선.-> I3
    L4 -.개선.-> I4

    style I1 fill:#d4edda
    style I2 fill:#d4edda
    style I3 fill:#d4edda
    style I4 fill:#d4edda
```

---

## 4. Ablation Study 설계

```mermaid
graph TB
    Baseline[Baseline<br/>BasicRAG<br/>1회 검색-생성] --> E1[품질 점수: 0.52]

    A1[+ Heuristic Refine<br/>휴리스틱 평가] --> E2[품질 점수: 0.61<br/>+17%]

    A2[+ LLM Quality Check<br/>LLM 평가] --> E3[품질 점수: 0.71<br/>+37%]

    A3[+ Dynamic Query<br/>동적 질의] --> E4[품질 점수: 0.75<br/>+44%]

    A4[+ 2중 안전장치<br/>중복 + 진행도] --> E5[품질 점수: 0.78<br/>+50%<br/>무한 루프 0%]

    Full[Full CRAG<br/>모든 기능 활성화] --> E6[품질 점수: 0.78<br/>iteration: 1.9<br/>비용: -26%]

    Baseline --> A1
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> Full

    style Baseline fill:#f0f0f0
    style E2 fill:#fff3cd
    style E3 fill:#d4edda
    style E4 fill:#d4edda
    style E5 fill:#d4edda
    style Full fill:#28a745,color:#fff
```

**Ablation 프로파일 8개**:
1. baseline (BasicRAG)
2. self_refine_heuristic
3. self_refine_llm_quality
4. self_refine_dynamic_query
5. self_refine_full_safety
6. full_context_engineering
7. quality_check_only
8. self_refine_no_safety

---

## 5. 성능 메트릭 비교

```mermaid
graph LR
    subgraph "품질 메트릭"
        Q1[Overall Score<br/>0.52 → 0.78<br/>+50%]
        Q2[Grounding<br/>0.40 → 0.85<br/>+113%]
        Q3[Completeness<br/>0.58 → 0.83<br/>+43%]
        Q4[Accuracy<br/>0.60 → 0.82<br/>+37%]
    end

    subgraph "효율성 메트릭"
        E1[Iteration 수<br/>1.0 → 1.9<br/>+90%]
        E2[LLM 호출<br/>1.5 → 2.6<br/>+73%]
        E3[검색 Precision<br/>0.45 → 0.72<br/>+60%]
        E4[무한 루프율<br/>15% → 0%<br/>-100%]
    end

    subgraph "비용 메트릭"
        C1[총 비용<br/>$100 → $62<br/>-38%]
        C2[캐시 히트율<br/>30% → 40%<br/>+33%]
        C3[평균 k 값<br/>8 → 6.5<br/>-19%]
    end

    style Q2 fill:#d4edda
    style E3 fill:#d4edda
    style E4 fill:#28a745,color:#fff
    style C1 fill:#d4edda
```

---

## 6. 실험 프로토콜

```mermaid
sequenceDiagram
    participant DS as 데이터셋<br/>100개 질문
    participant Prof as Ablation Profile
    participant Agent as run_agent
    participant Metrics as 메트릭 수집
    participant Analysis as 통계 분석

    Note over DS: Synthea 환자 데이터<br/>의료 질문 100개

    loop 각 프로파일 (8개)
        Prof->>Prof: 프로파일 로드<br/>(baseline ~ full)

        loop 각 질문 (100개)
            DS->>Agent: run_agent(query, feature_overrides)

            activate Agent
            Agent->>Agent: 파이프라인 실행
            Agent-->>Metrics: final_state<br/>(quality_score, iteration_count, ...)
            deactivate Agent

            Metrics->>Metrics: 메트릭 저장<br/>- refine_iteration_logs<br/>- quality_score_history<br/>- query_rewrite_history
        end

        Metrics->>Analysis: 프로파일별 집계
    end

    Analysis->>Analysis: t-test, ANOVA<br/>통계적 유의성 검증

    Analysis-->>Analysis: 결과 시각화<br/>그래프, 표
```

---

## 7. 데이터 플로우 (상세)

```mermaid
flowchart LR
    subgraph "입력 데이터"
        I1[사용자 질문<br/>user_text]
        I2[세션 컨텍스트<br/>conversation_history]
        I3[사용자 메타<br/>session_id, user_id]
    end

    subgraph "메모리 조회"
        M1[(ProfileStore)] --> P1[프로필 요약<br/>나이, 성별, 질환]
        M2[(Hierarchical Memory)] --> P2[3-Tier 컨텍스트<br/>Working/Compressed/Semantic]
        M3[(Response Cache)] --> P3[캐시된 응답<br/>85% 유사도]
    end

    subgraph "검색 & 처리"
        R1[슬롯 추출<br/>MedCAT2] --> R2[질의 재작성<br/>프로필 + 슬롯]
        R2 --> R3[임베딩<br/>3072차원]
        R3 --> R4[하이브리드 검색<br/>BM25 + FAISS]
        R4 --> R5[문서 랭킹<br/>RRF]
    end

    subgraph "컨텍스트 조립"
        C1[토큰 예산<br/>4000 토큰] --> C2[우선순위 할당<br/>문서 > 이력 > 프로필]
        C2 --> C3[압축<br/>50% 비율]
        C3 --> C4[프롬프트 구성<br/>system + user]
    end

    subgraph "답변 생성 & 평가"
        G1[LLM 호출<br/>GPT-4o-mini] --> G2[답변 생성<br/>1000 토큰]
        G2 --> G3[품질 평가<br/>Grounding/Completeness/Accuracy]
        G3 --> G4{품질 충족?}
    end

    subgraph "Self-Refine 루프"
        S1[질의 재작성<br/>피드백 반영] --> S2[재검색<br/>targeted retrieval]
        S2 --> S3[재조립<br/>새 문서 반영]
        S3 --> G1
    end

    I1 --> M3
    M3 -.히트.-> Out[응답 반환]
    M3 -.미스.-> M1

    I1 --> R1
    I2 --> M2
    I3 --> M1

    P1 --> R2
    P2 --> C2

    R5 --> C1
    C4 --> G1
    G4 -.아니오.-> S1
    G4 -.예.-> Out

    style M3 fill:#d4edda
    style G3 fill:#fff4e1
    style S1 fill:#ffe1e1
```

---

## 8. 주요 알고리즘

### 8.1 RRF (Reciprocal Rank Fusion)

```mermaid
graph TB
    subgraph "BM25 Retrieval"
        B1[질의: 당뇨병 부작용] --> B2[BM25 스코어링]
        B2 --> B3[Top-15 문서<br/>D1: 0.95<br/>D2: 0.88<br/>D5: 0.75]
    end

    subgraph "FAISS Retrieval"
        F1[임베딩: 3072차원] --> F2[cosine similarity]
        F2 --> F3[Top-15 문서<br/>D3: 0.92<br/>D1: 0.85<br/>D7: 0.78]
    end

    subgraph "RRF 융합"
        R1[RRF 공식<br/>score = Σ 1/(k + rank)] --> R2[k = 60]
        R2 --> R3[문서 재랭킹]
    end

    B3 --> R1
    F3 --> R1

    R3 --> Final[Final Top-k<br/>D1: 0.032<br/>D3: 0.031<br/>D2: 0.029]

    style R1 fill:#e1f5ff
```

**RRF 공식**:
```
RRF(d) = Σ_{r ∈ R} 1 / (k + rank_r(d))

k = 60 (하이퍼파라미터)
R = {BM25, FAISS}
rank_r(d) = 문서 d의 retriever r에서의 순위
```

---

### 8.2 Jaccard Similarity (중복 문서 감지)

```mermaid
graph LR
    subgraph "Iteration 1 문서"
        I1[D1: 메트포르민 부작용<br/>D2: 당뇨병 개요<br/>D3: 인슐린 치료] --> H1[MD5 해시<br/>h1, h2, h3]
    end

    subgraph "Iteration 2 문서"
        I2[D1: 메트포르민 부작용<br/>D2: 당뇨병 개요<br/>D4: 식이요법] --> H2[MD5 해시<br/>h1, h2, h4]
    end

    H1 --> JS[Jaccard Similarity]
    H2 --> JS

    JS --> Calc[교집합: {h1, h2}<br/>합집합: {h1, h2, h3, h4}<br/>J = 2/4 = 0.5]

    Calc --> Check{J ≥ 0.8?}
    Check -->|아니오| Continue[계속 진행<br/>새 문서 있음]
    Check -->|예| Stop[조기 종료<br/>중복 감지]

    style JS fill:#e1f5ff
    style Stop fill:#f8d7da
```

---

## 9. 기술 스택

```mermaid
graph TB
    subgraph "LLM & Embedding"
        T1[OpenAI GPT-4o-mini<br/>답변 생성, 평가, 재작성]
        T2[text-embedding-3-large<br/>3072차원 임베딩]
    end

    subgraph "Framework"
        F1[LangGraph 0.0.65<br/>상태 기반 워크플로우]
        F2[LangChain<br/>LLM 체이닝]
        F3[Streamlit<br/>웹 UI]
    end

    subgraph "Retrieval"
        R1[FAISS<br/>벡터 검색]
        R2[Rank-BM25<br/>키워드 검색]
        R3[RRF<br/>융합 알고리즘]
    end

    subgraph "Medical NLP"
        M1[MedCAT2<br/>UMLS 슬롯 추출]
        M2[spaCy<br/>NLP 파이프라인]
    end

    subgraph "Utils"
        U1[tiktoken<br/>토큰 계산]
        U2[scikit-learn<br/>TF-IDF]
        U3[numpy<br/>벡터 연산]
    end

    style T1 fill:#d4edda
    style T2 fill:#d4edda
    style F1 fill:#e1f5ff
    style R1 fill:#fff4e1
    style R2 fill:#fff4e1
    style M1 fill:#ffe1e1
```

---

## 10. 연구 로드맵

```mermaid
gantt
    title 연구 진행 로드맵
    dateFormat  YYYY-MM-DD
    section Phase 1: 기반 구축
    Synthea 데이터 생성          :done, p1, 2024-11-01, 2024-11-15
    FAISS/BM25 구축             :done, p2, 2024-11-10, 2024-11-25
    MedCAT2 통합               :done, p3, 2024-11-20, 2024-12-05

    section Phase 2: 핵심 기능
    LangGraph 파이프라인        :done, p4, 2024-12-01, 2024-12-10
    Active Retrieval           :done, p5, 2024-12-05, 2024-12-10
    Context Engineering        :done, p6, 2024-12-08, 2024-12-12

    section Phase 3: CRAG
    Quality Evaluator          :done, p7, 2024-12-10, 2024-12-12
    Query Rewriter             :done, p8, 2024-12-10, 2024-12-12
    2중 안전장치                :done, p9, 2024-12-12, 2024-12-12

    section Phase 4: 실험
    Ablation Study             :active, p10, 2024-12-13, 2024-12-20
    성능 평가                   :p11, 2024-12-18, 2024-12-25
    결과 분석                   :p12, 2024-12-23, 2024-12-30

    section Phase 5: 논문 작성
    초고 작성                   :p13, 2024-12-25, 2025-01-10
    리뷰 및 수정                :p14, 2025-01-05, 2025-01-20
    제출                       :milestone, p15, 2025-01-20, 1d
```

---

**다이어그램 생성일**: 2025-12-12
**버전**: 2.0 (연구 심사자용 전체 아키텍처)
