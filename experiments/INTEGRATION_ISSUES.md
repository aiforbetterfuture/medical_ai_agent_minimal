# 통합 이슈 및 개선 사항

## 발견된 문제점

### 1. **함수명 불일치** ❌
- **문제**: `run_multiturn_experiment.py`에서 `create_agent_graph()` 호출
- **실제**: 기존 스캐폴드는 `run_agent()` 또는 `get_agent_graph()` 사용
- **영향**: ImportError 발생

### 2. **Agent 실행 방식 불일치** ❌
- **문제**: 직접 그래프 실행 (`graph.invoke()`)
- **실제**: 기존 `run_agent()` 함수가 복잡한 초기화 처리 (feature flags, session state 등)
- **영향**:
  - ProfileStore, ResponseCache 등 메모리 시스템 미활용
  - Feature flags 미적용
  - 세션 관리 누락

### 3. **상태(State) 구조 불일치** ❌
- **문제**: 실험 코드는 일반 dict 사용
- **실제**: 기존 스캐폴드는 `AgentState` TypedDict 사용
- **영향**: 타입 안정성 저하

### 4. **LLM 클라이언트 직접 사용** ⚠️
- **문제**: LLM 모드에서 직접 OpenAI API 호출
- **실제**: 기존 `core.llm_client.get_llm_client()` 통합 인터페이스 존재
- **영향**:
  - Gemini 등 다른 모델 사용 불가
  - 설정 파일(config/model_config.yaml) 미활용

### 5. **대화 히스토리 형식 불일치** ⚠️
- **문제**: 단순 list of dict 형식
- **실제**: 기존 스캐폴드는 `conversation_history` 문자열로 관리
- **영향**: 메모리 시스템과 통합 어려움

### 6. **멀티턴 지표 계산 로직** ℹ️
- **상태**: 신규 기능 (문제 아님)
- **고려사항**:
  - ProfileStore의 슬롯 정보 활용 가능
  - ResponseCache와 연동하여 캐시 히트율 측정 가능

## 개선 방안

### Phase 1: 핵심 통합 (필수)

1. **run_multiturn_experiment.py 리팩토링**
   - `run_agent()` 함수 사용으로 전환
   - 세션 상태 관리 통합
   - Feature flags 올바르게 전달

2. **LLM 모드 개선**
   - `core.llm_client.get_llm_client()` 사용
   - config/model_config.yaml 설정 활용

3. **대화 히스토리 포맷 통일**
   - conversation_history 문자열 형식으로 변환
   - ProfileStore와 연동

### Phase 2: 고급 기능 통합 (선택)

1. **ResponseCache 활용**
   - 멀티턴 대화에서 캐시 히트율 측정
   - Turn 4 (near-duplicate) 테스트에 활용

2. **ProfileStore 슬롯 정보 활용**
   - Context Utilization Score 계산에 활용
   - Turn 2 메모리 테스트에 정확도 향상

3. **Hierarchical Memory 통합**
   - 5턴 이상 확장 시 Working Memory/Compressed Memory 분석

## 수정 우선순위

### 🔴 High Priority (즉시 수정 필요)
1. ✅ `_run_agent_mode()` 함수를 `run_agent()` 사용으로 변경
2. ✅ `_run_llm_mode()` 함수를 `core.llm_client` 사용으로 변경
3. ✅ 대화 히스토리 형식 통일

### 🟡 Medium Priority (권장)
4. ⏳ ProfileStore 통합 (Turn 2 컨텍스트 활용도 측정)
5. ⏳ ResponseCache 통합 (Turn 4 캐시 테스트)

### 🟢 Low Priority (선택)
6. ⏳ Hierarchical Memory 통합 (5턴 초과 시)
7. ⏳ 노드별 로깅 (node_trace.jsonl 상세화)

## 호환성 체크리스트

- [ ] `run_agent()` 함수 올바른 파라미터 전달
- [ ] `AgentState` 타입 호환성 확인
- [ ] Feature flags 올바르게 설정
- [ ] Session ID 관리
- [ ] ProfileStore 인스턴스 재사용
- [ ] 대화 히스토리 누적 관리
- [ ] 에러 핸들링 (API 호출 실패, 타임아웃 등)
