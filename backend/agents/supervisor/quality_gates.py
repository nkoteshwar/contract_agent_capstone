from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class ValidationResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"

@dataclass
class QualityCheck:
    check_name: str
    result: ValidationResult
    score: float
    message: str
    details: Dict[str, Any] = None

@dataclass
class QualityGateResult:
    gate_name: str
    overall_result: ValidationResult
    overall_score: float
    checks: List[QualityCheck]
    can_proceed: bool

class QualityValidator:
    def __init__(self):
        self.min_pass_score = 0.7
        self.min_warning_score = 0.5
    
    def validate_pdf_processing(self, result: Dict[str, Any]) -> QualityGateResult:
        """Validate PDF processing output"""
        checks = []
        
        # Check text extraction quality
        text_content = result.get("text_content", "")
        text_score = min(len(text_content) / 1000, 1.0) if text_content else 0.0
        
        checks.append(QualityCheck(
            check_name="text_extraction_completeness",
            result=ValidationResult.PASS if text_score > self.min_pass_score else ValidationResult.FAIL,
            score=text_score,
            message=f"Extracted {len(text_content)} characters"
        ))
        
        # Check metadata presence
        metadata_score = 1.0 if result.get("metadata") else 0.0
        checks.append(QualityCheck(
            check_name="metadata_extraction",
            result=ValidationResult.PASS if metadata_score > 0 else ValidationResult.WARNING,
            score=metadata_score,
            message="Metadata extraction status"
        ))
        
        return self._aggregate_results("pdf_processing_gate", checks)
    
    def validate_clause_extraction(self, result: Dict[str, Any]) -> QualityGateResult:
        """Validate clause extraction output"""
        checks = []
        
        clauses = result.get("clauses", [])
        clause_count_score = min(len(clauses) / 10, 1.0)  # Expect ~10 clauses
        
        checks.append(QualityCheck(
            check_name="clause_count",
            result=ValidationResult.PASS if clause_count_score > self.min_warning_score else ValidationResult.WARNING,
            score=clause_count_score,
            message=f"Extracted {len(clauses)} clauses"
        ))
        
        # Check confidence scores
        if clauses:
            avg_confidence = sum(c.get("confidence_score", 0) for c in clauses) / len(clauses)
            confidence_result = ValidationResult.PASS if avg_confidence > self.min_pass_score else ValidationResult.WARNING
            
            checks.append(QualityCheck(
                check_name="clause_confidence",
                result=confidence_result,
                score=avg_confidence,
                message=f"Average confidence: {avg_confidence:.2f}"
            ))
        
        return self._aggregate_results("clause_extraction_gate", checks)
    
    def validate_risk_assessment(self, result: Dict[str, Any]) -> QualityGateResult:
        """Validate risk assessment output"""
        checks = []
        
        risk_score = result.get("risk_score", 0)
        risk_level = result.get("risk_level", "")
        
        # Validate risk score range
        score_valid = 0 <= risk_score <= 100
        checks.append(QualityCheck(
            check_name="risk_score_range",
            result=ValidationResult.PASS if score_valid else ValidationResult.FAIL,
            score=1.0 if score_valid else 0.0,
            message=f"Risk score: {risk_score}"
        ))
        
        # Validate risk level consistency
        level_consistent = self._validate_risk_level_consistency(risk_score, risk_level)
        checks.append(QualityCheck(
            check_name="risk_level_consistency",
            result=ValidationResult.PASS if level_consistent else ValidationResult.WARNING,
            score=1.0 if level_consistent else 0.5,
            message=f"Risk level: {risk_level}"
        ))
        
        return self._aggregate_results("risk_assessment_gate", checks)
    
    def _validate_risk_level_consistency(self, score: float, level: str) -> bool:
        """Check if risk level matches score"""
        if score >= 80 and level == "CRITICAL":
            return True
        elif 60 <= score < 80 and level == "HIGH":
            return True
        elif 40 <= score < 60 and level == "MEDIUM":
            return True
        elif score < 40 and level == "LOW":
            return True
        return False
    
    def _aggregate_results(self, gate_name: str, checks: List[QualityCheck]) -> QualityGateResult:
        """Aggregate individual checks into gate result"""
        if not checks:
            return QualityGateResult(gate_name, ValidationResult.FAIL, 0.0, [], False)
        
        # Calculate overall score
        overall_score = sum(check.score for check in checks) / len(checks)
        
        # Determine overall result
        has_failures = any(check.result == ValidationResult.FAIL for check in checks)
        has_warnings = any(check.result == ValidationResult.WARNING for check in checks)
        
        if has_failures:
            overall_result = ValidationResult.FAIL
        elif has_warnings:
            overall_result = ValidationResult.WARNING
        else:
            overall_result = ValidationResult.PASS
        
        # Can proceed if no failures
        can_proceed = not has_failures
        
        return QualityGateResult(
            gate_name=gate_name,
            overall_result=overall_result,
            overall_score=overall_score,
            checks=checks,
            can_proceed=can_proceed
        )