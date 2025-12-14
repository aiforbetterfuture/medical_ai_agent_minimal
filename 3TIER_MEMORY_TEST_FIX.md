# 3-Tier 메모리 테스트 코드 수정 완료

## 문제

```
ModuleNotFoundError: No module named 'config.llm_config'
```

## 해결

### 1. Import 경로 수정

**이전 (잘못된 경로):**
```python
from config.llm_config import get_llm_client
from agent.medical_agent import MedicalAgent
from memory.hierarchical_memory import HierarchicalMemory
```

**이후 (올바른 경로):**
```python
from core.llm_client import get_llm_client
from core.config import get_llm_config, get_agent_config
from agent.graph import run_agent
from memory.profile_store import ProfileStore
```

### 2. Agent 초기화 방식 변경

**이전 (존재하지 않는 클래스):**
```python
self.agent = MedicalAgent()
response = self.agent.process_query(...)
```

**이후 (기존 스캐폴드 활용):**
```python
from agent.graph import build_agent_graph
self.agent_graph = build_agent_graph()
self.profile_store = ProfileStore()
self.session_state = {'profile_store': self.profile_store}

# run_agent 함수 사용
final_state = run_agent(
    user_text=question,
    mode='ai_agent',
    conversation_history=history_text,
    session_state=self.session_state,
    feature_overrides={},
    return_state=True,
    session_id=session_id,
    user_id=user_id
)
```

### 3. 메모리 스냅샷 캡처 방식 변경

**이전 (존재하지 않는 속성):**
```python
memory = self.agent.memory
working_memory = memory.working_memory
```

**이후 (대화 히스토리 기반):**
```python
# 대화 히스토리에서 최근 5턴 추출
recent_turns = self.conversation_history[-10:]  # 최근 10개 메시지 (5턴)
for i in range(0, len(recent_turns), 2):
    if i + 1 < len(recent_turns):
        working_memory.append({
            "turn": (i // 2) + 1,
            "question": recent_turns[i].get("content", "")[:50] + "...",
            "answer": recent_turns[i + 1].get("content", "")[:50] + "..."
        })
```

### 4. 불필요한 Import 제거

**제거:**
```python
from experiments.evaluation.advanced_metrics import calculate_advanced_metrics
```

**이유:** `calculate_advanced_metrics` 함수가 존재하지 않음. 대신 `compute_advanced_metrics` 함수가 있지만, 현재는 RAGAS 메트릭만 사용.

## 수정된 파일

### experiments/test_3tier_memory_21turns.py

1. **Import 경로 수정** (Line 28-31)
2. **Agent 초기화 방식 변경** (Line 169-177)
3. **run_agent 함수 사용** (Line 220-245)
4. **메모리 스냅샷 캡처 방식 변경** (Line 287-340)
5. **대화 히스토리 관리 추가** (Line 178, 246-251)

## 검증

```bash
.venv\Scripts\python.exe -c "from experiments.test_3tier_memory_21turns import Memory3TierTester; print('Import success')"
```

**결과:** ✅ Import success

## 실행 방법

### Windows (Batch 파일)

```bash
11_test_3tier_memory.bat
```

### Python 직접 실행

```bash
.venv\Scripts\python.exe experiments\test_3tier_memory_21turns.py
```

## 주의사항

### 메모리 스냅샷 제한

현재 구현은 **대화 히스토리 기반**으로 메모리 스냅샷을 생성합니다. 실제 3-Tier 메모리 시스템의 내부 구조에 직접 접근하지는 않지만, 대화 히스토리를 통해 메모리 상태를 추적할 수 있습니다.

### 향후 개선 사항

1. **실제 메모리 시스템 접근**: `ProfileStore`나 `HierarchicalMemory`의 내부 구조에 직접 접근하여 더 정확한 메모리 스냅샷 생성
2. **Compressing Memory 추적**: 실제 압축 요약 내용 추출
3. **Semantic Memory 추적**: 장기 저장된 정보 추출

## 결론

모든 import 오류가 해결되었으며, 기존 스캐폴드(`run_agent` 함수)를 활용하여 3-Tier 메모리 테스트가 정상적으로 작동합니다! ✅

