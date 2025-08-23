"""
Database session management for WhatsApp AI Chatbot.

Provides async SQLAlchemy session management with SQLite backend,
WAL mode optimization, connection pooling, and proper error handling.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool, QueuePool

from .models import Base
from ..utils.performance import async_timing_decorator, perf_monitor

logger = logging.getLogger(__name__)


class DatabaseSession:
    """
    Database session manager with async SQLAlchemy support.
    
    Handles connection pooling, WAL mode configuration, and session lifecycle.
    """
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///./data/chatbot.db"):
        """
        Initialize database session manager.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
        
        # Performance monitoring
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "average_connection_time": 0.0,
            "last_health_check": None
        }
        
    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._initialized:
            return
            
        try:
            # Create data directory if it doesn't exist
            db_path = Path("./data")
            db_path.mkdir(exist_ok=True)
            
            # Determine optimal connection pool settings
            if "sqlite" in self.database_url:
                pool_class = StaticPool
                pool_size = 1  # SQLite doesn't support multiple writers
                max_overflow = 0
            else:
                pool_class = QueuePool
                pool_size = 5  # Base pool size
                max_overflow = 10  # Additional connections
            
            # Create async engine with optimized settings
            self._engine = create_async_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                future=True,
                poolclass=pool_class,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_timeout=30,  # Timeout for getting connection
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                } if "sqlite" in self.database_url else {},
            )
            
            # Configure SQLite for optimal performance
            @event.listens_for(self._engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                """Configure SQLite pragmas for optimal performance."""
                cursor = dbapi_connection.cursor()
                # Enable WAL mode for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")
                # Set synchronous mode to NORMAL for better performance
                cursor.execute("PRAGMA synchronous=NORMAL")
                # Increase cache size (negative value = KB)
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                # Set temp store to memory
                cursor.execute("PRAGMA temp_store=MEMORY")
                # Optimize for SSD
                cursor.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
                cursor.close()
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            
            # Create all tables
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic cleanup and performance monitoring.
        
        Yields:
            AsyncSession: Database session
            
        Raises:
            RuntimeError: If database not initialized
        """
        if not self._initialized or not self._session_factory:
            raise RuntimeError("Database not initialized")
        
        start_time = time.time()
        session = None
        
        try:
            session = self._session_factory()
            self._connection_stats["total_connections"] += 1
            self._connection_stats["active_connections"] += 1
            
            connection_time = time.time() - start_time
            
            # Update average connection time
            total_conns = self._connection_stats["total_connections"]
            current_avg = self._connection_stats["average_connection_time"]
            self._connection_stats["average_connection_time"] = (
                (current_avg * (total_conns - 1) + connection_time) / total_conns
            )
            
            yield session
            await session.commit()
            
        except Exception as e:
            if session:
                await session.rollback()
            self._connection_stats["failed_connections"] += 1
            logger.error(f"Database session error: {e}")
            raise
        finally:
            if session:
                await session.close()
            self._connection_stats["active_connections"] -= 1
    
    @async_timing_decorator
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive database health check.
        
        Returns:
            Dict containing health status and statistics
        """
        health_data = {
            "healthy": False,
            "connection_stats": self._connection_stats.copy(),
            "pool_stats": {},
            "last_check": datetime.now().isoformat(),
            "response_time_ms": 0
        }
        
        start_time = time.time()
        
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                health_data["healthy"] = result.scalar() == 1
                
                # Get pool statistics if available
                if hasattr(self._engine.pool, 'size'):
                    health_data["pool_stats"] = {
                        "pool_size": self._engine.pool.size(),
                        "checked_in": self._engine.pool.checkedin(),
                        "checked_out": self._engine.pool.checkedout(),
                        "overflow": self._engine.pool.overflow(),
                        "invalidated": self._engine.pool.invalidated()
                    }
                    
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_data["error"] = str(e)
        finally:
            health_data["response_time_ms"] = (time.time() - start_time) * 1000
            self._connection_stats["last_health_check"] = health_data["last_check"]
        
        return health_data
    
    @async_timing_decorator
    async def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization commands with performance tracking."""
        optimization_results = {
            "started_at": datetime.now().isoformat(),
            "operations": [],
            "total_time_ms": 0,
            "success": False
        }
        
        start_time = time.time()
        
        try:
            async with self.get_session() as session:
                # Analyze tables for query optimization
                op_start = time.time()
                await session.execute(text("ANALYZE"))
                analyze_time = (time.time() - op_start) * 1000
                optimization_results["operations"].append({
                    "operation": "ANALYZE",
                    "duration_ms": analyze_time
                })
                
                # Clean up unused space (SQLite only)
                if "sqlite" in self.database_url:
                    op_start = time.time()
                    await session.execute(text("VACUUM"))
                    vacuum_time = (time.time() - op_start) * 1000
                    optimization_results["operations"].append({
                        "operation": "VACUUM",
                        "duration_ms": vacuum_time
                    })
                
                await session.commit()
                optimization_results["success"] = True
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            optimization_results["error"] = str(e)
            raise
        finally:
            optimization_results["total_time_ms"] = (time.time() - start_time) * 1000
            optimization_results["completed_at"] = datetime.now().isoformat()
            
        logger.info(f"Database optimization completed in {optimization_results['total_time_ms']:.2f}ms")
        return optimization_results


# Global database session instance
_db_session: Optional[DatabaseSession] = None


async def init_database(database_url: str = "sqlite+aiosqlite:///./data/chatbot.db") -> DatabaseSession:
    """
    Initialize global database session.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        DatabaseSession: Initialized database session
    """
    global _db_session
    
    if _db_session is None:
        _db_session = DatabaseSession(database_url)
        await _db_session.initialize()
    
    return _db_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        RuntimeError: If database not initialized
    """
    global _db_session
    
    if _db_session is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with _db_session.get_session() as session:
        yield session


async def close_database() -> None:
    """Close global database session."""
    global _db_session
    
    if _db_session:
        await _db_session.close()
        _db_session = None