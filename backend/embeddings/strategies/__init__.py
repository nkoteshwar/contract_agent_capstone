from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum

class EmbeddingType(Enum):
    DOCUMENT = "document"
    CLAUSE = "clause"
    RELATIONSHIP = "relationship"
    SECTION = "section"

class EmbeddingStrategy(ABC):
    """Abstract base class for different embedding strategies"""
    
    @abstractmethod
    def generate_embedding(self, content: str, metadata: Dict[str, Any] = None) -> List[float]:
        """Generate embedding for given content"""
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this strategy"""
        pass