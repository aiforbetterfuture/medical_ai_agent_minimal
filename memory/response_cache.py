"""
Response Cache Module
---------------------
This module provides caching functionality for agent responses with semantic similarity checking.
Stores query-response pairs and allows retrieval based on semantic similarity.

This implementation uses:
1. Sentence transformers for semantic similarity calculation
2. LRU caching for memory efficiency
3. Time-based expiry for cache freshness
4. Style variation for repeated responses
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
import json
import random
from collections import OrderedDict


@dataclass
class CachedResponse:
    """Represents a cached response with metadata"""
    query: str
    query_embedding: np.ndarray
    response: str
    timestamp: datetime
    hit_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    query_hash: str = field(init=False)

    def __post_init__(self):
        """Calculate hash for exact matching"""
        self.query_hash = hashlib.md5(self.query.lower().strip().encode()).hexdigest()


class ResponseCache:
    """
    Manages response caching with semantic similarity matching

    Features:
    - Semantic similarity matching using cosine similarity
    - LRU eviction for memory management
    - Time-based expiry
    - Style variation for repeated responses
    """

    def __init__(
        self,
        max_cache_size: int = 100,
        similarity_threshold: float = 0.85,
        cache_ttl_minutes: int = 60,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Initialize ResponseCache

        Args:
            max_cache_size: Maximum number of cached responses
            similarity_threshold: Minimum cosine similarity for cache hit (0-1)
            cache_ttl_minutes: Time-to-live for cached items in minutes
            model_name: Sentence transformer model for embeddings
        """
        self.max_cache_size = max_cache_size
        self.similarity_threshold = similarity_threshold
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)

        # Initialize sentence transformer
        self.encoder = SentenceTransformer(model_name)

        # OrderedDict for LRU implementation
        self.cache: OrderedDict[str, CachedResponse] = OrderedDict()

        # Statistics
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_tokens_saved': 0,
            'total_time_saved_ms': 0
        }

    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text"""
        return self.encoder.encode(text, convert_to_tensor=False)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _is_expired(self, cached_item: CachedResponse) -> bool:
        """Check if cached item has expired"""
        return datetime.now() - cached_item.timestamp > self.cache_ttl

    def _evict_expired(self):
        """Remove expired items from cache"""
        expired_keys = [
            key for key, item in self.cache.items()
            if self._is_expired(item)
        ]
        for key in expired_keys:
            del self.cache[key]

    def _evict_lru(self):
        """Evict least recently used item if cache is full"""
        if len(self.cache) >= self.max_cache_size:
            self.cache.popitem(last=False)  # Remove oldest item

    def find_similar(self, query: str) -> Optional[Tuple[CachedResponse, float]]:
        """
        Find the most similar cached query

        Args:
            query: User query to match

        Returns:
            Tuple of (cached_response, similarity_score) or None if no match
        """
        self.stats['total_queries'] += 1

        # Clean up expired items
        self._evict_expired()

        # Check for exact match first (faster)
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
        if query_hash in self.cache:
            cached = self.cache[query_hash]
            if not self._is_expired(cached):
                # Move to end (most recently used)
                self.cache.move_to_end(query_hash)
                cached.hit_count += 1
                self.stats['cache_hits'] += 1
                return (cached, 1.0)

        # Compute embedding for semantic search
        query_embedding = self._compute_embedding(query)

        # Find best semantic match
        best_match = None
        best_similarity = 0.0

        for key, cached_item in self.cache.items():
            if self._is_expired(cached_item):
                continue

            similarity = self._cosine_similarity(query_embedding, cached_item.query_embedding)

            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = cached_item

        if best_match:
            # Move to end (most recently used)
            self.cache.move_to_end(best_match.query_hash)
            best_match.hit_count += 1
            self.stats['cache_hits'] += 1
            return (best_match, best_similarity)

        self.stats['cache_misses'] += 1
        return None

    def add(
        self,
        query: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CachedResponse:
        """
        Add a new query-response pair to cache

        Args:
            query: User query
            response: Generated response
            metadata: Additional metadata to store

        Returns:
            CachedResponse object
        """
        # Evict LRU if needed
        self._evict_lru()

        # Create cached response
        cached = CachedResponse(
            query=query,
            query_embedding=self._compute_embedding(query),
            response=response,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        # Add to cache
        self.cache[cached.query_hash] = cached

        return cached

    def update_stats(self, tokens_saved: int, time_saved_ms: int):
        """Update statistics for reporting"""
        self.stats['total_tokens_saved'] += tokens_saved
        self.stats['total_time_saved_ms'] += time_saved_ms

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_hit_rate = (
            self.stats['cache_hits'] / self.stats['total_queries']
            if self.stats['total_queries'] > 0 else 0
        )

        return {
            **self.stats,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.cache),
            'max_cache_size': self.max_cache_size
        }

    def clear(self):
        """Clear all cached items"""
        self.cache.clear()
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_tokens_saved': 0,
            'total_time_saved_ms': 0
        }


class ResponseStyleVariator:
    """
    Provides style variation for cached responses to avoid repetitive outputs
    while preserving semantic meaning
    """

    def __init__(self):
        """Initialize style variator with variation patterns"""
        self.greeting_variations = [
            "",
            "다시 말씀드리면,\n",
            "앞서 말씀드린 내용을 정리하면,\n",
            "이전에 설명드린 바와 같이,\n",
            "요약하자면,\n",
        ]

        self.ending_variations = [
            "",
            "\n\n추가로 궁금하신 점이 있으시면 말씀해 주세요.",
            "\n\n더 자세한 정보가 필요하시면 알려주세요.",
            "\n\n다른 관련 질문이 있으시다면 언제든 문의해 주세요.",
            "\n\n이해에 도움이 되셨기를 바랍니다.",
        ]

        self.connector_variations = {
            "또한": ["그리고", "더불어", "아울러", "게다가"],
            "그러나": ["하지만", "그렇지만", "그럼에도", "다만"],
            "따라서": ["그러므로", "그래서", "이에 따라", "결과적으로"],
            "예를 들어": ["예컨대", "가령", "이를테면", "구체적으로"],
        }

    def vary_response(self, original_response: str, variation_level: float = 0.3) -> str:
        """
        Apply style variations to a response

        Args:
            original_response: Original cached response
            variation_level: How much to vary (0-1, where 0 is no change)

        Returns:
            Style-varied response
        """
        if random.random() > variation_level:
            return original_response

        varied = original_response

        # Add greeting variation
        if random.random() < 0.5:
            greeting = random.choice(self.greeting_variations)
            if greeting:
                varied = greeting + varied

        # Replace some connectors
        for original, variations in self.connector_variations.items():
            if original in varied and random.random() < 0.3:
                replacement = random.choice(variations)
                varied = varied.replace(original, replacement, 1)

        # Add ending variation
        if random.random() < 0.3:
            ending = random.choice(self.ending_variations)
            if ending and not varied.strip().endswith(tuple([e.strip() for e in self.ending_variations])):
                varied = varied.rstrip() + ending

        return varied