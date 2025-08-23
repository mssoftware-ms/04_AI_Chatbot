"""
Batch processing utilities for efficient data handling.

This module provides optimized batch processing capabilities for document ingestion,
embedding generation, and other bulk operations in the RAG system.
"""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class BatchStrategy(Enum):
    """Batch processing strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel" 
    ADAPTIVE = "adaptive"
    PIPELINE = "pipeline"


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 100
    max_concurrent: int = 5
    timeout_per_batch: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    strategy: BatchStrategy = BatchStrategy.ADAPTIVE
    preserve_order: bool = True
    fail_fast: bool = False


@dataclass
class BatchResult(Generic[R]):
    """Result of batch processing operation."""
    success_count: int = 0
    error_count: int = 0
    total_items: int = 0
    processing_time: float = 0.0
    results: List[R] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.success_count / self.total_items) * 100
    
    @property
    def throughput(self) -> float:
        """Calculate throughput (items per second)."""
        if self.processing_time == 0:
            return 0.0
        return self.total_items / self.processing_time


class BatchProcessor(Generic[T, R]):
    """Generic batch processor with configurable strategies."""
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """
        Initialize batch processor.
        
        Args:
            config: Batch processing configuration
        """
        self.config = config or BatchConfig()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent)
        
    async def process_batches(
        self,
        items: List[T],
        processor_func: Callable[[List[T]], Awaitable[List[R]]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> BatchResult[R]:
        """
        Process items in batches using configured strategy.
        
        Args:
            items: Items to process
            processor_func: Function to process each batch
            progress_callback: Optional progress callback
            
        Returns:
            BatchResult with processing statistics and results
        """
        start_time = time.time()
        
        result = BatchResult[R](total_items=len(items))
        
        if not items:
            return result
        
        # Split items into batches
        batches = self._create_batches(items)
        
        logger.info(f"Processing {len(items)} items in {len(batches)} batches")
        
        try:
            # Process batches based on strategy
            if self.config.strategy == BatchStrategy.SEQUENTIAL:
                batch_results = await self._process_sequential(
                    batches, processor_func, progress_callback
                )
            elif self.config.strategy == BatchStrategy.PARALLEL:
                batch_results = await self._process_parallel(
                    batches, processor_func, progress_callback
                )
            elif self.config.strategy == BatchStrategy.ADAPTIVE:
                batch_results = await self._process_adaptive(
                    batches, processor_func, progress_callback
                )
            elif self.config.strategy == BatchStrategy.PIPELINE:
                batch_results = await self._process_pipeline(
                    batches, processor_func, progress_callback
                )
            else:
                raise ValueError(f"Unknown batch strategy: {self.config.strategy}")
            
            # Aggregate results
            self._aggregate_results(result, batch_results)
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            result.errors.append({
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "batch_strategy": self.config.strategy.value
            })
        
        result.processing_time = time.time() - start_time
        
        logger.info(
            f"Batch processing completed: {result.success_count}/{result.total_items} "
            f"successful ({result.success_rate:.1f}%) in {result.processing_time:.2f}s"
        )
        
        return result
    
    def _create_batches(self, items: List[T]) -> List[List[T]]:
        """Split items into batches."""
        batch_size = self.config.batch_size
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    async def _process_sequential(
        self,
        batches: List[List[T]],
        processor_func: Callable[[List[T]], Awaitable[List[R]]],
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[BatchResult[R]]:
        """Process batches sequentially."""
        batch_results = []
        
        for i, batch in enumerate(batches):
            batch_result = await self._process_single_batch(batch, processor_func, i)
            batch_results.append(batch_result)
            
            if progress_callback:
                progress_callback(i + 1, len(batches))
        
        return batch_results
    
    async def _process_parallel(
        self,
        batches: List[List[T]],
        processor_func: Callable[[List[T]], Awaitable[List[R]]],
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[BatchResult[R]]:
        """Process batches in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        completed = 0
        
        async def process_with_semaphore(batch, batch_idx):
            nonlocal completed
            async with semaphore:
                result = await self._process_single_batch(batch, processor_func, batch_idx)
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(batches))
                return result
        
        # Execute all batches concurrently
        tasks = [
            process_with_semaphore(batch, i)
            for i, batch in enumerate(batches)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_adaptive(
        self,
        batches: List[List[T]],
        processor_func: Callable[[List[T]], Awaitable[List[R]]],
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[BatchResult[R]]:
        """Adaptively process batches based on performance."""
        batch_results = []
        current_concurrency = min(2, self.config.max_concurrent)
        avg_processing_time = 0.0
        
        # Process first few batches to establish baseline
        initial_batches = min(3, len(batches))
        for i in range(initial_batches):
            start_time = time.time()
            batch_result = await self._process_single_batch(
                batches[i], processor_func, i
            )
            processing_time = time.time() - start_time
            
            avg_processing_time = (
                (avg_processing_time * i + processing_time) / (i + 1)
            )
            
            batch_results.append(batch_result)
            
            if progress_callback:
                progress_callback(i + 1, len(batches))
        
        # Process remaining batches with adaptive concurrency
        if len(batches) > initial_batches:
            # Adjust concurrency based on performance
            if avg_processing_time < 1.0:  # Fast processing
                current_concurrency = self.config.max_concurrent
            elif avg_processing_time < 5.0:  # Medium processing
                current_concurrency = max(2, self.config.max_concurrent // 2)
            else:  # Slow processing
                current_concurrency = 1
            
            remaining_batches = batches[initial_batches:]
            
            # Process remaining batches with adjusted concurrency
            semaphore = asyncio.Semaphore(current_concurrency)
            completed = initial_batches
            
            async def adaptive_process(batch, batch_idx):
                nonlocal completed
                async with semaphore:
                    result = await self._process_single_batch(
                        batch, processor_func, batch_idx + initial_batches
                    )
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(batches))
                    return result
            
            tasks = [
                adaptive_process(batch, i)
                for i, batch in enumerate(remaining_batches)
            ]
            
            remaining_results = await asyncio.gather(*tasks, return_exceptions=True)
            batch_results.extend(remaining_results)
        
        return batch_results
    
    async def _process_pipeline(
        self,
        batches: List[List[T]],
        processor_func: Callable[[List[T]], Awaitable[List[R]]],
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[BatchResult[R]]:
        """Process batches using pipeline approach."""
        # Create a queue for batch processing
        batch_queue = asyncio.Queue(maxsize=self.config.max_concurrent * 2)
        result_queue = asyncio.Queue()
        
        # Producer: Add batches to queue
        async def producer():
            for i, batch in enumerate(batches):
                await batch_queue.put((i, batch))
            
            # Signal completion
            for _ in range(self.config.max_concurrent):
                await batch_queue.put(None)
        
        # Consumer: Process batches from queue
        async def consumer():
            while True:
                item = await batch_queue.get()
                if item is None:
                    break
                
                batch_idx, batch = item
                batch_result = await self._process_single_batch(
                    batch, processor_func, batch_idx
                )
                await result_queue.put((batch_idx, batch_result))
        
        # Start producer and consumers
        producer_task = asyncio.create_task(producer())
        consumer_tasks = [
            asyncio.create_task(consumer())
            for _ in range(self.config.max_concurrent)
        ]
        
        # Collect results
        batch_results = [None] * len(batches)
        completed = 0
        
        while completed < len(batches):
            batch_idx, batch_result = await result_queue.get()
            batch_results[batch_idx] = batch_result
            completed += 1
            
            if progress_callback:
                progress_callback(completed, len(batches))
        
        # Wait for all tasks to complete
        await producer_task
        await asyncio.gather(*consumer_tasks)
        
        return batch_results
    
    async def _process_single_batch(
        self,
        batch: List[T],
        processor_func: Callable[[List[T]], Awaitable[List[R]]],
        batch_idx: int
    ) -> BatchResult[R]:
        """Process a single batch with retry logic."""
        result = BatchResult[R](total_items=len(batch))
        
        for attempt in range(self.config.retry_attempts):
            try:
                # Apply timeout
                batch_results = await asyncio.wait_for(
                    processor_func(batch),
                    timeout=self.config.timeout_per_batch
                )
                
                result.results = batch_results
                result.success_count = len(batch_results)
                return result
                
            except asyncio.TimeoutError:
                error_msg = f"Batch {batch_idx} timed out (attempt {attempt + 1})"
                logger.warning(error_msg)
                
                if attempt == self.config.retry_attempts - 1:
                    result.errors.append({
                        "error": "Timeout",
                        "batch_idx": batch_idx,
                        "attempt": attempt + 1,
                        "message": error_msg
                    })
                    result.error_count = len(batch)
                else:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                
            except Exception as e:
                error_msg = f"Batch {batch_idx} failed: {str(e)} (attempt {attempt + 1})"
                logger.error(error_msg)
                
                if attempt == self.config.retry_attempts - 1:
                    result.errors.append({
                        "error": str(e),
                        "batch_idx": batch_idx,
                        "attempt": attempt + 1,
                        "message": error_msg
                    })
                    result.error_count = len(batch)
                    
                    if self.config.fail_fast:
                        raise
                else:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return result
    
    def _aggregate_results(
        self,
        final_result: BatchResult[R],
        batch_results: List[BatchResult[R]]
    ) -> None:
        """Aggregate results from individual batch processing."""
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                final_result.errors.append({
                    "error": str(batch_result),
                    "type": type(batch_result).__name__,
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            final_result.success_count += batch_result.success_count
            final_result.error_count += batch_result.error_count
            
            if self.config.preserve_order:
                final_result.results.extend(batch_result.results)
            
            final_result.errors.extend(batch_result.errors)
    
    async def close(self):
        """Clean up resources."""
        self.executor.shutdown(wait=True)


class DocumentBatchProcessor(BatchProcessor[str, Dict[str, Any]]):
    """Specialized batch processor for document processing."""
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """Initialize document batch processor."""
        if config is None:
            config = BatchConfig(
                batch_size=50,  # Smaller batches for documents
                max_concurrent=3,  # Limit concurrency for memory usage
                timeout_per_batch=60.0,  # Longer timeout for document processing
                strategy=BatchStrategy.ADAPTIVE
            )
        super().__init__(config)
    
    async def process_documents(
        self,
        documents: List[str],
        chunker: Callable[[List[str]], Awaitable[List[List[str]]]],
        embedder: Callable[[List[str]], Awaitable[List[List[float]]]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> BatchResult[Dict[str, Any]]:
        """
        Process documents through chunking and embedding pipeline.
        
        Args:
            documents: Documents to process
            chunker: Function to chunk documents
            embedder: Function to generate embeddings
            progress_callback: Optional progress callback
            
        Returns:
            BatchResult with processed document data
        """
        async def process_batch(doc_batch: List[str]) -> List[Dict[str, Any]]:
            """Process a batch of documents."""
            batch_results = []
            
            # Chunk documents
            chunks_batch = await chunker(doc_batch)
            
            # Generate embeddings for all chunks
            all_chunks = [chunk for doc_chunks in chunks_batch for chunk in doc_chunks]
            
            if all_chunks:
                embeddings = await embedder(all_chunks)
                
                # Reconstruct document structure
                embedding_idx = 0
                for i, doc_chunks in enumerate(chunks_batch):
                    doc_embeddings = embeddings[embedding_idx:embedding_idx + len(doc_chunks)]
                    embedding_idx += len(doc_chunks)
                    
                    batch_results.append({
                        "document": doc_batch[i],
                        "chunks": doc_chunks,
                        "embeddings": doc_embeddings,
                        "chunk_count": len(doc_chunks)
                    })
            else:
                # Handle documents with no chunks
                for doc in doc_batch:
                    batch_results.append({
                        "document": doc,
                        "chunks": [],
                        "embeddings": [],
                        "chunk_count": 0
                    })
            
            return batch_results
        
        return await self.process_batches(documents, process_batch, progress_callback)


# Utility functions for common batch operations
async def batch_process_simple(
    items: List[T],
    processor: Callable[[T], Awaitable[R]],
    batch_size: int = 100,
    max_concurrent: int = 5
) -> List[R]:
    """
    Simple utility for batch processing individual items.
    
    Args:
        items: Items to process
        processor: Function to process individual items
        batch_size: Size of each batch
        max_concurrent: Maximum concurrent batches
        
    Returns:
        List of processed results
    """
    async def batch_processor(batch: List[T]) -> List[R]:
        """Process a batch of items."""
        tasks = [processor(item) for item in batch]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    config = BatchConfig(
        batch_size=batch_size,
        max_concurrent=max_concurrent,
        strategy=BatchStrategy.PARALLEL
    )
    
    batch_proc = BatchProcessor[T, R](config)
    result = await batch_proc.process_batches(items, batch_processor)
    await batch_proc.close()
    
    return result.results


__all__ = [
    'BatchStrategy',
    'BatchConfig', 
    'BatchResult',
    'BatchProcessor',
    'DocumentBatchProcessor',
    'batch_process_simple'
]