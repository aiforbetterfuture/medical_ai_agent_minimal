# Diagram 02: CRAG Self-Refine with Strategy Pattern

**최종 업데이트**: 2025-12-12
**설명**: Strategy Pattern 기반 Corrective RAG Self-Refine 상세 플로우

---

## 1. Strategy Pattern 구조

```mermaid
classDiagram
    class RefineStrategy {
        <<interface>>
        +refine(state: AgentState) dict
        +should_retrieve(state: AgentState) bool
        +get_strategy_name() str
        +get_metrics(state: AgentState) dict
    }

    class CorrectiveRAGStrategy {
        -llm_client: LLMClient
        -quality_evaluator: QualityEvaluator
        -query_rewriter: QueryRewriter
        +refine(state) dict
        +should_retrieve(state) bool
        +get_strategy_name() "Corrective RAG"
    }

    class BasicRAGStrategy {
        +refine(state) dict
        +should_retrieve(state) bool
        +get_strategy_name() "Basic RAG (Baseline)"
    }

    class RefineStrategyFactory {
        +create(feature_flags) RefineStrategy
    }

    RefineStrategy <|-- CorrectiveRAGStrategy
    RefineStrategy <|-- BasicRAGStrategy
    RefineStrategyFactory --> RefineStrategy : creates

    note for CorrectiveRAGStrategy "Context Engineering 기반\n- LLM 품질 평가\n- 동적 질의 재작성\n- 2중 안전장치"
    note for BasicRAGStrategy "베이스라인\n- 품질 평가 없음\n- 재검색 없음\n- 1회 생성 후 종료"
```

---

## 2. CorrectiveRAG Strategy 상세 플로우

```mermaid
flowchart TB
    Start[refine_node 진입] --> CheckMode{LLM 모드 or<br/>self_refine<br/>비활성화?}

    CheckMode -->|예| Bypass[quality_score = 1.0<br/>needs_retrieval = False<br/>종료]
    CheckMode -->|아니오| Factory[RefineStrategyFactory.create]

    Factory --> SelectStrategy{feature_flags<br/>['refine_strategy']}

    SelectStrategy -->|'corrective_rag'<br/>기본값| CRAG[CorrectiveRAGStrategy]
    SelectStrategy -->|'basic_rag'| Basic[BasicRAGStrategy]

    CRAG --> Evaluate[LLM 기반 품질 평가]
    Basic --> Skip[quality_score = 1.0<br/>needs_retrieval = False]

    Evaluate --> Evaluator[QualityEvaluator.evaluate]

    Evaluator --> Grounding[Grounding Check<br/>검색 문서 근거 확인]
    Evaluator --> Completeness[Completeness Check<br/>질문 완전 답변 확인]
    Evaluator --> Accuracy[Accuracy Check<br/>의학적 정확성 확인]

    Grounding --> Score[종합 품질 점수<br/>grounding * 0.4<br/>+ completeness * 0.4<br/>+ accuracy * 0.2]
    Completeness --> Score
    Accuracy --> Score

    Score --> Feedback[피드백 생성<br/>missing_info: List[str]<br/>improvement_suggestions: List[str]]

    Feedback --> Threshold{quality_score<br/>< 0.5?}

    Threshold -->|예| NeedRewrite[needs_retrieval = True]
    Threshold -->|아니오| NoRewrite[needs_retrieval = False]

    NeedRewrite --> Rewrite[QueryRewriter.rewrite]
    NoRewrite --> End1[refine 완료]

    Rewrite --> NewQuery[재작성된 질의<br/>부족 정보 키워드 추가<br/>사용자 맥락 반영]

    NewQuery --> End2[refine 완료<br/>query_for_retrieval 업데이트]

    Skip --> End3[refine 완료<br/>재검색 없음]

    style CRAG fill:#e1ffe1
    style Evaluator fill:#fff4e1
    style Rewrite fill:#ffe1e1
    style Basic fill:#f0f0f0
```

---

## 3. LLM 기반 품질 평가 상세

