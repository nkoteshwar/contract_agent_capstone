from typing import Callable, Any, Dict
import time
import logging
from dataclasses import dataclass

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True

class RetryManager:
    def __init__(self):
        self.default_config = RetryConfig()
        self.agent_configs: Dict[str, RetryConfig] = {}
    
    def set_agent_config(self, agent_id: str, config: RetryConfig):
        """Set retry configuration for specific agent"""
        self.agent_configs[agent_id] = config
    
    def execute_with_retry(self, agent_id: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry"""
        config = self.agent_configs.get(agent_id, self.default_config)
        
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt, config)
                    logger.info(f"🔄 Retry {attempt}/{config.max_attempts} for {agent_id} in {delay}s")
                    time.sleep(delay)
                
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"✅ Retry successful for {agent_id} on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ Attempt {attempt + 1} failed for {agent_id}: {str(e)}")
                
                if attempt == config.max_attempts - 1:
                    logger.error(f"❌ All retry attempts exhausted for {agent_id}")
                    break
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = min(config.base_delay * (config.backoff_multiplier ** (attempt - 1)), config.max_delay)
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay