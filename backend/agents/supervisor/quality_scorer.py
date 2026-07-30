from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

@dataclass
class QualityMetrics:
    completeness: float
    accuracy: float
    consistency: float
    confidence: float
    overall_score: float

@dataclass
class QualityReport:
    agent_id: str
    task_type: str
    metrics: QualityMetrics
    grade: str
    recommendations: List[str]

class QualityScorer:
    def __init__(self):
        self.weights = {
            "completeness": 0.3,
            "accuracy": 0.3,
            "consistency": 0.2,
            "confidence": 0.2
        }
    
    def score_agent_output(self, agent_id: str, task_type: str, 
                          output: Dict[str, Any], 
                          expected_schema: Dict[str, Any] = None) -> QualityReport:
        """Score agent output quality"""
        
        # Calculate individual metrics
        completeness = self._score_completeness(output, expected_schema)
        accuracy = self._score_accuracy(output, task_type)
        consistency = self._score_consistency(output, task_type)
        confidence = self._score_confidence(output)
        
        # Calculate weighted overall score
        overall_score = (
            completeness * self.weights["completeness"] +
            accuracy * self.weights["accuracy"] +
            consistency * self.weights["consistency"] +
            confidence * self.weights["confidence"]
        )
        
        metrics = QualityMetrics(
            completeness=completeness,
            accuracy=accuracy,
            consistency=consistency,
            confidence=confidence,
            overall_score=overall_score
        )
        
        grade = self._calculate_grade(overall_score)
        recommendations = self._generate_recommendations(metrics, task_type)
        
        return QualityReport(
            agent_id=agent_id,
            task_type=task_type,
            metrics=metrics,
            grade=grade,
            recommendations=recommendations
        )
    
    def _score_completeness(self, output: Dict[str, Any], expected_schema: Dict[str, Any] = None) -> float:
        """Score output completeness"""
        if not expected_schema:
            # Basic completeness check
            required_fields = ["status", "result"]
            present_fields = sum(1 for field in required_fields if field in output)
            return present_fields / len(required_fields)
        
        # Schema-based completeness
        required_fields = expected_schema.get("required", [])
        if not required_fields:
            return 1.0
        
        present_fields = sum(1 for field in required_fields if field in output)
        return present_fields / len(required_fields)
    
    def _score_accuracy(self, output: Dict[str, Any], task_type: str) -> float:
        """Score output accuracy based on task type"""
        if task_type == "extract_text":
            # For text extraction, check if text is present and reasonable length
            text = output.get("text_content", "")
            if not text:
                return 0.0
            return min(len(text) / 500, 1.0)  # Expect at least 500 chars
        
        elif task_type == "extract_clauses":
            # For clause extraction, check clause structure
            clauses = output.get("clauses", [])
            if not clauses:
                return 0.0
            
            valid_clauses = sum(1 for clause in clauses 
                              if isinstance(clause, dict) and 
                              "clause_type" in clause and 
                              "content" in clause)
            return valid_clauses / len(clauses)
        
        elif task_type == "assess_risk":
            # For risk assessment, check score validity
            risk_score = output.get("risk_score")
            if risk_score is None:
                return 0.0
            
            try:
                score = float(risk_score)
                return 1.0 if 0 <= score <= 100 else 0.5
            except (ValueError, TypeError):
                return 0.0
        
        # Default accuracy check
        return 0.8 if output.get("status") == "success" else 0.3
    
    def _score_consistency(self, output: Dict[str, Any], task_type: str) -> float:
        """Score internal consistency of output"""
        if task_type == "assess_risk":
            # Check risk score and level consistency
            risk_score = output.get("risk_score", 0)
            risk_level = output.get("risk_level", "")
            
            try:
                score = float(risk_score)
                expected_level = self._get_expected_risk_level(score)
                return 1.0 if risk_level == expected_level else 0.5
            except (ValueError, TypeError):
                return 0.0
        
        elif task_type == "extract_clauses":
            # Check clause confidence consistency
            clauses = output.get("clauses", [])
            if not clauses:
                return 1.0
            
            confidence_scores = [c.get("confidence_score", 0) for c in clauses if isinstance(c, dict)]
            if not confidence_scores:
                return 0.5
            
            # Check if confidence scores are reasonable
            valid_scores = sum(1 for score in confidence_scores if 0 <= score <= 1)
            return valid_scores / len(confidence_scores)
        
        return 0.8  # Default consistency score
    
    def _score_confidence(self, output: Dict[str, Any]) -> float:
        """Score confidence indicators in output"""
        # Look for explicit confidence scores
        if "confidence_score" in output:
            try:
                return float(output["confidence_score"])
            except (ValueError, TypeError):
                pass
        
        # Look for confidence in nested structures
        if "clauses" in output:
            clauses = output["clauses"]
            if clauses and isinstance(clauses, list):
                confidence_scores = [c.get("confidence_score", 0) for c in clauses if isinstance(c, dict)]
                if confidence_scores:
                    return sum(confidence_scores) / len(confidence_scores)
        
        # Default confidence based on output quality
        return 0.7 if output.get("status") == "success" else 0.3
    
    def _get_expected_risk_level(self, score: float) -> str:
        """Get expected risk level for score"""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self, metrics: QualityMetrics, task_type: str) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if metrics.completeness < 0.8:
            recommendations.append("Improve output completeness - ensure all required fields are present")
        
        if metrics.accuracy < 0.7:
            recommendations.append(f"Enhance accuracy for {task_type} - review extraction/analysis logic")
        
        if metrics.consistency < 0.7:
            recommendations.append("Improve internal consistency - validate cross-field relationships")
        
        if metrics.confidence < 0.6:
            recommendations.append("Increase confidence scoring - provide better uncertainty estimates")
        
        if not recommendations:
            recommendations.append("Quality metrics are good - maintain current performance")
        
        return recommendations