```mermaid
sequenceDiagram
    participant R as refine_node
    participant E as QualityEvaluator
    participant L as LLM (GPT-4o-mini)
    participant QR as QueryRewriter

    Note over R: 품질 평가 시작

    R->>E: evaluate(user_query, answer, retrieved_docs)

    E->>E: 평가 프롬프트 생성

    Note over E: 프롬프트 구성<br/>- 사용자 질문<br/>- 생성된 답변<br/>- 검색된 문서 (최대 5개)<br/>- 사용자 프로필<br/>- 이전 피드백 (반복 개선)

    E->>L: generate(prompt, system_prompt)

    L-->>E: JSON 응답<br/>{"grounding_score": 0.6,<br/> "completeness_score": 0.7,<br/> "accuracy_score": 0.8,<br/> "missing_info": ["부작용", "금기사항"],<br/> "improvement_suggestions": [...],<br/> "needs_retrieval": true}

    E->>E: JSON 파싱 및 검증

    E-->>R: quality_feedback

    Note over R: 재검색 필요 판단

    R->>QR: rewrite(original_query, quality_feedback, ...)

    QR->>QR: 재작성 프롬프트 생성<br/>- 원본 질의<br/>- 부족한 정보<br/>- 개선 제안<br/>- 사용자 프로필

    QR->>L: generate(rewrite_prompt)

    L-->>QR: 재작성된 질의<br/>"당뇨병 환자(60세, 신장 기능 저하)에게<br/> 메트포르민의 부작용(설사, 구토, 유산증)<br/> 및 금기사항(신부전, 심부전) 포함 설명"

    QR-->>R: new_query

    R-->>R: state 업데이트<br/>query_for_retrieval = new_query
```

---

## 4. Quality Check Node (2중 안전장치)

```mermaid
flowchart TB
    QC[quality_check_node] --> CheckEnabled{self_refine_enabled<br/>AND<br/>quality_check_enabled?}

    CheckEnabled -->|아니오| End1([종료])
    CheckEnabled -->|예| GetStrategy[RefineStrategyFactory.create]

    GetStrategy --> Strategy{전략 타입}

    Strategy -->|CorrectiveRAG| Check[should_retrieve 확인]
    Strategy -->|BasicRAG| End2([종료<br/>재검색 없음])

    Check --> NeedsRetrieval{needs_retrieval<br/>AND<br/>iteration < max?}

    NeedsRetrieval -->|아니오| End3([종료])
    NeedsRetrieval -->|예| Safety1{안전장치 1<br/>중복 문서 감지}

    Safety1 -->|중복 80% 이상| End4([조기 종료<br/>동일 문서 재검색])
    Safety1 -->|통과| Safety2{안전장치 2<br/>품질 진행도 모니터링}

    Safety2 -->|개선 < 5%| End5([조기 종료<br/>품질 정체])
    Safety2 -->|개선 하락| End6([조기 종료<br/>품질 하락])
    Safety2 -->|통과| Retrieve([retrieve로 분기<br/>재검색 수행])

    style Safety1 fill:#f8d7da
    style Safety2 fill:#f8d7da
    style End4 fill:#ffc107
    style End5 fill:#ffc107
    style End6 fill:#dc3545
```

---

## 5. 2중 안전장치 상세

### 5.1 안전장치 1: 중복 문서 재검색 방지

```mermaid
flowchart LR
    A[현재 iteration<br/>retrieved_docs] --> B[문서 해시 계산<br/>MD5]
    B --> C[retrieved_docs_history<br/>에 추가]

    C --> D{이전 iteration<br/>존재?}
    D -->|아니오| E[중복 아님<br/>계속 진행]
    D -->|예| F[Jaccard Similarity<br/>계산]

    F --> G{similarity<br/>≥ 0.8?}
    G -->|예| H[중복 감지<br/>조기 종료]
    G -->|아니오| E

    style H fill:#dc3545
    style E fill:#28a745
```

**수식**:
```
Jaccard Similarity = |현재 문서 ∩ 이전 문서| / |현재 문서 ∪ 이전 문서|

중복 조건: Similarity ≥ 0.8 (80% 이상 중복)
```

---

### 5.2 안전장치 2: 품질 점수 진행도 모니터링

```mermaid
flowchart LR
    A[quality_score_history] --> B[최근 2개 점수 비교]

    B --> C[improvement<br/>= current - previous]

    C --> D{improvement<br/>< 0.05?}
    D -->|예| E[정체 감지<br/>조기 종료]
    D -->|아니오| F{improvement<br/>< 0?}

    F -->|예| G[품질 하락<br/>조기 종료]
    F -->|아니오| H[품질 개선<br/>계속 진행]

    style E fill:#ffc107
    style G fill:#dc3545
    style H fill:#28a745
```

