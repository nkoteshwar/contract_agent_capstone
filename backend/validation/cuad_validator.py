from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

@dataclass
class ValidationResult:
    """Validation result for CUAD analysis"""
    is_valid: bool
    confidence_score: float
    validation_errors: List[str]
    warnings: List[str]
    corrected_data: Optional[Dict[str, Any]] = None

class CUADValidator:
    """Validates CUAD analysis results for accuracy and consistency"""
    
    def validate_analysis_result(self, analysis_result: Dict[str, Any]) -> ValidationResult:
        """Validate complete CUAD analysis result"""
        errors = []
        warnings = []
        
        # Validate clauses
        clause_errors, clause_warnings = self._validate_clauses(analysis_result.get("clauses", []))
        errors.extend(clause_errors)
        warnings.extend(clause_warnings)
        
        # Validate deviations
        dev_errors, dev_warnings = self._validate_deviations(analysis_result.get("cuad_deviations", []))
        errors.extend(dev_errors)
        warnings.extend(dev_warnings)
        
        # Validate risk consistency
        risk_errors, risk_warnings = self._validate_risk_consistency(
            analysis_result.get("risk_assessment", {}),
            analysis_result.get("policy_violations", []),
            analysis_result.get("cuad_deviations", [])
        )
        errors.extend(risk_errors)
        warnings.extend(risk_warnings)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(errors, warnings, analysis_result)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            confidence_score=confidence_score,
            validation_errors=errors,
            warnings=warnings
        )
    
    def _validate_clauses(self, clauses: List[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        """Validate extracted clauses"""
        errors = []
        warnings = []
        
        for i, clause in enumerate(clauses):
            if not clause.get("clause_type"):
                errors.append(f"Clause {i}: Missing clause_type")
            
            if not clause.get("content"):
                errors.append(f"Clause {i}: Missing content")
            
            confidence = clause.get("confidence_score", 0)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                errors.append(f"Clause {i}: Invalid confidence_score: {confidence}")
            elif confidence < 0.5:
                warnings.append(f"Clause {i}: Low confidence score: {confidence}")
            
            risk_level = clause.get("risk_level", "")
            if risk_level not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                errors.append(f"Clause {i}: Invalid risk_level: {risk_level}")
        
        return errors, warnings
    
    def _validate_deviations(self, deviations: List[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        """Validate detected deviations"""
        errors = []
        warnings = []
        
        for i, deviation in enumerate(deviations):
            required_fields = ["clause_type", "deviation_type", "severity", "issue"]
            for field in required_fields:
                if not deviation.get(field):
                    errors.append(f"Deviation {i}: Missing {field}")
            
            severity = deviation.get("severity", "")
            if severity not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                errors.append(f"Deviation {i}: Invalid severity: {severity}")
        
        return errors, warnings
    
    def _validate_risk_consistency(self, risk_assessment: Dict[str, Any], 
                                 violations: List[Dict[str, Any]], 
                                 deviations: List[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        """Validate risk assessment consistency"""
        errors = []
        warnings = []
        
        risk_score = risk_assessment.get("overall_risk_score", 0)
        risk_level = risk_assessment.get("risk_level", "")
        
        if not isinstance(risk_score, (int, float)) or risk_score < 0 or risk_score > 100:
            errors.append(f"Invalid risk_score: {risk_score}")
        
        if risk_level not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            errors.append(f"Invalid risk_level: {risk_level}")
        
        # Consistency checks
        critical_issues = len([v for v in violations if v.get("severity") == "CRITICAL"]) + \
                         len([d for d in deviations if d.get("severity") == "CRITICAL"])
        
        if critical_issues > 0 and risk_score < 70:
            warnings.append(f"Risk score {risk_score} seems low for {critical_issues} critical issues")
        
        if critical_issues == 0 and risk_score > 80:
            warnings.append(f"Risk score {risk_score} seems high with no critical issues")
        
        return errors, warnings
    
    def _calculate_confidence_score(self, errors: List[str], warnings: List[str], 
                                  analysis_result: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        base_confidence = 1.0
        
        base_confidence -= len(errors) * 0.2
        base_confidence -= len(warnings) * 0.05
        
        clauses = analysis_result.get("clauses", [])
        if clauses:
            avg_clause_confidence = sum(c.get("confidence_score", 0) for c in clauses) / len(clauses)
            base_confidence = (base_confidence + avg_clause_confidence) / 2
        
        return max(0.0, min(1.0, base_confidence))

def validate_cuad_analysis(analysis_result: Dict[str, Any]) -> ValidationResult:
    """Validate CUAD analysis result"""
    validator = CUADValidator()
    return validator.validate_analysis_result(analysis_result)