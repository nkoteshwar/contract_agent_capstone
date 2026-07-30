from typing import Dict, Any, Optional
from .audit_logger import AuditLogger, AuditEventType
from backend.shared.utils.logger import get_logger

logger = get_logger(__name__)

class AgentAuditService:
    """
    Service for granular agentic auditing.
    Provides methods to log specific agent lifecycle events.
    """
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        self.audit_logger = audit_logger or AuditLogger()

    def log_user_interaction(self, user_id: str, prompt: str, session_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Log the initial user prompt"""
        self.audit_logger.log_event(
            event_type=AuditEventType.USER_INTERACTION,
            resource_id=session_id,
            action="receive_prompt",
            user_id=user_id,
            metadata={
                "prompt_preview": prompt[:100] + ("..." if len(prompt) > 100 else ""),
                **(metadata or {})
            }
        )

    def log_tool_execution(self, tool_name: str, args: Dict[str, Any], result: str, session_id: str, status: str = "success"):
        """Log a tool execution and its result"""
        self.audit_logger.log_event(
            event_type=AuditEventType.AGENT_TOOL_CALL,
            resource_id=session_id,
            action=f"execute_{tool_name}",
            status=status,
            metadata={
                "tool_name": tool_name,
                "arguments": args,
                "result_preview": str(result)[:200] + ("..." if len(str(result)) > 200 else "")
            }
        )

    def log_model_decision(self, rationale: str, session_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an LLM thought or decision step"""
        self.audit_logger.log_event(
            event_type=AuditEventType.AGENT_THOUGHT,
            resource_id=session_id,
            action="llm_decision",
            metadata={
                "rationale": rationale,
                **(metadata or {})
            }
        )

    def log_guard_check(self, guard_name: str, is_safe: bool, violation_type: Optional[str], session_id: str):
        """Log a governance guard check (Prompt/Output Guard)"""
        self.audit_logger.log_event(
            event_type=AuditEventType.MODEL_GUARD_CHECK,
            resource_id=session_id,
            action=f"check_{guard_name.lower().replace(' ', '_')}",
            status="success" if is_safe else "violation",
            metadata={
                "guard": guard_name,
                "is_safe": is_safe,
                "violation_type": violation_type
            }
        )
