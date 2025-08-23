"""Project management system with isolated vector collections."""

import logging
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import asyncio
import aiofiles
import shutil

from pydantic import BaseModel, Field
from chromadb import Client as ChromaClient
from chromadb.config import Settings
import chromadb

from src.database.models import Project, Document
from src.database.session import DatabaseManager
from src.database.crud import ProjectCRUD, DocumentCRUD
from src.core.rag_system import RAGSystem
from config.settings import settings

logger = logging.getLogger(__name__)


class ProjectConfig(BaseModel):
    """Project configuration model."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    github_repo: Optional[str] = None
    file_patterns: List[str] = Field(default_factory=lambda: ["*.py", "*.md", "*.txt"])
    ignore_patterns: List[str] = Field(default_factory=lambda: ["__pycache__", "*.pyc", ".git"])
    max_file_size: int = Field(default=10485760)  # 10MB
    auto_index: bool = Field(default=True)
    rag_settings: Dict[str, Any] = Field(default_factory=dict)


class ProjectStatistics(BaseModel):
    """Project statistics model."""
    
    document_count: int = 0
    total_chunks: int = 0
    total_tokens: int = 0
    index_size_bytes: int = 0
    last_indexed: Optional[datetime] = None
    conversations_count: int = 0
    messages_count: int = 0


class ProjectManager:
    """Manages multiple isolated projects with separate vector collections."""
    
    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.chroma_client: Optional[ChromaClient] = None
        self.rag_systems: Dict[int, RAGSystem] = {}
        self.project_configs: Dict[int, ProjectConfig] = {}
        self.active_project_id: Optional[int] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the project manager."""
        if self._initialized:
            return
            
        try:
            # Initialize database
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            
            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=str(settings.chroma_persist_directory)
            )
            
            # Load existing projects
            await self._load_projects()
            
            self._initialized = True
            logger.info("✅ Project Manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Project Manager: {e}")
            raise
    
    async def _load_projects(self):
        """Load existing projects from database."""
        try:
            async with self.db_manager.get_session() as session:
                crud = ProjectCRUD(session)
                projects = await crud.get_all()
                
                for project in projects:
                    if project.settings:
                        config = ProjectConfig(**project.settings)
                        self.project_configs[project.id] = config
                        
            logger.info(f"📁 Loaded {len(self.project_configs)} projects")
            
        except Exception as e:
            logger.error(f"❌ Failed to load projects: {e}")
    
    async def create_project(
        self,
        config: ProjectConfig,
        user_id: Optional[int] = None
    ) -> Project:
        """Create a new project with isolated vector collection."""
        
        try:
            # Generate unique collection name
            collection_name = f"project_{config.name.lower().replace(' ', '_')}_{datetime.now().timestamp():.0f}"
            
            # Create ChromaDB collection
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"project_name": config.name}
            )
            
            # Save to database
            async with self.db_manager.get_session() as session:
                crud = ProjectCRUD(session)
                project = await crud.create({
                    "name": config.name,
                    "description": config.description,
                    "github_repo": config.github_repo,
                    "settings": config.dict(),
                    "vector_collection_name": collection_name,
                    "user_id": user_id
                })
                
            # Initialize RAG system for project
            rag_system = RAGSystem()
            await rag_system.initialize()
            rag_system.collection_name = collection_name
            self.rag_systems[project.id] = rag_system
            
            # Store config
            self.project_configs[project.id] = config
            
            # Create project directory
            project_dir = Path(f"./data/projects/{project.id}")
            project_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"✅ Created project: {config.name} (ID: {project.id})")
            return project
            
        except Exception as e:
            logger.error(f"❌ Failed to create project: {e}")
            raise
    
    async def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        
        try:
            async with self.db_manager.get_session() as session:
                crud = ProjectCRUD(session)
                return await crud.get(project_id)
                
        except Exception as e:
            logger.error(f"❌ Failed to get project {project_id}: {e}")
            return None
    
    async def list_projects(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """List all projects, optionally filtered by user."""
        
        try:
            async with self.db_manager.get_session() as session:
                crud = ProjectCRUD(session)
                
                filters = {}
                if user_id:
                    filters["user_id"] = user_id
                    
                return await crud.get_multi(
                    skip=skip,
                    limit=limit,
                    filters=filters
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to list projects: {e}")
            return []
    
    async def update_project(
        self,
        project_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Project]:
        """Update project configuration."""
        
        try:
            async with self.db_manager.get_session() as session:
                crud = ProjectCRUD(session)
                project = await crud.update(project_id, updates)
                
                if project and "settings" in updates:
                    config = ProjectConfig(**updates["settings"])
                    self.project_configs[project_id] = config
                    
                return project
                
        except Exception as e:
            logger.error(f"❌ Failed to update project {project_id}: {e}")
            return None
    
    async def delete_project(self, project_id: int) -> bool:
        """Delete a project and its vector collection."""
        
        try:
            # Get project details
            project = await self.get_project(project_id)
            if not project:
                return False
            
            # Delete ChromaDB collection
            if project.vector_collection_name:
                try:
                    self.chroma_client.delete_collection(project.vector_collection_name)
                except:
                    pass  # Collection might not exist
            
            # Delete from database
            async with self.db_manager.get_session() as session:
                crud = ProjectCRUD(session)
                await crud.delete(project_id)
            
            # Clean up memory
            if project_id in self.rag_systems:
                del self.rag_systems[project_id]
            if project_id in self.project_configs:
                del self.project_configs[project_id]
            
            # Delete project directory
            project_dir = Path(f"./data/projects/{project_id}")
            if project_dir.exists():
                shutil.rmtree(project_dir)
            
            logger.info(f"✅ Deleted project: {project.name} (ID: {project_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete project {project_id}: {e}")
            return False
    
    async def switch_project(self, project_id: int) -> bool:
        """Switch to a different project."""
        
        try:
            project = await self.get_project(project_id)
            if not project:
                logger.error(f"Project {project_id} not found")
                return False
            
            # Initialize RAG system if not loaded
            if project_id not in self.rag_systems:
                rag_system = RAGSystem()
                await rag_system.initialize()
                rag_system.collection_name = project.vector_collection_name
                self.rag_systems[project_id] = rag_system
            
            self.active_project_id = project_id
            logger.info(f"✅ Switched to project: {project.name} (ID: {project_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to switch to project {project_id}: {e}")
            return False
    
    def get_active_rag_system(self) -> Optional[RAGSystem]:
        """Get RAG system for active project."""
        
        if not self.active_project_id:
            logger.warning("No active project selected")
            return None
            
        return self.rag_systems.get(self.active_project_id)
    
    async def get_project_statistics(self, project_id: int) -> ProjectStatistics:
        """Get statistics for a project."""
        
        stats = ProjectStatistics()
        
        try:
            # Get document count
            async with self.db_manager.get_session() as session:
                doc_crud = DocumentCRUD(session)
                documents = await doc_crud.get_multi(
                    filters={"project_id": project_id}
                )
                stats.document_count = len(documents)
                
                # Calculate totals
                for doc in documents:
                    if doc.metadata:
                        stats.total_chunks += doc.metadata.get("chunk_count", 0)
                        stats.total_tokens += doc.metadata.get("token_count", 0)
                        
                if documents:
                    stats.last_indexed = max(d.created_at for d in documents)
            
            # Get collection size
            project = await self.get_project(project_id)
            if project and project.vector_collection_name:
                try:
                    collection = self.chroma_client.get_collection(
                        project.vector_collection_name
                    )
                    stats.total_chunks = collection.count()
                except:
                    pass
            
            # Get conversation/message counts
            # This would require conversation/message CRUD operations
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get statistics for project {project_id}: {e}")
            return stats
    
    async def import_project(self, project_path: Path) -> Optional[Project]:
        """Import a project from exported JSON."""
        
        try:
            async with aiofiles.open(project_path, 'r') as f:
                data = json.loads(await f.read())
            
            config = ProjectConfig(**data["config"])
            project = await self.create_project(config)
            
            # Import documents if included
            if "documents" in data:
                rag_system = self.rag_systems[project.id]
                await rag_system.add_documents(data["documents"], project.id)
            
            logger.info(f"✅ Imported project from {project_path}")
            return project
            
        except Exception as e:
            logger.error(f"❌ Failed to import project from {project_path}: {e}")
            return None
    
    async def export_project(self, project_id: int, export_path: Path) -> bool:
        """Export a project to JSON."""
        
        try:
            project = await self.get_project(project_id)
            if not project:
                return False
            
            config = self.project_configs.get(project_id)
            if not config:
                config = ProjectConfig(name=project.name)
            
            # Get documents
            async with self.db_manager.get_session() as session:
                doc_crud = DocumentCRUD(session)
                documents = await doc_crud.get_multi(
                    filters={"project_id": project_id}
                )
            
            # Prepare export data
            export_data = {
                "project": {
                    "name": project.name,
                    "description": project.description,
                    "github_repo": project.github_repo
                },
                "config": config.dict(),
                "documents": [
                    {
                        "title": doc.title,
                        "content": doc.content,
                        "metadata": doc.metadata
                    }
                    for doc in documents
                ],
                "exported_at": datetime.now().isoformat()
            }
            
            # Write to file
            export_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(export_path, 'w') as f:
                await f.write(json.dumps(export_data, indent=2, default=str))
            
            logger.info(f"✅ Exported project {project_id} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to export project {project_id}: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        
        try:
            # Clean up RAG systems
            for rag_system in self.rag_systems.values():
                await rag_system.cleanup()
            
            # Close database
            if self.db_manager:
                await self.db_manager.close()
            
            self._initialized = False
            logger.info("✅ Project Manager cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


# Global project manager instance
project_manager = ProjectManager()