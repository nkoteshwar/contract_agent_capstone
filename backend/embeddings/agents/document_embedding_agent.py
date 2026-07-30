from typing import Dict, Any, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from . import EmbeddingAgent, EmbeddingResult
from backend.embeddings.strategies.factory import EmbeddingFactory
from backend.embeddings.strategies import EmbeddingType

class DocumentEmbeddingAgent(EmbeddingAgent):
    """Agent for processing document-level embeddings"""
    
    def __init__(self):
        self.factory = EmbeddingFactory()
        self.strategy = self.factory.create_strategy(EmbeddingType.DOCUMENT)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " "]
        )
    
    def process(self, content: str, metadata: Dict[str, Any] = None) -> List[EmbeddingResult]:
        """Process document and create hierarchical embeddings"""
        results = []
        
        # Full document embedding
        doc_embedding = self.strategy.generate_embedding(content, metadata)
        results.append(EmbeddingResult(
            embedding=doc_embedding,
            metadata={**(metadata or {}), "level": "document"},
            content=content[:500] + "..." if len(content) > 500 else content,
            embedding_type="document"
        ))
        
        # Section embeddings (split by double newlines for sections)
        sections = content.split("\n\n")
        for i, section in enumerate(sections):
            if len(section.strip()) > 100:  # Only process substantial sections
                section_embedding = self.strategy.generate_embedding(section, {
                    **(metadata or {}), 
                    "section_index": i,
                    "section_type": self._identify_section_type(section)
                })
                results.append(EmbeddingResult(
                    embedding=section_embedding,
                    metadata={
                        **(metadata or {}), 
                        "level": "section",
                        "section_index": i,
                        "section_type": self._identify_section_type(section)
                    },
                    content=section,
                    embedding_type="section"
                ))
        
        return results
    
    def _identify_section_type(self, section: str) -> str:
        """Identify section type based on content"""
        section_lower = section.lower()
        
        if any(term in section_lower for term in ["payment", "fee", "cost", "price"]):
            return "payment"
        elif any(term in section_lower for term in ["termination", "terminate", "end"]):
            return "termination"
        elif any(term in section_lower for term in ["liability", "damages", "loss"]):
            return "liability"
        elif any(term in section_lower for term in ["intellectual property", "ip", "patent", "copyright"]):
            return "intellectual_property"
        elif any(term in section_lower for term in ["confidential", "non-disclosure", "proprietary"]):
            return "confidentiality"
        else:
            return "general"