"""Policy domain entities using existing patterns."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class PolicyRule:
    id: str
    rule_text: str
    rule_type: str  # 'mandatory', 'recommended', 'prohibited'
    applies_to: List[str]  # Contract types
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    section_reference: str
    exceptions: List[str] = None


@dataclass
class PolicyDocument:
    id: str
    name: str
    tenant_id: str
    version: str
    rules: List[PolicyRule]
    created_at: datetime
    checksum: str


@dataclass
class PolicyViolation:
    policy_rule_id: str
    clause_content: str
    violation_type: str
    severity: str
    message: str
    recommendation: str
    confidence: float