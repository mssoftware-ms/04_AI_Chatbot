"""
Prompt Templates and Engineering Module

This module provides advanced prompt management with templates, 
context building, and streaming response generation.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of prompts available"""
    GENERAL_CHAT = "general_chat"
    TECHNICAL_SUPPORT = "technical_support"
    INFORMATION_REQUEST = "information_request"
    PROBLEM_SOLVING = "problem_solving"
    SUMMARIZATION = "summarization"
    CLARIFICATION = "clarification"
    GREETING = "greeting"
    FAREWELL = "farewell"


@dataclass
class PromptTemplate:
    """Template for constructing prompts"""
    name: str
    system_prompt: str
    user_template: str
    context_template: str
    variables: List[str]
    max_context_length: int = 4000
    temperature: float = 0.7


class PromptManager:
    """
    Advanced Prompt Management System
    
    Provides intelligent prompt templates, context building,
    and optimized response generation with streaming support.
    """
    
    def __init__(
        self,
        api_key: str,
        chat_model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        response_timeout: float = 30.0
    ):
        """
        Initialize Prompt Manager
        
        Args:
            api_key: OpenAI API key
            chat_model: OpenAI chat model to use
            max_tokens: Maximum response tokens
            temperature: Model temperature
            response_timeout: Response timeout in seconds
        """
        self.api_key = api_key
        self.chat_model = chat_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.response_timeout = response_timeout
        
        # Initialize async OpenAI client
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Performance tracking
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "total_tokens_used": 0,
            "avg_tokens_per_request": 0,
            "stream_requests": 0
        }
        
        # Initialize prompt templates
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[PromptType, PromptTemplate]:
        """Initialize predefined prompt templates"""
        templates = {}
        
        # General chat template
        templates[PromptType.GENERAL_CHAT] = PromptTemplate(
            name="general_chat",
            system_prompt="""You are a helpful and knowledgeable AI assistant for a WhatsApp chatbot. 
You provide accurate, helpful, and conversational responses. Keep responses natural and engaging.
Use the provided context to inform your responses when relevant, but don't mention the retrieval process explicitly.""",
            user_template="{question}",
            context_template="""Relevant information:
{retrieved_context}

Previous conversation:
{conversation_history}""",
            variables=["question", "retrieved_context", "conversation_history"],
            temperature=0.7
        )
        
        # Technical support template
        templates[PromptType.TECHNICAL_SUPPORT] = PromptTemplate(
            name="technical_support",
            system_prompt="""You are a technical support specialist AI assistant. Your role is to:
1. Diagnose technical problems accurately
2. Provide step-by-step solutions
3. Explain technical concepts clearly
4. Suggest preventive measures
5. Ask clarifying questions when needed

Use the provided context and conversation history to give personalized assistance.""",
            user_template="Technical issue: {question}",
            context_template="""Technical documentation:
{retrieved_context}

Previous troubleshooting steps:
{conversation_history}

User context: {user_context}""",
            variables=["question", "retrieved_context", "conversation_history", "user_context"],
            temperature=0.3
        )
        
        # Information request template
        templates[PromptType.INFORMATION_REQUEST] = PromptTemplate(
            name="information_request",
            system_prompt="""You are an information specialist AI assistant. Provide comprehensive, accurate information based on the available context.
Structure your responses clearly with:
1. Direct answer to the question
2. Additional relevant details
3. Sources or references when applicable
Be factual and cite the provided context appropriately.""",
            user_template="Information request: {question}",
            context_template="""Available information:
{retrieved_context}

Related discussion:
{conversation_history}""",
            variables=["question", "retrieved_context", "conversation_history"],
            temperature=0.2
        )
        
        # Problem-solving template
        templates[PromptType.PROBLEM_SOLVING] = PromptTemplate(
            name="problem_solving",
            system_prompt="""You are a problem-solving AI assistant. Approach problems systematically:
1. Understand the problem clearly
2. Break it down into manageable parts
3. Suggest multiple solution approaches
4. Provide step-by-step guidance
5. Anticipate potential challenges

Use available context and conversation history to provide personalized solutions.""",
            user_template="Problem: {question}",
            context_template="""Relevant solutions and approaches:
{retrieved_context}

Problem-solving history:
{conversation_history}

Context: {user_context}""",
            variables=["question", "retrieved_context", "conversation_history", "user_context"],
            temperature=0.4
        )
        
        # Summarization template
        templates[PromptType.SUMMARIZATION] = PromptTemplate(
            name="summarization",
            system_prompt="""You are a summarization specialist. Create concise, comprehensive summaries that:
1. Capture key points and main ideas
2. Maintain important details
3. Organize information logically
4. Highlight actionable items
Use the provided context to create accurate summaries.""",
            user_template="Please summarize: {question}",
            context_template="""Content to summarize:
{retrieved_context}

Additional context:
{conversation_history}""",
            variables=["question", "retrieved_context", "conversation_history"],
            temperature=0.1
        )
        
        # Clarification template
        templates[PromptType.CLARIFICATION] = PromptTemplate(
            name="clarification",
            system_prompt="""You are a clarification specialist. When users ask unclear questions:
1. Acknowledge their question
2. Ask specific clarifying questions
3. Provide examples of what information would be helpful
4. Suggest how they can rephrase their question
Use conversation history to understand context and avoid repetitive clarifications.""",
            user_template="Unclear question: {question}",
            context_template="""Conversation context:
{conversation_history}

Available information:
{retrieved_context}""",
            variables=["question", "conversation_history", "retrieved_context"],
            temperature=0.5
        )
        
        return templates
    
    def classify_prompt_type(self, question: str) -> PromptType:
        """Classify the type of prompt based on the question"""
        question_lower = question.lower()
        
        # Technical support indicators
        if any(word in question_lower for word in [
            "error", "problem", "issue", "broken", "not working",
            "troubleshoot", "fix", "debug", "help", "support"
        ]):
            return PromptType.TECHNICAL_SUPPORT
        
        # Information request indicators
        if any(word in question_lower for word in [
            "what is", "what are", "define", "explain", "tell me about",
            "information", "details", "describe", "meaning"
        ]):
            return PromptType.INFORMATION_REQUEST
        
        # Problem-solving indicators
        if any(word in question_lower for word in [
            "how to", "how can", "solve", "solution", "approach",
            "method", "way", "strategy", "plan"
        ]):
            return PromptType.PROBLEM_SOLVING
        
        # Summarization indicators
        if any(word in question_lower for word in [
            "summarize", "summary", "overview", "recap",
            "key points", "main ideas", "brief"
        ]):
            return PromptType.SUMMARIZATION
        
        # Greeting indicators
        if any(word in question_lower for word in [
            "hello", "hi", "hey", "good morning", "good afternoon",
            "good evening", "greetings"
        ]):
            return PromptType.GREETING
        
        # Clarification needed
        if len(question.split()) < 3 or question.count('?') > 2:
            return PromptType.CLARIFICATION
        
        # Default to general chat
        return PromptType.GENERAL_CHAT
    
    def build_context(
        self,
        retrieved_documents: List[Dict[str, Any]],
        conversation_history: List[str],
        user_context: Optional[Dict[str, Any]] = None,
        max_length: int = 4000
    ) -> str:
        """
        Build context string from retrieved documents and conversation history
        
        Args:
            retrieved_documents: Retrieved document results
            conversation_history: Previous conversation messages
            user_context: Additional user context
            max_length: Maximum context length in characters
            
        Returns:
            str: Formatted context string
        """
        context_parts = []
        current_length = 0
        
        # Add retrieved documents
        if retrieved_documents:
            doc_context = "Retrieved Information:\n"
            for i, doc in enumerate(retrieved_documents[:5]):  # Limit to top 5
                content = doc.get('content', '')
                source = doc.get('source', f'Document {i+1}')
                confidence = doc.get('confidence_score', 0.0)
                
                doc_section = f"\n[Source: {source}] (Confidence: {confidence:.2f})\n{content}\n"
                
                if current_length + len(doc_section) <= max_length:
                    doc_context += doc_section
                    current_length += len(doc_section)
                else:
                    break
            
            context_parts.append(doc_context)
        
        # Add conversation history
        if conversation_history:
            history_context = "\nRecent Conversation:\n"
            # Take last few messages that fit
            for message in reversed(conversation_history[-10:]):  # Last 10 messages
                message_section = f"- {message}\n"
                if current_length + len(message_section) <= max_length:
                    history_context = f"- {message}\n" + history_context[len("\nRecent Conversation:\n"):]
                    current_length += len(message_section)
                else:
                    break
            
            if len(history_context) > len("\nRecent Conversation:\n"):
                context_parts.append(history_context)
        
        # Add user context
        if user_context:
            user_info = f"\nUser Context: {json.dumps(user_context, default=str)}\n"
            if current_length + len(user_info) <= max_length:
                context_parts.append(user_info)
        
        return "\n".join(context_parts)
    
    async def generate_response(
        self,
        question: str,
        context: Dict[str, Any],
        prompt_type: Optional[PromptType] = None,
        custom_template: Optional[PromptTemplate] = None
    ) -> str:
        """
        Generate a complete response using the appropriate template
        
        Args:
            question: User question
            context: Context data including retrieved documents
            prompt_type: Type of prompt to use (auto-detected if None)
            custom_template: Custom template to use instead of predefined ones
            
        Returns:
            str: Generated response
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            # Determine prompt type
            if prompt_type is None:
                prompt_type = self.classify_prompt_type(question)
            
            # Get template
            template = custom_template or self.templates.get(prompt_type, self.templates[PromptType.GENERAL_CHAT])
            
            # Build context string
            context_str = self.build_context(
                retrieved_documents=context.get('retrieved_documents', []),
                conversation_history=context.get('conversation_history', []),
                user_context=context.get('user_context', {}),
                max_length=template.max_context_length
            )
            
            # Format messages
            messages = [
                {"role": "system", "content": template.system_prompt}
            ]
            
            # Add context if available
            if context_str.strip():
                messages.append({"role": "system", "content": context_str})
            
            # Add user question
            user_message = template.user_template.format(
                question=question,
                retrieved_context=context_str,
                conversation_history="\n".join(context.get('conversation_history', [])),
                user_context=json.dumps(context.get('user_context', {}), default=str)
            )
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.chat_model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=template.temperature
                ),
                timeout=self.response_timeout
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Update statistics
            response_time = time.time() - start_time
            self.stats["successful_requests"] += 1
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (self.stats["successful_requests"] - 1) + 
                 response_time) / self.stats["successful_requests"]
            )
            
            if hasattr(response, 'usage') and response.usage:
                self.stats["total_tokens_used"] += response.usage.total_tokens
                self.stats["avg_tokens_per_request"] = (
                    self.stats["total_tokens_used"] / self.stats["successful_requests"]
                )
            
            logger.debug(
                f"Response generated in {response_time:.3f}s "
                f"(type: {prompt_type.value}, tokens: {getattr(response.usage, 'total_tokens', 'unknown')})"
            )
            
            return response_text
            
        except asyncio.TimeoutError:
            self.stats["failed_requests"] += 1
            logger.error(f"Response generation timed out after {self.response_timeout}s")
            return "I apologize, but I'm experiencing high load. Please try again shortly."
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Response generation failed: {e}")
            return "I apologize, but I encountered an error. Please try rephrasing your question."
    
    async def generate_streaming_response(
        self,
        question: str,
        context: Dict[str, Any],
        prompt_type: Optional[PromptType] = None,
        custom_template: Optional[PromptTemplate] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response
        
        Args:
            question: User question
            context: Context data including retrieved documents
            prompt_type: Type of prompt to use (auto-detected if None)
            custom_template: Custom template to use instead of predefined ones
            
        Yields:
            str: Response chunks
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        self.stats["stream_requests"] += 1
        
        try:
            # Determine prompt type
            if prompt_type is None:
                prompt_type = self.classify_prompt_type(question)
            
            # Get template
            template = custom_template or self.templates.get(prompt_type, self.templates[PromptType.GENERAL_CHAT])
            
            # Build context string
            context_str = self.build_context(
                retrieved_documents=context.get('retrieved_documents', []),
                conversation_history=context.get('conversation_history', []),
                user_context=context.get('user_context', {}),
                max_length=template.max_context_length
            )
            
            # Format messages
            messages = [
                {"role": "system", "content": template.system_prompt}
            ]
            
            # Add context if available
            if context_str.strip():
                messages.append({"role": "system", "content": context_str})
            
            # Add user question
            user_message = template.user_template.format(
                question=question,
                retrieved_context=context_str,
                conversation_history="\n".join(context.get('conversation_history', [])),
                user_context=json.dumps(context.get('user_context', {}), default=str)
            )
            messages.append({"role": "user", "content": user_message})
            
            # Generate streaming response
            stream = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=template.temperature,
                stream=True
            )
            
            response_text = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    response_text += content_chunk
                    yield content_chunk
            
            # Update statistics
            response_time = time.time() - start_time
            self.stats["successful_requests"] += 1
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (self.stats["successful_requests"] - 1) + 
                 response_time) / self.stats["successful_requests"]
            )
            
            logger.debug(
                f"Streaming response completed in {response_time:.3f}s "
                f"(type: {prompt_type.value}, length: {len(response_text)})"
            )
            
        except asyncio.TimeoutError:
            self.stats["failed_requests"] += 1
            logger.error("Streaming response timed out")
            yield "I apologize, but I'm experiencing high load. Please try again shortly."
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Streaming response failed: {e}")
            yield "I apologize, but I encountered an error. Please try rephrasing your question."
    
    def add_custom_template(
        self,
        prompt_type: PromptType,
        template: PromptTemplate
    ) -> None:
        """Add or update a custom prompt template"""
        self.templates[prompt_type] = template
        logger.info(f"Added custom template for {prompt_type.value}")
    
    def get_template(self, prompt_type: PromptType) -> Optional[PromptTemplate]:
        """Get a specific prompt template"""
        return self.templates.get(prompt_type)
    
    def estimate_token_usage(
        self,
        question: str,
        context: Dict[str, Any],
        prompt_type: Optional[PromptType] = None
    ) -> int:
        """Estimate token usage for a request"""
        if prompt_type is None:
            prompt_type = self.classify_prompt_type(question)
        
        template = self.templates.get(prompt_type, self.templates[PromptType.GENERAL_CHAT])
        
        # Build context string
        context_str = self.build_context(
            retrieved_documents=context.get('retrieved_documents', []),
            conversation_history=context.get('conversation_history', []),
            user_context=context.get('user_context', {}),
            max_length=template.max_context_length
        )
        
        # Rough token estimation (1 token ≈ 4 characters)
        total_chars = (
            len(template.system_prompt) +
            len(context_str) +
            len(question) +
            self.max_tokens  # Response tokens
        )
        
        return total_chars // 4
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        success_rate = (
            self.stats["successful_requests"] / 
            max(self.stats["total_requests"], 1)
        )
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "streaming_rate": (
                self.stats["stream_requests"] / 
                max(self.stats["total_requests"], 1)
            ),
            "model": self.chat_model,
            "max_tokens": self.max_tokens,
            "available_templates": list(self.templates.keys())
        }
    
    async def test_generation(self, test_question: str = "Hello, how are you?") -> bool:
        """Test prompt generation functionality"""
        try:
            response = await self.generate_response(
                question=test_question,
                context={"retrieved_documents": [], "conversation_history": []}
            )
            return len(response) > 0
        except Exception as e:
            logger.error(f"Prompt generation test failed: {e}")
            return False