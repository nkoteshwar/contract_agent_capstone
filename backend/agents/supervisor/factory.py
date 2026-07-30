from .supervisor_agent import SupervisorAgent
from .agent_registry import AgentRegistry

class SupervisorFactory:
    @staticmethod
    def create_supervisor() -> SupervisorAgent:
        """Create supervisor with registered agents"""
        registry = AgentRegistry()
        
        # TODO: Register existing agents with adapters
        # registry.register_agent("pdf-processing", PDFProcessingAgentAdapter())
        # registry.register_agent("clause-extraction", ClauseExtractionAgentAdapter())
        
        return SupervisorAgent(registry)