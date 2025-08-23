"""File watching service for real-time document indexing."""

import logging
import asyncio
from typing import List, Set, Dict, Optional, Callable, Any
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import json

from watchfiles import awatch, Change
import aiofiles
from pydantic import BaseModel, Field

from src.core.rag_system import RAGSystem
from src.database.models import Document
from src.database.session import DatabaseManager
from src.database.crud import DocumentCRUD
from config.settings import settings

logger = logging.getLogger(__name__)


class FileEvent(BaseModel):
    """File change event model."""
    
    path: Path
    change_type: str  # added, modified, deleted
    timestamp: datetime = Field(default_factory=datetime.now)
    size: Optional[int] = None
    hash: Optional[str] = None


class FileWatcherConfig(BaseModel):
    """File watcher configuration."""
    
    directories: List[Path] = Field(default_factory=list)
    file_patterns: List[str] = Field(default_factory=lambda: ["*.py", "*.md", "*.txt", "*.json"])
    ignore_patterns: List[str] = Field(default_factory=lambda: ["__pycache__", "*.pyc", ".git", ".env"])
    max_file_size: int = Field(default=10485760)  # 10MB
    batch_interval: float = Field(default=2.0)  # seconds
    hash_check: bool = Field(default=True)


class FileWatcher:
    """Watches directories for file changes and triggers RAG indexing."""
    
    def __init__(self, rag_system: RAGSystem):
        self.rag_system = rag_system
        self.db_manager: Optional[DatabaseManager] = None
        self.config = FileWatcherConfig()
        self.watch_task: Optional[asyncio.Task] = None
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.file_hashes: Dict[Path, str] = {}
        self.callbacks: List[Callable[[FileEvent], Any]] = []
        self._running = False
        
    async def initialize(self):
        """Initialize the file watcher."""
        
        try:
            # Initialize database
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            
            # Load existing file hashes
            await self._load_file_hashes()
            
            logger.info("✅ File Watcher initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize File Watcher: {e}")
            raise
    
    async def _load_file_hashes(self):
        """Load existing file hashes from database."""
        
        try:
            async with self.db_manager.get_session() as session:
                crud = DocumentCRUD(session)
                documents = await crud.get_all()
                
                for doc in documents:
                    if doc.source_path and doc.metadata and "file_hash" in doc.metadata:
                        self.file_hashes[Path(doc.source_path)] = doc.metadata["file_hash"]
                        
            logger.info(f"📁 Loaded {len(self.file_hashes)} file hashes")
            
        except Exception as e:
            logger.error(f"❌ Failed to load file hashes: {e}")
    
    def configure(self, config: FileWatcherConfig):
        """Update watcher configuration."""
        self.config = config
        logger.info(f"⚙️ Updated watcher config: {len(config.directories)} directories")
    
    def add_directory(self, directory: Path):
        """Add a directory to watch."""
        
        if directory not in self.config.directories:
            self.config.directories.append(directory)
            logger.info(f"➕ Added watch directory: {directory}")
            
            # Restart watcher if running
            if self._running:
                asyncio.create_task(self._restart_watcher())
    
    def remove_directory(self, directory: Path):
        """Remove a directory from watching."""
        
        if directory in self.config.directories:
            self.config.directories.remove(directory)
            logger.info(f"➖ Removed watch directory: {directory}")
            
            # Restart watcher if running
            if self._running:
                asyncio.create_task(self._restart_watcher())
    
    def add_callback(self, callback: Callable[[FileEvent], Any]):
        """Add a callback for file events."""
        self.callbacks.append(callback)
    
    async def start(self):
        """Start watching for file changes."""
        
        if self._running:
            logger.warning("File watcher already running")
            return
            
        if not self.config.directories:
            logger.warning("No directories configured for watching")
            return
        
        self._running = True
        
        # Start watch task
        self.watch_task = asyncio.create_task(self._watch_files())
        
        # Start processing task
        self.processing_task = asyncio.create_task(self._process_events())
        
        logger.info(f"🔍 Started watching {len(self.config.directories)} directories")
    
    async def stop(self):
        """Stop watching for file changes."""
        
        self._running = False
        
        # Cancel tasks
        if self.watch_task:
            self.watch_task.cancel()
            try:
                await self.watch_task
            except asyncio.CancelledError:
                pass
                
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Stopped file watching")
    
    async def _restart_watcher(self):
        """Restart the watcher with updated configuration."""
        
        await self.stop()
        await asyncio.sleep(0.5)
        await self.start()
    
    async def _watch_files(self):
        """Watch for file changes."""
        
        try:
            # Convert paths to strings for watchfiles
            watch_paths = [str(d) for d in self.config.directories]
            
            async for changes in awatch(*watch_paths):
                for change_type, path_str in changes:
                    path = Path(path_str)
                    
                    # Check if file matches patterns
                    if not self._should_watch_file(path):
                        continue
                    
                    # Create event
                    event = await self._create_file_event(path, change_type)
                    if event:
                        await self.event_queue.put(event)
                        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"❌ Error in file watcher: {e}")
            self._running = False
    
    def _should_watch_file(self, path: Path) -> bool:
        """Check if file should be watched based on patterns."""
        
        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            if path.match(pattern):
                return False
        
        # Check file patterns
        for pattern in self.config.file_patterns:
            if path.match(pattern):
                return True
                
        return False
    
    async def _create_file_event(self, path: Path, change_type: Change) -> Optional[FileEvent]:
        """Create a file event from change."""
        
        try:
            # Map change type
            if change_type == Change.added:
                event_type = "added"
            elif change_type == Change.modified:
                event_type = "modified"
            elif change_type == Change.deleted:
                event_type = "deleted"
            else:
                return None
            
            # Get file info for non-deleted files
            size = None
            file_hash = None
            
            if event_type != "deleted" and path.exists():
                stat = path.stat()
                size = stat.st_size
                
                # Check file size
                if size > self.config.max_file_size:
                    logger.warning(f"File too large, skipping: {path} ({size} bytes)")
                    return None
                
                # Calculate hash if needed
                if self.config.hash_check:
                    file_hash = await self._calculate_file_hash(path)
                    
                    # Check if file actually changed
                    if event_type == "modified":
                        old_hash = self.file_hashes.get(path)
                        if old_hash == file_hash:
                            return None  # No actual change
                    
                    # Update hash cache
                    self.file_hashes[path] = file_hash
            
            return FileEvent(
                path=path,
                change_type=event_type,
                size=size,
                hash=file_hash
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating file event for {path}: {e}")
            return None
    
    async def _calculate_file_hash(self, path: Path) -> str:
        """Calculate file hash for change detection."""
        
        hasher = hashlib.md5()
        
        async with aiofiles.open(path, 'rb') as f:
            while chunk := await f.read(8192):
                hasher.update(chunk)
                
        return hasher.hexdigest()
    
    async def _process_events(self):
        """Process file events in batches."""
        
        batch: List[FileEvent] = []
        last_process_time = datetime.now()
        
        try:
            while self._running:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.config.batch_interval
                    )
                    batch.append(event)
                    
                except asyncio.TimeoutError:
                    pass
                
                # Process batch if interval elapsed or batch is large
                now = datetime.now()
                time_elapsed = (now - last_process_time).total_seconds()
                
                if batch and (time_elapsed >= self.config.batch_interval or len(batch) >= 10):
                    await self._process_batch(batch)
                    batch = []
                    last_process_time = now
                    
        except asyncio.CancelledError:
            # Process remaining events
            if batch:
                await self._process_batch(batch)
            raise
        except Exception as e:
            logger.error(f"❌ Error processing events: {e}")
    
    async def _process_batch(self, events: List[FileEvent]):
        """Process a batch of file events."""
        
        if not events:
            return
            
        logger.info(f"📦 Processing batch of {len(events)} file events")
        
        # Group events by type
        added_files = []
        modified_files = []
        deleted_files = []
        
        for event in events:
            if event.change_type == "added":
                added_files.append(event)
            elif event.change_type == "modified":
                modified_files.append(event)
            elif event.change_type == "deleted":
                deleted_files.append(event)
        
        # Process deletions first
        for event in deleted_files:
            await self._handle_file_deleted(event)
        
        # Process additions
        for event in added_files:
            await self._handle_file_added(event)
        
        # Process modifications
        for event in modified_files:
            await self._handle_file_modified(event)
        
        # Call callbacks
        for event in events:
            for callback in self.callbacks:
                try:
                    result = callback(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"❌ Error in callback for {event.path}: {e}")
    
    async def _handle_file_added(self, event: FileEvent):
        """Handle file addition."""
        
        try:
            # Read file content
            async with aiofiles.open(event.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            # Create document
            document = {
                "title": event.path.name,
                "content": content,
                "source_path": str(event.path),
                "metadata": {
                    "file_type": event.path.suffix,
                    "file_size": event.size,
                    "file_hash": event.hash,
                    "indexed_at": datetime.now().isoformat()
                }
            }
            
            # Add to RAG system
            project_id = getattr(self.rag_system, 'project_id', 1)
            await self.rag_system.add_documents([document], project_id)
            
            logger.info(f"✅ Indexed new file: {event.path.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to index new file {event.path}: {e}")
    
    async def _handle_file_modified(self, event: FileEvent):
        """Handle file modification."""
        
        try:
            # Delete old version from index
            await self._remove_from_index(event.path)
            
            # Add updated version
            await self._handle_file_added(event)
            
            logger.info(f"✅ Re-indexed modified file: {event.path.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to re-index modified file {event.path}: {e}")
    
    async def _handle_file_deleted(self, event: FileEvent):
        """Handle file deletion."""
        
        try:
            await self._remove_from_index(event.path)
            
            # Remove from hash cache
            if event.path in self.file_hashes:
                del self.file_hashes[event.path]
            
            logger.info(f"✅ Removed deleted file from index: {event.path.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to remove deleted file {event.path}: {e}")
    
    async def _remove_from_index(self, path: Path):
        """Remove a file from the index."""
        
        try:
            # Remove from database
            async with self.db_manager.get_session() as session:
                crud = DocumentCRUD(session)
                documents = await crud.get_multi(
                    filters={"source_path": str(path)}
                )
                
                for doc in documents:
                    await crud.delete(doc.id)
            
            # Remove from vector store
            # This would require ChromaDB delete by metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to remove {path} from index: {e}")
    
    async def index_directory(self, directory: Path, recursive: bool = True):
        """Index all files in a directory."""
        
        indexed_count = 0
        
        try:
            pattern = "**/*" if recursive else "*"
            
            for file_pattern in self.config.file_patterns:
                for path in directory.glob(f"{pattern}{file_pattern}"):
                    if not path.is_file():
                        continue
                    
                    if not self._should_watch_file(path):
                        continue
                    
                    # Check if already indexed
                    file_hash = await self._calculate_file_hash(path)
                    if path in self.file_hashes and self.file_hashes[path] == file_hash:
                        continue
                    
                    # Create and process event
                    event = FileEvent(
                        path=path,
                        change_type="added",
                        size=path.stat().st_size,
                        hash=file_hash
                    )
                    
                    await self._handle_file_added(event)
                    indexed_count += 1
            
            logger.info(f"✅ Indexed {indexed_count} files from {directory}")
            return indexed_count
            
        except Exception as e:
            logger.error(f"❌ Failed to index directory {directory}: {e}")
            return indexed_count
    
    async def cleanup(self):
        """Clean up resources."""
        
        try:
            await self.stop()
            
            if self.db_manager:
                await self.db_manager.close()
            
            logger.info("✅ File Watcher cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


# Global file watcher instance
file_watcher = None