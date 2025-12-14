# Diagram 04: Active Retrieval & Context Engineering Architecture

**최종 업데이트**: 2025-12-12
**설명**: Active Retrieval과 Context Engineering의 전체 아키텍처

---

## 1. Active Retrieval 상세 플로우

```mermaid
flowchart TB
    Start[사용자 질문<br/>user_text] --> Cache{check_similarity<br/>캐시 확인}

    Cache -->|캐시 히트<br/>유사도 ≥ 0.85| Return[캐시된 응답<br/>스타일 30% 변경]
    Cache -->|캐시 미스| Classify[classify_intent<br/>IntentClassifier]

    Classify --> LLM[LLM 기반 분류<br/>GPT-4o-mini]

    LLM --> Complexity{질의 복잡도}

    Complexity -->|simple<br/>간단한 인사/확인| Simple[needs_retrieval = False<br/>dynamic_k = 3<br/>검색 스킵]
    Complexity -->|moderate<br/>일반적 의료 질문| Moderate[needs_retrieval = True<br/>dynamic_k = 8]
    Complexity -->|complex<br/>복잡한 진단/상호작용| Complex[needs_retrieval = True<br/>dynamic_k = 15]

    Simple --> Skip[assemble_context<br/>검색 없이 컨텍스트 조립]
    Moderate --> Extract[extract_slots<br/>슬롯 추출]
    Complex --> Extract

    Skip --> GenDirect[generate_answer<br/>직접 생성]

    Extract --> Store[store_memory<br/>프로필 업데이트]
    Store --> Assemble[assemble_context<br/>컨텍스트 조립]
    Assemble --> Retrieve[retrieve<br/>하이브리드 검색<br/>k = dynamic_k]

    Retrieve --> Gen[generate_answer]

    GenDirect --> End([답변 반환])
    Gen --> End

    style Classify fill:#fff4e1
    style Simple fill:#d4edda
    style Moderate fill:#fff3cd
    style Complex fill:#f8d7da
    style Retrieve fill:#e1f5ff
```

---

## 2. IntentClassifier 상세

```mermaid
sequenceDiagram
    participant CI as classify_intent_node
    participant IC as IntentClassifier
    participant LLM as GPT-4o-mini
    participant State as AgentState

    Note over CI: Active Retrieval 활성화 확인

    CI->>IC: classify(user_text)

    activate IC

    IC->>IC: 분류 프롬프트 생성

    Note over IC: 프롬프트 예시<br/>"다음 의료 질의의 복잡도를 분류하세요.<br/>simple: 간단한 인사/확인<br/>moderate: 일반적 의료 질문<br/>complex: 복잡한 진단/약물 상호작용"

    IC->>LLM: generate(prompt, temperature=0.3)

    activate LLM
    LLM-->>IC: "moderate"
    deactivate LLM

    IC->>IC: 복잡도 → k 매핑<br/>moderate → k=8

    IC-->>CI: {complexity: "moderate", k: 8, needs_retrieval: True}

    deactivate IC

    CI->>State: dynamic_k = 8<br/>query_complexity = "moderate"<br/>needs_retrieval = True

    Note over State: 상태 업데이트 완료
```

---

## 3. 복잡도별 k 값 매핑

```mermaid
graph LR
    subgraph "질의 복잡도 분류"
        Q1["안녕하세요"] --> S[simple]
        Q2["당뇨병이란?"] --> M[moderate]
        Q3["당뇨병 환자가 고혈압약<br/>리시노프릴과 메트포르민을<br/>같이 복용해도 되나요?"] --> C[complex]
    end

    subgraph "k 값 매핑"
        S --> K3[k = 3<br/>검색 스킵 or 최소 검색]
        M --> K8[k = 8<br/>일반 검색]
        C --> K15[k = 15<br/>광범위 검색]
    end

    subgraph "토큰 예산 제약"
        K3 --> B3[예상 토큰: 600<br/>예산 내 여유]
        K8 --> B8[예상 토큰: 1600<br/>예산 적절]
        K15 --> B15[예상 토큰: 3000<br/>예산 근접]
    end

    style S fill:#d4edda
    style M fill:#fff3cd
    style C fill:#f8d7da
```

