"""
FAISS 인덱스 관리
- 인덱스 로드/저장
- 벡터 검색
"""

import os
from typing import List, Dict, Any, Optional
import json

try:
    import faiss
    import numpy as np
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None
    np = None


class FAISSIndex:
    """
    FAISS 인덱스 관리 클래스
    """
    
    def __init__(self, index_path: str, meta_path: Optional[str] = None):
        """
        Args:
            index_path: FAISS 인덱스 파일 경로
            meta_path: 메타데이터 파일 경로 (선택)
        """
        self.index_path = index_path
        self.meta_path = meta_path or index_path.replace('.faiss', '.meta.jsonl').replace('.index', '.meta.jsonl')
        self.index = None
        self.metadata = []
        
        if os.path.exists(index_path):
            self.load()
    
    def load(self):
        """인덱스 로드"""
        if not HAS_FAISS:
            print("[WARNING] faiss가 설치되지 않았습니다.")
            return
        
        if not os.path.exists(self.index_path):
            print(f"[WARNING] 인덱스 파일을 찾을 수 없습니다: {self.index_path}")
            return
        
        try:
            self.index = faiss.read_index(self.index_path)
            print(f"[FAISS] 인덱스 로드 완료: {self.index_path}")
            
            # 메타데이터 로드
            if os.path.exists(self.meta_path):
                self._load_metadata()
        except Exception as e:
            print(f"[ERROR] 인덱스 로드 실패: {e}")
            self.index = None
    
    def _load_metadata(self):
        """메타데이터 로드"""
        try:
            with open(self.meta_path, 'r', encoding='utf-8') as f:
                self.metadata = [json.loads(line) for line in f if line.strip()]
            print(f"[FAISS] 메타데이터 로드 완료: {len(self.metadata)}개 문서")
        except Exception as e:
            print(f"[WARNING] 메타데이터 로드 실패: {e}")
            self.metadata = []
    
    def search(self, query_vector: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """
        벡터 검색
        
        Args:
            query_vector: 쿼리 벡터
            k: 반환할 상위 k개
        
        Returns:
            검색 결과 리스트
        """
        if not HAS_FAISS or self.index is None:
            return []
        
        try:
            # 벡터를 numpy 배열로 변환
            query_vec = np.array([query_vector], dtype=np.float32)
            
            # 검색 실행
            scores, indices = self.index.search(query_vec, k)
            
            # 결과 구성
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < 0 or idx >= len(self.metadata):
                    continue
                
                doc = self.metadata[idx].copy()
                doc['score'] = float(score)
                doc['rank'] = i + 1
                results.append(doc)
            
            return results
        except Exception as e:
            print(f"[ERROR] 검색 실패: {e}")
            return []
    
    def build(self, vectors: List[List[float]], metadata: List[Dict[str, Any]], metric: str = 'ip'):
        """
        인덱스 구축
        
        Args:
            vectors: 벡터 리스트
            metadata: 메타데이터 리스트
            metric: 거리 메트릭 ('ip' 또는 'l2')
        """
        if not HAS_FAISS:
            print("[WARNING] faiss가 설치되지 않았습니다.")
            return
        
        try:
            vecs = np.array(vectors, dtype=np.float32)
            dim = vecs.shape[1]
            
            # 인덱스 생성
            if metric == 'ip':
                index = faiss.IndexFlatIP(dim)
            else:
                index = faiss.IndexFlatL2(dim)
            
            # 벡터 정규화 (IP의 경우)
            if metric == 'ip':
                faiss.normalize_L2(vecs)
            
            index.add(vecs)
            
            # 저장
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            faiss.write_index(index, self.index_path)
            
            # 메타데이터 저장
            with open(self.meta_path, 'w', encoding='utf-8') as f:
                for meta in metadata:
                    f.write(json.dumps(meta, ensure_ascii=False) + '\n')
            
            self.index = index
            self.metadata = metadata
            
            print(f"[FAISS] 인덱스 구축 완료: {len(vectors)}개 벡터")
        except Exception as e:
            print(f"[ERROR] 인덱스 구축 실패: {e}")

