from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import statistics

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class ConsensusStrategy(Enum):
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    CONFIDENCE_THRESHOLD = "confidence_threshold"

@dataclass
class AgentOpinion:
    agent_id: str
    value: Any
    confidence: float
    reasoning: str = ""

@dataclass
class ConsensusResult:
    final_value: Any
    confidence: float
    agreement_level: float
    participating_agents: List[str]
    strategy_used: ConsensusStrategy

class ConsensusManager:
    def __init__(self):
        self.min_consensus_agents = 2
        self.confidence_threshold = 0.7
    
    def reach_consensus(self, 
                       opinions: List[AgentOpinion], 
                       strategy: ConsensusStrategy = ConsensusStrategy.WEIGHTED_AVERAGE) -> ConsensusResult:
        """Reach consensus among multiple agent opinions"""
        
        if len(opinions) < self.min_consensus_agents:
            logger.warning(f"Insufficient agents for consensus: {len(opinions)}")
            return self._single_agent_result(opinions[0] if opinions else None)
        
        if strategy == ConsensusStrategy.MAJORITY_VOTE:
            return self._majority_vote_consensus(opinions)
        elif strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
            return self._weighted_average_consensus(opinions)
        elif strategy == ConsensusStrategy.CONFIDENCE_THRESHOLD:
            return self._confidence_threshold_consensus(opinions)
        
        return self._weighted_average_consensus(opinions)  # Default
    
    def validate_risk_consensus(self, risk_opinions: List[AgentOpinion]) -> ConsensusResult:
        """Specialized consensus for risk assessment"""
        # Use weighted average for risk scores
        if all(isinstance(op.value, (int, float)) for op in risk_opinions):
            return self._weighted_average_consensus(risk_opinions)
        
        # Use majority vote for risk levels
        return self._majority_vote_consensus(risk_opinions)
    
    def validate_clause_consensus(self, clause_opinions: List[AgentOpinion]) -> ConsensusResult:
        """Specialized consensus for clause extraction"""
        # For clause extraction, use confidence threshold
        return self._confidence_threshold_consensus(clause_opinions)
    
    def _majority_vote_consensus(self, opinions: List[AgentOpinion]) -> ConsensusResult:
        """Simple majority vote consensus"""
        value_counts = {}
        total_confidence = 0
        
        for opinion in opinions:
            value = str(opinion.value)  # Convert to string for comparison
            if value not in value_counts:
                value_counts[value] = {"count": 0, "confidence": 0, "agents": []}
            
            value_counts[value]["count"] += 1
            value_counts[value]["confidence"] += opinion.confidence
            value_counts[value]["agents"].append(opinion.agent_id)
            total_confidence += opinion.confidence
        
        # Find majority
        majority_value = max(value_counts.items(), key=lambda x: x[1]["count"])
        majority_count = majority_value[1]["count"]
        
        agreement_level = majority_count / len(opinions)
        avg_confidence = total_confidence / len(opinions)
        
        return ConsensusResult(
            final_value=majority_value[0],
            confidence=avg_confidence,
            agreement_level=agreement_level,
            participating_agents=[op.agent_id for op in opinions],
            strategy_used=ConsensusStrategy.MAJORITY_VOTE
        )
    
    def _weighted_average_consensus(self, opinions: List[AgentOpinion]) -> ConsensusResult:
        """Weighted average consensus for numeric values"""
        try:
            # Extract numeric values
            numeric_opinions = [(float(op.value), op.confidence, op.agent_id) for op in opinions 
                              if isinstance(op.value, (int, float)) or str(op.value).replace('.', '').isdigit()]
            
            if not numeric_opinions:
                return self._majority_vote_consensus(opinions)
            
            # Calculate weighted average
            total_weight = sum(confidence for _, confidence, _ in numeric_opinions)
            weighted_sum = sum(value * confidence for value, confidence, _ in numeric_opinions)
            
            final_value = weighted_sum / total_weight if total_weight > 0 else 0
            
            # Calculate agreement level (how close values are)
            values = [value for value, _, _ in numeric_opinions]
            if len(values) > 1:
                std_dev = statistics.stdev(values)
                max_value = max(values)
                agreement_level = 1 - (std_dev / max_value) if max_value > 0 else 1
            else:
                agreement_level = 1.0
            
            avg_confidence = sum(op.confidence for op in opinions) / len(opinions)
            
            return ConsensusResult(
                final_value=final_value,
                confidence=avg_confidence,
                agreement_level=max(0, min(1, agreement_level)),
                participating_agents=[op.agent_id for op in opinions],
                strategy_used=ConsensusStrategy.WEIGHTED_AVERAGE
            )
            
        except Exception as e:
            logger.error(f"Weighted average consensus failed: {e}")
            return self._majority_vote_consensus(opinions)
    
    def _confidence_threshold_consensus(self, opinions: List[AgentOpinion]) -> ConsensusResult:
        """Consensus based on confidence threshold"""
        # Filter high-confidence opinions
        high_confidence_opinions = [op for op in opinions if op.confidence >= self.confidence_threshold]
        
        if not high_confidence_opinions:
            # If no high-confidence opinions, use all with warning
            logger.warning("No high-confidence opinions available")
            return self._weighted_average_consensus(opinions)
        
        # Use weighted average of high-confidence opinions
        return self._weighted_average_consensus(high_confidence_opinions)
    
    def _single_agent_result(self, opinion: Optional[AgentOpinion]) -> ConsensusResult:
        """Handle single agent case"""
        if not opinion:
            return ConsensusResult(
                final_value=None,
                confidence=0.0,
                agreement_level=0.0,
                participating_agents=[],
                strategy_used=ConsensusStrategy.MAJORITY_VOTE
            )
        
        return ConsensusResult(
            final_value=opinion.value,
            confidence=opinion.confidence,
            agreement_level=1.0,
            participating_agents=[opinion.agent_id],
            strategy_used=ConsensusStrategy.MAJORITY_VOTE
        )