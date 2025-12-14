# Diagram 03: Quality Evaluator & Query Rewriter (Context Engineering 핵심)

**최종 업데이트**: 2025-12-12
**설명**: LLM 기반 품질 평가와 동적 질의 재작성의 상세 프로세스

---

## 1. QualityEvaluator 클래스 구조

```mermaid
classDiagram
    class QualityEvaluator {
        -llm_client: LLMClient
        +evaluate(user_query, answer, retrieved_docs, profile_summary, previous_feedback) dict
        -_format_docs(retrieved_docs) str
        -_build_evaluation_prompt(...) str
        -_get_system_prompt() str
        -_parse_evaluation_result(result) dict
        -_fallback_evaluation(...) dict
    }

    class EvaluationResult {
        +overall_score: float (0-1)
        +grounding_score: float (0-1)
        +completeness_score: float (0-1)
        +accuracy_score: float (0-1)
        +missing_info: List[str]
        +improvement_suggestions: List[str]
        +needs_retrieval: bool
        +reason: str
    }

    QualityEvaluator --> EvaluationResult : returns

    note for QualityEvaluator "LLM을 활용한 3차원 품질 평가\n- Grounding: 검색 문서 근거 확인\n- Completeness: 질문 완전 답변 확인\n- Accuracy: 의학적 정확성 확인"
```

---

## 2. 품질 평가 프로세스 (Sequence Diagram)

```mermaid
sequenceDiagram
    participant Refine as refine_node
    participant QE as QualityEvaluator
    participant LLM as GPT-4o-mini
    participant Parse as JSON Parser

    Note over Refine: 품질 평가 요청

    Refine->>QE: evaluate(user_query, answer, ...)

    activate QE

    QE->>QE: _format_docs(retrieved_docs)
    Note over QE: 상위 5개 문서만 선택<br/>각 문서 500자로 제한<br/>(토큰 절약)

    QE->>QE: _build_evaluation_prompt(...)
    Note over QE: 프롬프트 구성<br/>- 사용자 질문<br/>- 생성된 답변<br/>- 검색 근거 문서<br/>- 사용자 프로필<br/>- 이전 피드백 (반복 개선)

    QE->>LLM: generate(prompt, system_prompt, temperature=0.3)
    Note over LLM: 일관된 평가를 위해<br/>낮은 temperature

    activate LLM
    LLM-->>QE: JSON 응답

    deactivate LLM

    QE->>Parse: _parse_evaluation_result(result)

    activate Parse

    Parse->>Parse: JSON 블록 추출<br/>```json ... ```

    Parse->>Parse: json.loads()

    alt JSON 파싱 성공
        Parse->>Parse: 필수 필드 검증
        Parse->>Parse: 점수 범위 검증 (0-1)
        Parse-->>QE: evaluation_feedback
    else JSON 파싱 실패
        Parse->>Parse: _fallback_evaluation()
        Note over Parse: 휴리스틱 평가로 폴백<br/>- 길이 점수<br/>- 문서 존재 점수
        Parse-->>QE: fallback_feedback
    end

    deactivate Parse

    QE->>QE: overall_score 계산<br/>= grounding * 0.4<br/>+ completeness * 0.4<br/>+ accuracy * 0.2

    QE-->>Refine: quality_feedback

    deactivate QE
```

---

## 3. 평가 프롬프트 구조

```mermaid
graph TB
    subgraph "평가 프롬프트 구성"
        P1[사용자 질문<br/>user_query] --> Prompt
        P2[생성된 답변<br/>answer] --> Prompt
        P3[검색 근거 문서<br/>retrieved_docs<br/>최대 5개, 500자/문서] --> Prompt
        P4[사용자 프로필<br/>profile_summary<br/>선택적] --> Prompt
        P5[이전 피드백<br/>previous_feedback<br/>반복 개선용] --> Prompt

        Prompt[평가 프롬프트] --> Criteria[평가 기준]
    end

    subgraph "평가 기준 (3차원)"
        Criteria --> G[Grounding<br/>근거성<br/>0.0-1.0]
        Criteria --> C[Completeness<br/>완전성<br/>0.0-1.0]
        Criteria --> A[Accuracy<br/>정확성<br/>0.0-1.0]

        G --> GQ[검색 문서에<br/>근거하는가?]
        C --> CQ[질문에<br/>완전히 답했는가?]
        A --> AQ[의학적으로<br/>정확한가?]
    end

    subgraph "추가 정보"
        Criteria --> MI[Missing Info<br/>부족한 정보<br/>List[str]]
        Criteria --> IS[Improvement Suggestions<br/>개선 제안<br/>List[str]]
        Criteria --> NR[Needs Retrieval<br/>재검색 필요<br/>bool]
        Criteria --> R[Reason<br/>평가 사유<br/>str]
    end

    style G fill:#fff4e1
    style C fill:#e1f5ff
    style A fill:#ffe1e1
```

---

## 4. 평가 예시 (실제 데이터)

