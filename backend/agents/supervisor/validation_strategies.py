from .interfaces import IValidationStrategy, AgentResult, ValidationResult

class ValidationStrategyFactory:
    """Factory for validation strategies - OCP compliance"""
    
    _strategies = {}
    
    @classmethod
    def register_strategy(cls, agent_type: str, strategy: IValidationStrategy):
        cls._strategies[agent_type] = strategy
    
    @classmethod
    def get_strategy(cls, agent_type: str) -> IValidationStrategy:
        return cls._strategies.get(agent_type, DefaultValidationStrategy())

class DefaultValidationStrategy(IValidationStrategy):
    def validate(self, result: AgentResult) -> ValidationResult:
        passed = result.status == "success"
        score = 0.8 if passed else 0.2
        
        return ValidationResult(
            passed=passed,
            score=score,
            message=f"Default validation: {result.status}",
            details={"agent_id": result.agent_id}
        )

class PDFValidationStrategy(IValidationStrategy):
    def validate(self, result: AgentResult) -> ValidationResult:
        text_content = result.data.get("text_content", "")
        contract_id = result.data.get("contract_id")
        
        # Validation checks
        has_text = len(text_content) > 100
        has_contract_id = contract_id is not None
        
        score = 0.0
        if has_text:
            score += 0.6
        if has_contract_id:
            score += 0.4
        
        passed = score >= 0.7
        
        return ValidationResult(
            passed=passed,
            score=score,
            message=f"PDF validation: text={len(text_content)} chars, contract_id={bool(contract_id)}",
            details={
                "text_length": len(text_content),
                "has_contract_id": has_contract_id
            }
        )

class ClauseValidationStrategy(IValidationStrategy):
    def validate(self, result: AgentResult) -> ValidationResult:
        clauses = result.data.get("clauses", [])
        
        if not clauses:
            return ValidationResult(
                passed=False,
                score=0.0,
                message="No clauses extracted",
                details={"clause_count": 0}
            )
        
        # Check clause quality
        valid_clauses = sum(1 for clause in clauses 
                          if isinstance(clause, dict) and 
                          "clause_type" in clause and 
                          "content" in clause)
        
        avg_confidence = sum(clause.get("confidence_score", 0) for clause in clauses) / len(clauses)
        
        score = (valid_clauses / len(clauses)) * 0.6 + avg_confidence * 0.4
        passed = score >= 0.6
        
        return ValidationResult(
            passed=passed,
            score=score,
            message=f"Clause validation: {valid_clauses}/{len(clauses)} valid, avg_confidence={avg_confidence:.2f}",
            details={
                "clause_count": len(clauses),
                "valid_clauses": valid_clauses,
                "avg_confidence": avg_confidence
            }
        )

class RiskValidationStrategy(IValidationStrategy):
    def validate(self, result: AgentResult) -> ValidationResult:
        risk_score = result.data.get("risk_score")
        risk_level = result.data.get("risk_level")
        
        if risk_score is None:
            return ValidationResult(
                passed=False,
                score=0.0,
                message="No risk score provided",
                details={}
            )
        
        # Validate score range
        score_valid = 0 <= risk_score <= 100
        
        # Validate level consistency
        level_consistent = self._validate_level_consistency(risk_score, risk_level)
        
        score = 0.0
        if score_valid:
            score += 0.5
        if level_consistent:
            score += 0.5
        
        passed = score >= 0.8
        
        return ValidationResult(
            passed=passed,
            score=score,
            message=f"Risk validation: score={risk_score}, level={risk_level}, consistent={level_consistent}",
            details={
                "risk_score": risk_score,
                "risk_level": risk_level,
                "score_valid": score_valid,
                "level_consistent": level_consistent
            }
        )
    
    def _validate_level_consistency(self, score: float, level: str) -> bool:
        if score >= 80 and level == "CRITICAL":
            return True
        elif 60 <= score < 80 and level == "HIGH":
            return True
        elif 40 <= score < 60 and level == "MEDIUM":
            return True
        elif score < 40 and level == "LOW":
            return True
        return False

# Register strategies
ValidationStrategyFactory.register_strategy("pdf_processing", PDFValidationStrategy())
ValidationStrategyFactory.register_strategy("clause_extraction", ClauseValidationStrategy())
ValidationStrategyFactory.register_strategy("risk_assessment", RiskValidationStrategy())