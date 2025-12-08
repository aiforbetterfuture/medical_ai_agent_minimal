# Medical AI Agent 아키텍처 다이어그램

이 문서는 현재 스캐폴드의 LangGraph 기반 구조와 Corrective RAG (CRAG) 메커니즘을 시각화합니다.

---

## CRAG 내부 루프 vs LangGraph 외부 루프 (요약)
- **외부 루프 (LangGraph 매크로 플로우)**: `extract_slots → store_memory → assemble_context → retrieve → generate_answer → refine → quality_check` 순서로 세션 상태를 관리하며 멀티턴 컨텍스트, 메모리, 라우팅을 담당합니다.
- **내부 루프 (CRAG Self-Refine 마이크로 루프)**: `generate_answer → refine → quality_check → retrieve`의 반복으로 단일 턴 품질을 보정합니다. 기능 플래그로 on/off하며 최대 반복 수를 제한합니다.
- **실험용 기능 플래그** (`config/agent_config.yaml`):
  - `self_refine_enabled`: 내부 루프 on/off
  - `max_refine_iterations`: 내부 루프 반복 한계
  - `dynamic_rag_routing`: 질문 유형별 인덱스 라우팅 on/off
  - `medcat2_enabled`: MedCAT2 기반 사용자 정보 추출 on/off
  - `memory_mode`: `structured`(기본) / `none` (메모리 미사용 ablation)
  - `query_rewrite_enabled`: 슬롯·프로필을 반영한 질의 재작성 on/off
- **라벨과 코드 연결**:
  - 매크로 플로우: `agent/graph.py`, `agent/nodes/*`
  - 마이크로 루프: `refine_node` + `quality_check_node`에서 반복 제어
  - 라우팅·재작성: `retrieve_node`에서 슬롯 기반 라우팅 + 질의 재작성
  - 메모리: `store_memory_node` + `memory/profile_store.py` (구조화 슬롯)

---

## 1. 전체 워크플로우 (LangGraph 노드 및 엣지)

```mermaid
graph TD
    START([사용자 입력<br/>user_text]) --> EXTRACT[extract_slots<br/>슬롯 추출]
    
    EXTRACT -->|slot_out| STORE[store_memory<br/>메모리 저장]
    STORE -->|profile_summary| ASSEMBLE[assemble_context<br/>컨텍스트 조립]
    ASSEMBLE -->|system_prompt<br/>user_prompt| RETRIEVE[retrieve<br/>하이브리드 검색]
    
    RETRIEVE -->|retrieved_docs<br/>query_vector| GENERATE[generate_answer<br/>LLM 답변 생성]
    GENERATE -->|answer| REFINE[refine<br/>Self-Refine 품질 검증]
    
    REFINE -->|quality_score<br/>needs_retrieval| QUALITY{quality_check<br/>품질 검사}
    
    QUALITY -->|품질 낮음<br/>iteration_count < 2| RETRIEVE
    QUALITY -->|품질 양호<br/>또는 iteration_count >= 2| END([최종 답변<br/>answer])
    
    style START fill:#e1f5ff
    style END fill:#d4edda
    style QUALITY fill:#fff3cd
    style RETRIEVE fill:#f8d7da
    style REFINE fill:#d1ecf1
```

---

## 2. Corrective RAG (CRAG) 순환 구조 상세

```mermaid
graph LR
    subgraph "1차 검색 및 생성"
        R1[retrieve<br/>하이브리드 검색] --> G1[generate_answer<br/>답변 생성]
        G1 --> RF1[refine<br/>품질 평가]
    end
    
    subgraph "품질 검증 루프"
        RF1 --> QC{quality_check<br/>품질 검사}
        QC -->|quality_score < 0.5<br/>needs_retrieval = True<br/>iteration_count < 2| R2[retrieve<br/>재검색]
        QC -->|quality_score >= 0.5<br/>또는 iteration_count >= 2| END2[END<br/>답변 반환]
        R2 --> G2[generate_answer<br/>재생성]
        G2 --> RF2[refine<br/>재평가]
        RF2 --> QC
    end
    
    style QC fill:#fff3cd
    style R2 fill:#f8d7da
    style END2 fill:#d4edda
```

