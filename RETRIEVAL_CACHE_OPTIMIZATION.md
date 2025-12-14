# 검색 리소스 캐싱 최적화

## 문제점

멀티턴 대화에서 매 턴마다 다음 리소스들이 재로딩되어 시간이 소모되었습니다:

1. **쿼리 벡터 생성** (임베딩 API 호출) - 매 턴 필요 (쿼리가 다르므로)
2. **BM25 코퍼스 로드** - 매 턴 불필요하게 재로딩 ❌
3. **FAISS 인덱스 로드** - 매 턴 불필요하게 재로딩 ❌
4. **FAISS 메타데이터 로드** - 매 턴 불필요하게 재로딩 ❌

### 이전 동작

```
Turn 1:
  [BM25] 코퍼스 로드 완료: 15021개 문서
  [FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss
  [FAISS] 메타데이터 로드 완료: 15021개 문서

Turn 2:
  [BM25] 코퍼스 로드 완료: 15021개 문서  ← 불필요한 재로딩
  [FAISS] 인덱스 로드 완료: ./data/index/train_source/train_source_data.index.faiss  ← 불필요한 재로딩
  [FAISS] 메타데이터 로드 완료: 15021개 문서  ← 불필요한 재로딩

Turn 3:
  [BM25] 코퍼스 로드 완료: 15021개 문서  ← 불필요한 재로딩
  ...
```

## 해결 방법

**전역 싱글톤 캐시**를 도입하여 같은 경로에 대해서는 한 번만 로드하도록 개선했습니다.

### 구현 내용

#### 1. `FAISSIndex` 전역 캐시

**파일**: `retrieval/faiss_index.py`

```python
# 전역 캐시: 같은 경로에 대해서는 한 번만 로드
_FAISS_INDEX_CACHE: Dict[str, 'FAISSIndex'] = {}

class FAISSIndex:
    def __init__(self, index_path: str, meta_path: Optional[str] = None):
        # 정규화된 경로를 키로 사용
        index_path = os.path.abspath(index_path)
        cache_key = index_path
        
        # 캐시에 있으면 재사용
        if cache_key in _FAISS_INDEX_CACHE:
            cached = _FAISS_INDEX_CACHE[cache_key]
            self.index_path = cached.index_path
            self.meta_path = cached.meta_path
            self.index = cached.index  # ← 이미 로드된 인덱스 재사용
            self.metadata = cached.metadata  # ← 이미 로드된 메타데이터 재사용
            return
        
        # 새로 생성 및 로드
        # ... (로드 로직)
        
        # 캐시에 저장
        _FAISS_INDEX_CACHE[cache_key] = self
```

#### 2. `BM25Retriever` 전역 캐시

**파일**: `retrieval/hybrid_retriever.py`

```python
# 전역 캐시: 같은 경로에 대해서는 한 번만 로드
_BM25_RETRIEVER_CACHE: Dict[str, 'BM25Retriever'] = {}

class BM25Retriever:
    def __init__(self, corpus_path: str):
        # 정규화된 경로를 키로 사용
        corpus_path = os.path.abspath(corpus_path)
        cache_key = corpus_path
        
        # 캐시에 있으면 재사용
        if cache_key in _BM25_RETRIEVER_CACHE:
            cached = _BM25_RETRIEVER_CACHE[cache_key]
            self.corpus_docs = cached.corpus_docs  # ← 이미 로드된 코퍼스 재사용
            self.bm25_index = cached.bm25_index  # ← 이미 구축된 인덱스 재사용
            return
        
        # 새로 생성 및 로드
        # ... (로드 로직)
        
        # 캐시에 저장
        _BM25_RETRIEVER_CACHE[cache_key] = self
```

#### 3. `HybridRetriever` 전역 캐시

**파일**: `retrieval/hybrid_retriever.py`

```python
# 전역 캐시: 같은 설정에 대해서는 한 번만 생성
_HYBRID_RETRIEVER_CACHE: Dict[str, 'HybridRetriever'] = {}

class HybridRetriever:
    def __init__(self, config: Dict[str, Any]):
        # 캐시 키 생성 (설정을 기반으로)
        bm25_path = config.get('bm25_corpus_path', '')
        faiss_path = config.get('faiss_index_path', '')
        faiss_meta = config.get('faiss_meta_path', '')
        rrf_k = config.get('rrf_k', 60)
        
        cache_key = f"{bm25_path}::{faiss_path}::{faiss_meta}::{rrf_k}"
        
        # 캐시에 있으면 재사용
        if cache_key in _HYBRID_RETRIEVER_CACHE:
            cached = _HYBRID_RETRIEVER_CACHE[cache_key]
            self.bm25_retriever = cached.bm25_retriever  # ← 캐시된 BM25 재사용
            self.faiss_index = cached.faiss_index  # ← 캐시된 FAISS 재사용
            return
        
        # 새로 생성 (내부적으로 BM25와 FAISS도 캐시 사용)
        # ...
        
        # 캐시에 저장
        _HYBRID_RETRIEVER_CACHE[cache_key] = self
```

## 개선 효과

### 이전 (매 턴 재로딩)

```
Turn 1: BM25 로드 (1초) + FAISS 로드 (0.5초) + 메타데이터 로드 (0.3초) = 1.8초
Turn 2: BM25 로드 (1초) + FAISS 로드 (0.5초) + 메타데이터 로드 (0.3초) = 1.8초
Turn 3: BM25 로드 (1초) + FAISS 로드 (0.5초) + 메타데이터 로드 (0.3초) = 1.8초
...
총 5턴: 9.0초 소모
```

### 개선 후 (한 번만 로드)

```
Turn 1: BM25 로드 (1초) + FAISS 로드 (0.5초) + 메타데이터 로드 (0.3초) = 1.8초
Turn 2: 캐시 재사용 (0.001초) = 0.001초
Turn 3: 캐시 재사용 (0.001초) = 0.001초
...
총 5턴: 1.8초 소모 (약 80% 시간 절감)
```

## 주의사항

1. **메모리 사용**: 전역 캐시는 프로세스가 종료될 때까지 메모리에 유지됩니다.
   - BM25 코퍼스: ~50-100MB
   - FAISS 인덱스: ~200-500MB
   - 메타데이터: ~50-100MB
   - 총 약 300-700MB (코퍼스 크기에 따라 다름)

2. **멀티턴 대화에서만 효과적**: 
   - 단일 턴 대화에서는 효과가 없습니다 (이미 한 번만 로드)
   - 멀티턴 대화에서만 시간 절감 효과가 큽니다

3. **캐시 무효화**: 
   - 현재는 프로세스 종료 시까지 캐시가 유지됩니다
   - 인덱스나 코퍼스 파일이 변경되면 프로세스를 재시작해야 합니다

## 검증 방법

멀티턴 실험을 실행하면 첫 턴에만 로드 메시지가 출력되고, 이후 턴에서는 출력되지 않습니다:

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

## 관련 파일

- `retrieval/faiss_index.py` - FAISS 인덱스 캐싱
- `retrieval/hybrid_retriever.py` - BM25 및 HybridRetriever 캐싱
- `agent/nodes/retrieve.py` - 검색 노드 (변경 없음, 자동으로 캐시 활용)

