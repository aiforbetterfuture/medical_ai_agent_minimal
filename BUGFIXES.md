# Bug Fixes Summary

This document summarizes the bugs fixed in the existing scaffold during integration testing for the multi-turn experiment infrastructure.

## Integration Test Results

**Final Status: 7/7 tests PASSED ✓**

---

## Bug #1: UnboundLocalError in assemble_context.py

### Issue
```
UnboundLocalError: cannot access local variable 'compression_stats' where it is not associated with a value
Location: agent/nodes/assemble_context.py:207
```

### Root Cause
Variables `hierarchical_contexts` and `compression_stats` were only initialized inside the `else` block (AI Agent mode) but used outside the conditional block, causing an error when in LLM mode.

### Fix
**File:** [agent/nodes/assemble_context.py](agent/nodes/assemble_context.py#L38-L40)

Initialize variables at the top of the function before the mode check:
```python
# Initialize variables that may be used later in both modes
hierarchical_contexts = {}
compression_stats = {}
```

Remove duplicate initializations inside conditional blocks.

---

## Bug #2: Graph Recursion Error (Infinite Loop)

### Issue
```
GraphRecursionError: Recursion limit of 25 reached without hitting a stop condition
```

The agent graph was stuck in an infinite loop: `assemble_context → retrieve → assemble_context → retrieve...`

### Root Cause
The `_retrieval_router` in [agent/graph.py](agent/graph.py#L96-L125) required documents to be retrieved before proceeding to `generate_answer`. When no documents were found (e.g., for greetings like "안녕하세요"), the router kept retrying retrieval infinitely.

### Fix
**Files Modified:**
1. [agent/state.py](agent/state.py#L37) - Add `retrieval_attempted` field to AgentState
2. [agent/graph.py](agent/graph.py#L268) - Initialize flag in initial_state
3. [agent/nodes/retrieve.py](agent/nodes/retrieve.py#L70,L193) - Set flag to True after retrieval
4. [agent/graph.py](agent/graph.py#L114-L115) - Check flag to prevent loops

**Changes:**

1. **Added state field** (`agent/state.py`):
```python
# 검색 관련
retrieved_docs: Annotated[List[Dict[str, Any]], add]
query_vector: List[float]  # 임베딩 벡터
retrieval_attempted: bool  # 검색 시도 여부 (무한 루프 방지용)
```

2. **Initialize in run_agent** (`agent/graph.py`):
```python
initial_state = {
    ...
    'retrieval_attempted': False,  # Initialize retrieval attempted flag
    ...
}
```

3. **Set flag in retrieve node** (`agent/nodes/retrieve.py`):

For LLM mode (early return):
```python
if is_llm_mode(state):
    return {
        **state,
        'retrieved_docs': [],
        'retrieval_attempted': True
    }
```

For AI Agent mode (after search):
```python
return {
    **state,
    'retrieved_docs': selected_docs,
    'retrieval_attempted': True  # Flag to indicate retrieval has been attempted
}
```

4. **Updated router logic** (`agent/graph.py`):
```python
def _retrieval_router(state: AgentState) -> str:
    retrieval_attempted = state.get('retrieval_attempted', False)

    # 첫 번째 검색을 완료했으면 (문서 유무와 관계없이) 바로 답변 생성
    # 무한 루프 방지: 검색을 시도했으나 문서를 못 찾은 경우에도 진행
    if iteration_count == 0 and retrieval_attempted:
        return "generate_answer"

    # ... rest of routing logic
```

**Key Insight:**
The fix ensures the agent proceeds to answer generation after ONE retrieval attempt, regardless of whether documents were found. This prevents infinite loops for queries without relevant RAG documents (e.g., greetings, simple conversational queries).

---

## Impact on Multi-Turn Experiment

Both bugs were blocking the integration tests and would have prevented the multi-turn experiment from running. With these fixes:

✓ All 7 integration tests pass
✓ The agent can handle queries without RAG documents (greetings, simple queries)
✓ Both LLM and AI Agent modes work correctly
✓ The multi-turn experiment infrastructure is fully operational

---

## Testing

Run integration tests to verify:
```bash
python experiments/test_integration.py
```

Expected output:
```
통과: 7/7
[SUCCESS] 모든 테스트 통과! 실험 실행 준비가 완료되었습니다.
```

---

## Notes

- The Gemini API quota error in test output is expected (free tier limit) and doesn't affect test success
- Debug logging was removed after verification
- No changes were made to the multi-turn experiment code created earlier