---

## 3. AgentState 상태 흐름

```mermaid
stateDiagram-v2
    [*] --> InitialState
    
    state InitialState {
        [*] --> State1
        note right of State1
            user_text, mode
            slot_out = {}
            profile_summary = ''
            retrieved_docs = []
            answer = ''
            quality_score = 0.0
            iteration_count = 0
        end note
    }
    
    InitialState --> ExtractSlots
    state ExtractSlots {
        [*] --> State2
        note right of State2
            slot_out = conditions, symptoms, ...
        end note
    }
    
    ExtractSlots --> StoreMemory
    state StoreMemory {
        [*] --> State3
        note right of State3
            profile_summary = 환자 정보 요약
        end note
    }
    
    StoreMemory --> AssembleContext
    state AssembleContext {
        [*] --> State4
        note right of State4
            system_prompt
            user_prompt
        end note
    }
    
    AssembleContext --> Retrieve
    state Retrieve {
        [*] --> State5
        note right of State5
            retrieved_docs = [...]
            query_vector = [...]
        end note
    }
    
    Retrieve --> GenerateAnswer
    state GenerateAnswer {
        [*] --> State6
        note right of State6
            answer = 생성된 답변
        end note
    }
    
    GenerateAnswer --> Refine
    state Refine {
        [*] --> State7
        note right of State7
            quality_score = 0.0~1.0
            needs_retrieval = bool
        end note
    }
    
    Refine --> QualityCheck
    state QualityCheck {
        [*] --> State8
    }
    
    QualityCheck --> Retrieve: 재검색 필요
    QualityCheck --> [*]: 품질 양호 또는 최대 반복
```

---

## 4. 하이브리드 검색 구조 (retrieve 노드 내부)

### 4.1 전체 하이브리드 검색 파이프라인

```mermaid
graph TB
    QUERY[사용자 질의<br/>user_text] --> PARALLEL{병렬 검색 실행}
    
    subgraph BM25["BM25 키워드 검색 파이프라인"]
        Q1[질의 텍스트] --> T1["토큰화<br/>tokenize_ko_en<br/>한국어/영어 혼용"]
        T1 --> B1["BM25 점수 계산<br/>BM25Okapi.get_scores<br/>O(n*m)"]
        B1 --> R1["상위 k개 선택<br/>heapq.nlargest<br/>O(n log k)"]
        R1 --> RES1["BM25 결과<br/>List[Dict]<br/>각 문서: score, rank"]
    end
    
    subgraph FAISS["FAISS 벡터 검색 파이프라인"]
        Q2[질의 텍스트] --> E1["임베딩 생성<br/>OpenAI API<br/>text-embedding-3-small<br/>1536차원"]
        E1 --> V1["쿼리 벡터<br/>List[float]"]
        V1 --> F1["FAISS 검색<br/>IndexFlatIP.search<br/>Inner Product"]
        F1 --> F2["메타데이터 결합<br/>인덱스 -> 문서 텍스트"]
        F2 --> RES2["FAISS 결과<br/>List[Dict]<br/>각 문서: score, rank"]
    end
    
    QUERY --> Q1
    QUERY --> Q2
    
    RES1 --> FUSION["RRF 융합<br/>Reciprocal Rank Fusion<br/>RRF_score = sum(1/(rank + k))"]
    RES2 --> FUSION
    
    FUSION --> SORT["점수 기준 정렬<br/>내림차순"]
    SORT --> FINAL["최종 검색 결과<br/>상위 k개 문서<br/>각 문서: rrf_score 포함"]
    
    style PARALLEL fill:#e1f5ff
    style FUSION fill:#fff3cd
    style FINAL fill:#d4edda
```

