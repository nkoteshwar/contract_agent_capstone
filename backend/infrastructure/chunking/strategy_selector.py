"""Strategy selection pipeline using Chain of Responsibility pattern."""

from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StrategyScore:
    """Strategy scoring result."""
    strategy_name: str
    score: float
    reasoning: str
    predicted_quality: float


class StrategySelector(ABC):
    """Base class for strategy selection components."""
    
    def __init__(self):
        self._next_selector: Optional['StrategySelector'] = None
    
    def set_next(self, selector: 'StrategySelector') -> 'StrategySelector':
        """Set the next selector in the chain."""
        self._next_selector = selector
        return selector
    
    def select(self, text: str, doc_analysis: Dict[str, Any], 
              content_metrics: Any) -> List[StrategyScore]:
        """Select strategies and pass to next selector."""
        scores = self._evaluate_strategies(text, doc_analysis, content_metrics)
        
        if self._next_selector:
            next_scores = self._next_selector.select(text, doc_analysis, content_metrics)
            # Merge scores, keeping best score for each strategy
            merged = {score.strategy_name: score for score in scores}
            for score in next_scores:
                if score.strategy_name not in merged or score.score > merged[score.strategy_name].score:
                    merged[score.strategy_name] = score
            return list(merged.values())
        
        return scores
    
    @abstractmethod
    def _evaluate_strategies(self, text: str, doc_analysis: Dict[str, Any], 
                           content_metrics: Any) -> List[StrategyScore]:
        """Evaluate strategies based on specific criteria."""
        pass


class DocumentTypeSelector(StrategySelector):
    """Selects strategies based on document type and structure."""
    
    def _evaluate_strategies(self, text: str, doc_analysis: Dict[str, Any], 
                           content_metrics: Any) -> List[StrategyScore]:
        """Evaluate based on document structure."""
        scores = []
        
        # Section strategy scoring
        section_count = doc_analysis.get('section_count', 0)
        has_structure = doc_analysis.get('has_hierarchical_structure', False)
        
        if has_structure and section_count >= 3:
            scores.append(StrategyScore(
                'section', 0.9, 
                f'Document has {section_count} sections with clear hierarchy',
                0.85
            ))
        elif section_count >= 2:
            scores.append(StrategyScore(
                'section', 0.7,
                f'Document has {section_count} sections',
                0.75
            ))
        
        # Clause strategy scoring
        is_legal = doc_analysis.get('is_legal_document', False)
        clause_density = content_metrics.clause_density if hasattr(content_metrics, 'clause_density') else 0
        
        if is_legal and clause_density > 3.0:
            scores.append(StrategyScore(
                'clause', 0.85,
                f'Legal document with high clause density ({clause_density:.1f}%)',
                0.8
            ))
        elif is_legal and clause_density > 1.0:
            scores.append(StrategyScore(
                'clause', 0.6,
                f'Legal document with moderate clause density ({clause_density:.1f}%)',
                0.7
            ))
        
        # Paragraph strategy scoring
        paragraph_count = doc_analysis.get('paragraph_count', 0)
        if paragraph_count >= 5:
            scores.append(StrategyScore(
                'paragraph', 0.75,
                f'Well-structured document with {paragraph_count} paragraphs',
                0.75
            ))
        
        return scores


class ContentDensitySelector(StrategySelector):
    """Selects strategies based on content complexity and density."""
    
    def _evaluate_strategies(self, text: str, doc_analysis: Dict[str, Any], 
                           content_metrics: Any) -> List[StrategyScore]:
        """Evaluate based on content complexity."""
        scores = []
        
        complexity = getattr(content_metrics, 'complexity_score', 0)
        legal_density = getattr(content_metrics, 'legal_term_density', 0)
        
        # Hybrid strategy for complex content
        if complexity > 0.7 or legal_density > 3.0:
            scores.append(StrategyScore(
                'hybrid', 0.8,
                f'Complex content (complexity: {complexity:.2f}, legal density: {legal_density:.1f}%)',
                0.8
            ))
        
        # Sentence strategy as reliable fallback
        scores.append(StrategyScore(
            'sentence', 0.6,
            'Reliable sentence-based chunking',
            0.7
        ))
        
        return scores


class QualityPredictor(StrategySelector):
    """Predicts chunk quality for each strategy."""
    
    def _evaluate_strategies(self, text: str, doc_analysis: Dict[str, Any], 
                           content_metrics: Any) -> List[StrategyScore]:
        """Predict quality based on document characteristics."""
        scores = []
        doc_length = len(text)
        
        # Adjust scores based on document length and complexity
        complexity = getattr(content_metrics, 'complexity_score', 0)
        
        # Section strategy quality prediction
        if doc_analysis.get('has_hierarchical_structure'):
            quality = 0.9 if doc_length > 5000 else 0.8
            scores.append(StrategyScore(
                'section', quality,
                'High quality expected for structured documents',
                quality
            ))
        
        # Clause strategy quality prediction
        if doc_analysis.get('is_legal_document'):
            quality = 0.85 if complexity < 0.8 else 0.75
            scores.append(StrategyScore(
                'clause', quality,
                'Good quality expected for legal documents',
                quality
            ))
        
        return scores


class FallbackChainBuilder:
    """Builds fallback chain: Section → Clause → Paragraph → Sentence."""
    
    def build_chain(self, strategy_scores: List[StrategyScore]) -> List[str]:
        """Build fallback chain based on scores."""
        # Sort strategies by score
        sorted_strategies = sorted(strategy_scores, key=lambda x: x.score, reverse=True)
        
        # Build fallback chain with preferred order
        preferred_order = ['section', 'clause', 'paragraph', 'hybrid', 'sentence']
        fallback_chain = []
        
        # Add strategies in order of preference and score
        for strategy_name in preferred_order:
            for score in sorted_strategies:
                if score.strategy_name == strategy_name and score.score > 0.5:
                    fallback_chain.append(strategy_name)
                    break
        
        # Ensure sentence is always last fallback
        if 'sentence' not in fallback_chain:
            fallback_chain.append('sentence')
        
        return fallback_chain


def create_strategy_selection_pipeline() -> StrategySelector:
    """Create the complete strategy selection pipeline."""
    document_selector = DocumentTypeSelector()
    content_selector = ContentDensitySelector()
    quality_predictor = QualityPredictor()
    
    # Chain the selectors
    document_selector.set_next(content_selector).set_next(quality_predictor)
    
    return document_selector


def select_best_strategy(text: str, doc_analysis: Dict[str, Any], 
                        content_metrics: Any) -> Tuple[str, List[str], Dict[str, StrategyScore]]:
    """Select best strategy with fallback chain."""
    # Run selection pipeline
    pipeline = create_strategy_selection_pipeline()
    strategy_scores = pipeline.select(text, doc_analysis, content_metrics)
    
    # Build fallback chain
    chain_builder = FallbackChainBuilder()
    fallback_chain = chain_builder.build_chain(strategy_scores)
    
    # Select best strategy
    best_strategy = fallback_chain[0] if fallback_chain else 'sentence'
    
    # Create scores dict for reference
    scores_dict = {score.strategy_name: score for score in strategy_scores}
    
    return best_strategy, fallback_chain, scores_dict