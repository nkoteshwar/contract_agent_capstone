from typing import Dict, Any, List
import re
from . import EmbeddingAgent, EmbeddingResult
from backend.embeddings.strategies.factory import EmbeddingFactory
from backend.embeddings.strategies import EmbeddingType

class RelationshipEmbeddingAgent(EmbeddingAgent):
    """Agent for extracting and embedding relationship contexts"""
    
    def __init__(self):
        self.factory = EmbeddingFactory()
        self.strategy = self.factory.create_strategy(EmbeddingType.RELATIONSHIP)
    
    def process(self, content: str, metadata: Dict[str, Any] = None) -> List[EmbeddingResult]:
        """Extract relationship contexts and create embeddings"""
        results = []
        
        # Extract party relationships
        party_relationships = self._extract_party_relationships(content)
        for rel in party_relationships:
            rel_embedding = self.strategy.generate_embedding(
                rel["context"],
                {
                    "relationship_type": "PARTY_TO",
                    "source_entity": rel["party"],
                    "target_entity": "Contract",
                    "role": rel["role"]
                }
            )
            
            results.append(EmbeddingResult(
                embedding=rel_embedding,
                metadata={
                    **(metadata or {}),
                    "relationship_type": "PARTY_TO",
                    "party_name": rel["party"],
                    "role": rel["role"]
                },
                content=rel["context"],
                embedding_type="relationship"
            ))
        
        # Extract governing law relationships
        gov_law_relationships = self._extract_governing_law(content)
        for rel in gov_law_relationships:
            rel_embedding = self.strategy.generate_embedding(
                rel["context"],
                {
                    "relationship_type": "HAS_GOVERNING_LAW",
                    "source_entity": "Contract",
                    "target_entity": rel["jurisdiction"]
                }
            )
            
            results.append(EmbeddingResult(
                embedding=rel_embedding,
                metadata={
                    **(metadata or {}),
                    "relationship_type": "HAS_GOVERNING_LAW",
                    "jurisdiction": rel["jurisdiction"]
                },
                content=rel["context"],
                embedding_type="relationship"
            ))
        
        return results
    
    def _extract_party_relationships(self, content: str) -> List[Dict[str, Any]]:
        """Extract party relationships from contract text"""
        relationships = []
        
        # Common party role patterns
        role_patterns = {
            "contractor": r"contractor.*?([A-Z][a-zA-Z\s&,\.]+?)(?:\s|,|\.|$)",
            "client": r"client.*?([A-Z][a-zA-Z\s&,\.]+?)(?:\s|,|\.|$)",
            "vendor": r"vendor.*?([A-Z][a-zA-Z\s&,\.]+?)(?:\s|,|\.|$)",
            "supplier": r"supplier.*?([A-Z][a-zA-Z\s&,\.]+?)(?:\s|,|\.|$)",
            "licensee": r"licensee.*?([A-Z][a-zA-Z\s&,\.]+?)(?:\s|,|\.|$)",
            "licensor": r"licensor.*?([A-Z][a-zA-Z\s&,\.]+?)(?:\s|,|\.|$)"
        }
        
        for role, pattern in role_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                party_name = match.group(1).strip()
                if len(party_name) > 2 and len(party_name) < 100:
                    # Get surrounding context
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end].strip()
                    
                    relationships.append({
                        "party": party_name,
                        "role": role,
                        "context": context
                    })
        
        return relationships
    
    def _extract_governing_law(self, content: str) -> List[Dict[str, Any]]:
        """Extract governing law relationships"""
        relationships = []
        
        # Governing law patterns
        patterns = [
            r"governed by.*?law.*?of\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|$)",
            r"jurisdiction.*?of\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|$)",
            r"laws?\s+of\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|$)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                jurisdiction = match.group(1).strip()
                if len(jurisdiction) > 2 and len(jurisdiction) < 50:
                    # Get surrounding context
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end].strip()
                    
                    relationships.append({
                        "jurisdiction": jurisdiction,
                        "context": context
                    })
        
        return relationships