from typing import Dict, Optional, List
from .interfaces import IAgent, IAgentRegistry

class AgentRegistry(IAgentRegistry):
    """Registry for agent discovery and management"""
    
    def __init__(self):
        self.agents: Dict[str, IAgent] = {}
    
    def register_agent(self, agent_id: str, agent: IAgent):
        """Register an agent"""
        self.agents[agent_id] = agent
    
    def get_agent(self, agent_id: str) -> Optional[IAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all registered agent IDs"""
        return list(self.agents.keys())
    
    def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get capabilities of specific agent"""
        agent = self.get_agent(agent_id)
        return agent.get_capabilities() if agent else []
    
    def find_agents_by_capability(self, capability: str) -> List[str]:
        """Find agents that have specific capability"""
        matching_agents = []
        for agent_id, agent in self.agents.items():
            if capability in agent.get_capabilities():
                matching_agents.append(agent_id)
        return matching_agents