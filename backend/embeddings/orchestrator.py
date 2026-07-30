from typing import Dict, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .agents import EmbeddingResult
from .agents.document_embedding_agent import DocumentEmbeddingAgent
from .agents.clause_embedding_agent import ClauseEmbeddingAgent
from .agents.relationship_embedding_agent import RelationshipEmbeddingAgent

@dataclass
class ProcessingResult:
    """Result of document processing"""
    document_embeddings: List[EmbeddingResult]
    clause_embeddings: List[EmbeddingResult]
    relationship_embeddings: List[EmbeddingResult]
    metadata: Dict[str, Any]

class EmbeddingCommand(ABC):
    """Abstract command for embedding processing"""
    
    @abstractmethod
    def execute(self, content: str, metadata: Dict[str, Any]) -> List[EmbeddingResult]:
        pass

class DocumentEmbeddingCommand(EmbeddingCommand):
    """Command for document embedding processing"""
    
    def __init__(self):
        self.agent = DocumentEmbeddingAgent()
    
    def execute(self, content: str, metadata: Dict[str, Any]) -> List[EmbeddingResult]:
        return self.agent.process(content, metadata)

class ClauseEmbeddingCommand(EmbeddingCommand):
    """Command for clause embedding processing"""
    
    def __init__(self):
        self.agent = ClauseEmbeddingAgent()
    
    def execute(self, content: str, metadata: Dict[str, Any]) -> List[EmbeddingResult]:
        return self.agent.process(content, metadata)

class RelationshipEmbeddingCommand(EmbeddingCommand):
    """Command for relationship embedding processing"""
    
    def __init__(self):
        self.agent = RelationshipEmbeddingAgent()
    
    def execute(self, content: str, metadata: Dict[str, Any]) -> List[EmbeddingResult]:
        return self.agent.process(content, metadata)

class EmbeddingOrchestrator:
    """Orchestrates multi-level embedding processing"""
    
    def __init__(self):
        self.commands = [
            DocumentEmbeddingCommand(),
            ClauseEmbeddingCommand(),
            RelationshipEmbeddingCommand()
        ]
    
    def process_document(self, content: str, metadata: Dict[str, Any] = None) -> ProcessingResult:
        """Process document through all embedding agents"""
        if metadata is None:
            metadata = {}
        
        document_embeddings = []
        clause_embeddings = []
        relationship_embeddings = []
        
        for command in self.commands:
            results = command.execute(content, metadata)
            
            for result in results:
                if result.embedding_type == "document" or result.embedding_type == "section":
                    document_embeddings.append(result)
                elif result.embedding_type == "clause":
                    clause_embeddings.append(result)
                elif result.embedding_type == "relationship":
                    relationship_embeddings.append(result)
        
        return ProcessingResult(
            document_embeddings=document_embeddings,
            clause_embeddings=clause_embeddings,
            relationship_embeddings=relationship_embeddings,
            metadata={
                **metadata,
                "total_embeddings": len(document_embeddings) + len(clause_embeddings) + len(relationship_embeddings),
                "processing_complete": True
            }
        )