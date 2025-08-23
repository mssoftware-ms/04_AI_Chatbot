"""
Main RAG System with ChromaDB Integration

This module provides the core RAG system implementation with async support,
ChromaDB integration, and performance optimizations for <2 second response times.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import hashlib
import json
from functools import lru_cache, wraps

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import openai

from .embeddings import EmbeddingGenerator
from .chunking import DocumentChunker
from .retrieval import SemanticRetriever
from .prompts import PromptManager
from .memory import ConversationMemory

logger = logging.getLogger(__name__)


class RAGSystem:
    """
    Main RAG (Retrieval-Augmented Generation) System
    
    Provides comprehensive RAG functionality with ChromaDB integration,
    OpenAI embeddings, and conversation memory management.
    """
    
    def __init__(
        self,
        openai_api_key: str,
        chroma_db_path: str = "./data/chroma_db",
        collection_name: str = "whatsapp_chatbot",
        embedding_model: str = "text-embedding-3-large",
        chat_model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        response_timeout: float = 1.8  # <2 seconds target
    ):
        """
        Initialize RAG System
        
        Args:
            openai_api_key: OpenAI API key
            chroma_db_path: Path to ChromaDB storage
            collection_name: ChromaDB collection name
            embedding_model: OpenAI embedding model
            chat_model: OpenAI chat model
            max_tokens: Maximum response tokens
            temperature: Model temperature
            response_timeout: Target response time in seconds
        """
        self.openai_api_key = openai_api_key
        self.chroma_db_path = chroma_db_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.response_timeout = response_timeout
        
        # Initialize components
        self.embedding_generator: Optional[EmbeddingGenerator] = None
        self.document_chunker: Optional[DocumentChunker] = None
        self.semantic_retriever: Optional[SemanticRetriever] = None
        self.prompt_manager: Optional[PromptManager] = None
        self.conversation_memory: Optional[ConversationMemory] = None
        
        # ChromaDB components
        self.chroma_client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None
        
        # Performance monitoring
        self.performance_stats = {
            "total_queries": 0,
            "avg_response_time": 0.0,
            "successful_queries": 0,
            "failed_queries": 0,
            "cache_hits": 0
        }
        
        # Enhanced caching system
        self._response_cache: Dict[str, Tuple[str, datetime]] = {}
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._max_cache_size = 1000
        
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Async initialization of RAG system components
        
        Returns:
            bool: True if initialization successful
        """
        try:
            start_time = time.time()
            logger.info("Initializing RAG System...")
            
            # Initialize OpenAI client
            openai.api_key = self.openai_api_key
            
            # Initialize ChromaDB
            await self._initialize_chromadb()
            
            # Initialize components
            self.embedding_generator = EmbeddingGenerator(
                api_key=self.openai_api_key,
                model=self.embedding_model
            )
            
            self.document_chunker = DocumentChunker(
                chunk_size=1000,
                chunk_overlap=200,
                enable_semantic_chunking=True
            )
            
            self.semantic_retriever = SemanticRetriever(
                collection=self.collection,
                embedding_generator=self.embedding_generator,
                top_k=5,
                min_similarity=0.7
            )
            
            self.prompt_manager = PromptManager(
                chat_model=self.chat_model,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            self.conversation_memory = ConversationMemory(
                max_history=10,
                context_window=4000
            )
            
            # Initialize components
            await self.embedding_generator.initialize()
            
            self._initialized = True
            
            init_time = time.time() - start_time
            logger.info(f"RAG System initialized successfully in {init_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG System: {e}")
            return False
    
    async def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client and collection"""
        try:
            # Create ChromaDB client with persistent storage
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection with embedding function
            embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.openai_api_key,
                model_name=self.embedding_model
            )
            
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name,
                    embedding_function=embedding_function
                )
                logger.info(f"Connected to existing collection: {self.collection_name}")
            except ValueError:
                # Collection doesn't exist, create it
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_function,
                    metadata={"description": "WhatsApp AI Chatbot RAG Collection"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 100
    ) -> bool:
        """
        Add documents to the vector database with batch processing
        
        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            batch_size: Size of processing batches
            
        Returns:
            bool: True if successful
        """
        if not self._initialized:
            raise RuntimeError("RAG System not initialized")
            
        try:
            start_time = time.time()
            
            # Chunk documents
            all_chunks = []
            all_metadatas = []
            
            for i, doc in enumerate(documents):
                chunks = await self.document_chunker.chunk_document(doc)
                doc_metadata = metadatas[i] if metadatas else {}
                
                for j, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    chunk_metadata = {
                        **doc_metadata,
                        "document_id": f"doc_{i}",
                        "chunk_id": f"doc_{i}_chunk_{j}",
                        "chunk_index": j,
                        "timestamp": datetime.now().isoformat()
                    }
                    all_metadatas.append(chunk_metadata)
            
            # Process in batches
            total_chunks = len(all_chunks)
            successful_batches = 0
            
            for batch_start in range(0, total_chunks, batch_size):
                batch_end = min(batch_start + batch_size, total_chunks)
                batch_chunks = all_chunks[batch_start:batch_end]
                batch_metadatas = all_metadatas[batch_start:batch_end]
                
                # Generate unique IDs for this batch
                batch_ids = [f"chunk_{batch_start + i}" for i in range(len(batch_chunks))]
                
                try:
                    # Add to ChromaDB collection
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.collection.add(
                            documents=batch_chunks,
                            metadatas=batch_metadatas,
                            ids=batch_ids
                        )
                    )
                    successful_batches += 1
                    
                except Exception as e:
                    logger.error(f"Failed to add batch {batch_start}-{batch_end}: {e}")
                    
            processing_time = time.time() - start_time
            logger.info(
                f"Added {total_chunks} chunks in {successful_batches} batches "
                f"({processing_time:.2f}s)"
            )
            
            return successful_batches > 0
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    async def query(
        self,
        question: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Process a query with RAG pipeline
        
        Args:
            question: User question
            user_id: Unique user identifier
            context: Additional context information
            stream: Whether to stream response
            
        Yields:
            str: Response chunks if streaming, complete response if not
        """
        if not self._initialized:
            raise RuntimeError("RAG System not initialized")
            
        start_time = time.time()
        self.performance_stats["total_queries"] += 1
        
        try:
            # Enhanced cache check with proper hashing
            cache_key = self._generate_cache_key(user_id, question)
            cached_response = await self._check_cache(cache_key)
            if cached_response:
                self.performance_stats["cache_hits"] += 1
                if stream:
                    for chunk in cached_response.split():
                        yield chunk + " "
                        await asyncio.sleep(0.01)  # Simulate streaming
                else:
                    yield cached_response
                return
            
            # Retrieve relevant context
            retrieval_start = time.time()
            retrieved_docs = await self.semantic_retriever.retrieve(
                query=question,
                top_k=5
            )
            retrieval_time = time.time() - retrieval_start
            
            # Get conversation history
            conversation_history = await self.conversation_memory.get_context(user_id)
            
            # Build context for generation
            context_data = {
                "retrieved_documents": retrieved_docs,
                "conversation_history": conversation_history,
                "user_context": context or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate response
            generation_start = time.time()
            response = ""
            
            if stream:
                async for chunk in self.prompt_manager.generate_streaming_response(
                    question=question,
                    context=context_data
                ):
                    response += chunk
                    yield chunk
            else:
                response = await self.prompt_manager.generate_response(
                    question=question,
                    context=context_data
                )
                yield response
                
            generation_time = time.time() - generation_start
            
            # Update conversation memory
            await self.conversation_memory.add_interaction(
                user_id=user_id,
                user_message=question,
                assistant_response=response,
                context=context_data
            )
            
            # Cache response with size management
            await self._cache_response(cache_key, response)
            
            # Update performance stats
            total_time = time.time() - start_time
            self.performance_stats["successful_queries"] += 1
            self.performance_stats["avg_response_time"] = (
                (self.performance_stats["avg_response_time"] * 
                 (self.performance_stats["successful_queries"] - 1) + total_time) /
                self.performance_stats["successful_queries"]
            )
            
            logger.info(
                f"Query processed in {total_time:.2f}s "
                f"(retrieval: {retrieval_time:.2f}s, generation: {generation_time:.2f}s)"
            )
            
            # Performance warning if over target
            if total_time > self.response_timeout:
                logger.warning(
                    f"Response time {total_time:.2f}s exceeded target {self.response_timeout}s"
                )
                
        except asyncio.TimeoutError:
            self.performance_stats["failed_queries"] += 1
            logger.error("Query timed out")
            yield "I apologize, but I'm experiencing high load. Please try again shortly."
            
        except Exception as e:
            self.performance_stats["failed_queries"] += 1
            logger.error(f"Query failed: {e}")
            yield "I apologize, but I encountered an error processing your request. Please try again."
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        if not self._initialized or not self.collection:
            return {}
            
        try:
            count = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.collection.count()
            )
            
            return {
                "document_count": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model,
                "performance_stats": self.performance_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def _generate_cache_key(self, user_id: str, question: str) -> str:
        """Generate a consistent cache key from user ID and question."""
        content = f"{user_id}:{question}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _check_cache(self, cache_key: str) -> Optional[str]:
        """Check if a response is cached and still valid."""
        if cache_key in self._response_cache:
            cached_response, timestamp = self._response_cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                return cached_response
            else:
                # Remove expired entry
                del self._response_cache[cache_key]
        return None
    
    async def _cache_response(self, cache_key: str, response: str) -> None:
        """Cache a response with size management."""
        # Implement LRU cache behavior
        if len(self._response_cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest_key = min(self._response_cache.keys(), 
                           key=lambda k: self._response_cache[k][1])
            del self._response_cache[oldest_key]
        
        self._response_cache[cache_key] = (response, datetime.now())
    
    async def clear_cache(self) -> None:
        """Clear all caches"""
        self._response_cache.clear()
        self._embedding_cache.clear()
        logger.info("All caches cleared")
    
    async def reset_collection(self) -> bool:
        """Reset the ChromaDB collection (delete all documents)"""
        if not self._initialized or not self.chroma_client:
            return False
            
        try:
            # Delete existing collection
            self.chroma_client.delete_collection(name=self.collection_name)
            
            # Recreate collection
            embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.openai_api_key,
                model_name=self.embedding_model
            )
            
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                embedding_function=embedding_function,
                metadata={"description": "WhatsApp AI Chatbot RAG Collection"}
            )
            
            # Update retriever reference
            if self.semantic_retriever:
                self.semantic_retriever.collection = self.collection
                
            logger.info(f"Collection {self.collection_name} reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False
    
    @asynccontextmanager
    async def timeout_context(self, timeout: float):
        """Context manager for operation timeout"""
        try:
            await asyncio.wait_for(asyncio.sleep(0), timeout=timeout)
            yield
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Operation exceeded {timeout}s timeout")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        health_status = {
            "initialized": self._initialized,
            "chromadb_connected": False,
            "openai_available": False,
            "collection_accessible": False,
            "cache_stats": {
                "response_cache_size": len(self._response_cache),
                "embedding_cache_size": len(self._embedding_cache),
                "cache_hit_rate": (
                    self.performance_stats["cache_hits"] / 
                    max(self.performance_stats["total_queries"], 1)
                ) * 100
            }
        }
        
        try:
            # Check ChromaDB connection
            if self.chroma_client:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.chroma_client.heartbeat()
                )
                health_status["chromadb_connected"] = True
                
            # Check collection access
            if self.collection:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.collection.count()
                )
                health_status["collection_accessible"] = True
                
            # Check OpenAI availability
            if self.embedding_generator:
                await self.embedding_generator.generate_embedding("test")
                health_status["openai_available"] = True
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            
        return health_status
    
    async def shutdown(self) -> None:
        """Graceful shutdown of RAG system"""
        try:
            logger.info("Shutting down RAG System...")
            
            # Clear cache
            await self.clear_cache()
            
            # Close connections
            if self.chroma_client:
                # ChromaDB client doesn't need explicit closing
                pass
                
            self._initialized = False
            logger.info("RAG System shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")