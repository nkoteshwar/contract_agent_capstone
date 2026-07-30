from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class RecoveryStrategy(Enum):
    RETRY_SAME_AGENT = "retry_same"
    SWITCH_AGENT = "switch_agent"
    DEGRADE_GRACEFULLY = "degrade"
    ESCALATE_HUMAN = "escalate"

@dataclass
class AgentFailure:
    agent_id: str
    task_type: str
    error_message: str
    failure_time: datetime
    attempt_count: int = 1

@dataclass
class RecoveryAction:
    strategy: RecoveryStrategy
    target_agent: str
    retry_delay: int = 0
    fallback_data: Dict[str, Any] = None

class ErrorRecoveryManager:
    def __init__(self):
        self.failure_history: Dict[str, list] = {}
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    def handle_failure(self, failure: AgentFailure) -> RecoveryAction:
        """Determine recovery strategy for agent failure"""
        self._record_failure(failure)
        
        # Check failure patterns
        recent_failures = self._get_recent_failures(failure.agent_id)
        
        if failure.attempt_count < self.max_retries:
            if len(recent_failures) < 2:
                return RecoveryAction(
                    strategy=RecoveryStrategy.RETRY_SAME_AGENT,
                    target_agent=failure.agent_id,
                    retry_delay=self.retry_delay * failure.attempt_count
                )
            else:
                return RecoveryAction(
                    strategy=RecoveryStrategy.SWITCH_AGENT,
                    target_agent=self._get_backup_agent(failure.agent_id)
                )
        
        # Max retries exceeded
        if self._has_fallback_data(failure.task_type):
            return RecoveryAction(
                strategy=RecoveryStrategy.DEGRADE_GRACEFULLY,
                target_agent=failure.agent_id,
                fallback_data=self._get_fallback_data(failure.task_type)
            )
        
        return RecoveryAction(
            strategy=RecoveryStrategy.ESCALATE_HUMAN,
            target_agent=failure.agent_id
        )
    
    def _record_failure(self, failure: AgentFailure):
        """Record failure for pattern analysis"""
        if failure.agent_id not in self.failure_history:
            self.failure_history[failure.agent_id] = []
        
        self.failure_history[failure.agent_id].append(failure)
        logger.error(f"❌ Agent failure recorded: {failure.agent_id} - {failure.error_message}")
    
    def _get_recent_failures(self, agent_id: str, hours: int = 1) -> list:
        """Get recent failures for agent"""
        if agent_id not in self.failure_history:
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        return [f for f in self.failure_history[agent_id] if f.failure_time > cutoff]
    
    def _get_backup_agent(self, failed_agent_id: str) -> str:
        """Get backup agent for failed agent"""
        backup_mapping = {
            "pdf-processing": "pdf-processing-backup",
            "clause-extraction": "clause-extraction-alt",
            "policy-compliance": "policy-compliance-simple",
            "risk-assessment": "risk-assessment-basic"
        }
        return backup_mapping.get(failed_agent_id, failed_agent_id)
    
    def _has_fallback_data(self, task_type: str) -> bool:
        """Check if fallback data exists for task type"""
        return task_type in ["extract_clauses", "assess_risk"]
    
    def _get_fallback_data(self, task_type: str) -> Dict[str, Any]:
        """Get fallback data for graceful degradation"""
        fallback_data = {
            "extract_clauses": {"clauses": [], "confidence": 0.0, "source": "fallback"},
            "assess_risk": {"risk_score": 50, "risk_level": "MEDIUM", "source": "fallback"}
        }
        return fallback_data.get(task_type, {})