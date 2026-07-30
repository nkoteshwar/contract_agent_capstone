from typing import List
from .interfaces import IConsensusStrategy, AgentResult
import statistics

class WeightedConsensusStrategy(IConsensusStrategy):
    def reach_consensus(self, opinions: List[AgentResult]) -> AgentResult:
        """Weighted consensus based on confidence scores"""
        if not opinions:
            return AgentResult("error", {"error": "No opinions provided"}, 0.0)
        
        if len(opinions) == 1:
            return opinions[0]
        
        # For numeric values (like risk scores)
        numeric_values = []
        total_weight = 0
        
        for opinion in opinions:
            if "risk_score" in opinion.data:
                value = opinion.data["risk_score"]
                weight = opinion.confidence
                numeric_values.append((value, weight))
                total_weight += weight
        
        if numeric_values and total_weight > 0:
            weighted_sum = sum(value * weight for value, weight in numeric_values)
            consensus_value = weighted_sum / total_weight
            avg_confidence = total_weight / len(numeric_values)
            
            return AgentResult(
                status="consensus",
                data={"risk_score": consensus_value, "consensus_method": "weighted_average"},
                confidence=avg_confidence,
                agent_id="consensus"
            )
        
        # Fallback to majority vote for non-numeric
        return self._majority_vote(opinions)
    
    def _majority_vote(self, opinions: List[AgentResult]) -> AgentResult:
        """Simple majority vote fallback"""
        status_counts = {}
        for opinion in opinions:
            status = opinion.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        majority_status = max(status_counts.items(), key=lambda x: x[1])[0]
        avg_confidence = sum(op.confidence for op in opinions) / len(opinions)
        
        return AgentResult(
            status=majority_status,
            data={"consensus_method": "majority_vote"},
            confidence=avg_confidence,
            agent_id="consensus"
        )