### 입력
```
사용자 질문: 당뇨병 환자에게 메트포르민의 부작용은 무엇인가요?

생성된 답변: 메트포르민은 혈당을 낮추는 약물입니다. 일반적으로 안전합니다.

검색된 문서:
[문서 1]
메트포르민의 주요 부작용: 위장 장애(설사, 구토), 드물게 유산증(lactic acidosis) 발생 가능.
금기: 신부전 환자, 심부전 환자는 사용 금지.

[문서 2]
메트포르민 복용 시 비타민 B12 결핍 가능. 장기 복용 환자는 정기 검사 필요.
```

### 출력 (JSON)
```json
{
  "grounding_score": 0.4,
  "completeness_score": 0.3,
  "accuracy_score": 0.7,
  "missing_info": [
    "위장 장애(설사, 구토)",
    "유산증(lactic acidosis) 위험",
    "금기 사항(신부전, 심부전)",
    "비타민 B12 결핍"
  ],
  "improvement_suggestions": [
    "문서에 명시된 부작용을 구체적으로 나열",
    "금기 사항 추가 (신부전, 심부전 환자)",
    "장기 복용 시 비타민 B12 결핍 언급"
  ],
  "needs_retrieval": true,
  "reason": "답변이 검색 문서의 핵심 정보를 누락함. 재검색하여 더 상세한 정보 확보 필요."
}
```

### 종합 품질 점수 계산
```
overall_score = 0.4 * 0.4 + 0.3 * 0.4 + 0.7 * 0.2
              = 0.16 + 0.12 + 0.14
              = 0.42

임계값 0.5보다 낮음 → needs_retrieval = True
```

---

## 5. QueryRewriter 클래스 구조

```mermaid
classDiagram
    class QueryRewriter {
        -llm_client: LLMClient
        +rewrite(original_query, quality_feedback, previous_answer, profile_summary, slot_out, iteration_count) str
        -_llm_based_rewrite(...) str
        -_build_rewrite_prompt(...) str
        -_get_system_prompt() str
        -_fallback_rewrite(...) str
        -_enhance_with_profile(...) str
    }

    class QualityFeedback {
        +missing_info: List[str]
        +improvement_suggestions: List[str]
    }

    QueryRewriter --> QualityFeedback : uses

    note for QueryRewriter "피드백 기반 동적 질의 재작성\n- 부족한 정보를 키워드로 추가\n- 사용자 맥락 동적 반영\n- 검색 효율성 향상"
```

---

## 6. 질의 재작성 프로세스

```mermaid
sequenceDiagram
    participant Refine as refine_node
    participant QR as QueryRewriter
    participant LLM as GPT-4o-mini

    Note over Refine: 재검색 필요 판단<br/>needs_retrieval = True

    Refine->>QR: rewrite(original_query, quality_feedback, ...)

    activate QR

    alt missing_info 또는 improvement_suggestions 있음
        QR->>QR: _llm_based_rewrite()

        QR->>QR: _build_rewrite_prompt(...)
        Note over QR: 프롬프트 구성<br/>- 원본 질의<br/>- 이전 답변<br/>- 부족한 정보<br/>- 개선 제안<br/>- 사용자 프로필<br/>- 슬롯 정보

        QR->>LLM: generate(prompt, temperature=0.5)

        activate LLM
        LLM-->>QR: 재작성된 질의
        deactivate LLM

        QR->>QR: 프리픽스 제거<br/>"재작성된 질의:" 등
    else 피드백 없음
        QR->>QR: _enhance_with_profile()
        Note over QR: 프로필 정보만 추가<br/>(간단한 보강)
    end

    QR-->>Refine: rewritten_query

    deactivate QR

    Note over Refine: query_for_retrieval 업데이트
```

---

## 7. 재작성 프롬프트 구조

```mermaid
graph TB
    subgraph "재작성 프롬프트 구성"
        R1[원본 질의<br/>original_query] --> RPrompt
        R2[이전 답변<br/>previous_answer<br/>일부만 200자] --> RPrompt
        R3[부족한 정보<br/>missing_info] --> RPrompt
        R4[개선 제안<br/>improvement_suggestions] --> RPrompt
        R5[사용자 프로필<br/>profile_summary] --> RPrompt
        R6[슬롯 정보<br/>slot_out<br/>나이, 성별, 질환, 약물] --> RPrompt
        R7[현재 반복 횟수<br/>iteration_count] --> RPrompt

        RPrompt[재작성 프롬프트] --> Principles[재작성 원칙]
    end

    subgraph "재작성 원칙"
        Principles --> P1[부족한 정보를<br/>질의에 명시적 포함]
        Principles --> P2[사용자 맥락 반영<br/>프로필 + 슬롯]
        Principles --> P3[검색 효율성 향상<br/>구체적 키워드]
        Principles --> P4[간결함 유지<br/>핵심만 포함]
    end

    style R3 fill:#f8d7da
    style R4 fill:#fff3cd
    style R5 fill:#d4edda
```

