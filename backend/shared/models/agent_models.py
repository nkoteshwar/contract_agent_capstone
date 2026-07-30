"""
Agent models following SOLID principles and existing codebase patterns.
Reuses patterns from backend.domain.entities and intelligence_state.py.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

from .base_models import BaseEntity, BaseValueObject, TimestampedEntity


class AgentStatus(str, Enum):
    """Agent execution status - follows existing enum patterns"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AgentCapability(BaseValueObject):
    """Agent capability definition - immutable value object (SOLID: SRP)"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    dependencies: List[str] = Field(default_factory=list)


class AgentContext(BaseEntity):
    """
    Agent execution context - follows existing intelligence_state pattern.
    Single Responsibility: Holds agent input data and context.
    """
    input_data: Dict[str, Any] = Field(default_factory=dict)
    workflow_context: Optional[Dict[str, Any]] = None
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Reuse existing intelligence patterns
    contract_text: Optional[str] = None
    extracted_clauses: List[Dict[str, Any]] = Field(default_factory=list)
    policy_violations: List[Dict[str, Any]] = Field(default_factory=list)
    
    def add_clause(self, clause: Dict[str, Any]) -> None:
        """Add clause following existing clause structure"""
        self.extracted_clauses.append(clause)
    
    def add_violation(self, violation: Dict[str, Any]) -> None:
        """Add policy violation following existing violation structure"""
        self.policy_violations.append(violation)


class AgentResult(BaseEntity):
    """
    Agent execution result - follows existing processing result patterns.
    Single Responsibility: Holds agent output and execution metadata.
    """
    status: AgentStatus
    data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    confidence_score: Optional[float] = None
    
    # Reuse existing intelligence result patterns
    processing_complete: bool = False
    requires_human_review: bool = False
    
    @classmethod
    def success(cls, data: Dict[str, Any], execution_time: float = None) -> "AgentResult":
        """Factory method for successful results (DRY)"""
        return cls(
            status=AgentStatus.SUCCESS,
            data=data,
            execution_time=execution_time,
            processing_complete=True
        )
    
    @classmethod
    def error(cls, error_message: str, data: Dict[str, Any] = None) -> "AgentResult":
        """Factory method for error results (DRY)"""
        return cls(
            status=AgentStatus.ERROR,
            error_message=error_message,
            data=data or {},
            processing_complete=False
        )


class WorkflowContext(TimestampedEntity):
    """
    Multi-agent workflow context - extends existing workflow patterns.
    Single Responsibility: Manages workflow state and coordination.
    """
    workflow_id: str
    workflow_type: str = "intelligence_analysis"
    current_step: str
    steps_completed: List[str] = Field(default_factory=list)
    shared_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Reuse existing intelligence workflow patterns
    contract_text: Optional[str] = None
    final_result: Optional[Dict[str, Any]] = None
    
    def complete_step(self, step_name: str, result_data: Dict[str, Any] = None) -> None:
        """Mark step as completed and store result data"""
        if step_name not in self.steps_completed:
            self.steps_completed.append(step_name)
        
        if result_data:
            self.shared_data[f"{step_name}_result"] = result_data
        
        self.update_timestamp()
    
    def is_step_completed(self, step_name: str) -> bool:
        """Check if step is completed"""
        return step_name in self.steps_completed
    
    def get_step_result(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Get result data from completed step"""
        return self.shared_data.get(f"{step_name}_result")


class AgentExecution(TimestampedEntity):
    """
    Individual agent execution tracking - follows existing workflow_tracker patterns.
    Single Responsibility: Track single agent execution lifecycle.
    """
    execution_id: str
    agent_name: str
    agent_description: str
    input_summary: str
    
    status: AgentStatus = AgentStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    
    result_summary: Optional[str] = None
    error_details: Optional[str] = None
    
    def start_execution(self) -> None:
        """Start agent execution"""
        self.status = AgentStatus.RUNNING
        self.start_time = datetime.now()
        self.update_timestamp()
    
    def complete_execution(self, result_summary: str) -> None:
        """Complete successful execution"""
        self.status = AgentStatus.SUCCESS
        self.end_time = datetime.now()
        self.result_summary = result_summary
        
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
        
        self.update_timestamp()
    
    def fail_execution(self, error_details: str) -> None:
        """Mark execution as failed"""
        self.status = AgentStatus.ERROR
        self.end_time = datetime.now()
        self.error_details = error_details
        
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
        
        self.update_timestamp()


# Type aliases for backward compatibility with existing code
AgentContextType = AgentContext
AgentResultType = AgentResult
WorkflowContextType = WorkflowContext