### 4.2 BM25 검색 상세 프로세스

```mermaid
graph LR
    subgraph CORPUS["1. 코퍼스 로드"]
        JSONL["JSONL 파일<br/>train_questions.index.jsonl"] --> LOAD["문서 로드<br/>각 라인 JSON 파싱"]
        LOAD --> EXTRACT["텍스트 추출<br/>doc.get('text')"]
    end
    
    subgraph INDEX["2. 인덱스 구축"]
        EXTRACT --> TOKEN["토큰화<br/>tokenize_ko_en<br/>정규표현식"]
        TOKEN --> BUILD["BM25Okapi 인덱스<br/>토큰 빈도 계산<br/>IDF 계산"]
    end
    
    subgraph SEARCH["3. 검색 실행"]
        QUERY[사용자 질의] --> QTOKEN[쿼리 토큰화]
        QTOKEN --> SCORE["BM25 점수 계산<br/>모든 문서에 대해<br/>BM25(q, d) 공식"]
        SCORE --> TOPK["상위 k개 선택<br/>heapq.nlargest<br/>최적화: O(n log k)"]
        TOPK --> RESULT["검색 결과<br/>문서 + 점수 + 순위"]
    end
    
    BUILD --> SCORE
    
    style BUILD fill:#d1ecf1
    style SCORE fill:#fff3cd
    style TOPK fill:#f8d7da
```

### 4.3 FAISS 검색 상세 프로세스

```mermaid
graph LR
    subgraph PREP["1. 인덱스 준비"]
        FAISS_FILE["FAISS 인덱스 파일<br/>.faiss 파일"] --> LOAD_IDX["인덱스 로드<br/>faiss.read_index"]
        META_FILE["메타데이터 파일<br/>.meta.jsonl"] --> LOAD_META["메타데이터 로드<br/>문서 텍스트 매핑"]
        LOAD_IDX --> READY["인덱스 준비 완료<br/>IndexFlatIP<br/>Inner Product 메트릭"]
        LOAD_META --> READY
    end
    
    subgraph EMBED["2. 임베딩 생성"]
        QUERY[사용자 질의] --> API["OpenAI Embedding API<br/>text-embedding-3-small"]
        API --> VECTOR["1536차원 벡터<br/>List[float]"]
    end
    
    subgraph VSEARCH["3. 벡터 검색"]
        VECTOR --> NP["NumPy 배열 변환<br/>np.array, float32"]
        NP --> SEARCH["FAISS 검색<br/>index.search<br/>Inner Product 계산"]
        SEARCH --> INDICES["상위 k개 인덱스<br/>+ 유사도 점수"]
        INDICES --> META["메타데이터 조회<br/>인덱스 -> 문서 텍스트"]
        META --> RESULT["검색 결과<br/>문서 + 점수 + 순위"]
    end
    
    READY --> SEARCH
    
    style API fill:#e1f5ff
    style SEARCH fill:#fff3cd
    style RESULT fill:#d4edda
```

### 4.4 RRF 융합 알고리즘 상세

```mermaid
graph TD
    INPUT["검색 결과 리스트<br/>BM25_results, FAISS_results"] --> INIT["문서별 점수 딕셔너리 초기화<br/>doc_scores = {}"]
    
    INIT --> LOOP1[각 검색 결과 리스트 순회]
    
    LOOP1 --> LOOP2["각 문서 순회<br/>rank, doc"]
    
    LOOP2 --> CHECK{"문서 ID<br/>이미 존재?"}
    
    CHECK -->|No| CREATE["새 항목 생성<br/>doc_scores[doc_id]"]
    CHECK -->|Yes| EXIST[기존 항목 사용]
    
    CREATE --> CALC["RRF 점수 계산<br/>score += 1 / (rank + k)<br/>k = 60"]
    EXIST --> CALC
    
    CALC --> NEXT{"다음 문서?"}
    NEXT -->|Yes| LOOP2
    NEXT -->|No| NEXT_LIST{"다음 리스트?"}
    
    NEXT_LIST -->|Yes| LOOP1
    NEXT_LIST -->|No| SORT["점수 기준 정렬<br/>내림차순"]
    
    SORT --> TOPK[상위 k개 선택]
    TOPK --> OUTPUT["융합된 결과<br/>각 문서: rrf_score 포함"]
    
    style CALC fill:#fff3cd
    style SORT fill:#f8d7da
    style OUTPUT fill:#d4edda
```

