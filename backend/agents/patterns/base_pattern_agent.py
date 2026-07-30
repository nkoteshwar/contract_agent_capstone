"""
Base Pattern Agent - SOLID principles foundation for all pattern agents.
Provides centralized logging, audit trails, and workflow tracking.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.infrastructure.audit_logger import AuditLogger, AuditEventType
from backend.agents.agent_workflow_tracker import workflow_tracker
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)


class BasePatternAgent(ABC):
    """
    Base class for all pattern agents (SOLID: SRP, DIP, OCP).
    Provides common infrastructure for logging, auditing, and tracking.
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.audit_logger = AuditLogger()
        self.execution = None
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Template Method Pattern - defines execution flow.
        Subclasses implement _execute_pattern for specific logic.
        """
        self.execution = workflow_tracker.start_agent(
            self.agent_name,
            self.get_agent_role(),
            self.get_input_summary(context)
        )
        
        try:
            # Audit log start
            self.audit_logger.log_event(
                AuditEventType.ANALYSIS_REQUEST,
                context.get('contract_id', 'unknown'),
                f"{self.agent_name}_start",
                metadata={"pattern": self.get_pattern_name()}
            )
            
            logger.info(f"{self.agent_name} starting execution")
            
            # Execute pattern-specific logic
            result = await self._execute_pattern(context)
            
            # Complete tracking
            workflow_tracker.complete_agent(
                self.execution,
                self.get_output_summary(result)
            )
            
            # Audit log completion
            self.audit_logger.log_event(
                AuditEventType.ANALYSIS_REQUEST,
                context.get('contract_id', 'unknown'),
                f"{self.agent_name}_complete",
                metadata={"result": result.get('success', False)}
            )
            
            logger.info(f"{self.agent_name} completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"{self.agent_name} failed: {e}", exc_info=True)
            workflow_tracker.error_agent(self.execution, str(e))
            
            self.audit_logger.log_event(
                AuditEventType.PROCESSING_ERROR,
                context.get('contract_id', 'unknown'),
                f"{self.agent_name}_error",
                status="failure",
                error_details=str(e)
            )
            
            return {'success': False, 'error': str(e), 'pattern': self.get_pattern_name()}
    
    @abstractmethod
    async def _execute_pattern(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Pattern-specific execution logic - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_agent_role(self) -> str:
        """Return agent role description for tracking."""
        pass
    
    @abstractmethod
    def get_pattern_name(self) -> str:
        """Return pattern name for identification."""
        pass
    
    def get_input_summary(self, context: Dict[str, Any]) -> str:
        """Generate input summary for tracking."""
        clauses = context.get('clauses', [])
        text_len = len(context.get('contract_text', ''))
        return f"Processing {len(clauses)} clauses, {text_len} chars"
    
    def get_output_summary(self, result: Dict[str, Any]) -> str:
        """Generate output summary for tracking."""
        if result.get('success'):
            return f"Pattern: {self.get_pattern_name()}, Success: True"
        return f"Pattern: {self.get_pattern_name()}, Error: {result.get('error', 'Unknown')}"
