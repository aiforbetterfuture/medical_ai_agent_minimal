# 다이어그램 18: 전체 워크플로우 플로우차트 (10개 노드)

```mermaid
graph TB
    START([사용자 입력<br/>user_text]) --> CACHE[1. check_similarity<br/>응답 캐시 확인<br/>벡터 유사도 >= 0.85?]
    
    CACHE -->|캐시 히트<br/>30%| CACHE_RETURN[캐시된 응답 반환<br/>스타일 변형 적용]
    CACHE -->|캐시 미스<br/>70%| CLASSIFY[2. classify_intent<br/>Active Retrieval<br/>의도 분류]
    
    CLASSIFY -->|인사/단순응답<br/>20%| ASSEMBLE_DIRECT[5. assemble_context<br/>검색 스킵]
    CLASSIFY -->|사실 기반 질문<br/>80%| EXTRACT[3. extract_slots<br/>MedCAT2 + Regex<br/>엔티티 추출]
    
    EXTRACT --> EXTRACT_OUT[slot_out<br/>6개 슬롯]
    EXTRACT_OUT --> STORE[4. store_memory<br/>ProfileStore<br/>시간 가중치 적용]
    
    STORE --> PROFILE[profile_summary<br/>환자 프로필 요약]
    PROFILE --> ASSEMBLE[5. assemble_context<br/>프롬프트 조립]
    ASSEMBLE_DIRECT --> ASSEMBLE_2[5. assemble_context<br/>프로필만 사용]
    
    ASSEMBLE -->|needs_retrieval=True| RETRIEVE[6. retrieve<br/>Hybrid Retrieval<br/>BM25 + FAISS + RRF]
    ASSEMBLE_2 -->|검색 스킵| GEN_DIRECT[7. generate_answer<br/>LLM 호출]
    
    RETRIEVE --> DOCS[retrieved_docs<br/>동적 k개 문서]
    DOCS --> REASSEMBLE[5. assemble_context<br/>재조립<br/>프로필 + 근거]
    
    REASSEMBLE --> GEN[7. generate_answer<br/>LLM 답변 생성]
    GEN_DIRECT --> REFINE_2
    GEN --> REFINE[8. refine<br/>품질 평가<br/>질의 재작성]
    
    REFINE --> QUALITY[quality_score<br/>quality_feedback<br/>query_for_retrieval]
    
    QUALITY --> QC{9. quality_check<br/>재검색 필요?}
    
    QC -->|Score < 0.5<br/>AND<br/>iter < 2| RETRIEVE_AGAIN[6. retrieve<br/>재검색<br/>재작성된 질의 사용]
    
    RETRIEVE_AGAIN --> REASSEMBLE_2[5. assemble_context<br/>새 문서 반영]
    REASSEMBLE_2 --> GEN_2[7. generate_answer<br/>재생성<br/>iteration += 1]
    GEN_2 --> REFINE_2[8. refine<br/>재평가]
    REFINE_2 --> QC
    
    QC -->|Score >= 0.5<br/>OR<br/>iter >= 2<br/>OR<br/>안전장치 트리거| STORE_RESP[10. store_response<br/>응답 캐싱]
    CACHE_RETURN --> END
    
    STORE_RESP --> END([최종 답변 반환])
    
    style START fill:#e8f5e9
    style CACHE fill:#e3f2fd
    style CLASSIFY fill:#fff3e0
    style EXTRACT fill:#f3e5f5
    style STORE fill:#ffecb3
    style ASSEMBLE fill:#f8bbd0
    style RETRIEVE fill:#ffe0b2
    style GEN fill:#c8e6c9
    style REFINE fill:#c8e6c9
    style QC fill:#ffcdd2
    style STORE_RESP fill:#d1c4e9
    style END fill:#c5cae9
```

## 노드별 상세 정보

| # | 노드 | 입력 필드 | 출력 필드 | 평균 처리 시간 |
|---|------|----------|----------|-------------|
| 1 | check_similarity | user_text, query_vector | cache_hit, cached_response | 100ms |
| 2 | classify_intent | user_text, (slot_out) | needs_retrieval, dynamic_k, complexity | 10-15ms |
| 3 | extract_slots | user_text | slot_out (6개 슬롯) | 30-50ms |
| 4 | store_memory | slot_out, user_id | profile_summary | 5-10ms |
| 5 | assemble_context | profile_summary, retrieved_docs | system_prompt, user_prompt | 10ms |
| 6 | retrieve | query_for_retrieval, dynamic_k | retrieved_docs | 50-150ms |
| 7 | generate_answer | system_prompt, user_prompt | answer | 500-1500ms |
| 8 | refine | answer, retrieved_docs | quality_score, query_for_retrieval | 300-800ms |
| 9 | quality_check | quality_score, iteration_count | 'retrieve' or END | 5ms |
| 10 | store_response | answer, query_vector | - | 20ms |