### 4.5 RRF 점수 계산 예시

```mermaid
graph LR
    subgraph INPUTS["입력: 두 검색 결과"]
        BM25["BM25 결과<br/>문서 A: rank 1<br/>문서 B: rank 3<br/>문서 C: rank 5"]
        FAISS["FAISS 결과<br/>문서 A: rank 2<br/>문서 B: rank 1<br/>문서 D: rank 3"]
    end
    
    subgraph CALCS["RRF 점수 계산 (k=60)"]
        CALC1["문서 A<br/>RRF = 1/(1+60) + 1/(2+60)<br/>= 0.0164 + 0.0161<br/>= 0.0325"]
        CALC2["문서 B<br/>RRF = 1/(3+60) + 1/(1+60)<br/>= 0.0159 + 0.0164<br/>= 0.0323"]
        CALC3["문서 C<br/>RRF = 1/(5+60)<br/>= 0.0154"]
        CALC4["문서 D<br/>RRF = 1/(3+60)<br/>= 0.0159"]
    end
    
    subgraph RANKS["최종 순위"]
        RANK1["1위: 문서 A<br/>RRF = 0.0325"]
        RANK2["2위: 문서 B<br/>RRF = 0.0323"]
        RANK3["3위: 문서 D<br/>RRF = 0.0159"]
        RANK4["4위: 문서 C<br/>RRF = 0.0154"]
    end
    
    BM25 --> CALC1
    BM25 --> CALC2
    BM25 --> CALC3
    FAISS --> CALC1
    FAISS --> CALC2
    FAISS --> CALC4
    
    CALC1 --> RANK1
    CALC2 --> RANK2
    CALC4 --> RANK3
    CALC3 --> RANK4
    
    style CALC1 fill:#fff3cd
    style RANK1 fill:#d4edda
```

---

## 5. 모드별 분기 처리 (LLM vs AI Agent)

```mermaid
graph TD
    INPUT[사용자 입력<br/>+ mode 선택] --> MODE_CHECK{mode == 'llm'?}
    
    MODE_CHECK -->|Yes: LLM 모드| LLM_FLOW[LLM 모드 워크플로우]
    MODE_CHECK -->|No: AI Agent 모드| AGENT_FLOW[AI Agent 모드 워크플로우]
    
    subgraph "LLM 모드 (간소화)"
        LLM_FLOW --> LLM_SKIP1[extract_slots<br/>건너뛰기]
        LLM_SKIP1 --> LLM_SKIP2[store_memory<br/>건너뛰기]
        LLM_SKIP2 --> LLM_SKIP3[retrieve<br/>건너뛰기]
        LLM_SKIP3 --> LLM_ASSEMBLE[assemble_context<br/>간단한 프롬프트]
        LLM_ASSEMBLE --> LLM_GEN[generate_answer<br/>원문 그대로 출력]
        LLM_GEN --> LLM_REFINE[refine<br/>품질 검증 건너뛰기]
        LLM_REFINE --> LLM_END[END<br/>즉시 종료]
    end
    
    subgraph "AI Agent 모드 (전체 워크플로우)"
        AGENT_FLOW --> AGENT_EXTRACT[extract_slots<br/>슬롯 추출]
        AGENT_EXTRACT --> AGENT_STORE[store_memory<br/>메모리 저장]
        AGENT_STORE --> AGENT_ASSEMBLE[assemble_context<br/>컨텍스트 조립]
        AGENT_ASSEMBLE --> AGENT_RETRIEVE[retrieve<br/>하이브리드 검색]
        AGENT_RETRIEVE --> AGENT_GEN[generate_answer<br/>답변 생성]
        AGENT_GEN --> AGENT_REFINE[refine<br/>품질 검증]
        AGENT_REFINE --> AGENT_QC{quality_check<br/>재검색 결정}
        AGENT_QC -->|재검색| AGENT_RETRIEVE
        AGENT_QC -->|종료| AGENT_END[END]
    end
    
    style MODE_CHECK fill:#fff3cd
    style LLM_END fill:#d4edda
    style AGENT_END fill:#d4edda
```

