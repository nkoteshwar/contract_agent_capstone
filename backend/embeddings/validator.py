from typing import Dict, List, Any
from dataclasses import dataclass
from .agents import EmbeddingResult

@dataclass
class ValidationResult:
    """Result of embedding validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class EmbeddingValidator:
    """Validates embedding quality and consistency"""
    
    def __init__(self):
        self.expected_dimension = 1536  # Google gemini-embedding-001 dimension
        self.min_similarity_threshold = 0.1
        self.max_similarity_threshold = 0.99
    
    def validate_embeddings(self, embeddings: List[EmbeddingResult]) -> ValidationResult:
        """Validate a list of embedding results"""
        errors = []
        warnings = []
        
        for i, embedding in enumerate(embeddings):
            # Validate embedding dimensions
            if len(embedding.embedding) != self.expected_dimension:
                errors.append(f"Embedding {i}: Expected dimension {self.expected_dimension}, got {len(embedding.embedding)}")
            
            # Check for null/corrupted embeddings
            if not embedding.embedding or all(x == 0 for x in embedding.embedding):
                errors.append(f"Embedding {i}: Null or zero embedding detected")
            
            # Check for NaN values
            if any(x != x for x in embedding.embedding):  # NaN check
                errors.append(f"Embedding {i}: NaN values detected")
            
            # Validate content length
            if not embedding.content or len(embedding.content.strip()) < 10:
                warnings.append(f"Embedding {i}: Very short content (less than 10 characters)")
            
            # Validate metadata
            if not embedding.metadata:
                warnings.append(f"Embedding {i}: Missing metadata")
        
        # Check for potential duplicates
        duplicate_pairs = self._find_duplicates(embeddings)
        if duplicate_pairs:
            warnings.extend([f"Potential duplicate embeddings: {pair}" for pair in duplicate_pairs])
        
        # Validate semantic consistency
        consistency_issues = self._check_semantic_consistency(embeddings)
        if consistency_issues:
            warnings.extend(consistency_issues)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                "total_embeddings": len(embeddings),
                "error_count": len(errors),
                "warning_count": len(warnings)
            }
        )
    
    def _find_duplicates(self, embeddings: List[EmbeddingResult]) -> List[tuple]:
        """Find potential duplicate embeddings"""
        duplicates = []
        
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = self._cosine_similarity(
                    embeddings[i].embedding, 
                    embeddings[j].embedding
                )
                
                if similarity > self.max_similarity_threshold:
                    duplicates.append((i, j))
        
        return duplicates
    
    def _check_semantic_consistency(self, embeddings: List[EmbeddingResult]) -> List[str]:
        """Check for semantic consistency issues"""
        issues = []
        
        # Group embeddings by type
        by_type = {}
        for i, embedding in enumerate(embeddings):
            embedding_type = embedding.embedding_type
            if embedding_type not in by_type:
                by_type[embedding_type] = []
            by_type[embedding_type].append((i, embedding))
        
        # Check consistency within each type
        for embedding_type, type_embeddings in by_type.items():
            if len(type_embeddings) > 1:
                similarities = []
                for i in range(len(type_embeddings)):
                    for j in range(i + 1, len(type_embeddings)):
                        sim = self._cosine_similarity(
                            type_embeddings[i][1].embedding,
                            type_embeddings[j][1].embedding
                        )
                        similarities.append(sim)
                
                if similarities:
                    avg_similarity = sum(similarities) / len(similarities)
                    if avg_similarity < self.min_similarity_threshold:
                        issues.append(f"Low semantic consistency in {embedding_type} embeddings (avg similarity: {avg_similarity:.3f})")
        
        return issues
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)