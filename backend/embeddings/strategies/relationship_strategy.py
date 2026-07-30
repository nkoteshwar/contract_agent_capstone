from typing import List, Dict, Any
from backend.shared.utils.gemini_embedding_service import embedding
from . import EmbeddingStrategy

class RelationshipEmbeddingStrategy(EmbeddingStrategy):
    """Strategy for generating relationship context embeddings"""
    
    def __init__(self):
        self.embeddings = embedding
    
    def generate_embedding(self, content: str, metadata: Dict[str, Any] = None) -> List[float]:
        """Generate embedding for relationship context"""
        if not metadata:
            return self.embeddings.embed_query(content)
        
        # Build relationship context
        relationship_type = metadata.get("relationship_type", "")
        source_entity = metadata.get("source_entity", "")
        target_entity = metadata.get("target_entity", "")
        role = metadata.get("role", "")
        
        # Create contextual relationship description
        context_parts = []
        if source_entity and target_entity:
            context_parts.append(f"{source_entity} {relationship_type} {target_entity}")
        if role:
            context_parts.append(f"Role: {role}")
        if content:
            context_parts.append(f"Context: {content}")
        
        enhanced_content = ". ".join(context_parts)
        return self.embeddings.embed_query(enhanced_content)
    
    def get_embedding_dimension(self) -> int:
        return 1536