**토큰 예산 계산**:
```
평균 문서 길이: 200 토큰
예상 총 토큰 = k × 200

simple: 3 × 200 = 600 토큰
moderate: 8 × 200 = 1600 토큰
complex: 15 × 200 = 3000 토큰

토큰 예산 상한: 4000 토큰 (안전 마진 포함)
```

---

## 4. Context Engineering 4단계 프로세스

```mermaid
graph TB
    subgraph "Stage 1: Context Acquisition (컨텍스트 획득)"
        S1A[사용자 질문] --> S1B[슬롯 추출<br/>MedCAT/LLM]
        S1B --> S1C[프로필 조회<br/>ProfileStore]
        S1C --> S1D[대화 이력 조회<br/>Hierarchical Memory]
        S1D --> S1E[하이브리드 검색<br/>BM25 + FAISS]
    end

    subgraph "Stage 2: Context Assembly (컨텍스트 조립)"
        S2A[토큰 예산 계산<br/>TokenManager] --> S2B[컨텍스트 압축<br/>ContextCompressor<br/>선택적]
        S2B --> S2C[프롬프트 구성<br/>system + user]
        S2C --> S2D[검색 문서 포맷팅<br/>상위 5개, 500자/문서]
    end

    subgraph "Stage 3: Answer Generation (답변 생성)"
        S3A[LLM 호출<br/>GPT-4o-mini] --> S3B[답변 생성<br/>근거 기반]
        S3B --> S3C[메타데이터 추가<br/>출처, 신뢰도]
    end

    subgraph "Stage 4: Quality Refinement (품질 개선)"
        S4A[품질 평가<br/>QualityEvaluator] --> S4B{품질 충족?}
        S4B -->|아니오| S4C[질의 재작성<br/>QueryRewriter]
        S4C --> S4D[재검색<br/>targeted retrieval]
        S4D --> S2A
        S4B -->|예| S4E[응답 반환<br/>캐싱]
    end

    S1E --> S2A
    S2D --> S3A
    S3C --> S4A

    style S1E fill:#e1f5ff
    style S2C fill:#fff4e1
    style S3B fill:#d4edda
    style S4A fill:#ffe1e1
```

---

## 5. Context Manager & Token Manager

```mermaid
classDiagram
    class TokenManager {
        -max_total_tokens: int (4000)
        +count_tokens(text: str) int
        +calculate_budget(contexts: dict) dict
        +fits_budget(text: str, budget: int) bool
    }

    class ContextManager {
        -token_manager: TokenManager
        +build_context(user_id, session_id, current_query, ...) dict
        -_allocate_budget() dict
        -_trim_to_budget(text: str, budget: int) str
    }

    class ContextCompressor {
        -token_manager: TokenManager
        -llm_client: LLMClient
        +compress_docs(docs, query, budget) tuple
        -_extractive_compression(docs, query) list
        -_abstractive_compression(docs, query) str
    }

    ContextManager --> TokenManager : uses
    ContextCompressor --> TokenManager : uses

    note for TokenManager "토큰 예산 관리<br/>- 4000 토큰 상한<br/>- tiktoken 기반 정확한 계산"
    note for ContextManager "컨텍스트 조립<br/>- 대화 이력: 300 토큰<br/>- 프로필: 200 토큰<br/>- 검색 문서: 900 토큰"
    note for ContextCompressor "Context Compression<br/>- Extractive: 핵심 문장 추출<br/>- Abstractive: LLM 요약<br/>- Hybrid: 조합"
```

---

## 6. 토큰 예산 할당 전략

