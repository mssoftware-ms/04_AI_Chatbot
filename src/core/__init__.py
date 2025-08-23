"""
Core RAG System Module for WhatsApp AI Chatbot

This module provides the main RAG (Retrieval-Augmented Generation) system
with ChromaDB integration and OpenAI embeddings for intelligent conversation handling.
"""

from .rag_system import RAGSystem
from .embeddings import EmbeddingGenerator
from .chunking import DocumentChunker
from .retrieval import SemanticRetriever
from .prompts import PromptManager
from .memory import ConversationMemory

__version__ = "1.0.0"

__all__ = [
    "RAGSystem",
    "EmbeddingGenerator",
    "DocumentChunker", 
    "SemanticRetriever",
    "PromptManager",
    "ConversationMemory"
]