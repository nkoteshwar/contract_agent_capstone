import re
from typing import List, Optional, Dict, Any
from ..base import IGuardValidator, GuardResult

class TopicValidator(IGuardValidator):
    """Ensures the prompt stays within the domain of contract analysis"""
    
    ALLOWED_KEYWORDS = {
        "contract", "agreement", "lease", "clause", "liability", 
        "termination", "party", "parties", "legal", "provision",
        "indemnity", "warranty", "signature", "effective date",
        "expiration", "amendment", "addendum", "exhibit"
    }

    def validate(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> GuardResult:
        prompt_lower = input_text.lower()
        if len(input_text.split()) < 3:
            return GuardResult(is_safe=True)
            
        has_context = any(re.search(r'\b' + re.escape(keyword) + r'\b', prompt_lower) for keyword in self.ALLOWED_KEYWORDS)
        
        OFF_TOPIC_TASKS = [
            "tell me a joke", "write a poem", "how to make a bomb", 
            "python code for", "how do i cook", "weather in",
            "capital of", "who is the president"
        ]
        for task in OFF_TOPIC_TASKS:
            if task in prompt_lower:
                return GuardResult(
                    is_safe=False,
                    violation_type="OUT_OF_SCOPE",
                    message=f"Request is outside the scope of contract analysis: '{task}'"
                )

        if not has_context and len(input_text.split()) >= 4:
             return GuardResult(
                is_safe=False,
                violation_type="OUT_OF_SCOPE",
                message="The request does not appear to be related to contract analysis."
            )
            
        return GuardResult(is_safe=True)