---

## 6. Context Engineering 4단계 프로세스

```mermaid
graph LR
    subgraph "1. 추출 (Extract)"
        E1[extract_slots<br/>MedCAT2 + 정규표현식] --> E1_OUT[slot_out<br/>conditions, symptoms,<br/>medications, vitals, labs]
    end
    
    subgraph "2. 저장 (Store)"
        S1[store_memory<br/>ProfileStore] --> S1_OUT[profile_summary<br/>환자 정보 요약]
    end
    
    subgraph "3. 주입 (Inject)"
        I1[assemble_context<br/>프롬프트 조립] --> I1_OUT[system_prompt<br/>+ user_prompt<br/>+ retrieved_docs]
    end
    
    subgraph "4. 검증 (Verify)"
        V1[refine<br/>품질 평가] --> V1_OUT[quality_score<br/>needs_retrieval]
        V1_OUT --> V2{quality_check<br/>재검색?}
        V2 -->|Yes| RETRIEVE[retrieve<br/>재검색]
        V2 -->|No| FINAL[최종 답변]
    end
    
    E1_OUT --> S1
    S1_OUT --> I1
    I1_OUT --> V1
    RETRIEVE --> I1
    
    style E1 fill:#e1f5ff
    style S1 fill:#d1ecf1
    style I1 fill:#fff3cd
    style V1 fill:#f8d7da
    style FINAL fill:#d4edda
```

---

## 7. Self-Refine 메커니즘 상세

```mermaid
graph TD
    ANSWER[생성된 답변<br/>answer] --> EVAL[refine 노드<br/>품질 평가]
    
    subgraph "품질 평가 지표"
        EVAL --> LEN[답변 길이 점수<br/>length_score<br/>30% 가중치]
        EVAL --> EVID[근거 문서 점수<br/>evidence_score<br/>40% 가중치]
        EVAL --> PERS[개인화 점수<br/>personalization_score<br/>30% 가중치]
    end
    
    LEN --> CALC[가중 평균 계산<br/>quality_score]
    EVID --> CALC
    PERS --> CALC
    
    CALC --> THRESH{quality_score<br/>< 0.5?}
    
    THRESH -->|Yes| ITER_CHECK{iteration_count<br/>< 2?}
    THRESH -->|No| PASS[품질 양호<br/>needs_retrieval = False]
    
    ITER_CHECK -->|Yes| RETRY[재검색 필요<br/>needs_retrieval = True]
    ITER_CHECK -->|No| MAX[최대 반복 도달<br/>needs_retrieval = False]
    
    RETRY --> RETRIEVE[retrieve 노드로<br/>돌아가기]
    PASS --> END1[END]
    MAX --> END2[END]
    
    style EVAL fill:#d1ecf1
    style THRESH fill:#fff3cd
    style RETRY fill:#f8d7da
    style END1 fill:#d4edda
    style END2 fill:#d4edda
```

---

## 8. 전체 시스템 아키텍처 (고수준)

