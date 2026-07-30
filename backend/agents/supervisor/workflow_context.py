from typing import Dict, Any, Optional
from .interfaces import AgentResult

class WorkflowContext:
    """Shared context for workflow execution - Agentic AI pattern"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.shared_memory: Dict[str, Any] = {}
        self.agent_results: Dict[str, AgentResult] = {}
        self.metadata: Dict[str, Any] = {}
    
    def set_shared_data(self, key: str, value: Any):
        """Store data accessible to all agents"""
        self.shared_memory[key] = value
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Retrieve shared data"""
        return self.shared_memory.get(key, default)
    
    def set_agent_result(self, agent_id: str, result: AgentResult):
        """Store agent execution result"""
        self.agent_results[agent_id] = result
    
    def get_agent_result(self, agent_id: str) -> Optional[AgentResult]:
        """Get result from specific agent"""
        return self.agent_results.get(agent_id)
    
    def get_all_results(self) -> Dict[str, AgentResult]:
        """Get all agent results"""
        return self.agent_results.copy()
    
    def set_metadata(self, key: str, value: Any):
        """Set workflow metadata"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get workflow metadata"""
        return self.metadata.get(key, default)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get workflow execution summary"""
        return {
            "workflow_id": self.workflow_id,
            "completed_agents": list(self.agent_results.keys()),
            "total_agents": len(self.agent_results),
            "success_rate": len([r for r in self.agent_results.values() if r.status == "success"]) / len(self.agent_results) if self.agent_results else 0,
            "metadata": self.metadata
        }