# 검색 리소스 캐싱 적용 확인서

## ✅ 자동 적용 완료

**중요**: 모든 실험 파일들은 **자동으로** 수정된 캐싱 기능을 사용합니다.

### 적용 원리

모든 실험 파일들은 다음과 같은 경로로 검색 기능을 사용합니다:

```
실험 파일 (experiments/*.py)
    ↓
agent.graph.create_agent_graph() 또는 run_agent()
    ↓
agent/nodes/retrieve.py
    ↓
retrieval/hybrid_retriever.py (✅ 캐싱 적용됨)
    ↓
retrieval/faiss_index.py (✅ 캐싱 적용됨)
retrieval/hybrid_retriever.py의 BM25Retriever (✅ 캐싱 적용됨)
```

**결론**: `retrieval/faiss_index.py`와 `retrieval/hybrid_retriever.py`를 수정했으므로, 이들을 import하는 모든 파일이 자동으로 캐싱 기능을 사용합니다.

---

## 📋 실험 파일별 확인

### 1. 멀티턴 실험 파일

#### ✅ `experiments/run_multiturn_experiment_v2.py`
- **사용**: `agent.graph.run_agent()` 또는 `create_agent_graph()`
- **경로**: `agent/nodes/retrieve.py` → `retrieval/hybrid_retriever.py`
- **캐싱 적용**: ✅ 자동 적용
- **호출하는 bat 파일**:
  - `7_test_single_turn.bat`
  - `8_test_multi_turn_single_patient.bat`
  - `9_run_full_experiment.bat`
  - `5_run_multiturn_test.bat`

#### ✅ `experiments/run_multiturn_experiment.py`
- **사용**: `agent.graph.create_agent_graph()`
- **경로**: `agent/nodes/retrieve.py` → `retrieval/hybrid_retriever.py`
- **캐싱 적용**: ✅ 자동 적용

### 2. Basic vs CRAG 실험 파일

#### ✅ `experiments/run_basic_vs_crag_single_patient.py`
- **사용**: `agent.graph.run_agent()`
- **경로**: `agent/nodes/retrieve.py` → `retrieval/hybrid_retriever.py`
- **캐싱 적용**: ✅ 자동 적용
- **호출하는 bat 파일**:
  - `run_basic_vs_crag_experiment.bat`

### 3. Ablation 실험 파일

#### ✅ `experiments/run_ablation_comparison.py`
- **사용**: `agent.graph.run_agent()`
- **경로**: `agent/nodes/retrieve.py` → `retrieval/hybrid_retriever.py`
- **캐싱 적용**: ✅ 자동 적용
- **호출하는 bat 파일**:
  - `run_ablation_comparison.bat`

#### ✅ `experiments/run_ablation_single.py`
- **사용**: `agent.graph.run_agent()`
- **경로**: `agent/nodes/retrieve.py` → `retrieval/hybrid_retriever.py`
- **캐싱 적용**: ✅ 자동 적용
- **호출하는 bat 파일**:
  - `run_ablation_single.bat`

#### ✅ `experiments/compare_crag_vs_basic_rag.py`
- **사용**: `agent.graph.run_agent()`
- **경로**: `agent/nodes/retrieve.py` → `retrieval/hybrid_retriever.py`
- **캐싱 적용**: ✅ 자동 적용

### 4. 테스트 파일

#### ✅ `experiments/test_basic_vs_crag_quick.py`
- **사용**: `agent.graph.run_agent()`
- **경로**: `agent/nodes/retrieve.py` → `retrieval/hybrid_retriever.py`
- **캐싱 적용**: ✅ 자동 적용

#### ⚠️ `test_optimizations.py`
- **사용**: `retrieval.hybrid_retriever.BM25Retriever` 직접 import (테스트용)
- **캐싱 적용**: ✅ 자동 적용 (BM25Retriever 클래스 자체에 캐싱이 구현되어 있음)

---

## 🔍 핵심 확인 사항

### 수정된 파일 (캐싱 구현)

1. ✅ `retrieval/faiss_index.py`
   - 전역 캐시 `_FAISS_INDEX_CACHE` 추가
   - `FAISSIndex.__init__()`에서 캐시 확인 및 재사용

