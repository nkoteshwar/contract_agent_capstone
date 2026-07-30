import re
from typing import Dict, List, Tuple

class PIIEngine:
    """
    Centralized engine for detecting and redacting Personally Identifiable Information (PII).
    Uses optimized regex patterns for high-performance scanning.
    """
    
    # Standard PII Patterns
    PATTERNS: Dict[str, str] = {
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]*[a-zA-Z0-9-]",
        "PHONE": r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "SSN": r"\d{3}-\d{2}-\d{4}",
        "CREDIT_CARD": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
        "IP_ADDRESS": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    }

    @classmethod
    def detect(cls, text: str) -> List[Tuple[str, str]]:
        """
        Detect PII in the given text.
        Returns a list of (PII_TYPE, MATCHED_TEXT) tuples.
        """
        matches = []
        for pii_type, pattern in cls.PATTERNS.items():
            found = re.findall(pattern, text)
            for item in found:
                matches.append((pii_type, item))
        return matches

    @classmethod
    def redact(cls, text: str, placeholder_template: str = "[REDACTED_{type}]") -> str:
        """
        Redact all detected PII in the given text.
        """
        redacted_text = text
        for pii_type, pattern in cls.PATTERNS.items():
            placeholder = placeholder_template.format(type=pii_type)
            redacted_text = re.sub(pattern, placeholder, redacted_text)
        return redacted_text

if __name__ == "__main__":
    # Simple test
    test_text = "Contact me at user@example.com or 555-123-4567. My SSN is 123-45-6789."
    print("Original:", test_text)
    print("Redacted:", PIIEngine.redact(test_text))
