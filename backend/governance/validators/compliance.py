from typing import List, Optional, Dict, Any
from ..base import IGuardValidator, GuardResult

class DomainComplianceValidator(IGuardValidator):
    """
    Ensures the output is compliant with contract management domain rules.
    """
    def validate(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> GuardResult:
        forbidden_phrases = [
            "this is binding legal advice",
            "i am a licensed attorney",
            "you should definitely sign this without review"
        ]
        
        input_lower = input_text.lower() # Changed from output_lower = output.lower()
        for phrase in forbidden_phrases:
            if phrase in input_lower: # Changed from output_lower
                return GuardResult(
                    is_safe=False,
                    violation_type="DOMAIN_VIOLATION",
                    message=f"Output contains unauthorized legal claim: '{phrase}'"
                )
        
        return GuardResult(is_safe=True)
