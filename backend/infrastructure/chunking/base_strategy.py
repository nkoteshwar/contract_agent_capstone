from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ChunkResult:
    chunk_id: str
    content: str
    chunk_type: str
    start_pos: int
    end_pos: int
    confidence: float
    overlap_with: List[str] = None

class IChunkingStrategy(ABC):
    @abstractmethod
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[ChunkResult]:
        pass
    
    @abstractmethod
    def get_chunk_size(self) -> int:
        pass