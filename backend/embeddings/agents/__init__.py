from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    embedding: List[float]
    metadata: Dict[str, Any]
    content: str
    embedding_type: str

class EmbeddingAgent(ABC):
    """Abstract base class for embedding agents"""
    
    @abstractmethod
    def process(self, content: str, metadata: Dict[str, Any] = None) -> List[EmbeddingResult]:
        """Process content and return embedding results"""
        pass