```mermaid
graph TB
    subgraph "입력 계층"
        USER[사용자<br/>Streamlit UI]
        MODE[모드 선택<br/>llm / ai_agent]
    end
    
    subgraph "LangGraph 워크플로우"
        GRAPH[StateGraph<br/>AgentState]
        
        subgraph "Context Engineering"
            N1[extract_slots]
            N2[store_memory]
            N3[assemble_context]
        end
        
        subgraph "Retrieval"
            N4[retrieve]
        end
        
        subgraph "Generation"
            N5[generate_answer]
        end
        
        subgraph "Self-Refine Loop"
            N6[refine]
            N7[quality_check]
        end
    end
    
    subgraph "외부 서비스"
        LLM[LLM API<br/>OpenAI / Gemini]
        EMBED[Embedding API<br/>text-embedding-3-small]
        BM25_SVC[BM25<br/>키워드 검색]
        FAISS_SVC[FAISS<br/>벡터 검색]
        MEDCAT[MedCAT2<br/>엔티티 추출]
    end
    
    subgraph "데이터 저장소"
        MEMORY[ProfileStore<br/>환자 프로필]
        CORPUS[Corpus<br/>JSONL 파일]
        INDEX[FAISS Index<br/>벡터 인덱스]
    end
    
    USER --> GRAPH
    MODE --> GRAPH
    
    GRAPH --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 -->|재검색| N4
    N7 -->|종료| USER
    
    N1 --> MEDCAT
    N2 --> MEMORY
    N4 --> BM25_SVC
    N4 --> FAISS_SVC
    N4 --> EMBED
    N5 --> LLM
    
    BM25_SVC --> CORPUS
    FAISS_SVC --> INDEX
    
    style GRAPH fill:#e1f5ff
    style N7 fill:#fff3cd
    style USER fill:#d4edda
```

---

## 9. 노드별 입출력 데이터 흐름

```mermaid
graph LR
    subgraph INPUT["입력"]
        IN["user_text: str<br/>mode: str"]
    end
    
    subgraph EXTRACT["extract_slots"]
        E_IN[user_text] --> E["MedCAT2 추출<br/>정규표현식 매칭"]
        E --> E_OUT["slot_out:<br/>conditions, symptoms,<br/>medications, vitals, labs"]
    end
    
    subgraph STORE["store_memory"]
        S_IN[slot_out] --> S["ProfileStore<br/>업데이트"]
        S --> S_OUT["profile_summary:<br/>환자 정보 요약"]
    end
    
    subgraph ASSEMBLE["assemble_context"]
        A_IN1[profile_summary] --> A[프롬프트 조립]
        A_IN2[retrieved_docs] --> A
        A_IN3[user_text] --> A
        A --> A_OUT["system_prompt<br/>user_prompt"]
    end
    
    subgraph RETRIEVE["retrieve"]
        R_IN[user_text] --> R1[임베딩 생성]
        R1 --> R2[BM25 검색]
        R1 --> R3[FAISS 검색]
        R2 --> R4[RRF Fusion]
        R3 --> R4
        R4 --> R_OUT["retrieved_docs:<br/>List[Dict]"]
    end
    
    subgraph GENERATE["generate_answer"]
        G_IN1[system_prompt] --> G[LLM API 호출]
        G_IN2[user_prompt] --> G
        G --> G_OUT["answer: str"]
    end
    
    subgraph REFINE["refine"]
        RF_IN1[answer] --> RF[품질 평가]
        RF_IN2[retrieved_docs] --> RF
        RF_IN3[profile_summary] --> RF
        RF --> RF_OUT["quality_score: float<br/>needs_retrieval: bool"]
    end
    
    subgraph QUALITY["quality_check"]
        QC_IN["quality_score<br/>needs_retrieval<br/>iteration_count"] --> QC{"조건 판단"}
        QC --> QC_OUT1["retrieve<br/>재검색"]
        QC --> QC_OUT2["END<br/>종료"]
    end
    
    IN --> E_IN
    E_OUT --> S_IN
    S_OUT --> A_IN1
    R_OUT --> A_IN2
    A_OUT --> G_IN1
    A_OUT --> G_IN2
    G_OUT --> RF_IN1
    R_OUT --> RF_IN2
    S_OUT --> RF_IN3
    RF_OUT --> QC_IN
    QC_OUT1 --> R_IN
    
    style QC fill:#fff3cd
```