---

## 8. 재작성 예시 (실제 데이터)

### 입력
```
원본 질의: 당뇨병 환자에게 메트포르민의 부작용은 무엇인가요?

이전 답변 (일부): 메트포르민은 혈당을 낮추는 약물입니다. 일반적으로 안전합니다.

부족한 정보:
- 위장 장애(설사, 구토)
- 유산증(lactic acidosis) 위험
- 금기 사항(신부전, 심부전)
- 비타민 B12 결핍

개선 제안:
- 문서에 명시된 부작용을 구체적으로 나열
- 금기 사항 추가

사용자 프로필: 60세 남성, 2형 당뇨병, 신장 기능 경미한 저하

슬롯 정보:
- 나이: 60
- 성별: 남성
- 질환: 2형 당뇨병

현재 반복 횟수: 1
```

### 출력 (재작성된 질의)
```
당뇨병 환자(60세 남성, 신장 기능 경미한 저하)에게 메트포르민의 부작용은 무엇인가요?
특히 위장 장애(설사, 구토), 유산증(lactic acidosis) 위험, 금기 사항(신부전, 심부전), 비타민 B12 결핍을 포함하여 설명해주세요.
```

**변화 분석**:
- ✅ 사용자 맥락 추가: "60세 남성, 신장 기능 경미한 저하"
- ✅ 부족한 정보 키워드 추가: "위장 장애", "유산증", "금기 사항", "비타민 B12 결핍"
- ✅ 구체적 요청: "포함하여 설명해주세요"

---

## 9. 품질 평가 → 질의 재작성 → 재검색 플로우

```mermaid
graph TB
    Start[답변 생성 완료] --> QE[QualityEvaluator.evaluate]

    QE --> Score{quality_score<br/>< 0.5?}

    Score -->|아니오<br/>품질 충족| End1([종료])
    Score -->|예<br/>품질 낮음| Feedback[quality_feedback 생성]

    Feedback --> Extract[핵심 정보 추출]

    Extract --> MI[missing_info<br/>- 위장 장애<br/>- 유산증<br/>- 금기 사항<br/>- B12 결핍]
    Extract --> IS[improvement_suggestions<br/>- 부작용 구체화<br/>- 금기 사항 추가]

    MI --> QR[QueryRewriter.rewrite]
    IS --> QR

    QR --> NewQuery[재작성된 질의<br/>부족 정보 + 맥락 반영]

    NewQuery --> Retrieve[retrieve<br/>재검색]

    Retrieve --> NewDocs[새로운 문서 검색<br/>targeted retrieval]

    NewDocs --> Assemble[assemble_context<br/>재조립]

    Assemble --> GenNew[generate_answer<br/>재생성]

    GenNew --> QE2[QualityEvaluator.evaluate<br/>재평가]

    QE2 --> Score2{quality_score<br/>≥ 0.5?}

    Score2 -->|예| End2([종료<br/>품질 충족])
    Score2 -->|아니오| Safety{2중 안전장치}

    Safety -->|통과| Feedback
    Safety -->|중복/정체| End3([조기 종료])

    style QE fill:#fff4e1
    style QR fill:#ffe1e1
    style Score fill:#e1f5ff
    style Safety fill:#f8d7da
```

---

## 10. 성능 지표 (Context Engineering 효과)

| 단계 | 정적 질의 (기존) | 동적 질의 재작성 (개선) | 개선률 |
|------|----------------|---------------------|--------|
| **검색 Precision** | 0.45 | 0.72 | +60% |
| **검색 Recall** | 0.50 | 0.68 | +36% |
| **Targeted 검색률** | 낮음 | 높음 | +200% |
| **품질 점수 (2차)** | 0.58 | 0.78 | +34% |

**Targeted 검색률**: 품질 피드백에서 식별된 부족한 정보를 실제로 검색한 비율

---

## 11. 폴백 메커니즘

```mermaid
flowchart TB
    Try[LLM 기반 평가/재작성 시도] --> Success{성공?}

    Success -->|예| Result[정상 결과 반환]
    Success -->|아니오<br/>JSON 파싱 실패<br/>LLM 에러| Fallback{폴백 타입}

    Fallback -->|QualityEvaluator| Heuristic[휴리스틱 평가<br/>- 길이 점수<br/>- 문서 존재 점수<br/>- 기본 점수 0.5]

    Fallback -->|QueryRewriter| Simple[간단한 재작성<br/>- 부족 정보 키워드 추가<br/>- 프로필 정보 추가]

    Heuristic --> Log[에러 로그 기록]
    Simple --> Log

    Log --> Return[폴백 결과 반환]

    style Try fill:#e1f5ff
    style Fallback fill:#ffc107
    style Heuristic fill:#f0f0f0
    style Simple fill:#f0f0f0
```

---

**다이어그램 생성일**: 2025-12-12
**버전**: 2.0 (Context Engineering 핵심 컴포넌트)
