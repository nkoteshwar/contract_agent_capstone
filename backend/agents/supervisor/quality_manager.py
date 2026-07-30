from .interfaces import IQualityManager, AgentResult, QualityReport, ValidationResult
from .validation_strategies import ValidationStrategyFactory

class QualityManager(IQualityManager):
    """Quality management using composite pattern"""
    
    def __init__(self):
        self.min_pass_score = 0.7
    
    def validate_agent_output(self, agent_type: str, result: AgentResult) -> QualityReport:
        """Validate agent output using appropriate strategy"""
        
        # Get validation strategy
        strategy = ValidationStrategyFactory.get_strategy(agent_type)
        validation = strategy.validate(result)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(result, validation)
        
        # Determine grade
        grade = self._calculate_grade(quality_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(validation, quality_score)
        
        return QualityReport(
            validation=validation,
            score=quality_score,
            grade=grade,
            recommendations=recommendations
        )
    
    def _calculate_quality_score(self, result: AgentResult, validation: ValidationResult) -> float:
        """Calculate overall quality score"""
        # Combine validation score with confidence
        validation_weight = 0.7
        confidence_weight = 0.3
        
        return (validation.score * validation_weight + 
                result.confidence * confidence_weight)
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to letter grade"""
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
    
    def _generate_recommendations(self, validation: ValidationResult, score: float) -> list:
        """Generate improvement recommendations"""
        recommendations = []
        
        if not validation.passed:
            recommendations.append("Address validation failures before proceeding")
        
        if score < self.min_pass_score:
            recommendations.append("Improve output quality - score below threshold")
        
        if validation.score < 0.6:
            recommendations.append("Review validation logic and data completeness")
        
        if not recommendations:
            recommendations.append("Quality metrics are acceptable")
        
        return recommendations