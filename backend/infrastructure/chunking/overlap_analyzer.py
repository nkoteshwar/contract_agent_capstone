"""Advanced overlap analysis using Strategy pattern."""

import re
from typing import List, Dict, Any, Tuple
from abc import ABC, abstractmethod


class OverlapStrategy(ABC):
    """Base strategy for overlap calculation."""
    
    @abstractmethod
    def calculate_overlap(self, current_chunk: str, next_chunk: str, 
                         context: Dict[str, Any]) -> Tuple[str, float]:
        """Calculate overlap content and quality score."""
        pass


class SemanticOverlapStrategy(OverlapStrategy):
    """Content-aware overlap that preserves semantic meaning."""
    
    def calculate_overlap(self, current_chunk: str, next_chunk: str, 
                         context: Dict[str, Any]) -> Tuple[str, float]:
        """Calculate semantic overlap based on sentence boundaries."""
        # Get last N sentences from current chunk
        overlap_ratio = context.get('overlap_ratio', 0.2)
        sentences = self._split_sentences(current_chunk)
        
        if not sentences:
            return "", 0.0
        
        # Calculate number of sentences to overlap
        overlap_count = max(1, int(len(sentences) * overlap_ratio))
        overlap_sentences = sentences[-overlap_count:]
        
        # Check if overlap preserves complete thoughts
        overlap_content = ' '.join(overlap_sentences)
        quality_score = self._assess_semantic_quality(overlap_content, next_chunk)
        
        return overlap_content, quality_score
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _assess_semantic_quality(self, overlap: str, next_chunk: str) -> float:
        """Assess if overlap preserves semantic meaning."""
        # Check if overlap ends with complete sentence
        completeness = 1.0 if overlap.rstrip().endswith(('.', '!', '?')) else 0.7
        
        # Check if overlap provides context for next chunk
        overlap_words = set(overlap.lower().split())
        next_words = set(next_chunk[:200].lower().split())
        context_overlap = len(overlap_words & next_words) / max(len(next_words), 1)
        
        # Combined quality score
        return (completeness * 0.6 + min(context_overlap * 2, 1.0) * 0.4)


class ClauseBoundaryOverlapStrategy(OverlapStrategy):
    """Overlap that respects legal clause boundaries."""
    
    def __init__(self):
        self.clause_patterns = [
            r'(?:PROVIDED|WHEREAS|THEREFORE|FURTHERMORE)',
            r'(?:shall|will|must|may)\s+(?:not\s+)?(?:be|have|do)',
            r'(?:Party|Parties|Company)\s+(?:agrees?|acknowledges?)',
            r'(?:In\s+the\s+event|If|Unless|Subject\s+to)'
        ]
    
    def calculate_overlap(self, current_chunk: str, next_chunk: str, 
                         context: Dict[str, Any]) -> Tuple[str, float]:
        """Calculate overlap respecting clause boundaries."""
        # Find clause boundaries in current chunk
        clause_boundaries = self._find_clause_boundaries(current_chunk)
        
        if not clause_boundaries:
            # Fallback to semantic overlap
            semantic_strategy = SemanticOverlapStrategy()
            return semantic_strategy.calculate_overlap(current_chunk, next_chunk, context)
        
        # Get last complete clause(s) for overlap
        overlap_ratio = context.get('overlap_ratio', 0.25)  # Higher for legal content
        overlap_boundary = int(len(current_chunk) * (1 - overlap_ratio))
        
        # Find nearest clause boundary before overlap point
        nearest_boundary = max([b for b in clause_boundaries if b <= overlap_boundary], 
                              default=clause_boundaries[-1])
        
        overlap_content = current_chunk[nearest_boundary:].strip()
        quality_score = self._assess_clause_quality(overlap_content)
        
        return overlap_content, quality_score
    
    def _find_clause_boundaries(self, text: str) -> List[int]:
        """Find positions of clause boundaries."""
        boundaries = []
        
        for pattern in self.clause_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                boundaries.append(match.start())
        
        # Also add sentence boundaries as potential clause boundaries
        for match in re.finditer(r'[.!?]\s+', text):
            boundaries.append(match.end())
        
        return sorted(set(boundaries))
    
    def _assess_clause_quality(self, overlap: str) -> float:
        """Assess if overlap contains complete clauses."""
        # Check for clause indicators
        has_clause_start = any(re.search(pattern, overlap, re.IGNORECASE) 
                              for pattern in self.clause_patterns)
        
        # Check for complete sentences
        complete_sentence = overlap.rstrip().endswith(('.', '!', '?', ';'))
        
        # Quality score based on clause completeness
        if has_clause_start and complete_sentence:
            return 0.95
        elif complete_sentence:
            return 0.85
        else:
            return 0.7


