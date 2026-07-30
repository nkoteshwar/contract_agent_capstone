"""
Pattern Selector - Strategy Pattern for choosing appropriate analysis pattern.
Selects ReACT, Chain-of-Thought, or standard workflow based on contract complexity.
"""

from enum import Enum
from typing import Dict, Any
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)


class AnalysisComplexity(Enum):
    """Contract analysis complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class PatternSelector:
    """
    Select appropriate pattern based on contract complexity (Strategy Pattern).
    SOLID: Single Responsibility - only selects patterns, doesn't execute them.
    """
    
    @staticmethod
    def select_pattern(context: Dict[str, Any]) -> str:
        """
        Select pattern based on complexity assessment.
        
        Returns:
            'react' for complex analysis
            'chain_of_thought' for moderate analysis
            'standard' for simple analysis
        """
        complexity = PatternSelector._assess_complexity(context)
        
        if complexity == AnalysisComplexity.COMPLEX:
            logger.info("Selected ReACT pattern for complex analysis")
            return "react"
        elif complexity == AnalysisComplexity.MODERATE:
            logger.info("Selected Chain-of-Thought pattern for moderate analysis")
            return "chain_of_thought"
        else:
            logger.info("Using standard workflow for simple analysis")
            return "standard"
    
    @staticmethod
    def _assess_complexity(context: Dict[str, Any]) -> AnalysisComplexity:
        """
        Assess contract complexity based on size and clause count.
        
        Complexity factors:
        - Contract text length
        - Number of clauses
        - Number of policy violations
        """
        contract_text = context.get('contract_text', '')
        clauses = context.get('clauses', [])
        violations = context.get('violations', [])
        
        text_length = len(contract_text)
        clause_count = len(clauses)
        violation_count = len(violations)
        
        # Complex: Large contracts or many issues
        if text_length > 50000 or clause_count > 20 or violation_count > 10:
            logger.info(f"Complex analysis: {text_length} chars, {clause_count} clauses, {violation_count} violations")
            return AnalysisComplexity.COMPLEX
        
        # Moderate: Medium-sized contracts
        elif text_length > 10000 or clause_count > 10 or violation_count > 5:
            logger.info(f"Moderate analysis: {text_length} chars, {clause_count} clauses, {violation_count} violations")
            return AnalysisComplexity.MODERATE
        
        # Simple: Small contracts
        logger.info(f"Simple analysis: {text_length} chars, {clause_count} clauses, {violation_count} violations")
        return AnalysisComplexity.SIMPLE
    
    @staticmethod
    def should_use_patterns(context: Dict[str, Any]) -> bool:
        """Check if pattern-based analysis should be used"""
        # Can be disabled via context flag
        if context.get('disable_patterns', False):
            return False
        
        # Only use patterns for non-trivial contracts
        complexity = PatternSelector._assess_complexity(context)
        return complexity != AnalysisComplexity.SIMPLE