2. ✅ `retrieval/hybrid_retriever.py`
   - 전역 캐시 `_BM25_RETRIEVER_CACHE` 추가
   - 전역 캐시 `_HYBRID_RETRIEVER_CACHE` 추가
   - `BM25Retriever.__init__()`에서 캐시 확인 및 재사용
   - `HybridRetriever.__init__()`에서 캐시 확인 및 재사용

### 사용하는 파일 (자동 적용)

1. ✅ `agent/nodes/retrieve.py`
   - `from retrieval.hybrid_retriever import HybridRetriever`
   - `HybridRetriever(retriever_config)` 생성 시 자동으로 캐싱 적용

### 직접 사용하지 않는 파일 (간접 적용)

모든 실험 파일들은 `agent.graph`를 통해 간접적으로 사용하므로 자동 적용됩니다:
- `experiments/run_multiturn_experiment_v2.py`
- `experiments/run_multiturn_experiment.py`
- `experiments/run_basic_vs_crag_single_patient.py`
- `experiments/run_ablation_comparison.py`
- `experiments/run_ablation_single.py`
- `experiments/compare_crag_vs_basic_rag.py`
- `experiments/test_basic_vs_crag_quick.py`

---

## 📊 적용 확인 방법

### 방법 1: 로그 메시지 확인

멀티턴 실험을 실행하면 첫 턴에만 로드 메시지가 출력됩니다:

```bash
# 멀티턴 실험 실행
8_test_multi_turn_single_patient.bat
```

**예상 출력**:
```
Turn 1:
  [BM25] 코퍼스 로드 완료: 15021개 문서
  [FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss
  [FAISS] 메타데이터 로드 완료: 15021개 문서

Turn 2:
  (로드 메시지 없음 - 캐시에서 재사용)

Turn 3:
  (로드 메시지 없음 - 캐시에서 재사용)
```

### 방법 2: 실행 시간 측정

멀티턴 실험의 각 턴 실행 시간을 측정하면:
- **Turn 1**: ~2-3초 (로딩 포함)
- **Turn 2-5**: ~1-2초 (캐시 재사용)

---

## ✅ 최종 확인

### 모든 실험용 bat 파일

다음 bat 파일들이 호출하는 Python 스크립트들은 모두 캐싱이 적용됩니다:

1. ✅ `7_test_single_turn.bat` → `experiments/run_multiturn_experiment_v2.py`
2. ✅ `8_test_multi_turn_single_patient.bat` → `experiments/run_multiturn_experiment_v2.py`
3. ✅ `9_run_full_experiment.bat` → `experiments/run_multiturn_experiment_v2.py`
4. ✅ `5_run_multiturn_test.bat` → `experiments/run_multiturn_experiment_v2.py`
5. ✅ `run_basic_vs_crag_experiment.bat` → `experiments/run_basic_vs_crag_single_patient.py`
6. ✅ `run_ablation_comparison.bat` → `experiments/run_ablation_comparison.py`
7. ✅ `run_ablation_single.bat` → `experiments/run_ablation_single.py`

### 멀티턴 테스트 파일

1. ✅ `experiments/run_multiturn_experiment_v2.py` - 캐싱 적용됨
2. ✅ `experiments/run_multiturn_experiment.py` - 캐싱 적용됨
3. ✅ `experiments/run_basic_vs_crag_single_patient.py` - 캐싱 적용됨

---

## 🎯 결론

**모든 실험 파일과 멀티턴 테스트 파일에 캐싱이 자동으로 적용되었습니다.**

추가 작업이 필요하지 않습니다. 모든 파일이 수정된 `retrieval/faiss_index.py`와 `retrieval/hybrid_retriever.py`를 import하여 사용하므로, 자동으로 캐싱 기능이 활성화됩니다.

---

## 📝 참고사항

1. **캐시는 프로세스 수준에서 유지됩니다**
   - Python 프로세스가 종료되면 캐시도 사라집니다
   - 새로운 프로세스가 시작되면 첫 턴에서 다시 로드됩니다

2. **멀티턴 대화에서만 효과적입니다**
   - 단일 턴 대화에서는 효과가 없습니다 (이미 한 번만 로드)
   - 멀티턴 대화에서만 시간 절감 효과가 큽니다

3. **메모리 사용량**
   - BM25 코퍼스: ~50-100MB
   - FAISS 인덱스: ~200-500MB
   - 메타데이터: ~50-100MB
   - 총 약 300-700MB (코퍼스 크기에 따라 다름)

