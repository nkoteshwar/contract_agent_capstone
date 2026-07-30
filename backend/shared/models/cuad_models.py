"""
CUAD mitigation models extending base agent models.
Demonstrates how to add new features while following existing patterns.
"""

from pydantic import Field
from typing import Dict, Any, List, Optional
from enum import Enum

from .agent_models import AgentContext, AgentResult
from .base_models import BaseValueObject


class DeviationType(str, Enum):
    """Types of deviations from standard patterns"""
    MERGED_CLAUSE = "merged_clause"
    CUSTOM_CLAUSE = "custom_clause" 
    MISSING_CLAUSE = "missing_clause"
    JURISDICTIONAL_VARIATION = "jurisdictional_variation"


class CUADDeviation(BaseValueObject):
    """CUAD deviation detection result - immutable value object"""
    deviation_type: DeviationType
    description: str
    location: str
    risk_level: str
    mitigation_strategy: str
    confidence_score: float = 0.0


class JurisdictionInfo(BaseValueObject):
    """Jurisdiction-specific information"""
    country: str
    state_province: Optional[str] = None
    applicable_laws: List[str] = Field(default_factory=list)
    compliance_requirements: Dict[str, Any] = Field(default_factory=dict)


class PrecedentMatch(BaseValueObject):
    """Precedent contract match"""
    contract_id: str
    similarity_score: float
    clause_text: str
    approval_status: str
    business_context: str


class EnhancedAgentContext(AgentContext):
    """
    Extended agent context for CUAD mitigation features.
    Follows Open/Closed Principle - extends without modifying base.
    """
    
    # CUAD mitigation fields
    cuad_deviations: List[CUADDeviation] = Field(default_factory=list)
    jurisdiction_info: Optional[JurisdictionInfo] = None
    precedent_matches: List[PrecedentMatch] = Field(default_factory=list)
    
    # Company-specific policies
    company_policies: Dict[str, Any] = Field(default_factory=dict)
    industry_rules: Dict[str, Any] = Field(default_factory=dict)
    
    def add_deviation(self, deviation: CUADDeviation) -> None:
        """Add CUAD deviation following existing pattern"""
        self.cuad_deviations.append(deviation)
    
    def add_precedent_match(self, match: PrecedentMatch) -> None:
        """Add precedent match"""
        self.precedent_matches.append(match)
    
    def set_jurisdiction(self, jurisdiction: JurisdictionInfo) -> None:
        """Set jurisdiction information"""
        self.jurisdiction_info = jurisdiction


class EnhancedAgentResult(AgentResult):
    """
    Extended agent result with CUAD mitigation data.
    Follows Open/Closed Principle - extends without modifying base.
    """
    
    # CUAD mitigation results
    deviations_detected: int = 0
    precedents_found: int = 0
    jurisdiction_adapted: bool = False
    
    # Explanation and reasoning
    deviation_explanations: List[str] = Field(default_factory=list)
    reasoning_trace: List[str] = Field(default_factory=list)
    
    def add_explanation(self, explanation: str) -> None:
        """Add deviation explanation"""
        self.deviation_explanations.append(explanation)
    
    def add_reasoning_step(self, step: str) -> None:
        """Add reasoning step for explainability"""
        self.reasoning_trace.append(step)