---

## 10. Corrective RAG 루프 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant User
    participant Graph as LangGraph
    participant Retrieve as retrieve_node
    participant Generate as generate_answer_node
    participant Refine as refine_node
    participant Quality as quality_check_node
    participant LLM as LLM API
    
    User->>Graph: user_text 입력
    Graph->>Retrieve: 1차 검색 요청
    
    Retrieve->>Retrieve: BM25 + FAISS 검색
    Retrieve->>Graph: retrieved_docs 반환
    
    Graph->>Generate: 답변 생성 요청
    Generate->>LLM: API 호출 (system_prompt + user_prompt)
    LLM-->>Generate: answer 반환
    Generate->>Graph: answer 반환
    
    Graph->>Refine: 품질 평가 요청
    Refine->>Refine: quality_score 계산
    Note over Refine: length_score (30%)<br/>evidence_score (40%)<br/>personalization_score (30%)
    Refine->>Graph: quality_score, needs_retrieval 반환
    
    Graph->>Quality: 품질 검사 요청
    Quality->>Quality: 재검색 필요 여부 판단
    
    alt quality_score < 0.5 AND iteration_count < 2
        Quality->>Graph: "retrieve" 반환 (재검색)
        Graph->>Retrieve: 2차 검색 요청
        Note over Retrieve: iteration_count 증가
        Retrieve->>Retrieve: 재검색 수행
        Retrieve->>Graph: 새로운 retrieved_docs 반환
        Graph->>Generate: 재생성 요청
        Generate->>LLM: API 호출
        LLM-->>Generate: 새로운 answer 반환
        Generate->>Graph: answer 반환
        Graph->>Refine: 재평가 요청
        Refine->>Graph: quality_score 반환
        Graph->>Quality: 재검사 요청
        Quality->>Graph: "END" 반환
    else quality_score >= 0.5 OR iteration_count >= 2
        Quality->>Graph: "END" 반환
    end
    
    Graph->>User: 최종 answer 반환
```

---

## 11. 하이브리드 검색 상세 설명

본 시스템의 하이브리드 검색에 대한 상세한 기술적 설명은 **`HYBRID_RETRIEVAL_DETAILED.md`** 파일을 참조하세요.

해당 문서에는 다음 내용이 포함되어 있습니다:
- BM25 알고리즘의 수학적 배경 및 구현
- FAISS 벡터 검색의 메커니즘
- RRF 융합 알고리즘의 상세 설명
- 성능 특성 및 복잡도 분석
- 실제 코드 흐름 및 예시

---

## 다이어그램 사용 가이드

### Mermaid 렌더링 방법

1. **GitHub/GitLab**: 마크다운 파일에 자동 렌더링
2. **VS Code**: Mermaid 확장 프로그램 설치
3. **온라인**: [Mermaid Live Editor](https://mermaid.live/)
4. **로컬**: `npm install -g @mermaid-js/mermaid-cli`

### 주요 개념 설명

- **노드 (Node)**: LangGraph의 처리 단위, 각 노드는 AgentState를 받아서 업데이트된 상태를 반환
- **엣지 (Edge)**: 노드 간의 데이터 흐름, 순차적 또는 조건부
- **조건부 엣지**: `quality_check` 노드에서 반환값에 따라 다음 노드 결정
- **순환 구조**: `retrieve → generate → refine → quality_check → retrieve` 루프
- **Self-Refine**: 답변 품질이 낮으면 자동으로 재검색 및 재생성

---

**작성일**: 2025-01-XX  
**버전**: 1.0

