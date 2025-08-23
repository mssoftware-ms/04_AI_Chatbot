"""
Semantic Search and Retrieval Module

This module provides advanced semantic search capabilities with ChromaDB,
confidence scoring, and performance optimizations.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import numpy as np

import chromadb

from .embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from semantic retrieval"""
    id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    confidence_score: float
    source: Optional[str] = None


@dataclass
class SearchContext:
    """Context for search operations"""
    user_id: str
    conversation_history: List[str]
    filters: Optional[Dict[str, Any]] = None
    boost_recent: bool = True
    semantic_expansion: bool = True


class SemanticRetriever:
    """
    Advanced Semantic Retrieval System
    
    Provides intelligent document retrieval with confidence scoring,
    query expansion, and context-aware ranking.
    """
    
    def __init__(
        self,
        collection: chromadb.Collection,
        embedding_generator: EmbeddingGenerator,
        top_k: int = 5,
        min_similarity: float = 0.7,
        confidence_threshold: float = 0.6,
        max_results: int = 20,
        enable_reranking: bool = True
    ):
        """
        Initialize Semantic Retriever
        
        Args:
            collection: ChromaDB collection
            embedding_generator: Embedding generator instance
            top_k: Number of top results to retrieve
            min_similarity: Minimum similarity threshold
            confidence_threshold: Minimum confidence for results
            max_results: Maximum number of results to return
            enable_reranking: Whether to enable result reranking
        """
        self.collection = collection
        self.embedding_generator = embedding_generator
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.confidence_threshold = confidence_threshold
        self.max_results = max_results
        self.enable_reranking = enable_reranking
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "avg_retrieval_time": 0.0,
            "avg_results_returned": 0.0,
            "cache_hits": 0,
            "filter_applications": 0
        }
        
        # Query cache for performance
        self._query_cache: Dict[str, Tuple[List[RetrievalResult], datetime]] = {}
        self._cache_ttl_seconds = 300  # 5 minutes
        
        # Query expansion keywords
        self.expansion_terms = {
            "problem": ["issue", "error", "bug", "trouble", "difficulty"],
            "solution": ["fix", "resolve", "answer", "remedy", "workaround"],
            "how": ["method", "way", "process", "procedure", "steps"],
            "what": ["definition", "explanation", "meaning", "description"],
            "why": ["reason", "cause", "purpose", "explanation"],
            "when": ["time", "schedule", "timing", "date"],
            "where": ["location", "place", "position", "site"]
        }
    
    async def retrieve(
        self,
        query: str,
        context: Optional[SearchContext] = None,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            context: Search context with user info and filters
            top_k: Override default top_k
            filters: ChromaDB filters to apply
            
        Returns:
            List[RetrievalResult]: Ranked retrieval results
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # Use provided parameters or defaults
            k = top_k or self.top_k
            search_filters = filters or (context.filters if context else None)
            
            # Check cache first
            cache_key = self._generate_cache_key(query, search_filters)
            cached_results = self._get_cached_results(cache_key)
            if cached_results:
                self.stats["cache_hits"] += 1
                return cached_results[:k]
            
            # Expand query if enabled
            expanded_queries = self._expand_query(query, context)
            
            # Retrieve results for all query variations
            all_results = []
            for search_query, weight in expanded_queries:
                query_results = await self._perform_search(
                    search_query, k * 2, search_filters  # Get more results for reranking
                )
                
                # Apply weight to similarity scores
                for result in query_results:
                    result.similarity_score *= weight
                    
                all_results.extend(query_results)
            
            # Remove duplicates and merge results
            unique_results = self._deduplicate_results(all_results)
            
            # Apply confidence scoring
            scored_results = self._calculate_confidence_scores(unique_results, query)
            
            # Filter by thresholds
            filtered_results = [
                result for result in scored_results
                if (result.similarity_score >= self.min_similarity and 
                    result.confidence_score >= self.confidence_threshold)
            ]
            
            # Apply context-based ranking
            if context:
                filtered_results = self._apply_contextual_ranking(filtered_results, context)
            
            # Rerank if enabled
            if self.enable_reranking:
                filtered_results = await self._rerank_results(filtered_results, query)
            
            # Sort by combined score and take top results
            final_results = sorted(
                filtered_results,
                key=lambda x: x.similarity_score * x.confidence_score,
                reverse=True
            )[:k]
            
            # Cache results
            self._cache_results(cache_key, final_results)
            
            # Update statistics
            retrieval_time = time.time() - start_time
            self.stats["avg_retrieval_time"] = (
                (self.stats["avg_retrieval_time"] * (self.stats["total_queries"] - 1) + 
                 retrieval_time) / self.stats["total_queries"]
            )
            self.stats["avg_results_returned"] = (
                (self.stats["avg_results_returned"] * (self.stats["total_queries"] - 1) + 
                 len(final_results)) / self.stats["total_queries"]
            )
            
            logger.debug(
                f"Retrieved {len(final_results)} results in {retrieval_time:.3f}s "
                f"(query: '{query[:50]}...')"
            )
            
            return final_results
            
        except Exception as e:
            logger.error(f"Retrieval failed for query '{query}': {e}")
            return []
    
    async def _perform_search(
        self,
        query: str,
        n_results: int,
        where: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Perform the actual ChromaDB search"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_generator.generate_embedding(query)
            
            # Perform search
            search_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": n_results
            }
            
            if where:
                search_kwargs["where"] = where
                self.stats["filter_applications"] += 1
            
            results = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.collection.query(**search_kwargs)
            )
            
            # Convert to RetrievalResult objects
            retrieval_results = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = RetrievalResult(
                        id=results['ids'][0][i],
                        content=results['documents'][0][i],
                        metadata=results['metadatas'][0][i] if results['metadatas'][0] else {},
                        similarity_score=1 - results['distances'][0][i],  # Convert distance to similarity
                        confidence_score=0.0  # Will be calculated later
                    )
                    
                    # Add source from metadata
                    if result.metadata:
                        result.source = result.metadata.get('source', result.metadata.get('document_id'))
                    
                    retrieval_results.append(result)
            
            return retrieval_results
            
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            return []
    
    def _expand_query(
        self,
        query: str,
        context: Optional[SearchContext] = None
    ) -> List[Tuple[str, float]]:
        """
        Expand query with synonyms and related terms
        
        Returns:
            List[Tuple[str, float]]: List of (expanded_query, weight) tuples
        """
        queries = [(query, 1.0)]  # Original query with full weight
        
        if not context or not context.semantic_expansion:
            return queries
        
        query_lower = query.lower()
        
        # Add queries with expanded terms
        for term, expansions in self.expansion_terms.items():
            if term in query_lower:
                for expansion in expansions:
                    expanded_query = query_lower.replace(term, expansion)
                    queries.append((expanded_query, 0.7))  # Reduced weight for expansions
        
        # Add context from conversation history
        if context.conversation_history:
            # Use recent conversation for context (last 3 messages)
            recent_context = " ".join(context.conversation_history[-3:])
            contextual_query = f"{query} {recent_context}"
            queries.append((contextual_query, 0.8))
        
        return queries
    
    def _deduplicate_results(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Remove duplicate results and merge scores"""
        seen_ids: Set[str] = set()
        unique_results = []
        
        # Sort by similarity score first
        sorted_results = sorted(results, key=lambda x: x.similarity_score, reverse=True)
        
        for result in sorted_results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                unique_results.append(result)
            else:
                # Find existing result and potentially update score
                for existing in unique_results:
                    if existing.id == result.id:
                        # Take the higher similarity score
                        existing.similarity_score = max(
                            existing.similarity_score,
                            result.similarity_score
                        )
                        break
        
        return unique_results
    
    def _calculate_confidence_scores(
        self,
        results: List[RetrievalResult],
        query: str
    ) -> List[RetrievalResult]:
        """Calculate confidence scores for results"""
        if not results:
            return results
        
        query_words = set(query.lower().split())
        
        for result in results:
            confidence_factors = []
            
            # Similarity score factor
            confidence_factors.append(result.similarity_score)
            
            # Term overlap factor
            content_words = set(result.content.lower().split())
            term_overlap = len(query_words & content_words) / max(len(query_words), 1)
            confidence_factors.append(term_overlap * 0.8)
            
            # Content length factor (prefer substantial content)
            content_length_score = min(len(result.content) / 1000, 1.0) * 0.6
            confidence_factors.append(content_length_score)
            
            # Metadata quality factor
            metadata_score = 0.5
            if result.metadata:
                if result.metadata.get('source'):
                    metadata_score += 0.2
                if result.metadata.get('timestamp'):
                    metadata_score += 0.1
                if result.metadata.get('chunk_index', 0) == 0:
                    metadata_score += 0.2  # First chunk often more relevant
            confidence_factors.append(metadata_score)
            
            # Calculate final confidence score
            result.confidence_score = np.mean(confidence_factors)
        
        return results
    
    def _apply_contextual_ranking(
        self,
        results: List[RetrievalResult],
        context: SearchContext
    ) -> List[RetrievalResult]:
        """Apply context-based ranking adjustments"""
        if not context:
            return results
        
        for result in results:
            # Boost recent documents if enabled
            if context.boost_recent and result.metadata.get('timestamp'):
                try:
                    doc_time = datetime.fromisoformat(result.metadata['timestamp'])
                    days_old = (datetime.now() - doc_time).days
                    recency_boost = max(0, 1 - (days_old / 30)) * 0.2  # Boost up to 20%
                    result.similarity_score += recency_boost
                except (ValueError, KeyError):
                    pass
            
            # User-specific boosting (placeholder for future enhancement)
            if context.user_id and result.metadata.get('user_interactions'):
                # Could implement user preference learning here
                pass
        
        return results
    
    async def _rerank_results(
        self,
        results: List[RetrievalResult],
        query: str
    ) -> List[RetrievalResult]:
        """
        Rerank results using advanced scoring
        (Placeholder for future ML-based reranking)
        """
        # For now, use a simple reranking based on multiple factors
        for result in results:
            # Combine similarity and confidence with different weights
            combined_score = (
                result.similarity_score * 0.7 +
                result.confidence_score * 0.3
            )
            
            # Adjust based on content quality indicators
            content_quality = self._assess_content_quality(result.content)
            combined_score += content_quality * 0.1
            
            result.similarity_score = min(combined_score, 1.0)
        
        return results
    
    def _assess_content_quality(self, content: str) -> float:
        """Assess the quality of content for ranking purposes"""
        quality_score = 0.5  # Base score
        
        # Length factor (prefer substantial but not too long content)
        length = len(content)
        if 200 <= length <= 2000:
            quality_score += 0.3
        elif length < 50:
            quality_score -= 0.2
        
        # Structure factor (prefer well-formatted content)
        if '\n' in content:
            quality_score += 0.1
        if any(marker in content for marker in ['•', '-', '1.', '2.', '3.']):
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _generate_cache_key(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key for query and filters"""
        key_parts = [query]
        if filters:
            key_parts.append(str(sorted(filters.items())))
        return "|".join(key_parts)
    
    def _get_cached_results(self, cache_key: str) -> Optional[List[RetrievalResult]]:
        """Get cached results if still valid"""
        if cache_key in self._query_cache:
            results, timestamp = self._query_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl_seconds:
                return results
            else:
                del self._query_cache[cache_key]
        return None
    
    def _cache_results(self, cache_key: str, results: List[RetrievalResult]) -> None:
        """Cache search results"""
        self._query_cache[cache_key] = (results, datetime.now())
        
        # Clean up old cache entries periodically
        if len(self._query_cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Remove expired cache entries"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, (_, timestamp) in self._query_cache.items():
            if (current_time - timestamp).seconds > self._cache_ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._query_cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def search_similar_documents(
        self,
        document_id: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """Find documents similar to a given document"""
        try:
            # Get the document
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.collection.get(ids=[document_id])
            )
            
            if not result['documents'][0]:
                return []
            
            document_content = result['documents'][0][0]
            
            # Use document content as query
            return await self.retrieve(
                query=document_content[:500],  # Use first 500 chars as query
                top_k=top_k
            )
            
        except Exception as e:
            logger.error(f"Similar document search failed: {e}")
            return []
    
    async def get_document_by_id(self, document_id: str) -> Optional[RetrievalResult]:
        """Get a specific document by ID"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.collection.get(ids=[document_id])
            )
            
            if result['documents'][0]:
                return RetrievalResult(
                    id=document_id,
                    content=result['documents'][0][0],
                    metadata=result['metadatas'][0][0] if result['metadatas'][0] else {},
                    similarity_score=1.0,
                    confidence_score=1.0
                )
            
        except Exception as e:
            logger.error(f"Get document by ID failed: {e}")
        
        return None
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval performance statistics"""
        return {
            **self.stats,
            "cache_size": len(self._query_cache),
            "configuration": {
                "top_k": self.top_k,
                "min_similarity": self.min_similarity,
                "confidence_threshold": self.confidence_threshold,
                "enable_reranking": self.enable_reranking
            }
        }
    
    def clear_cache(self) -> None:
        """Clear the retrieval cache"""
        cache_size = len(self._query_cache)
        self._query_cache.clear()
        logger.info(f"Retrieval cache cleared ({cache_size} entries removed)")
    
    async def test_retrieval(self, test_query: str = "test") -> bool:
        """Test retrieval functionality"""
        try:
            results = await self.retrieve(test_query, top_k=1)
            return True
        except Exception as e:
            logger.error(f"Retrieval test failed: {e}")
            return False