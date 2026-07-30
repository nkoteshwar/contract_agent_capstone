from typing import Dict, Type
from .interfaces import IAgent
from .base_adapter import BaseAgentAdapter, AgentConfig
from .adapters import PDFProcessingAdapter, ClauseExtractionAdapter, RiskAssessmentAdapter
from ...llm_manager import LLMManager

class AgentFactory:
    """Factory for creating agents - DRY compliance"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.adapter_registry: Dict[str, Type[BaseAgentAdapter]] = {
            "pdf_processing": PDFProcessingAdapter,
            "clause_extraction": ClauseExtractionAdapter,
            "risk_assessment": RiskAssessmentAdapter
        }
    
    def register_adapter(self, agent_type: str, adapter_class: Type[BaseAgentAdapter]):
        """Register new adapter type"""
        self.adapter_registry[agent_type] = adapter_class
    
    def create_agent(self, agent_type: str, agent_id: str = None) -> IAgent:
        """Create agent instance"""
        if agent_type not in self.adapter_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        adapter_class = self.adapter_registry[agent_type]
        
        config = AgentConfig(
            agent_id=agent_id or agent_type,
            agent_type=agent_type,
            capabilities=self._get_default_capabilities(agent_type)
        )
        
        return adapter_class(config, self.llm_manager)
    
    def _get_default_capabilities(self, agent_type: str) -> list:
        """Get default capabilities for agent type"""
        capabilities_map = {
            "pdf_processing": ["text_extraction", "metadata_extraction", "document_analysis"],
            "clause_extraction": ["clause_detection", "cuad_compliance", "confidence_scoring"],
            "risk_assessment": ["risk_calculation", "policy_validation", "recommendation_generation"]
        }
        return capabilities_map.get(agent_type, ["general_processing"])
    
    def get_available_types(self) -> list:
        """Get list of available agent types"""
        return list(self.adapter_registry.keys())