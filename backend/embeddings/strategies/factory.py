from typing import Dict
from . import EmbeddingStrategy, EmbeddingType
from .document_strategy import DocumentEmbeddingStrategy
from .clause_strategy import ClauseEmbeddingStrategy
from .relationship_strategy import RelationshipEmbeddingStrategy

class EmbeddingFactory:
    """Factory for creating embedding strategies"""
    
    def __init__(self):
        self._strategies: Dict[EmbeddingType, EmbeddingStrategy] = {}
    
    def create_strategy(self, embedding_type: EmbeddingType) -> EmbeddingStrategy:
        """Create or return cached embedding strategy"""
        if embedding_type not in self._strategies:
            if embedding_type == EmbeddingType.DOCUMENT:
                self._strategies[embedding_type] = DocumentEmbeddingStrategy()
            elif embedding_type == EmbeddingType.CLAUSE:
                self._strategies[embedding_type] = ClauseEmbeddingStrategy()
            elif embedding_type == EmbeddingType.RELATIONSHIP:
                self._strategies[embedding_type] = RelationshipEmbeddingStrategy()
            elif embedding_type == EmbeddingType.SECTION:
                self._strategies[embedding_type] = DocumentEmbeddingStrategy()  # Reuse document strategy for sections
            else:
                raise ValueError(f"Unknown embedding type: {embedding_type}")
        
        return self._strategies[embedding_type]