class ContextPreservationScorer:
    """Measures how well overlap preserves context."""
    
    def score_overlap_quality(self, current_chunk: str, overlap: str, 
                             next_chunk: str) -> Dict[str, float]:
        """Comprehensive overlap quality scoring."""
        scores = {}
        
        # 1. Boundary quality - does overlap start/end at natural boundaries
        scores['boundary_quality'] = self._score_boundary_quality(overlap)
        
        # 2. Context continuity - does overlap provide context for next chunk
        scores['context_continuity'] = self._score_context_continuity(overlap, next_chunk)
        
        # 3. Information preservation - does overlap preserve key information
        scores['information_preservation'] = self._score_information_preservation(
            current_chunk, overlap
        )
        
        # 4. Legal context - does overlap preserve legal meaning
        scores['legal_context'] = self._score_legal_context(overlap)
        
        # Overall score
        scores['overall'] = (
            scores['boundary_quality'] * 0.3 +
            scores['context_continuity'] * 0.3 +
            scores['information_preservation'] * 0.2 +
            scores['legal_context'] * 0.2
        )
        
        return scores
    
    def _score_boundary_quality(self, overlap: str) -> float:
        """Score if overlap has clean boundaries."""
        if not overlap:
            return 0.0
        
        # Check start boundary
        starts_clean = overlap[0].isupper() or overlap[0].isdigit()
        
        # Check end boundary
        ends_clean = overlap.rstrip().endswith(('.', '!', '?', ';', ':'))
        
        return (starts_clean * 0.5 + ends_clean * 0.5)
    
    def _score_context_continuity(self, overlap: str, next_chunk: str) -> float:
        """Score if overlap provides context for next chunk."""
        if not overlap or not next_chunk:
            return 0.0
        
        # Check word overlap between overlap and next chunk
        overlap_words = set(overlap.lower().split())
        next_words = set(next_chunk[:300].lower().split())
        
        common_words = overlap_words & next_words
        continuity = len(common_words) / max(len(next_words), 1)
        
        return min(continuity * 3, 1.0)  # Scale up to max 1.0
    
    def _score_information_preservation(self, current_chunk: str, overlap: str) -> float:
        """Score if overlap preserves important information."""
        if not overlap or not current_chunk:
            return 0.0
        
        # Calculate what percentage of current chunk is in overlap
        overlap_ratio = len(overlap) / len(current_chunk)
        
        # Optimal overlap is 20-30%
        if 0.15 <= overlap_ratio <= 0.35:
            return 1.0
        elif 0.10 <= overlap_ratio <= 0.50:
            return 0.8
        else:
            return 0.6
    
    def _score_legal_context(self, overlap: str) -> float:
        """Enhanced legal context scoring with definitional relationship preservation."""
        if not overlap:
            return 0.0
        
        # Check for legal terms and patterns
        legal_indicators = [
            r'(?:shall|will|must|may|agree)',
            r'(?:party|parties|contract|agreement)',
            r'(?:provided|whereas|therefore)',
            r'(?:liability|indemnify|warranty)'
        ]
        
        legal_term_count = sum(1 for pattern in legal_indicators 
                              if re.search(pattern, overlap, re.IGNORECASE))
        
        # Enhanced scoring with definitional relationships
        definition_score = self._check_definitional_context(overlap)
        obligation_score = self._check_obligation_completeness(overlap)
        
        # Score based on legal term density
        words = len(overlap.split())
        legal_density = legal_term_count / max(words, 1) * 100
        
        base_score = 1.0 if legal_density > 5 else (0.8 if legal_density > 2 else 0.6)
        
        # Combine with enhanced scores
        return min(1.0, base_score * 0.6 + definition_score * 0.2 + obligation_score * 0.2)
    
    def _check_definitional_context(self, overlap: str) -> float:
        """Check if overlap preserves definitional relationships."""
        # Look for definition patterns
        definition_patterns = [
            r'"[^"]+"\s+means',
            r'shall\s+mean',
            r'defined\s+as',
            r'refers\s+to'
        ]
        
        has_definition = any(re.search(pattern, overlap, re.IGNORECASE) 
                           for pattern in definition_patterns)
        
        return 1.0 if has_definition else 0.5
    
    def _check_obligation_completeness(self, overlap: str) -> float:
        """Check if legal obligations are complete in overlap."""
        # Check for incomplete obligations
        incomplete_patterns = [
            r'shall\s*$',
            r'will\s*$', 
            r'must\s*$',
            r'agrees?\s+to\s*$'
        ]
        
        has_incomplete = any(re.search(pattern, overlap, re.IGNORECASE) 
                           for pattern in incomplete_patterns)
        
        return 0.3 if has_incomplete else 1.0  # Penalize incomplete obligations


class OverlapAnalyzer:
    """Main analyzer that selects and applies overlap strategies."""
    
    def __init__(self):
        self.semantic_strategy = SemanticOverlapStrategy()
        self.clause_strategy = ClauseBoundaryOverlapStrategy()
        self.scorer = ContextPreservationScorer()
    
    def analyze_and_apply_overlap(self, chunks: List[Dict[str, Any]], 
                                  context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze and apply optimal overlap to chunks."""
        if len(chunks) <= 1:
            return chunks
        
        # Determine strategy based on context
        is_legal = context.get('is_legal_document', False)
        strategy = self.clause_strategy if is_legal else self.semantic_strategy
        
        # Apply overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Calculate overlap
            overlap_content, overlap_quality = strategy.calculate_overlap(
                current_chunk['content'],
                next_chunk['content'],
                context
            )
            
            # Score overlap quality
            quality_scores = self.scorer.score_overlap_quality(
                current_chunk['content'],
                overlap_content,
                next_chunk['content']
            )
            
            # Apply overlap to next chunk
            if overlap_content and quality_scores['overall'] > 0.6:
                next_chunk['content'] = overlap_content + "\n\n" + next_chunk['content']
                next_chunk['has_overlap'] = True
                next_chunk['overlap_size'] = len(overlap_content)
                next_chunk['overlap_quality'] = quality_scores['overall']
                next_chunk['overlap_scores'] = quality_scores
            
        return chunks