## 경로별 처리 시간 분석

**경로 1: 캐시 히트 (30%)**
- check_similarity → store_response → END
- 총 시간: **~0.3s**
- 비용: **$0 (LLM 호출 없음)**

**경로 2: Simple 질의 + 검색 스킵 (20%)**
- classify_intent → extract_slots → store_memory → assemble_context → generate_answer → refine → quality_check → store_response
- 총 시간: **~0.9s**
- 비용: **~$0.005**

**경로 3: Moderate 질의 + 1회 검색 (40%)**
- classify_intent → extract_slots → store_memory → assemble_context → retrieve (k=8) → reassemble → generate_answer → refine → quality_check → store_response
- 총 시간: **~1.4s**
- 비용: **~$0.009**

**경로 4: Complex 질의 + 재검색 (10%)**
- ... → retrieve (k=15) → generate → refine → quality_check → retrieve (k=15) → generate → refine → quality_check → store_response
- 총 시간: **~3.2s** (2 iterations)
- 비용: **~$0.018**

**가중 평균**:
- 평균 처리 시간: **1.1s** (기존 2.0s 대비 -45%)
- 평균 비용: **$0.007** (기존 $0.015 대비 -53%)

## 조건부 엣지 상세

**1) check_similarity → ?**
- `cache_hit == True` → store_response (바로 종료)
- `cache_hit == False` → classify_intent

**2) classify_intent → ?**
- `needs_retrieval == False` → assemble_context (검색 스킵)
- `needs_retrieval == True` → extract_slots

**3) assemble_context → ?**
- `needs_retrieval == False` OR `iteration_count > 0` → generate_answer
- `needs_retrieval == True` → retrieve

**4) quality_check → ?**
- `quality_score >= 0.5` → store_response (END)
- `iteration_count >= 2` → store_response (최대 반복)
- `중복 문서 감지` → store_response (안전장치)
- `품질 정체` → store_response (안전장치)
- 위 조건 모두 False → retrieve (재검색)

## Self-Refine 순환 구조

```mermaid
graph LR
    INIT[초기 답변 생성] --> EVAL1[품질 평가 1]
    EVAL1 -->|Score < 0.5| REWRITE1[질의 재작성]
    REWRITE1 --> RETRIEVE2[재검색]
    RETRIEVE2 --> REGEN1[답변 재생성]
    REGEN1 --> EVAL2[품질 평가 2]
    EVAL2 -->|Score < 0.5<br/>AND iter < 2| REWRITE2[질의 재작성 2]
    REWRITE2 --> RETRIEVE3[재검색 2]
    RETRIEVE3 --> REGEN2[답변 재생성 2]
    REGEN2 --> EVAL3[품질 평가 3]
    EVAL3 --> FINAL[최종 답변]
    
    EVAL1 -->|Score >= 0.5| FINAL
    EVAL2 -->|Score >= 0.5<br/>OR iter >= 2| FINAL
    
    style INIT fill:#c8e6c9
    style EVAL1 fill:#ffcdd2
    style REWRITE1 fill:#ffe0b2
    style RETRIEVE2 fill:#fff9c4
    style REGEN1 fill:#c8e6c9
    style FINAL fill:#c5cae9
```

## 이중 안전장치 작동

**안전장치 1: 중복 문서 감지**
```python
current_docs_hashes = {hash(doc['text']) for doc in current_retrieved_docs}
previous_docs_hashes = retrieved_docs_history[-2]
jaccard_similarity = len(current & previous) / len(current | previous)

if jaccard_similarity >= 0.8:
    return END  # 조기 종료
```

**안전장치 2: 품질 진행도 모니터링**
```python
if len(quality_score_history) >= 2:
    improvement = quality_score_history[-1] - quality_score_history[-2]
    if improvement < 0.05:  # 5% 미만 개선
        return END  # 조기 종료
```

**효과**:
- 무한 루프 발생률: 15% → 0% (-100%)
- 불필요한 재검색: 35% → 5% (-86%)

