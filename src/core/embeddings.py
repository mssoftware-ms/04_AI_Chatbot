"""
OpenAI Embedding Generation Module

This module provides embedding generation functionality using OpenAI's 
text-embedding-3-large model with batch processing and caching optimizations.
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import json

import openai
import numpy as np
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    OpenAI Embedding Generator with Caching and Batch Processing
    
    Provides efficient embedding generation with automatic batching,
    caching, and retry mechanisms for optimal performance.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        cache_ttl_hours: int = 24
    ):
        """
        Initialize Embedding Generator
        
        Args:
            api_key: OpenAI API key
            model: OpenAI embedding model name
            batch_size: Maximum texts per batch request
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.api_key = api_key
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        
        # Async OpenAI client
        self.client: Optional[AsyncOpenAI] = None
        
        # Embedding cache for performance
        self._embedding_cache: Dict[str, Tuple[List[float], datetime]] = {}
        
        # Performance tracking
        self.stats = {
            "total_requests": 0,
            "cached_requests": 0,
            "failed_requests": 0,
            "batch_requests": 0,
            "avg_batch_time": 0.0,
            "total_tokens": 0
        }
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the async OpenAI client"""
        try:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self._initialized = True
            logger.info(f"EmbeddingGenerator initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingGenerator: {e}")
            raise
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{self.model}:{text_hash}"
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cached embedding is still valid"""
        return datetime.now() - timestamp < self.cache_ttl
    
    async def generate_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            List[float]: Embedding vector
        """
        if not self._initialized:
            raise RuntimeError("EmbeddingGenerator not initialized")
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                embedding, timestamp = self._embedding_cache[cache_key]
                if self._is_cache_valid(timestamp):
                    self.stats["cached_requests"] += 1
                    return embedding
        
        # Generate new embedding
        embeddings = await self.generate_embeddings([text], use_cache=False)
        return embeddings[0] if embeddings else []
    
    async def generate_embeddings(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batch processing
        
        Args:
            texts: List of input texts to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not self._initialized or not self.client:
            raise RuntimeError("EmbeddingGenerator not initialized")
        
        if not texts:
            return []
        
        start_time = time.time()
        all_embeddings = []
        texts_to_process = []
        cache_indices = {}
        
        # Check cache for each text
        for i, text in enumerate(texts):
            if use_cache:
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    embedding, timestamp = self._embedding_cache[cache_key]
                    if self._is_cache_valid(timestamp):
                        cache_indices[i] = embedding
                        self.stats["cached_requests"] += 1
                        continue
            
            texts_to_process.append((i, text))
        
        # Process uncached texts in batches
        new_embeddings = {}
        if texts_to_process:
            for batch_start in range(0, len(texts_to_process), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(texts_to_process))
                batch_indices_texts = texts_to_process[batch_start:batch_end]
                batch_texts = [text for _, text in batch_indices_texts]
                
                batch_embeddings = await self._generate_batch_embeddings(batch_texts)
                
                # Store embeddings with their original indices
                for j, embedding in enumerate(batch_embeddings):
                    original_index = batch_indices_texts[j][0]
                    original_text = batch_indices_texts[j][1]
                    new_embeddings[original_index] = embedding
                    
                    # Cache the embedding
                    if use_cache:
                        cache_key = self._get_cache_key(original_text)
                        self._embedding_cache[cache_key] = (embedding, datetime.now())
        
        # Combine cached and new embeddings in original order
        for i in range(len(texts)):
            if i in cache_indices:
                all_embeddings.append(cache_indices[i])
            elif i in new_embeddings:
                all_embeddings.append(new_embeddings[i])
            else:
                # This should not happen, but provide empty embedding as fallback
                logger.warning(f"No embedding found for text at index {i}")
                all_embeddings.append([])
        
        processing_time = time.time() - start_time
        logger.info(
            f"Generated {len(texts)} embeddings in {processing_time:.2f}s "
            f"({len(cache_indices)} cached, {len(new_embeddings)} new)"
        )
        
        return all_embeddings
    
    async def _generate_batch_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts with retry logic
        
        Args:
            texts: Batch of texts to embed
            
        Returns:
            List[List[float]]: Batch of embedding vectors
        """
        for attempt in range(self.max_retries + 1):
            try:
                batch_start = time.time()
                self.stats["batch_requests"] += 1
                
                # Clean texts (remove excessive whitespace, empty texts)
                cleaned_texts = []
                for text in texts:
                    cleaned = text.strip()
                    if not cleaned:
                        cleaned = "empty"  # OpenAI doesn't accept empty strings
                    # Truncate if too long (OpenAI has token limits)
                    if len(cleaned) > 8000:  # Conservative limit
                        cleaned = cleaned[:8000] + "..."
                    cleaned_texts.append(cleaned)
                
                # Make API request
                response = await self.client.embeddings.create(
                    input=cleaned_texts,
                    model=self.model
                )
                
                # Extract embeddings
                embeddings = [item.embedding for item in response.data]
                
                # Update statistics
                batch_time = time.time() - batch_start
                self.stats["avg_batch_time"] = (
                    (self.stats["avg_batch_time"] * (self.stats["batch_requests"] - 1) + batch_time) /
                    self.stats["batch_requests"]
                )
                self.stats["total_tokens"] += response.usage.total_tokens
                self.stats["total_requests"] += len(texts)
                
                logger.debug(
                    f"Batch embedding generated: {len(texts)} texts, "
                    f"{response.usage.total_tokens} tokens, {batch_time:.2f}s"
                )
                
                return embeddings
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Rate limit exceeded, max retries reached")
                    self.stats["failed_requests"] += len(texts)
                    raise
                    
            except openai.APIError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.warning(f"API error: {e}, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"API error after max retries: {e}")
                    self.stats["failed_requests"] += len(texts)
                    raise
                    
            except Exception as e:
                logger.error(f"Unexpected error in batch embedding: {e}")
                self.stats["failed_requests"] += len(texts)
                raise
        
        # Should never reach here
        return []
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model
        
        Returns:
            int: Embedding dimension
        """
        model_dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536
        }
        return model_dimensions.get(self.model, 1536)
    
    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Cosine similarity (-1 to 1)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to query
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            
        Returns:
            List[Tuple[int, float]]: List of (index, similarity) tuples
        """
        try:
            similarities = []
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append((i, similarity))
            
            # Sort by similarity (descending) and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar embeddings: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Clear embedding cache"""
        cache_size = len(self._embedding_cache)
        self._embedding_cache.clear()
        logger.info(f"Embedding cache cleared ({cache_size} entries removed)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        valid_entries = 0
        expired_entries = 0
        
        now = datetime.now()
        for _, (_, timestamp) in self._embedding_cache.items():
            if self._is_cache_valid(timestamp):
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": len(self._embedding_cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_hit_rate": (
                self.stats["cached_requests"] / 
                max(self.stats["total_requests"], 1)
            )
        }
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries"""
        expired_keys = []
        now = datetime.now()
        
        for key, (_, timestamp) in self._embedding_cache.items():
            if not self._is_cache_valid(timestamp):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._embedding_cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        return len(expired_keys)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            **self.stats,
            "cache_stats": self.get_cache_stats(),
            "model": self.model,
            "embedding_dimension": self.get_embedding_dimension(),
            "avg_requests_per_batch": (
                self.stats["total_requests"] / 
                max(self.stats["batch_requests"], 1)
            )
        }
    
    async def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            if not self._initialized:
                await self.initialize()
                
            test_embedding = await self.generate_embedding("test connection")
            return len(test_embedding) > 0
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False