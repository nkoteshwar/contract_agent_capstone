"""
Shared models module following SOLID principles and DRY patterns.
Reuses existing domain patterns from backend.domain.entities.
"""

from .agent_models import (
    AgentStatus,
    AgentContext, 
    AgentResult,
    WorkflowContext,
    AgentExecution,
    AgentCapability
)

from .base_models import (
    BaseEntity,
    BaseValueObject,
    TimestampedEntity
)

from .cuad_models import (
    DeviationType,
    CUADDeviation,
    JurisdictionInfo,
    PrecedentMatch,
    EnhancedAgentContext,
    EnhancedAgentResult
)

__all__ = [
    # Agent models
    "AgentStatus",
    "AgentContext",
    "AgentResult", 
    "WorkflowContext",
    "AgentExecution",
    "AgentCapability",
    
    # Base models
    "BaseEntity",
    "BaseValueObject", 
    "TimestampedEntity",
    
    # CUAD mitigation models
    "DeviationType",
    "CUADDeviation",
    "JurisdictionInfo", 
    "PrecedentMatch",
    "EnhancedAgentContext",
    "EnhancedAgentResult"
]