```mermaid
graph TB
    Total[총 토큰 예산<br/>4000 토큰] --> Reserve[시스템/사용자 프롬프트<br/>예약: 500 토큰]

    Reserve --> Available[사용 가능: 3500 토큰]

    Available --> History[대화 이력<br/>300 토큰 8.6%]
    Available --> Profile[프로필 요약<br/>200 토큰 5.7%]
    Available --> Longterm[장기 컨텍스트<br/>100 토큰 2.9%<br/>선택적]
    Available --> Docs[검색 문서<br/>900 토큰 25.7%]
    Available --> Query[현재 질문<br/>200 토큰 5.7%]
    Available --> Buffer[버퍼<br/>1800 토큰 51.4%]

    style Total fill:#e1f5ff
    style Docs fill:#f8d7da
    style Buffer fill:#f0f0f0
```

**우선순위**:
1. 현재 질문 (필수)
2. 검색 문서 (핵심 - 최대 할당)
3. 대화 이력 (컨텍스트 유지)
4. 프로필 요약 (개인화)
5. 장기 컨텍스트 (선택적)

---

## 7. Hierarchical Memory 3-Tier 구조

```mermaid
graph TB
    subgraph "Working Memory (단기)"
        W1[최근 5턴 대화] --> W2[전체 텍스트 보존]
        W2 --> W3[즉시 접근<br/>토큰: ~300]
    end

    subgraph "Compressed Memory (중기)"
        C1[6~20턴 대화] --> C2[LLM 요약<br/>핵심만 추출]
        C2 --> C3[압축 비율: 50%<br/>토큰: ~200]
    end

    subgraph "Semantic Memory (장기)"
        S1[21턴 이상 대화] --> S2[임베딩 기반<br/>의미 검색]
        S2 --> S3[관련성 높은<br/>대화만 추출<br/>토큰: ~100]
    end

    Query[현재 질문] --> Retrieve{3-Tier<br/>검색}

    Retrieve --> W3
    Retrieve --> C3
    Retrieve --> S3

    W3 --> Combine[컨텍스트 결합]
    C3 --> Combine
    S3 --> Combine

    Combine --> Context[Hierarchical Context<br/>총 600 토큰]

    style W3 fill:#d4edda
    style C3 fill:#fff3cd
    style S3 fill:#e1f5ff
```

---

## 8. Context Compression 전략

```mermaid
flowchart TB
    Start[검색 문서<br/>k개, 총 N 토큰] --> Budget{N > 예산?}

    Budget -->|아니오| NoComp[압축 불필요<br/>원본 사용]
    Budget -->|예| Strategy{압축 전략}

    Strategy -->|extractive| Extract[Extractive Compression<br/>핵심 문장 추출]
    Strategy -->|abstractive| Abstract[Abstractive Compression<br/>LLM 요약]
    Strategy -->|hybrid| Hybrid[Hybrid Compression<br/>추출 + 요약]

    Extract --> TF[TF-IDF 기반<br/>문장 스코어링]
    TF --> TopK[상위 K개 문장 선택]
    TopK --> Verify1{토큰 ≤ 예산?}

    Abstract --> LLM[LLM 호출<br/>요약 요청]
    LLM --> Summary[요약 텍스트 생성]
    Summary --> Verify2{토큰 ≤ 예산?}

    Hybrid --> Extract2[Extractive 먼저]
    Extract2 --> Abstract2[Abstractive 추가]
    Abstract2 --> Verify3{토큰 ≤ 예산?}

    Verify1 -->|예| Return1[압축 완료]
    Verify1 -->|아니오| Reduce1[K 감소]
    Reduce1 --> TopK

    Verify2 -->|예| Return2[압축 완료]
    Verify2 -->|아니오| Retry2[요약 재요청<br/>더 짧게]
    Retry2 --> LLM

    Verify3 -->|예| Return3[압축 완료]
    Verify3 -->|아니오| Fallback[폴백: Extractive만]

    NoComp --> End([반환])
    Return1 --> End
    Return2 --> End
    Return3 --> End
    Fallback --> End

    style Extract fill:#e1f5ff
    style Abstract fill:#fff4e1
    style Hybrid fill:#d4edda
```

