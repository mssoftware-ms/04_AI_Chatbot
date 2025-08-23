"""
Conversation Memory Management Module

This module provides advanced conversation memory management with
context preservation, user sessions, and intelligent memory pruning.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import pickle
import os

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Individual conversation turn"""
    user_id: str
    timestamp: datetime
    user_message: str
    assistant_response: str
    context_used: Dict[str, Any]
    response_time: float
    confidence_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UserSession:
    """User session data"""
    user_id: str
    session_id: str
    start_time: datetime
    last_activity: datetime
    conversation_turns: List[ConversationTurn]
    user_preferences: Dict[str, Any]
    context_summary: str = ""
    total_interactions: int = 0


class ConversationMemory:
    """
    Advanced Conversation Memory Management System
    
    Provides intelligent memory management with context preservation,
    session tracking, and performance optimizations.
    """
    
    def __init__(
        self,
        max_history: int = 10,
        context_window: int = 4000,
        session_timeout_hours: int = 24,
        memory_persistence_path: Optional[str] = None,
        enable_context_compression: bool = True,
        max_memory_size_mb: int = 100
    ):
        """
        Initialize Conversation Memory
        
        Args:
            max_history: Maximum conversation turns to keep in active memory
            context_window: Maximum context length in characters
            session_timeout_hours: Hours before session expires
            memory_persistence_path: Path for persistent memory storage
            enable_context_compression: Whether to compress old contexts
            max_memory_size_mb: Maximum memory usage in MB
        """
        self.max_history = max_history
        self.context_window = context_window
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self.memory_persistence_path = memory_persistence_path
        self.enable_context_compression = enable_context_compression
        self.max_memory_size_mb = max_memory_size_mb
        
        # In-memory storage
        self.active_sessions: Dict[str, UserSession] = {}
        self.conversation_history: Dict[str, deque] = {}  # user_id -> deque of turns
        self.user_summaries: Dict[str, str] = {}  # user_id -> conversation summary
        
        # Performance tracking
        self.stats = {
            "total_interactions": 0,
            "active_sessions": 0,
            "memory_operations": 0,
            "context_compressions": 0,
            "session_cleanups": 0,
            "avg_context_size": 0
        }
        
        # Context compression settings
        self.compression_threshold = max_history * 2
        self.summary_length_target = 500
        
        # Initialize persistence if path provided
        if self.memory_persistence_path:
            self._ensure_persistence_directory()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_background_cleanup()
    
    def _ensure_persistence_directory(self) -> None:
        """Ensure persistence directory exists"""
        if self.memory_persistence_path:
            os.makedirs(self.memory_persistence_path, exist_ok=True)
    
    def _start_background_cleanup(self) -> None:
        """Start background cleanup task"""
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._background_cleanup())
    
    async def _background_cleanup(self) -> None:
        """Background task for memory cleanup and maintenance"""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_expired_sessions()
                await self._compress_old_contexts()
                await self._manage_memory_usage()
                
        except asyncio.CancelledError:
            logger.info("Background cleanup task cancelled")
        except Exception as e:
            logger.error(f"Background cleanup error: {e}")
    
    async def add_interaction(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        context: Dict[str, Any],
        response_time: float = 0.0,
        confidence_score: float = 0.0,
        session_id: Optional[str] = None
    ) -> None:
        """
        Add a new interaction to memory
        
        Args:
            user_id: Unique user identifier
            user_message: User's message
            assistant_response: Assistant's response
            context: Context used for the response
            response_time: Time taken to generate response
            confidence_score: Confidence in the response
            session_id: Optional session identifier
        """
        try:
            self.stats["total_interactions"] += 1
            self.stats["memory_operations"] += 1
            
            # Create conversation turn
            turn = ConversationTurn(
                user_id=user_id,
                timestamp=datetime.now(),
                user_message=user_message,
                assistant_response=assistant_response,
                context_used=context,
                response_time=response_time,
                confidence_score=confidence_score,
                metadata={"session_id": session_id} if session_id else None
            )
            
            # Get or create session
            session = await self._get_or_create_session(user_id, session_id)
            session.conversation_turns.append(turn)
            session.last_activity = datetime.now()
            session.total_interactions += 1
            
            # Add to conversation history
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = deque(maxlen=self.max_history * 2)
            
            self.conversation_history[user_id].append(turn)
            
            # Manage memory size
            await self._manage_conversation_length(user_id)
            
            # Update context size stats
            context_size = len(json.dumps(context, default=str))
            self.stats["avg_context_size"] = (
                (self.stats["avg_context_size"] * (self.stats["total_interactions"] - 1) + 
                 context_size) / self.stats["total_interactions"]
            )
            
            # Persist if enabled
            if self.memory_persistence_path:
                await self._persist_user_data(user_id)
                
        except Exception as e:
            logger.error(f"Failed to add interaction for user {user_id}: {e}")
    
    async def get_context(
        self,
        user_id: str,
        max_turns: Optional[int] = None,
        include_context: bool = True
    ) -> List[str]:
        """
        Get conversation context for a user
        
        Args:
            user_id: User identifier
            max_turns: Maximum conversation turns to include
            include_context: Whether to include retrieval context
            
        Returns:
            List[str]: List of formatted conversation messages
        """
        try:
            self.stats["memory_operations"] += 1
            
            if user_id not in self.conversation_history:
                return []
            
            turns_limit = min(max_turns or self.max_history, len(self.conversation_history[user_id]))
            recent_turns = list(self.conversation_history[user_id])[-turns_limit:]
            
            context_messages = []
            current_length = 0
            
            for turn in recent_turns:
                # Format conversation turn
                message = f"User: {turn.user_message}\nAssistant: {turn.assistant_response}"
                
                # Add context if requested and available
                if include_context and turn.context_used:
                    retrieved_docs = turn.context_used.get('retrieved_documents', [])
                    if retrieved_docs:
                        context_info = f"\n[Context: {len(retrieved_docs)} documents retrieved]"
                        message += context_info
                
                # Check if adding this message exceeds context window
                if current_length + len(message) > self.context_window:
                    break
                
                context_messages.append(message)
                current_length += len(message)
            
            return context_messages
            
        except Exception as e:
            logger.error(f"Failed to get context for user {user_id}: {e}")
            return []
    
    async def get_user_summary(self, user_id: str) -> str:
        """
        Get or generate a summary of the user's conversation history
        
        Args:
            user_id: User identifier
            
        Returns:
            str: User conversation summary
        """
        try:
            # Check if we have a cached summary
            if user_id in self.user_summaries:
                return self.user_summaries[user_id]
            
            # Generate summary from conversation history
            if user_id in self.conversation_history:
                turns = list(self.conversation_history[user_id])
                if turns:
                    summary = await self._generate_conversation_summary(turns)
                    self.user_summaries[user_id] = summary
                    return summary
            
            return "No conversation history available."
            
        except Exception as e:
            logger.error(f"Failed to get user summary for {user_id}: {e}")
            return "Error retrieving conversation summary."
    
    async def _generate_conversation_summary(
        self,
        turns: List[ConversationTurn]
    ) -> str:
        """Generate a summary of conversation turns"""
        try:
            if not turns:
                return "No conversation history."
            
            # Extract key information
            topics = set()
            user_intents = []
            recent_context = []
            
            for turn in turns[-10:]:  # Focus on recent turns
                # Extract topics from user messages
                words = turn.user_message.lower().split()
                topics.update([word for word in words if len(word) > 3])
                
                # Categorize user intent
                user_intents.append(self._categorize_user_intent(turn.user_message))
                
                # Keep recent context
                recent_context.append(f"User asked about: {turn.user_message[:100]}")
            
            # Generate summary
            summary_parts = []
            
            # User interaction patterns
            total_turns = len(turns)
            avg_response_time = sum(turn.response_time for turn in turns) / max(total_turns, 1)
            summary_parts.append(f"Total interactions: {total_turns}")
            summary_parts.append(f"Average response time: {avg_response_time:.2f}s")
            
            # Common topics
            common_topics = sorted(topics, key=lambda x: sum(1 for turn in turns if x in turn.user_message.lower()))[-5:]
            if common_topics:
                summary_parts.append(f"Common topics: {', '.join(common_topics)}")
            
            # User intent patterns
            intent_counts = {}
            for intent in user_intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            if intent_counts:
                primary_intent = max(intent_counts, key=intent_counts.get)
                summary_parts.append(f"Primary intent: {primary_intent}")
            
            # Recent context
            if recent_context:
                summary_parts.append("Recent topics:")
                summary_parts.extend(recent_context[-3:])
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
            return "Error generating summary."
    
    def _categorize_user_intent(self, message: str) -> str:
        """Categorize user intent from message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["help", "problem", "issue", "error"]):
            return "support"
        elif any(word in message_lower for word in ["what", "how", "explain", "tell me"]):
            return "information"
        elif any(word in message_lower for word in ["hello", "hi", "hey", "good"]):
            return "greeting"
        elif any(word in message_lower for word in ["thank", "thanks", "bye", "goodbye"]):
            return "closing"
        else:
            return "general"
    
    async def _get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> UserSession:
        """Get existing session or create a new one"""
        session_key = session_id or user_id
        
        if session_key in self.active_sessions:
            session = self.active_sessions[session_key]
            # Check if session is still valid
            if datetime.now() - session.last_activity < self.session_timeout:
                return session
            else:
                # Session expired, create new one
                del self.active_sessions[session_key]
        
        # Create new session
        session = UserSession(
            user_id=user_id,
            session_id=session_id or f"{user_id}_{int(time.time())}",
            start_time=datetime.now(),
            last_activity=datetime.now(),
            conversation_turns=[],
            user_preferences={},
            total_interactions=0
        )
        
        self.active_sessions[session_key] = session
        self.stats["active_sessions"] = len(self.active_sessions)
        
        return session
    
    async def _manage_conversation_length(self, user_id: str) -> None:
        """Manage conversation length and compress if needed"""
        if user_id not in self.conversation_history:
            return
        
        history = self.conversation_history[user_id]
        
        # If history is getting too long, compress older parts
        if len(history) > self.compression_threshold:
            if self.enable_context_compression:
                await self._compress_user_context(user_id)
            else:
                # Simple truncation
                while len(history) > self.max_history:
                    history.popleft()
    
    async def _compress_user_context(self, user_id: str) -> None:
        """Compress older conversation context for a user"""
        try:
            if user_id not in self.conversation_history:
                return
            
            history = self.conversation_history[user_id]
            
            # Take older half of conversations for compression
            compress_count = len(history) // 2
            turns_to_compress = [history.popleft() for _ in range(compress_count)]
            
            # Generate summary of compressed turns
            summary = await self._generate_conversation_summary(turns_to_compress)
            
            # Store summary
            self.user_summaries[user_id] = summary
            self.stats["context_compressions"] += 1
            
            logger.debug(f"Compressed {compress_count} turns for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to compress context for user {user_id}: {e}")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
        try:
            expired_sessions = []
            current_time = datetime.now()
            
            for session_id, session in self.active_sessions.items():
                if current_time - session.last_activity > self.session_timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                self.stats["session_cleanups"] += 1
            
            self.stats["active_sessions"] = len(self.active_sessions)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
    
    async def _compress_old_contexts(self) -> None:
        """Compress old conversation contexts"""
        try:
            for user_id in list(self.conversation_history.keys()):
                history = self.conversation_history[user_id]
                if len(history) > self.compression_threshold:
                    await self._compress_user_context(user_id)
                    
        except Exception as e:
            logger.error(f"Context compression failed: {e}")
    
    async def _manage_memory_usage(self) -> None:
        """Monitor and manage memory usage"""
        try:
            # Estimate memory usage (simplified)
            total_turns = sum(len(history) for history in self.conversation_history.values())
            estimated_mb = total_turns * 0.01  # Rough estimate: 10KB per turn
            
            if estimated_mb > self.max_memory_size_mb:
                # Aggressive cleanup
                for user_id in list(self.conversation_history.keys()):
                    history = self.conversation_history[user_id]
                    if len(history) > self.max_history:
                        # Keep only most recent interactions
                        while len(history) > self.max_history // 2:
                            history.popleft()
                
                logger.warning(f"Performed aggressive memory cleanup (estimated: {estimated_mb:.1f}MB)")
                
        except Exception as e:
            logger.error(f"Memory management failed: {e}")
    
    async def _persist_user_data(self, user_id: str) -> None:
        """Persist user data to disk"""
        if not self.memory_persistence_path:
            return
        
        try:
            user_data = {
                "conversation_history": list(self.conversation_history.get(user_id, [])),
                "user_summary": self.user_summaries.get(user_id, ""),
                "last_updated": datetime.now().isoformat()
            }
            
            file_path = os.path.join(self.memory_persistence_path, f"user_{user_id}.json")
            
            # Convert ConversationTurn objects to dictionaries
            if "conversation_history" in user_data:
                user_data["conversation_history"] = [
                    asdict(turn) if hasattr(turn, '__dataclass_fields__') else turn
                    for turn in user_data["conversation_history"]
                ]
                
                # Convert datetime objects to ISO strings
                for turn_data in user_data["conversation_history"]:
                    if isinstance(turn_data, dict) and "timestamp" in turn_data:
                        if isinstance(turn_data["timestamp"], datetime):
                            turn_data["timestamp"] = turn_data["timestamp"].isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to persist data for user {user_id}: {e}")
    
    async def load_user_data(self, user_id: str) -> bool:
        """Load user data from disk"""
        if not self.memory_persistence_path:
            return False
        
        try:
            file_path = os.path.join(self.memory_persistence_path, f"user_{user_id}.json")
            
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            # Restore conversation history
            if "conversation_history" in user_data:
                history = deque(maxlen=self.max_history * 2)
                
                for turn_data in user_data["conversation_history"]:
                    # Convert back to ConversationTurn object
                    if "timestamp" in turn_data and isinstance(turn_data["timestamp"], str):
                        turn_data["timestamp"] = datetime.fromisoformat(turn_data["timestamp"])
                    
                    turn = ConversationTurn(**turn_data)
                    history.append(turn)
                
                self.conversation_history[user_id] = history
            
            # Restore user summary
            if "user_summary" in user_data:
                self.user_summaries[user_id] = user_data["user_summary"]
            
            logger.info(f"Loaded user data for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data for user {user_id}: {e}")
            return False
    
    async def clear_user_memory(self, user_id: str) -> bool:
        """Clear all memory for a specific user"""
        try:
            # Remove from in-memory structures
            if user_id in self.conversation_history:
                del self.conversation_history[user_id]
            
            if user_id in self.user_summaries:
                del self.user_summaries[user_id]
            
            # Remove sessions
            sessions_to_remove = [
                session_id for session_id, session in self.active_sessions.items()
                if session.user_id == user_id
            ]
            
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
            
            # Remove persistent data
            if self.memory_persistence_path:
                file_path = os.path.join(self.memory_persistence_path, f"user_{user_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            logger.info(f"Cleared memory for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear memory for user {user_id}: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        total_turns = sum(len(history) for history in self.conversation_history.values())
        
        return {
            **self.stats,
            "total_users": len(self.conversation_history),
            "total_conversation_turns": total_turns,
            "average_turns_per_user": total_turns / max(len(self.conversation_history), 1),
            "memory_settings": {
                "max_history": self.max_history,
                "context_window": self.context_window,
                "session_timeout_hours": self.session_timeout.total_seconds() / 3600,
                "enable_compression": self.enable_context_compression,
                "persistence_enabled": self.memory_persistence_path is not None
            }
        }
    
    async def export_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Export all data for a specific user"""
        try:
            export_data = {
                "user_id": user_id,
                "export_timestamp": datetime.now().isoformat(),
                "conversation_history": [],
                "user_summary": self.user_summaries.get(user_id, ""),
                "sessions": []
            }
            
            # Export conversation history
            if user_id in self.conversation_history:
                for turn in self.conversation_history[user_id]:
                    turn_dict = asdict(turn) if hasattr(turn, '__dataclass_fields__') else turn
                    if "timestamp" in turn_dict and isinstance(turn_dict["timestamp"], datetime):
                        turn_dict["timestamp"] = turn_dict["timestamp"].isoformat()
                    export_data["conversation_history"].append(turn_dict)
            
            # Export active sessions
            for session_id, session in self.active_sessions.items():
                if session.user_id == user_id:
                    session_dict = asdict(session)
                    # Convert datetime fields
                    for field in ["start_time", "last_activity"]:
                        if field in session_dict and isinstance(session_dict[field], datetime):
                            session_dict[field] = session_dict[field].isoformat()
                    # Convert conversation turns
                    session_dict["conversation_turns"] = [
                        asdict(turn) for turn in session_dict["conversation_turns"]
                    ]
                    export_data["sessions"].append(session_dict)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export data for user {user_id}: {e}")
            return None
    
    async def shutdown(self) -> None:
        """Graceful shutdown of memory system"""
        try:
            # Cancel background task
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Persist all user data if persistence is enabled
            if self.memory_persistence_path:
                for user_id in self.conversation_history.keys():
                    await self._persist_user_data(user_id)
            
            logger.info("Conversation memory system shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during memory system shutdown: {e}")