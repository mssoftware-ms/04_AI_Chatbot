"""
Document Chunking Strategies Module

This module provides advanced document chunking capabilities with
token counting, semantic chunking, and various splitting strategies.
"""

import asyncio
import logging
import re
from typing import List, Optional, Dict, Any, Tuple, Generator
from dataclasses import dataclass
from enum import Enum
import tiktoken

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    RECURSIVE_CHARACTER = "recursive_character"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    MARKDOWN = "markdown"
    CODE = "code"


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk"""
    chunk_id: str
    source_document: str
    chunk_index: int
    start_position: int
    end_position: int
    token_count: int
    overlap_with_previous: bool
    chunk_type: str
    language: Optional[str] = None


class DocumentChunker:
    """
    Advanced Document Chunker with Multiple Strategies
    
    Provides intelligent document chunking with token counting,
    overlap management, and semantic awareness.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE_CHARACTER,
        enable_semantic_chunking: bool = True,
        token_model: str = "cl100k_base",  # GPT-4 tokenizer
        min_chunk_size: int = 100,
        max_chunk_size: int = 4000
    ):
        """
        Initialize Document Chunker
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            strategy: Primary chunking strategy
            enable_semantic_chunking: Whether to use semantic boundaries
            token_model: Tokenizer model for token counting
            min_chunk_size: Minimum chunk size in tokens
            max_chunk_size: Maximum chunk size in tokens
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        self.enable_semantic_chunking = enable_semantic_chunking
        self.token_model = token_model
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding(token_model)
        except Exception as e:
            logger.warning(f"Failed to load tokenizer {token_model}: {e}")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Separators for different strategies
        self.separators = {
            ChunkingStrategy.RECURSIVE_CHARACTER: [
                "\n\n", "\n", " ", ""
            ],
            ChunkingStrategy.SENTENCE: [
                ". ", "! ", "? ", ".\n", "!\n", "?\n"
            ],
            ChunkingStrategy.PARAGRAPH: [
                "\n\n", "\n\n\n"
            ],
            ChunkingStrategy.MARKDOWN: [
                "\n## ", "\n### ", "\n#### ",
                "\n\n", "\n", " "
            ],
            ChunkingStrategy.CODE: [
                "\nclass ", "\ndef ", "\nasync def ",
                "\n\n", "\n", " "
            ]
        }
        
        # Language detection patterns
        self.language_patterns = {
            "python": re.compile(r"(def |class |import |from .+ import)"),
            "javascript": re.compile(r"(function |const |let |var |=>)"),
            "java": re.compile(r"(public class|private |protected |import java)"),
            "markdown": re.compile(r"(#{1,6} |```|\*\*|\*)"),
            "sql": re.compile(r"(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)", re.IGNORECASE)
        }
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Fallback: approximate token count (1 token ≈ 4 characters)
            return len(text) // 4
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect programming language or text type"""
        for language, pattern in self.language_patterns.items():
            if pattern.search(text):
                return language
        return None
    
    async def chunk_document(
        self,
        document: str,
        document_id: str = "doc",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Chunk a document using the configured strategy
        
        Args:
            document: Document text to chunk
            document_id: Unique document identifier
            metadata: Additional metadata for the document
            
        Returns:
            List[str]: List of document chunks
        """
        if not document.strip():
            return []
        
        # Detect document language/type
        detected_language = self.detect_language(document)
        
        # Choose appropriate strategy
        chunking_strategy = self.strategy
        if self.enable_semantic_chunking:
            if detected_language == "markdown":
                chunking_strategy = ChunkingStrategy.MARKDOWN
            elif detected_language in ["python", "javascript", "java"]:
                chunking_strategy = ChunkingStrategy.CODE
        
        # Apply chunking strategy
        if chunking_strategy == ChunkingStrategy.RECURSIVE_CHARACTER:
            chunks = await self._recursive_character_chunking(document)
        elif chunking_strategy == ChunkingStrategy.SEMANTIC:
            chunks = await self._semantic_chunking(document)
        elif chunking_strategy == ChunkingStrategy.SENTENCE:
            chunks = await self._sentence_chunking(document)
        elif chunking_strategy == ChunkingStrategy.PARAGRAPH:
            chunks = await self._paragraph_chunking(document)
        elif chunking_strategy == ChunkingStrategy.MARKDOWN:
            chunks = await self._markdown_chunking(document)
        elif chunking_strategy == ChunkingStrategy.CODE:
            chunks = await self._code_chunking(document)
        else:
            chunks = await self._recursive_character_chunking(document)
        
        # Post-process chunks
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Skip chunks that are too small
            if self.count_tokens(chunk) < self.min_chunk_size:
                if processed_chunks and i == len(chunks) - 1:
                    # Merge small final chunk with previous one
                    processed_chunks[-1] += "\n\n" + chunk
                continue
            
            # Split chunks that are too large
            if self.count_tokens(chunk) > self.max_chunk_size:
                sub_chunks = await self._split_oversized_chunk(chunk)
                processed_chunks.extend(sub_chunks)
            else:
                processed_chunks.append(chunk)
        
        logger.info(
            f"Document chunked: {len(processed_chunks)} chunks "
            f"(strategy: {chunking_strategy.value}, language: {detected_language})"
        )
        
        return processed_chunks
    
    async def _recursive_character_chunking(self, document: str) -> List[str]:
        """Recursive character-based chunking"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._split_text_recursive, document, 
            self.separators[ChunkingStrategy.RECURSIVE_CHARACTER]
        )
    
    def _split_text_recursive(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """Split text recursively using multiple separators"""
        chunks = []
        
        # Try each separator in order
        for i, separator in enumerate(separators):
            if separator == "":
                # Character-level splitting
                return self._split_by_characters(text)
            
            if separator in text:
                parts = text.split(separator)
                
                current_chunk = ""
                for part in parts:
                    # Calculate tokens for current chunk + new part
                    potential_chunk = current_chunk + separator + part if current_chunk else part
                    token_count = self.count_tokens(potential_chunk)
                    
                    if token_count <= self.chunk_size:
                        current_chunk = potential_chunk
                    else:
                        # Add current chunk if it's substantial
                        if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size:
                            chunks.append(current_chunk.strip())
                        
                        # Process the part that didn't fit
                        if self.count_tokens(part) > self.chunk_size:
                            # Recursively split the oversized part
                            sub_chunks = self._split_text_recursive(part, separators[i:])
                            chunks.extend(sub_chunks)
                            current_chunk = ""
                        else:
                            current_chunk = part
                
                # Add the final chunk
                if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk.strip())
                
                return [chunk for chunk in chunks if chunk.strip()]
        
        # If no separator worked, return the original text
        return [text] if text.strip() else []
    
    def _split_by_characters(self, text: str) -> List[str]:
        """Split text at character level with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position based on token count
            end = start
            while end < len(text):
                chunk = text[start:end + 1]
                if self.count_tokens(chunk) > self.chunk_size:
                    break
                end += 1
            
            if end <= start:
                end = start + 1  # Ensure progress
            
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            
            # Calculate next start position with overlap
            overlap_tokens = 0
            overlap_start = end
            while overlap_start > start and overlap_tokens < self.chunk_overlap:
                overlap_start -= 1
                overlap_chunk = text[overlap_start:end]
                overlap_tokens = self.count_tokens(overlap_chunk)
            
            start = max(overlap_start, start + 1)
        
        return chunks
    
    async def _semantic_chunking(self, document: str) -> List[str]:
        """Semantic-aware chunking (placeholder for future enhancement)"""
        # For now, fall back to recursive character chunking
        # In the future, this could use NLP models to find semantic boundaries
        return await self._recursive_character_chunking(document)
    
    async def _sentence_chunking(self, document: str) -> List[str]:
        """Sentence-based chunking"""
        sentences = re.split(r'[.!?]+', document)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            potential_chunk = current_chunk + ". " + sentence if current_chunk else sentence
            
            if self.count_tokens(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def _paragraph_chunking(self, document: str) -> List[str]:
        """Paragraph-based chunking"""
        paragraphs = [p.strip() for p in document.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if self.count_tokens(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If single paragraph is too large, split it further
                if self.count_tokens(paragraph) > self.chunk_size:
                    sub_chunks = await self._recursive_character_chunking(paragraph)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def _markdown_chunking(self, document: str) -> List[str]:
        """Markdown-aware chunking"""
        # Split by headers first
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        sections = []
        
        matches = list(header_pattern.finditer(document))
        if not matches:
            return await self._recursive_character_chunking(document)
        
        start_pos = 0
        for i, match in enumerate(matches):
            # Add content before first header
            if i == 0 and match.start() > 0:
                sections.append(document[0:match.start()].strip())
            
            # Add section content
            next_start = matches[i + 1].start() if i + 1 < len(matches) else len(document)
            section_content = document[match.start():next_start].strip()
            sections.append(section_content)
        
        # Process each section
        chunks = []
        for section in sections:
            if not section:
                continue
                
            if self.count_tokens(section) <= self.chunk_size:
                chunks.append(section)
            else:
                # Split large sections further
                sub_chunks = await self._recursive_character_chunking(section)
                chunks.extend(sub_chunks)
        
        return chunks
    
    async def _code_chunking(self, document: str) -> List[str]:
        """Code-aware chunking"""
        # Split by functions and classes
        code_patterns = [
            r'^(class\s+\w+.*?):',
            r'^(def\s+\w+.*?):',
            r'^(async\s+def\s+\w+.*?):',
            r'^(function\s+\w+.*?{)',
            r'^(const\s+\w+\s*=.*?{)',
        ]
        
        chunks = []
        current_chunk = ""
        lines = document.split('\n')
        
        for line in lines:
            potential_chunk = current_chunk + '\n' + line if current_chunk else line
            
            # Check if we hit a code boundary
            is_boundary = any(re.match(pattern, line.strip()) for pattern in code_patterns)
            
            if (self.count_tokens(potential_chunk) > self.chunk_size or 
                (is_boundary and current_chunk and self.count_tokens(current_chunk) > self.min_chunk_size)):
                
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk = potential_chunk
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Post-process to handle oversized chunks
        final_chunks = []
        for chunk in chunks:
            if self.count_tokens(chunk) > self.chunk_size:
                sub_chunks = await self._recursive_character_chunking(chunk)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    async def _split_oversized_chunk(self, chunk: str) -> List[str]:
        """Split a chunk that exceeds max_chunk_size"""
        if self.count_tokens(chunk) <= self.max_chunk_size:
            return [chunk]
        
        # Use recursive character splitting with smaller target size
        original_chunk_size = self.chunk_size
        self.chunk_size = min(self.chunk_size, self.max_chunk_size)
        
        try:
            sub_chunks = await self._recursive_character_chunking(chunk)
        finally:
            self.chunk_size = original_chunk_size
        
        return sub_chunks
    
    def get_chunk_metadata(
        self,
        chunks: List[str],
        document_id: str = "doc"
    ) -> List[ChunkMetadata]:
        """Generate metadata for chunks"""
        metadata_list = []
        position = 0
        
        for i, chunk in enumerate(chunks):
            start_pos = position
            end_pos = position + len(chunk)
            
            metadata = ChunkMetadata(
                chunk_id=f"{document_id}_chunk_{i}",
                source_document=document_id,
                chunk_index=i,
                start_position=start_pos,
                end_position=end_pos,
                token_count=self.count_tokens(chunk),
                overlap_with_previous=i > 0 and self.chunk_overlap > 0,
                chunk_type=self.strategy.value,
                language=self.detect_language(chunk)
            )
            
            metadata_list.append(metadata)
            position = end_pos
        
        return metadata_list
    
    async def chunk_multiple_documents(
        self,
        documents: List[Tuple[str, str]],  # (document_id, content)
        batch_size: int = 10
    ) -> Dict[str, List[str]]:
        """
        Chunk multiple documents in batches
        
        Args:
            documents: List of (document_id, content) tuples
            batch_size: Number of documents to process simultaneously
            
        Returns:
            Dict[str, List[str]]: Document ID to chunks mapping
        """
        all_chunks = {}
        
        for batch_start in range(0, len(documents), batch_size):
            batch_end = min(batch_start + batch_size, len(documents))
            batch_documents = documents[batch_start:batch_end]
            
            # Process batch concurrently
            tasks = []
            for doc_id, content in batch_documents:
                task = self.chunk_document(content, doc_id)
                tasks.append((doc_id, task))
            
            # Wait for batch completion
            for doc_id, task in tasks:
                try:
                    chunks = await task
                    all_chunks[doc_id] = chunks
                except Exception as e:
                    logger.error(f"Failed to chunk document {doc_id}: {e}")
                    all_chunks[doc_id] = []
        
        total_chunks = sum(len(chunks) for chunks in all_chunks.values())
        logger.info(f"Chunked {len(documents)} documents into {total_chunks} total chunks")
        
        return all_chunks
    
    def estimate_chunk_count(self, document: str) -> int:
        """Estimate number of chunks for a document"""
        token_count = self.count_tokens(document)
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        return max(1, (token_count + effective_chunk_size - 1) // effective_chunk_size)
    
    def get_chunking_stats(self) -> Dict[str, Any]:
        """Get chunking configuration and statistics"""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "strategy": self.strategy.value,
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
            "enable_semantic_chunking": self.enable_semantic_chunking,
            "token_model": self.token_model
        }