---

## 9. 전체 시스템 데이터 플로우

```mermaid
graph LR
    subgraph "입력"
        I1[사용자 질문]
        I2[세션 ID]
        I3[사용자 ID]
    end

    subgraph "메모리 계층"
        M1[(ProfileStore<br/>사용자 프로필)]
        M2[(Hierarchical Memory<br/>3-Tier 대화 이력)]
        M3[(FAISS Index<br/>의료 문서)]
        M4[(BM25 Corpus<br/>의료 문서)]
        M5[(Response Cache<br/>응답 캐시)]
    end

    subgraph "처리 파이프라인"
        P1[check_similarity]
        P2[classify_intent]
        P3[extract_slots]
        P4[store_memory]
        P5[assemble_context]
        P6[retrieve]
        P7[generate_answer]
        P8[refine]
        P9[quality_check]
    end

    subgraph "출력"
        O1[답변 텍스트]
        O2[품질 메트릭]
        O3[iteration 로그]
    end

    I1 --> P1
    I2 --> P1
    I3 --> P1

    P1 --> M5
    M5 -.캐시 히트.-> O1

    P1 --> P2
    P2 --> P3
    P3 --> M1
    M1 --> P4
    P4 --> M1
    P4 --> M2
    M2 --> P5

    P5 --> P6
    P6 --> M3
    P6 --> M4

    M3 --> P6
    M4 --> P6

    P6 --> P5
    P5 --> P7
    P7 --> P8
    P8 --> P9

    P9 -.재검색.-> P6
    P9 --> O1
    P9 --> O2
    P9 --> O3

    O1 --> M5

    style M1 fill:#fff4e1
    style M2 fill:#e1f5ff
    style M3 fill:#ffe1e1
    style M4 fill:#ffe1e1
    style M5 fill:#d4edda
```

---

## 10. 성능 최적화 체크리스트

```mermaid
graph TB
    Opt[성능 최적화] --> O1[캐시 활용<br/>✓ 응답 캐시 85% 유사도<br/>✓ 30~40% LLM 호출 절약]
    Opt --> O2[Active Retrieval<br/>✓ 복잡도 기반 동적 k<br/>✓ 20~30% 검색 비용 절약]
    Opt --> O3[토큰 예산 관리<br/>✓ 4000 토큰 이내 유지<br/>✓ 예산 초과 방지]
    Opt --> O4[Context Compression<br/>✓ 압축 비율 50%<br/>✓ 토큰 절약]
    Opt --> O5[Hierarchical Memory<br/>✓ 3-Tier 구조<br/>✓ 관련 대화만 로드]
    Opt --> O6[2중 안전장치<br/>✓ 중복 검색 방지<br/>✓ 무한 루프 방지]
    Opt --> O7[LLM 재사용<br/>✓ llm_client 캐싱<br/>✓ API 호출 최소화]

    style O1 fill:#d4edda
    style O2 fill:#d4edda
    style O3 fill:#d4edda
    style O6 fill:#f8d7da
```

---

## 11. 비용 분석 (예상)

| 컴포넌트 | 비용 ($/1000 질의) | 최적화 효과 |
|---------|-------------------|------------|
| **캐시 미스율** | 70% → 60% | -$15 (캐시 히트 증가) |
| **Active Retrieval** | k=8 고정 → 동적 k | -$10 (평균 k 감소) |
| **Context Compression** | 압축 없음 → 50% 압축 | -$8 (토큰 절약) |
| **Self-Refine** | +2.6 LLM 호출/질의 | +$20 (품질 향상 비용) |
| **2중 안전장치** | 무한 루프 15% → 0% | -$25 (비용 폭증 방지) |
| **총 비용 변화** | $100 → $62 | **-38% 절감** |

---

**다이어그램 생성일**: 2025-12-12
**버전**: 2.0 (Active Retrieval + Context Engineering)
