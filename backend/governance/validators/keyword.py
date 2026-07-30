from typing import List, Optional, Dict, Any
from ..base import IGuardValidator, GuardResult

class KeywordValidator(IGuardValidator):
    """Blocks sensitive or inappropriate keywords"""
    
    FORBIDDEN_KEYWORDS = {
        "password", "secret key", "admin", "root", "database credentials"
    }

    def validate(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> GuardResult:
        input_lower = input_text.lower()
        for word in self.FORBIDDEN_KEYWORDS:
            if word in input_lower:
                return GuardResult(
                    is_safe=False,
                    violation_type="SENSITIVE_CONTENT",
                    message=f"Request contains forbidden keyword: '{word}'"
                )
        return GuardResult(is_safe=True)
