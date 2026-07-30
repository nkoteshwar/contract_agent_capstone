from typing import Dict, Callable, List
from .interfaces import IMessageBus, AgentMessage
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class MessageBus(IMessageBus):
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[AgentMessage] = []
    
    def publish(self, message: AgentMessage):
        """Publish message to subscribers"""
        self.message_history.append(message)
        logger.info(f"📨 Message: {message.sender} → {message.receiver}")
        
        # Notify subscribers
        if message.receiver in self.subscribers:
            for handler in self.subscribers[message.receiver]:
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"Message handler failed: {e}")
    
    def subscribe(self, agent_id: str, handler: Callable):
        """Subscribe agent to messages"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(handler)