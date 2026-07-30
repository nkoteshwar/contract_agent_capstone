from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class AgentRole(Enum):
    DOCUMENT_INGESTION = "Document Ingestion"
    WORKFLOW_ORCHESTRATION = "Workflow Orchestration"
    SEMANTIC_PROCESSING = "Semantic Processing"
    CONTENT_ANALYSIS = "Content Analysis"
    RELATIONSHIP_ANALYSIS = "Relationship Analysis"
    COMPLIANCE_VALIDATION = "Compliance Validation"
    RISK_ANALYSIS = "Risk Analysis"
    CONTRACT_OPTIMIZATION = "Contract Optimization"
    QUALITY_ASSURANCE = "Quality Assurance"
    SCHEMA_MANAGEMENT = "Schema Management"

@dataclass
class Agent:
    id: str
    name: str
    role: AgentRole
    description: str
    capabilities: List[str]
    input_type: str
    output_type: str
    tools: List[str]

@dataclass
class WorkflowStep:
    agent_name: str
    description: str
    technology: str
    is_new: bool = False
    is_enhanced: bool = False

@dataclass
class Workflow:
    id: str
    title: str
    description: str
    steps: List[WorkflowStep]
    category: str