**조건**:
```
정체: improvement < 0.05 (5% 미만 개선)
하락: improvement < 0 (품질 점수 감소)
개선: improvement ≥ 0.05 (5% 이상 개선)
```

---

## 6. Iteration별 상태 추적

```mermaid
graph TB
    subgraph "Iteration 1 (초기 검색)"
        I1S[iteration_count = 0] --> I1R[retrieve]
        I1R --> I1A[assemble_context]
        I1A --> I1G[generate_answer]
        I1G --> I1Ref[refine]
        I1Ref --> I1Q[quality_score = 0.45<br/>needs_retrieval = True]
    end

    subgraph "Iteration 2 (재검색 1)"
        I2S[iteration_count = 1] --> I2Rew[query_rewriter<br/>부족 정보 추가]
        I2Rew --> I2R[retrieve<br/>재검색]
        I2R --> I2A[assemble_context<br/>재조립]
        I2A --> I2G[generate_answer]
        I2G --> I2Ref[refine]
        I2Ref --> I2Q[quality_score = 0.68<br/>improvement = +0.23]
        I2Q --> I2Safe[안전장치 통과<br/>needs_retrieval = True]
    end

    subgraph "Iteration 3 (재검색 2)"
        I3S[iteration_count = 2] --> I3Rew[query_rewriter]
        I3Rew --> I3R[retrieve]
        I3R --> I3A[assemble_context]
        I3A --> I3G[generate_answer]
        I3G --> I3Ref[refine]
        I3Ref --> I3Q[quality_score = 0.71<br/>improvement = +0.03]
        I3Q --> I3Safe{안전장치 2<br/>개선 < 5%}
        I3Safe -->|정체 감지| I3End[조기 종료]
    end

    I1Q --> I2S
    I2Safe --> I3S

    style I1Q fill:#f8d7da
    style I2Q fill:#fff3cd
    style I3Q fill:#fff3cd
    style I3End fill:#ffc107
```

---

## 7. 성능 비교: BasicRAG vs CorrectiveRAG

```mermaid
graph LR
    subgraph "BasicRAG (Baseline)"
        B1[generate_answer] --> B2[refine<br/>quality_score = 1.0<br/>needs_retrieval = False]
        B2 --> B3[quality_check<br/>항상 종료]
        B3 --> B4([END])
    end

    subgraph "CorrectiveRAG (CRAG)"
        C1[generate_answer] --> C2[refine<br/>LLM 품질 평가<br/>동적 질의 재작성]
        C2 --> C3{quality_check<br/>2중 안전장치}
        C3 -->|품질 낮음| C4[retrieve<br/>재검색]
        C3 -->|품질 충족| C5([END])
        C4 --> C1
    end

    style B2 fill:#f0f0f0
    style B3 fill:#f0f0f0
    style C2 fill:#e1ffe1
    style C3 fill:#ffe1f5
```

**성능 지표 (예상)**:

| 지표 | BasicRAG | CorrectiveRAG | 개선률 |
|------|----------|---------------|--------|
| 품질 점수 | 0.52 | 0.78 | +50% |
| Grounding 점수 | 0.40 | 0.85 | +113% |
| Iteration 수 | 1.0 | 1.9 | +90% |
| LLM 호출 수 | 1.5 | 2.6 | +73% |
| 무한 루프율 | N/A | 0% | - |

---

## 8. Ablation Study 프로파일

```mermaid
graph TB
    AB[Ablation Study] --> P1[baseline<br/>BasicRAG]
    AB --> P2[self_refine_heuristic<br/>휴리스틱 평가만]
    AB --> P3[self_refine_llm_quality<br/>LLM 평가<br/>정적 질의]
    AB --> P4[self_refine_dynamic_query<br/>LLM 평가<br/>동적 질의]
    AB --> P5[self_refine_full_safety<br/>LLM 평가<br/>동적 질의<br/>2중 안전장치]
    AB --> P6[full_context_engineering<br/>모든 기능 활성화]

    style P1 fill:#f0f0f0
    style P2 fill:#fff3cd
    style P3 fill:#d4edda
    style P4 fill:#d4edda
    style P5 fill:#d4edda
    style P6 fill:#28a745,color:#fff
```

---

**다이어그램 생성일**: 2025-12-12
**버전**: 2.0 (Strategy Pattern 포함)
