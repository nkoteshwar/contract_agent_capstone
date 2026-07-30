from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class ProcessingStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    REVIEW_REQUIRED = "review_required"

@dataclass
class ProcessingResult:
    status: ProcessingStatus
    contract_id: Optional[str] = None
    message: str = ""
    error: Optional[str] = None

@dataclass
class ContractData:
    is_contract: bool
    confidence_score: float
    contract_type: str
    summary: str
    parties: List[dict]
    effective_date: Optional[str] = None
    end_date: Optional[str] = None
    total_amount: Optional[float] = None
    governing_law: Optional[str] = None
    key_terms: List[str] = None
    
    def __post_init__(self):
        if self.key_terms is None:
            self.key_terms = []
    full_text: str = ""