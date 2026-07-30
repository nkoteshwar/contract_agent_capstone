"""Policy audit integration using existing audit infrastructure."""

from typing import Dict, Any
from backend.infrastructure.audit_logger import AuditLogger, AuditEventType
from backend.infrastructure.error_tracker import ErrorTracker, ErrorCategory


class PolicyAuditService:
    """Policy audit service extending existing audit infrastructure."""
    
    def __init__(self):
        self.audit_logger = AuditLogger()
        self.error_tracker = ErrorTracker()
    
    def log_policy_upload(self, tenant_id: str, policy_id: str, policy_name: str, 
                         user_id: str = None) -> None:
        """Log policy upload using existing audit patterns."""
        self.audit_logger.log_event(
            event_type=AuditEventType.DOCUMENT_UPLOAD,
            resource_id=policy_id,
            action="policy_upload",
            user_id=user_id or "system",
            tenant_id=tenant_id,
            metadata={
                "policy_name": policy_name,
                "policy_id": policy_id,
                "action": "policy_document_uploaded"
            },
            status="success"
        )
    
    def log_policy_processing(self, tenant_id: str, policy_id: str, 
                            processing_result: Dict[str, Any]) -> None:
        """Log policy processing results."""
        success = processing_result.get('status') == 'success'
        
        self.audit_logger.log_event(
            event_type=AuditEventType.ANALYSIS_REQUEST,
            resource_id=policy_id,
            action="policy_processing",
            user_id="system",
            tenant_id=tenant_id,
            metadata={
                "chunks_created": processing_result.get('chunks_created', 0),
                "rules_extracted": processing_result.get('rules_extracted', 0),
                "processing_steps": processing_result.get('steps', []),
                "workflow_id": processing_result.get('workflow_id')
            },
            status="success" if success else "failure",
            error_details=processing_result.get('error') if not success else None
        )
    
    def log_policy_compliance_check(self, tenant_id: str, contract_id: str, 
                                  compliance_result: Dict[str, Any]) -> None:
        """Log policy compliance checking."""
        event = AuditEvent(
            event_type="policy_compliance_check",
            tenant_id=tenant_id,
            user_id="system",
            resource_id=contract_id,
            resource_type="contract",
            action="compliance_check",
            details={
                "violations_found": compliance_result.get('violations_found', 0),
                "policies_checked": compliance_result.get('policies_checked', 0),
                "violations": compliance_result.get('violations', []),
                "compliance_score": self._calculate_compliance_score(compliance_result)
            },
            success=True
        )
        
        self.audit_logger.log_event(event)
    
    def log_policy_search(self, tenant_id: str, query: str, results_count: int,
                         user_id: str = None) -> None:
        """Log policy search activities."""
        event = AuditEvent(
            event_type="policy_search",
            tenant_id=tenant_id,
            user_id=user_id or "system",
            resource_id=None,
            resource_type="policy_search",
            action="search",
            details={
                "search_query": query,
                "results_count": results_count,
                "search_type": "semantic"
            },
            success=True
        )
        
        self.audit_logger.log_event(event)
    
    def log_policy_update(self, tenant_id: str, policy_id: str, old_version: str,
                         new_version: str, user_id: str = None) -> None:
        """Log policy updates and versioning."""
        event = AuditEvent(
            event_type="policy_update",
            tenant_id=tenant_id,
            user_id=user_id or "system",
            resource_id=policy_id,
            resource_type="policy_document",
            action="update",
            details={
                "old_version": old_version,
                "new_version": new_version,
                "update_type": "version_update"
            },
            success=True
        )
        
        self.audit_logger.log_event(event)
    
    def log_policy_deletion(self, tenant_id: str, policy_id: str, policy_name: str,
                          user_id: str = None) -> None:
        """Log policy deletion (soft delete)."""
        event = AuditEvent(
            event_type="policy_deletion",
            tenant_id=tenant_id,
            user_id=user_id or "system",
            resource_id=policy_id,
            resource_type="policy_document",
            action="delete",
            details={
                "policy_name": policy_name,
                "deletion_type": "soft_delete"
            },
            success=True
        )
        
        self.audit_logger.log_event(event)
    
    def _calculate_compliance_score(self, compliance_result: Dict[str, Any]) -> float:
        """Calculate compliance score based on violations."""
        violations = compliance_result.get('violations', [])
        if not violations:
            return 1.0
        
        # Weight violations by severity
        severity_weights = {'CRITICAL': 1.0, 'HIGH': 0.7, 'MEDIUM': 0.4, 'LOW': 0.2}
        total_weight = sum(severity_weights.get(v.get('severity', 'LOW'), 0.2) for v in violations)
        
        # Calculate score (lower is better for violations)
        max_possible_weight = len(violations) * 1.0  # If all were critical
        compliance_score = max(0.0, 1.0 - (total_weight / max_possible_weight))
        
        return compliance_score