"""Content density analyzer for adaptive chunking optimization."""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class ContentMetrics:
    """Content density and complexity metrics."""
    sentence_density: float
    clause_density: float
    legal_term_density: float
    complexity_score: float
    optimal_chunk_size: int
    recommended_overlap: float


class ContentDensityAnalyzer:
    """Singleton analyzer for content density and chunking optimization."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Legal terms for density calculation
        self.legal_terms = [
            'agreement', 'contract', 'party', 'parties', 'clause', 'provision',
            'shall', 'whereas', 'therefore', 'notwithstanding', 'pursuant',
            'liability', 'indemnify', 'breach', 'default', 'termination',
            'confidential', 'proprietary', 'intellectual property', 'copyright',
            'warranty', 'representation', 'covenant', 'obligation', 'consideration'
        ]
        
        # Complex sentence patterns
        self.complex_patterns = [
            r'(?:provided\s+that|subject\s+to|in\s+the\s+event)',
            r'(?:notwithstanding|furthermore|nevertheless)',
            r'(?:including\s+but\s+not\s+limited\s+to)',
            r'(?:to\s+the\s+extent\s+that|except\s+as\s+otherwise)',
        ]
        
        # Embedding model considerations (1536D)
        self.max_tokens_per_chunk = 512  # Conservative limit for 1536D embeddings
        self.chars_per_token = 4  # Approximate characters per token
        self.max_chars_for_embedding = self.max_tokens_per_chunk * self.chars_per_token
    
    def analyze_content_density(self, text: str, document_analysis: Dict[str, Any] = None) -> ContentMetrics:
        """Analyze content density and determine optimal chunking parameters."""
        # Basic metrics
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+\s+', text))
        
        # Calculate densities
        sentence_density = sentence_count / max(word_count, 1) * 100
        clause_density = self._calculate_clause_density(text)
        legal_term_density = self._calculate_legal_term_density(text)
        complexity_score = self._calculate_complexity_score(text)
        
        # Determine optimal chunk size based on content
        optimal_chunk_size = self._calculate_optimal_chunk_size(
            complexity_score, legal_term_density, len(text)
        )
        
        # Calculate recommended overlap
        recommended_overlap = self._calculate_optimal_overlap(
            complexity_score, clause_density, document_analysis
        )
        
        return ContentMetrics(
            sentence_density=sentence_density,
            clause_density=clause_density,
            legal_term_density=legal_term_density,
            complexity_score=complexity_score,
            optimal_chunk_size=optimal_chunk_size,
            recommended_overlap=recommended_overlap
        )
    
    def _calculate_clause_density(self, text: str) -> float:
        """Calculate density of legal clauses in text."""
        clause_indicators = [
            r'(?:shall|will|must|may)\s+(?:not\s+)?(?:be|have|do)',
            r'(?:party|parties)\s+(?:agrees?|acknowledges?)',
            r'(?:provided|whereas|therefore|furthermore)',
            r'(?:in\s+consideration|subject\s+to|notwithstanding)',
        ]
        
        total_matches = 0
        for pattern in clause_indicators:
            total_matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        word_count = len(text.split())
        return total_matches / max(word_count, 1) * 100
    
    def _calculate_legal_term_density(self, text: str) -> float:
        """Calculate density of legal terminology."""
        text_lower = text.lower()
        legal_term_count = sum(1 for term in self.legal_terms if term in text_lower)
        
        word_count = len(text.split())
        return legal_term_count / max(word_count, 1) * 100
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate overall text complexity score (0-1)."""
        # Sentence length complexity
        sentences = re.split(r'[.!?]+\s+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        length_complexity = min(1.0, avg_sentence_length / 30)  # Normalize to 30 words
        
        # Complex pattern density
        complex_matches = 0
        for pattern in self.complex_patterns:
            complex_matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        pattern_complexity = min(1.0, complex_matches / max(len(sentences), 1) * 5)
        
        # Punctuation complexity (nested clauses)
        comma_density = text.count(',') / max(len(text), 1) * 100
        semicolon_density = text.count(';') / max(len(text), 1) * 100
        punctuation_complexity = min(1.0, (comma_density + semicolon_density * 2) / 10)
        
        # Combined complexity score
        return (length_complexity * 0.4 + pattern_complexity * 0.4 + punctuation_complexity * 0.2)
    
    def _calculate_optimal_chunk_size(self, complexity: float, legal_density: float, doc_length: int) -> int:
        """Calculate optimal chunk size based on content characteristics."""
        # Base chunk size considering embedding limits
        base_size = min(1000, self.max_chars_for_embedding)
        
        # Adjust based on complexity
        if complexity > 0.7:
            # High complexity - smaller chunks for better comprehension
            size_multiplier = 0.6
        elif complexity > 0.4:
            # Medium complexity - moderate chunks
            size_multiplier = 0.8
        else:
            # Low complexity - larger chunks for efficiency
            size_multiplier = 1.0
        
        # Adjust based on legal term density
        if legal_density > 5.0:
            # High legal density - smaller chunks to preserve context
            size_multiplier *= 0.7
        elif legal_density > 2.0:
            # Medium legal density - slight reduction
            size_multiplier *= 0.85
        
        # Adjust based on document length
        if doc_length < 2000:
            # Short document - smaller chunks
            size_multiplier *= 0.7
        elif doc_length > 20000:
            # Long document - can use larger chunks
            size_multiplier *= 1.2
        
        optimal_size = int(base_size * size_multiplier)
        
        # Ensure within reasonable bounds
        return max(200, min(optimal_size, self.max_chars_for_embedding))
    
    def _calculate_optimal_overlap(self, complexity: float, clause_density: float, 
                                 document_analysis: Dict[str, Any] = None) -> float:
        """Calculate optimal overlap ratio based on content characteristics."""
        base_overlap = 0.2  # 20% base overlap
        
        # Increase overlap for complex content
        if complexity > 0.7:
            base_overlap += 0.15  # Up to 35% for very complex
        elif complexity > 0.4:
            base_overlap += 0.1   # Up to 30% for moderately complex
        
        # Increase overlap for high clause density
        if clause_density > 3.0:
            base_overlap += 0.1   # More overlap for clause-heavy content
        
        # Adjust based on document type
        if document_analysis:
            if document_analysis.get('is_contract', False):
                base_overlap += 0.05  # Contracts need more context preservation
            
            if document_analysis.get('has_hierarchical_structure', False):
                base_overlap += 0.05  # Structured documents benefit from overlap
        
        # Cap at reasonable maximum
        return min(base_overlap, 0.5)  # Maximum 50% overlap
    
    def get_embedding_optimized_size(self, content_length: int) -> int:
        """Get chunk size optimized for 1536D embeddings."""
        # Conservative approach to ensure embeddings fit
        if content_length <= self.max_chars_for_embedding:
            return content_length
        
        # Split into optimal sizes
        num_chunks = (content_length // self.max_chars_for_embedding) + 1
        return content_length // num_chunks
    
    def analyze_chunk_quality(self, chunk: str, target_size: int) -> Dict[str, Any]:
        """Analyze the quality of a generated chunk."""
        chunk_length = len(chunk)
        word_count = len(chunk.split())
        sentence_count = len(re.split(r'[.!?]+\s+', chunk))
        
        # Quality metrics
        size_score = 1.0 - abs(chunk_length - target_size) / target_size
        completeness_score = 1.0 if chunk.rstrip().endswith(('.', '!', '?', ';')) else 0.7
        
        # Check for incomplete sentences at boundaries
        boundary_quality = 1.0
        if not chunk.strip():
            boundary_quality = 0.0
        elif chunk.strip()[0].islower():
            boundary_quality *= 0.8  # Starts mid-sentence
        
        if not chunk.rstrip()[-1] in '.!?;':
            boundary_quality *= 0.8  # Ends mid-sentence
        
        overall_quality = (size_score * 0.4 + completeness_score * 0.3 + boundary_quality * 0.3)
        
        return {
            'chunk_length': chunk_length,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'size_score': size_score,
            'completeness_score': completeness_score,
            'boundary_quality': boundary_quality,
            'overall_quality': overall_quality,
            'embedding_ready': chunk_length <= self.max_chars_for_embedding
        }