from functools import lru_cache
from backend.services.document_processing_service import DocumentServiceFactory
from backend.agent_manager import AgentManager

# Dependency injection setup following SOLID principles

@lru_cache()
def get_agent_manager() -> AgentManager:
    """Get singleton agent manager instance"""
    return AgentManager()

@lru_cache()
def get_document_service():
    """Get document processing service with injected dependencies"""
    agent_manager = get_agent_manager()
    return DocumentServiceFactory.create_service(agent_manager)