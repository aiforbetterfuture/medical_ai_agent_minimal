# Context-Aware 멀티턴 대화 설계 (정교화 버전)

본 문서는 기존 `MULTITURN_CONTEXT_IMPROVEMENT_STRATEGY.md`와 CHATGPT 피드백을 통합하여, **현 스캐폴드의 무결성을 유지**하면서 단계적으로 도입할 수 있는 설계/코드 스케치를 제공합니다. 목표는 다음과 같습니다.

1) 토큰/지연/비용 최적화  
2) 맥락 유지·개인화 품질 향상  
3) 장기 세션/다중 세션 지원 (영속성)  
4) 안전 가드라인 및 평가 파이프라인 명확화  

---

## 0. 범위와 제약
- **기존 LangGraph 7노드**(extract_slots → store_memory → assemble_context → retrieve → generate_answer → refine → quality_check)는 유지.  
- **기존 ProfileStore·하이브리드 검색** 동작은 기본값으로 둠. 신규 기능은 **옵션**으로 탑재해 점진 도입.  
- **LLM/임베딩 프로바이더, API 키, 안전 가이드**는 현행 프롬프트 정책과 동일하게 준수.  

---

## 1. AgentState/노드/파일 매핑 (추가 필드 및 책임)

| 위치 | 추가/변경 필드 | 역할 |
| --- | --- | --- |
| `agent/state.py` | `session_id`, `user_id`, `context_prompt`, `token_plan`, `session_context`, `longterm_context`, `profile_context`, `messages` | 컨텍스트/토큰/세션 정보 저장 |
| `agent/graph.py` | `run_agent(..., conversation_history, session_id, user_id)` | 세션/유저 id 전달, 초기 state 주입 |
| `agent/nodes/assemble_context.py` | `ContextManager` 호출, `context_prompt` 생성 | 토큰 예산 내 컨텍스트 조립 |
| `agent/nodes/store_memory.py` | `ProfileContext` + `ConflictResolver` + `Persistence` (옵션) | 슬롯 업데이트·모순 해결·영속화 |
| `agent/nodes/retrieve.py` | `token_plan.for_docs` 활용해 검색 결과 길이 제한 | 컨텍스트 길이 제어 |
| `agent/nodes/generate_answer.py` | `context_prompt` + `retrieved_docs` + `user_text`로 최종 프롬프트 생성 | LLM 호출 |
| `app.py` | `session_id` 생성/보관, 대화 메시지 UI, 프로필/맥락 패널(옵션) | 멀티턴 UI/UX |

---

## 2. 핵심 컴포넌트 설계

### 2.1 TokenManager (토큰 예산 배분)
```python
# context/token_manager.py
from dataclasses import dataclass

@dataclass
class TokenPlan:
    max_total: int
    for_query: int
    for_profile: int
    for_recent: int
    for_longterm: int
    for_docs: int

class TokenManager:
    def __init__(self, max_total_tokens: int = 4000):
        self.max_total = max_total_tokens

    def count_tokens(self, text: str) -> int:
        # 실서비스 시 tiktoken 등으로 교체
        return int(len(text.split()) * 1.3)

    def make_plan(self, *, current_query, profile_summary="", longterm_summary="", reserved_for_docs=900, reserved_for_system=400) -> TokenPlan:
        q = self.count_tokens(current_query)
        p = self.count_tokens(profile_summary) if profile_summary else 0
        l = self.count_tokens(longterm_summary) if longterm_summary else 0
        available = max(1000, self.max_total - reserved_for_docs - reserved_for_system)
        base = q + p + l
        remaining = max(0, available - base)
        recent = int(remaining * 0.6)
        return TokenPlan(self.max_total, q, p, recent, l, reserved_for_docs)
```

