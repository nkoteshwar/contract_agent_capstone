from typing import List, Optional, Dict, Any
from .base import BaseGuard, IGuardValidator, GuardResult

class PromptGuard(BaseGuard):
    """
    Facade for the prompt guard system.
    Orchestrates multiple validators to ensure prompt safety.
    """
    def _default_chain(self) -> IGuardValidator:
        """Provide a default sensible security chain"""
        from .validators import InjectionValidator, TopicValidator, KeywordValidator, IntentValidator, PIIValidator
        
        # Order matters: check for blatant malicious intent and PII first
        injection = InjectionValidator()
        pii = PIIValidator()
        keyword = KeywordValidator()
        topic = TopicValidator()
        intent = IntentValidator()
        
        injection.set_next(pii).set_next(keyword).set_next(topic).set_next(intent)
        return injection

    def validate(self, prompt: str, context_metadata: Optional[Dict[str, Any]] = None) -> GuardResult:
        """
        Validate an incoming prompt against the configured security chain.
        Centralized entry point for all prompt security checks.
        """
        return self._execute_validation(prompt, "Prompt Guard", context_metadata)
