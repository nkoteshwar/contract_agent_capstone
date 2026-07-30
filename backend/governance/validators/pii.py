from typing import List, Optional, Dict, Any
from ..base import IGuardValidator, GuardResult
from ..pii_engine import PIIEngine

class PIIValidator(IGuardValidator):
    """Detects PII in user prompts to prevent sensitive data leakage to LLMs"""
    
    def validate(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> GuardResult:
        matches = PIIEngine.detect(input_text)
        if matches:
            pii_types = {m[0] for m in matches}
            return GuardResult(
                is_safe=False,
                violation_type="PII_DETECTED",
                message=f"Input contains sensitive PII data: {', '.join(pii_types)}. Please remove it before re-submitting.",
                metadata={"pii_found": matches}
            )
        return GuardResult(is_safe=True)
