from typing import List, Dict, Any
from backend.shared.utils.gemini_embedding_service import embedding
from . import EmbeddingStrategy

class ClauseEmbeddingStrategy(EmbeddingStrategy):
    """Strategy for generating clause-specific embeddings"""
    
    def __init__(self):
        self.embeddings = embedding
        self.cuad_clause_types = [
            "Document Name", "Parties", "Agreement Date", "Effective Date", "Expiration Date",
            "Renewal Term", "Notice Period To Terminate Renewal", "Governing Law", 
            "Most Favored Nation", "Non-Compete", "Exclusivity", "No-Solicit Of Customers",
            "No-Solicit Of Employees", "Non-Disparagement", "Termination For Convenience",
            "Rofr/Rofo/Rofn", "Change Of Control", "Anti-Assignment", "Revenue/Customer Sharing",
            "Price Restrictions", "Minimum Commitment", "Volume Restriction", "IP Ownership Assignment",
            "Joint IP Ownership", "License Grant", "Non-Transferable License", "Affiliate License-Licensor",
            "Affiliate License-Licensee", "Unlimited/All-You-Can-Eat-License", "Irrevocable Or Perpetual License",
            "Source Code Escrow", "Post-Termination Services", "Audit Rights", "Uncapped Liability",
            "Cap On Liability", "Liquidated Damages", "Warranty Duration", "Insurance",
            "Covenant Not To Sue", "Third Party Beneficiary", "Escrow"
        ]
    
    def generate_embedding(self, content: str, metadata: Dict[str, Any] = None) -> List[float]:
        """Generate embedding for clause content with type context"""
        clause_type = metadata.get("clause_type", "") if metadata else ""
        
        # Enhance content with clause type context for better embeddings
        enhanced_content = f"Contract clause type: {clause_type}. Content: {content}"
        
        return self.embeddings.embed_query(enhanced_content)
    
    def get_embedding_dimension(self) -> int:
        return 1536