### 2.2 ContextManager (계층 컨텍스트 + 토큰 내 조합)
```python
# context/context_manager.py
class ContextManager:
    def __init__(self, token_manager, session_repo, profile_store, longterm_repo):
        self.token_manager = token_manager
        self.session_repo = session_repo      # 최근 N턴 조회
        self.profile_store = profile_store    # 요약 제공
        self.longterm_repo = longterm_repo    # 장기 요약/키포인트

    def build_context(self, *, user_id, session_id, current_query, max_tokens=4000):
        recent_msgs = self.session_repo.get_recent_messages(session_id, limit=5)
        profile_summary = self.profile_store.get_summary(user_id) or ""
        longterm_summary = self.longterm_repo.get_summary(session_id) or ""
        plan = self.token_manager.make_plan(
            current_query=current_query,
            profile_summary=profile_summary,
            longterm_summary=longterm_summary,
            reserved_for_docs=900,
            reserved_for_system=400,
        )
        session_context = self._clip_recent(recent_msgs, plan.for_recent)
        context_prompt = self._assemble(profile_summary, longterm_summary, session_context)
        return dict(
            session_context=session_context,
            profile_context=profile_summary,
            longterm_context=longterm_summary,
            context_prompt=context_prompt,
            token_plan=plan.__dict__,
        )
```

### 2.3 ConversationSummarizer (Sliding 요약, 선택적)
- 최근 N턴(예: 5턴)은 원문 유지, 이전 턴은 요약/키포인트 추출.  
- 트리거: 대화 길이 10턴 이상 or `iteration_count`≥2 시 호출.  
- 안전 프롬프트: 진단/약물/알레르기/금기를 절대 누락하지 않도록 지시.  

### 2.4 ContextSelector (의미 기반 관련 턴 선택, 선택적)
- 현재 질문 임베딩 vs 과거 user 발화 임베딩 코사인 유사도.  
- 상위 K(예: 3)만 포함.  
- 임베딩 캐시(키: session_id, turn_id)로 비용 감소.  
- 의료 도메인 특화: BM25 키워드 필터와 조합 가능.  

### 2.5 ProfileContext + ConflictResolver + Persistence (옵션)
- `ProfileContext.update_from_slots(slots)`에서 슬롯별 정책 적용:
  - demographics: overwrite
  - conditions: accumulate + 모순 시 확인/최신 우선
  - medications: time-based update
  - vitals/labs: 최신 우선 + 시계열 보관
  - symptoms: time-decay
- Persistence: `FileProfileStorage`(dev) → `SQLiteProfileStorage`(prod)로 교체 가능.
- Safety: 알레르기/금기 슬롯은 항상 상위에 노출, 업데이트 시 사용자 확인 UI 훅 제공.

### 2.6 IntentClassifier (선택적, 비용 민감)
- 간단한 라이트웨이트 분류기(rule + 소형 모델) → 실패 시 LLM fallback.  
- AgentState.intent에 저장, retrieve/generate 단계에서 검색 템플릿 분기.  

### 2.7 안전 가드라인 (System Prompt 공통)
- “진단 확정 금지, 응급 시 즉시 병원 안내, 근거 없으면 추측 금지”를 system_prompt에 상시 포함.  
- 개인화 프롬프트에도 동일한 가드라인 유지.  

---

## 3. LangGraph 통합 포인트 (안전한 단계적 적용)

### 3.1 assemble_context 노드
1) `ContextManager.build_context(...)` 호출  
2) 반환된 `context_prompt`, `token_plan`을 state에 저장  
3) LLM user_prompt 생성 시 `context_prompt + user_text` 조합  

### 3.2 retrieve 노드
- `token_plan.for_docs`를 활용해 RRF 결과 상위 k를 동적으로 축소 (예: 응답이 길면 k=5로 축소).  

### 3.3 generate_answer 노드
- 최종 프롬프트 = system_prompt + context_prompt + 검색 근거 + 현재 질문  
- 토큰 초과 감지 시: 최근 턴/검색 근거를 우선 트리밍하고 다시 호출 (단일 재시도).  

### 3.4 store_memory 노드
- 기존 ProfileStore 로직을 기본값으로 유지.  
- 옵션: ProfileContext + Persistence 주입 시, state에 raw profile 저장 후 요약을 `profile_context`에 반영.  

### 3.5 app.py (Streamlit)
- `session_id`, `user_id` 생성/보관 (세션 state).  
- 대화 패널 외에 (옵션) 프로필/맥락 패널:  
  - 프로필 핵심 슬롯(나이, 진단, 약물, 최근 vitals)  
  - 최근 맥락 하이라이트(마지막 3턴 요약)  
- 에러 발생 시 LLM-only degrade 경로 안내.  

