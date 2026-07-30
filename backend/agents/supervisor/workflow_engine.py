from typing import Dict, List
from dataclasses import dataclass
from .interfaces import IWorkflowEngine

@dataclass
class WorkflowStep:
    agent_id: str
    agent_type: str
    dependencies: List[str] = None
    input_data: Dict = None

@dataclass 
class Workflow:
    workflow_id: str
    steps: List[WorkflowStep]

class WorkflowEngine(IWorkflowEngine):
    def __init__(self):
        self.workflow_templates = {
            "contract_analysis": [
                WorkflowStep("pdf-processing", "pdf_processing"),
                WorkflowStep("clause-extraction", "clause_extraction", ["pdf-processing"]),
                WorkflowStep("risk-assessment", "risk_assessment", ["clause-extraction"])
            ]
        }
    
    def create_workflow(self, workflow_type: str) -> Workflow:
        """Create workflow from template"""
        steps = self.workflow_templates.get(workflow_type, [])
        return Workflow(workflow_type, steps)
    
    def register_workflow_template(self, workflow_type: str, steps: List[WorkflowStep]):
        """Register new workflow template"""
        self.workflow_templates[workflow_type] = steps