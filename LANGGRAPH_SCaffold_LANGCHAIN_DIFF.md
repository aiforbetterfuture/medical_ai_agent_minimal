# LangGraph 선택 근거와 적용 현황, 추가 활용 방안

본 문서는 현재 스캐폴드가 LangGraph를 선택한 이유, LangChain 대비 차별점, 적용된 기능, 추가 활용 시 기대 개선점을 정리합니다.

---

## 1. 왜 LangGraph인가? (LangChain 대비)
- **LangChain**: 선형 체인/파이프라인에 강점. 정해진 순서를 한 번 타는 흐름에 적합.
- **LangGraph**: 상태(StateGraph) 기반의 그래프형 에이전트. 조건 분기, 반복 루프, 재시도, 서브그래프, 멀티에이전트, 장기 메모리(checkpointer/store) 등을 자연스럽게 표현.
- **본 스캐폴드 특성**: CRAG(재검색) 내부 루프 + Self-Refine(품질) 외부 루프가 공존하는 “이중 루프” 구조이며, 멀티턴 컨텍스트/메모리 관리가 필요함 → 그래프/상태머신 모델이 더 적합.

---

## 2. 현재 스캐폴드에서 LangGraph 적용 현황
- **7개 노드 + 조건부 엣지(StateGraph)**  
  - `extract_slots` → `store_memory` → `assemble_context` → `retrieve` → `generate_answer` → `refine` → `quality_check`  
  - `quality_check`에서 조건부 엣지: 품질 낮음이면 `retrieve`로 루프, 품질 양호면 종료.
- **명시적 상태(AgentState)**  
  - 입력, 프로필 요약, 검색 결과, 프롬프트, 품질 점수, 반복 횟수 등을 상태로 관리.  
  - 멀티턴 컨텍스트 강화를 위해 `session_id/user_id`, `context_prompt`, `token_plan`, `session_context`, `longterm_context`, `profile_context` 등 필드 확장.
- **모듈 분리**  
  - `extraction/`, `memory/`, `retrieval/`, `agent/nodes/` 등 계층화 → 노드 단일 책임, 교체/실험 용이.
- **이론-구현 매핑 (Context Engineering 4단계)**  
  - 추출→저장→주입→검증이 노드 구조로 1:1 매핑되어, 설계의 가시성과 재현성 확보.

---

## 3. LangGraph만이 주는 차별적 이점 (현재 코드 기준)
1) **이중 루프 가시성**  
   - CRAG(검색 품질) 내부 루프 + Self-Refine(답변 품질) 외부 루프를 그래프와 조건부 엣지로 명시 → 디버그/실험이 용이.
2) **상태 기반 멀티턴/메모리**  
   - AgentState에 컨텍스트/프로필/토큰 예산을 담아 노드 간 공유 → 멀티턴 맥락 유지.  
   - LangGraph의 checkpointer/store 패턴과 잘 어울림(추가 활용 여지).
3) **실험/AB 테스트 친화성**  
   - 그래프 정의만 바꿔 루프 횟수, 라우팅, retrieval 전략을 비교 가능.  
   - `test_agent_performance.py` 등과 결합해 지표(토큰/지연/품질) 측정이 수월.
4) **안전성 확장 용이성**  
   - 중간에 human-in-the-loop 노드 삽입, 재시도/인터럽트 패턴 적용이 용이 → 의료 도메인 안전 강화.

---

## 4. 추가로 활용하면 좋은 LangGraph 기능과 기대 개선
1) **Checkpointer/Store 도입**  
   - 세션/사용자별 상태·프로필을 장기 보관 → 세션 넘어도 맥락/개인화 유지.  
   - 기대: 장기 연속 대화 품질 상승, 재시작 시 복원 비용 감소.
2) **서브그래프(Subgraph) 분리**  
   - CRAG 내부 검색 품질 루프를 서브그래프로, 외부 Self-Refine 루프와 계층화 → 가독성·테스트성 향상.  
   - 기대: 검색 품질 실험(A/B) 단순화, 유지보수 용이.
3) **병렬 노드(Parallel execution)**  
   - 하이브리드 검색(BM25+FAISS)와 장기 메모리 조회를 병렬 실행 후 병합 → 지연(latency) 단축.  
   - 기대: 응답 속도 개선(수백 ms 단축 가능).
4) **Human-in-the-loop Interrupt**  
   - `quality_check` 이후 위험 응답 감지 시 human_review 노드로 분기 → 의료 안전성 강화.  
   - 기대: 오답/위험 답변율 감소, 신뢰도 향상.
5) **Graph-level 라우팅/정책 토글**  
   - feature_flags로 루프 횟수, retrieval k, 토큰 예산, 라우팅 전략을 그래프 파라미터화.  
   - 기대: 실험/운영 프로파일 전환이 코드 변경 없이 용이.

---

## 5. 심사위원/연구용 5포인트 요약
1) **상태머신으로 구현된 CRAG+Self-Refine 이중 루프** → 단순 체인보다 구조적 안정성/가시성 우수.  
2) **Context Engineering 4단계의 1:1 노드 매핑** → 이론·설계가 코드 그래프에 투명하게 반영.  
3) **명시적 상태(AgentState) 기반 멀티턴/프로필 컨텍스트 관리** → 장기 맥락 유지와 개인화 품질에 유리.  
4) **그래프 단위 AB 테스트/정책 전환 용이** → 토큰/지연/품질 지표 개선 실험이 체계적.  
5) **확장성: checkpointer, 서브그래프, 병렬, human-in-the-loop** → 의료 도메인 안전·성능을 단계적으로 강화할 수 있는 여지.

---

## 6. 결론
현재 스캐폴드는 LangGraph를 활용해 “상태를 가진 그래프형 의료 에이전트”를 명확히 구현했고, CRAG+Self-Refine 루프, 컨텍스트 엔지니어링 4단계를 구조적으로 녹여냈습니다. 추가로 LangGraph의 checkpointer/서브그래프/병렬/human-in-the-loop 기능을 도입하면, 장기 맥락 유지·성능(지연)·안전성 측면에서 더 큰 개선을 기대할 수 있습니다.

