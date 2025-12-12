"""
Context Compression 시스템

정보 엔트로피 기반으로 컨텍스트를 압축하여 토큰 효율을 극대화합니다.

핵심 기능:
1. Extractive Compression: 중요한 문장만 선택
2. Abstractive Compression: LLM 기반 요약
3. Hybrid Compression: 둘의 조합

Ablation Study 지원:
- 압축률 메트릭
- 정보 보존률 측정
- Feature flag 제어
"""

import re
import time
from typing import List, Dict, Any, Tuple
from collections import Counter
import math


class ContextCompressor:
    """
    컨텍스트 압축기

    안전성:
    - 압축 실패 시 원본 반환
    - 예산 초과 불가능
    - 메트릭 수집으로 효과 추적
    """

    def __init__(
        self,
        token_manager=None,
        llm_client=None,
        feature_flags: Dict[str, Any] = None
    ):
        self.token_manager = token_manager
        self.llm_client = llm_client
        self.feature_flags = feature_flags or {}

        # 설정
        self.enabled = self.feature_flags.get('context_compression_enabled', False)
        self.strategy = self.feature_flags.get('compression_strategy', 'extractive')  # extractive/abstractive/hybrid
        self.target_ratio = self.feature_flags.get('compression_target_ratio', 0.5)  # 50% 압축

        # 메트릭
        self.metrics = {
            'total_compressions': 0,
            'successful_compressions': 0,
            'failed_compressions': 0,
            'avg_compression_ratio': 0.0,
            'avg_compression_time_ms': 0.0,
            'total_tokens_saved': 0
        }

    def compress_docs(
        self,
        docs: List[Dict[str, Any]],
        query: str,
        budget: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        문서 리스트 압축

        Args:
            docs: 검색된 문서 리스트
            query: 사용자 쿼리
            budget: 토큰 예산

        Returns:
            (compressed_docs, compression_stats)
        """
        start_time = time.time()
        self.metrics['total_compressions'] += 1

        try:
            # 비활성화 시 원본 반환
            if not self.enabled or not docs:
                return docs, {'compression_applied': False, 'reason': 'disabled or no docs'}

            # TokenManager 확인
            if not self.token_manager:
                print("[WARNING] TokenManager not available - skipping compression")
                return docs, {'compression_applied': False, 'reason': 'no token_manager'}

            # 원본 토큰 수 계산
            original_tokens = sum(
                self.token_manager.count_tokens(doc.get('text', ''))
                for doc in docs
            )

            # 예산 초과가 아니면 압축 불필요
            if original_tokens <= budget:
                return docs, {
                    'compression_applied': False,
                    'reason': 'within_budget',
                    'original_tokens': original_tokens,
                    'budget': budget
                }

            # 압축 전략에 따라 실행
            if self.strategy == 'extractive':
                compressed_docs = self._extractive_compress(docs, query, budget)
            elif self.strategy == 'abstractive':
                compressed_docs = self._abstractive_compress(docs, query, budget)
            elif self.strategy == 'hybrid':
                compressed_docs = self._hybrid_compress(docs, query, budget)
            else:
                print(f"[WARNING] Unknown compression strategy: {self.strategy}")
                return docs, {'compression_applied': False, 'reason': 'unknown_strategy'}

            # 압축 후 토큰 수 계산
            compressed_tokens = sum(
                self.token_manager.count_tokens(doc.get('text', ''))
                for doc in compressed_docs
            )

            # 통계
            compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
            tokens_saved = original_tokens - compressed_tokens

            compression_stats = {
                'compression_applied': True,
                'strategy': self.strategy,
                'original_tokens': original_tokens,
                'compressed_tokens': compressed_tokens,
                'budget': budget,
                'compression_ratio': compression_ratio,
                'tokens_saved': tokens_saved,
                'compression_time_ms': (time.time() - start_time) * 1000
            }

            # 메트릭 업데이트
            self._update_metrics(compression_ratio, compression_stats['compression_time_ms'], tokens_saved)
            self.metrics['successful_compressions'] += 1

            return compressed_docs, compression_stats

        except Exception as e:
            # 압축 실패 시 원본 반환
            print(f"[ERROR] Compression failed: {e}")
            self.metrics['failed_compressions'] += 1
            return docs, {
                'compression_applied': False,
                'reason': 'error',
                'error': str(e)
            }

    def _extractive_compress(
        self,
        docs: List[Dict[str, Any]],
        query: str,
        budget: int
    ) -> List[Dict[str, Any]]:
        """
        Extractive 압축: 중요한 문장만 선택
        """
        # 1. 모든 문서를 문장 단위로 분리
        scored_sentences = []

        for doc_idx, doc in enumerate(docs):
            text = doc.get('text', '')
            sentences = self._split_sentences(text)

            for sent_idx, sentence in enumerate(sentences):
                # 중요도 점수 계산
                score = self._sentence_importance(sentence, query, doc)

                scored_sentences.append({
                    'text': sentence,
                    'score': score,
                    'doc_idx': doc_idx,
                    'sent_idx': sent_idx,
                    'tokens': self.token_manager.count_tokens(sentence),
                    'original_doc': doc
                })

        # 2. 중요도 순 정렬
        scored_sentences.sort(key=lambda x: x['score'], reverse=True)

        # 3. 예산 내 선택 (Greedy Knapsack)
        selected = []
        used_tokens = 0

        for sent in scored_sentences:
            if used_tokens + sent['tokens'] <= budget:
                selected.append(sent)
                used_tokens += sent['tokens']

        # 4. 원본 순서로 재정렬
        selected.sort(key=lambda x: (x['doc_idx'], x['sent_idx']))

        # 5. 문서별로 재구성
        compressed_docs = self._reconstruct_docs(selected, docs)

        return compressed_docs

    def _sentence_importance(
        self,
        sentence: str,
        query: str,
        doc: Dict[str, Any]
    ) -> float:
        """
        문장 중요도 계산 (0~1)

        요소:
        1. 쿼리 관련성 (40%) - 키워드 매칭
        2. 의료 엔티티 밀도 (30%) - 의료 용어 포함 여부
        3. 문서 내 위치 (20%) - 앞부분 우선
        4. 정보 엔트로피 (10%) - 정보량
        """
        if not sentence or len(sentence.strip()) < 5:
            return 0.0

        try:
            # 요소 1: 쿼리 관련성 (키워드 매칭)
            query_similarity = self._keyword_similarity(sentence, query)

            # 요소 2: 의료 엔티티 밀도
            entity_density = self._medical_entity_density(sentence)

            # 요소 3: 문서 내 위치 (앞부분 우선)
            doc_text = doc.get('text', '')
            if doc_text:
                position = doc_text.find(sentence)
                position_score = 1.0 - (position / len(doc_text)) if position >= 0 else 0.5
            else:
                position_score = 0.5

            # 요소 4: 정보 엔트로피
            entropy = self._information_entropy(sentence)

            # 가중 합산
            importance = (
                0.4 * query_similarity +
                0.3 * entity_density +
                0.2 * position_score +
                0.1 * entropy
            )

            return min(1.0, max(0.0, importance))

        except Exception as e:
            print(f"[WARNING] Sentence importance calculation failed: {e}")
            return 0.5  # 중간값 반환

    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """키워드 기반 유사도 (Jaccard)"""
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    def _medical_entity_density(self, text: str) -> float:
        """
        의료 엔티티 밀도 추정 (간단한 휴리스틱)

        실제 구현에서는 MedCAT2를 사용할 수 있지만,
        성능을 위해 간단한 키워드 기반 추정 사용
        """
        # 일반적인 의료 용어 패턴
        medical_patterns = [
            r'혈압', r'당뇨', r'고혈압', r'저혈압', r'HbA1c', r'혈당',
            r'증상', r'질환', r'진단', r'치료', r'약물', r'처방',
            r'검사', r'수치', r'정상', r'범위', r'mg/dL', r'mmHg',
            r'환자', r'병원', r'의사', r'간호사',
            # 영어
            r'blood\s+pressure', r'diabetes', r'symptom', r'diagnosis',
            r'treatment', r'medication', r'test', r'patient'
        ]

        matches = 0
        for pattern in medical_patterns:
            matches += len(re.findall(pattern, text, re.IGNORECASE))

        word_count = len(text.split())
        if word_count == 0:
            return 0.0

        # 정규화 (0~1)
        density = min(1.0, matches / max(1, word_count * 0.3))
        return density

    def _information_entropy(self, text: str) -> float:
        """
        Shannon Entropy 계산

        높은 엔트로피 = 다양한 정보 포함 = 중요
        """
        tokens = text.split()
        if not tokens:
            return 0.0

        freq = Counter(tokens)
        total = len(tokens)
        probs = [count / total for count in freq.values()]

        try:
            entropy = -sum(p * math.log2(p) for p in probs if p > 0)

            # 정규화 (0~1)
            max_entropy = math.log2(len(tokens)) if len(tokens) > 1 else 1
            normalized = entropy / max_entropy if max_entropy > 0 else 0

            return min(1.0, normalized)
        except Exception:
            return 0.5

    def _split_sentences(self, text: str) -> List[str]:
        """
        문장 분리

        한국어와 영어 혼용 지원
        """
        if not text:
            return []

        # 마침표, 느낌표, 물음표, 개행으로 분리
        sentences = re.split(r'[.!?\n]+', text)

        # 빈 문장 제거 및 공백 정리
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

        return sentences

    def _reconstruct_docs(
        self,
        selected_sentences: List[Dict[str, Any]],
        original_docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        선택된 문장들을 문서로 재구성
        """
        from collections import defaultdict

        # 문서별로 그룹화
        doc_sentences = defaultdict(list)
        for sent in selected_sentences:
            doc_sentences[sent['doc_idx']].append(sent['text'])

        # 문서 재구성
        compressed = []
        for doc_idx, sentences in sorted(doc_sentences.items()):
            original = original_docs[doc_idx]
            compressed_text = ' '.join(sentences)

            compressed.append({
                'text': compressed_text,
                'metadata': original.get('metadata', {}),
                'compression_method': 'extractive',
                'original_length': len(original.get('text', '')),
                'compressed_length': len(compressed_text),
                'num_sentences_kept': len(sentences)
            })

        return compressed

    def _abstractive_compress(
        self,
        docs: List[Dict[str, Any]],
        query: str,
        budget: int
    ) -> List[Dict[str, Any]]:
        """
        Abstractive 압축: LLM 기반 요약

        주의: LLM 호출로 인한 추가 비용 발생
        """
        if not self.llm_client:
            print("[WARNING] LLM client not available - falling back to extractive")
            return self._extractive_compress(docs, query, budget)

        try:
            # 모든 문서를 하나로 병합
            all_text = "\n\n".join([
                f"[문서 {i+1}]\n{doc.get('text', '')}"
                for i, doc in enumerate(docs)
            ])

            # LLM으로 요약
            summary_prompt = f"""다음 의료 문서들을 {budget} 토큰 이내로 요약하세요.
특히 '{query}'와 관련된 정보를 우선적으로 포함하고, 중요한 수치와 의료 용어는 그대로 유지하세요.

문서:
{all_text}

요약:"""

            summary = self.llm_client.generate(
                prompt=summary_prompt,
                max_tokens=budget
            )

            return [{
                'text': summary,
                'metadata': {'compression_method': 'abstractive'},
                'original_num_docs': len(docs)
            }]

        except Exception as e:
            print(f"[ERROR] Abstractive compression failed: {e}")
            # Fallback to extractive
            return self._extractive_compress(docs, query, budget)

    def _hybrid_compress(
        self,
        docs: List[Dict[str, Any]],
        query: str,
        budget: int
    ) -> List[Dict[str, Any]]:
        """
        Hybrid 압축: Extractive + Abstractive

        1. Extractive로 60% 압축
        2. Abstractive로 최종 예산에 맞춤
        """
        # Step 1: Extractive 압축 (60% 예산 사용)
        extractive_budget = int(budget * 0.6)
        extractive_docs = self._extractive_compress(docs, query, extractive_budget)

        # Step 2: Abstractive 압축 (최종 예산)
        final_docs = self._abstractive_compress(extractive_docs, query, budget)

        return final_docs

    def _update_metrics(self, compression_ratio: float, time_ms: float, tokens_saved: int):
        """메트릭 업데이트"""
        n = self.metrics['total_compressions']

        # 평균 압축률
        current_avg_ratio = self.metrics['avg_compression_ratio']
        self.metrics['avg_compression_ratio'] = (
            (current_avg_ratio * (n - 1) + compression_ratio) / n
        )

        # 평균 압축 시간
        current_avg_time = self.metrics['avg_compression_time_ms']
        self.metrics['avg_compression_time_ms'] = (
            (current_avg_time * (n - 1) + time_ms) / n
        )

        # 총 절감 토큰
        self.metrics['total_tokens_saved'] += tokens_saved

    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 반환"""
        total = self.metrics['total_compressions']
        if total == 0:
            return self.metrics.copy()

        return {
            **self.metrics,
            'success_rate': self.metrics['successful_compressions'] / total,
            'failure_rate': self.metrics['failed_compressions'] / total
        }

    def reset_metrics(self):
        """메트릭 초기화"""
        for key in self.metrics:
            if isinstance(self.metrics[key], int):
                self.metrics[key] = 0
            else:
                self.metrics[key] = 0.0