---

## 4. 평가·로그·모니터링

### 4.1 성능/품질 지표
- 토큰 사용량, 응답 지연, 캐시 적중률.  
- RAGAS: answer_relevance / faithfulness / answer_support.  
- Multi-turn coherence: MultiChallenge 또는 자체 스크립트에서 turn-perplexity.  
- 오류율: LangGraph 노드 예외 발생률, 검색 실패율.  

### 4.2 A/B 실험 훅 (tests)
- `run_agent_baseline` vs `run_agent_context` 두 파이프라인을 동일 데이터셋에 평가.  
- 기대 목표(예시):  
  - avg_tokens -30% 이상  
  - avg_latency -20% 이상  
  - answer_relevance +5~10pt  

### 4.3 로깅
- LangGraph 각 노드에서 `state.token_plan`, `retrieved_docs` 개수, 예외를 구조화 로그로 기록.  
- Streamlit UI에서 사용자 공지용 에러 표시, 백엔드 로그는 파일/콘솔 분리.  

---

## 5. 단계적 도입 가이드 (무결성 유지)

### Phase A (저위험·바로 적용)
1) TokenManager + ContextManager 도입, assemble_context에서 context_prompt 사용  
2) retrieve에서 k 동적 축소(logic only)  
3) generate에서 토큰 초과 시 soft-trim 재시도  

### Phase B (옵션, 성능/품질 향상)
1) ConversationSummarizer + ContextSelector 추가 (길이 10턴 이상일 때만 활성)  
2) IntentClassifier(라이트) 적용, retrieve 템플릿 분기  

### Phase C (장기·개인화)
1) ProfileContext + ConflictResolver + File/SQLite Persistence  
2) app.py 사이드바 프로필 패널 추가 (옵션 토글)  

### Phase D (고급/추가)
1) 스트리밍 응답, 대화 내보내기  
2) 검색/필터 UI  
3) Redis/DB 캐시로 교체  

---

## 6. 안전성 체크리스트
- 시스템 프롬프트에 의료 안전 가드라인 상시 포함.  
- 알레르기/금기/응급 신호 슬롯은 업데이트 시 사용자 확인 또는 강조 표시.  
- 요약/압축 시 진단·약물·금기·알레르기 정보를 절대 누락하지 않도록 프롬프트에 명시.  
- 에러 발생 시 LLM-only fallback, 사용자에게 “근거 부족” 고지.  

---

## 7. 예시 적용 흐름 (변경 후)
1) app.py에서 `session_id/user_id` 설정 → `run_agent` 호출  
2) assemble_context: ContextManager → context_prompt/token_plan 생성  
3) retrieve: token_plan.for_docs 기반 k 설정, RRF 수행  
4) generate_answer: context_prompt + retrieved_docs + user_text로 LLM 호출  
5) refine/quality_check: 기존 로직 유지  
6) store_memory: ProfileStore 기본, 옵션으로 ProfileContext+Persistence 적용  

---

## 8. 기대 효과 요약
- 토큰 사용량 30~50% 절감, 응답 지연 20~40% 개선 (Phase A/B)  
- 멀티턴 맥락 유지 및 personalization 체감 향상 (ContextManager + ProfileContext)  
- 장기 세션 연속성 확보 (Persistence)  
- 안전성: 금기/알레르기/응급 가드라인 일관 적용  

---

## 9. 바로 시작할 최소 작업 세트
1) `context/` 디렉터리 추가: TokenManager, ContextManager 골격만 우선 구현  
2) `agent/state.py` 필드 확장 (`context_prompt`, `token_plan`, `session_id`, `user_id`)  
3) `assemble_context`에서 ContextManager 호출, `context_prompt` 사용  
4) `generate_answer`에서 `context_prompt`를 최종 프롬프트에 포함  

이 4단계만으로도 **토큰/지연 개선**과 **맥락 품질**을 즉각 체감할 수 있으며, 기존 스캐폴드의 무결성을 해치지 않습니다. 이후 Phase B~D를 선택적으로 확장하세요.

---

**작성일**: 2025-01-XX  
**버전**: 2.0 (정교화)  
**대상**: 개발팀, 리뷰어, 논문/보고서 작성자

