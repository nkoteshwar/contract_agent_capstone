"""
Fix Enterprise Database Relationships
Connects enterprise nodes with proper relationships
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.infrastructure.contract_repository import Neo4jContractRepository
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class FixEnterpriseRelationships:
    """Fix missing enterprise relationships"""
    
    def __init__(self):
        self.repository = Neo4jContractRepository()
    
    def fix_relationships(self):
        """Fix all missing enterprise relationships"""
        try:
            self._fix_version_relationships()
            self._fix_chunk_relationships()
            self._fix_lineage_relationships()
            self._fix_analysis_relationships()
            logger.info("Enterprise relationships fixed successfully")
        except Exception as e:
            logger.error(f"Failed to fix enterprise relationships: {e}")
            raise
    
    def _fix_version_relationships(self):
        """Connect contracts to versions"""
        query = """
        MATCH (c:Contract), (cv:ContractVersion)
        WHERE cv.contract_id = 'sample_contract'
        MERGE (c)-[:HAS_VERSION]->(cv)
        """
        self.repository.graph.query(query)
        print("✅ Fixed HAS_VERSION relationships")
    
    def _fix_chunk_relationships(self):
        """Connect contracts to chunks"""
        query = """
        MATCH (c:Contract), (dc:DocumentChunk)
        WHERE dc.contract_id = 'sample_contract'
        MERGE (c)-[:CONTAINS_CHUNK]->(dc)
        """
        self.repository.graph.query(query)
        print("✅ Fixed CONTAINS_CHUNK relationships")
    
    def _fix_lineage_relationships(self):
        """Connect contracts to lineage"""
        query = """
        MATCH (c:Contract), (pl:ProcessingLineage)
        WHERE pl.contract_id = 'sample_contract'
        MERGE (c)-[:HAS_LINEAGE]->(pl)
        """
        self.repository.graph.query(query)
        print("✅ Fixed HAS_LINEAGE relationships")
    
    def _fix_analysis_relationships(self):
        """Connect contracts to analysis"""
        query = """
        MATCH (c:Contract), (ca:ContractAnalysis)
        WHERE ca.contract_id = 'sample_contract'
        MERGE (c)-[:HAS_ANALYSIS]->(ca)
        """
        self.repository.graph.query(query)
        print("✅ Fixed HAS_ANALYSIS relationships")

def run_relationship_fix():
    """Run the relationship fix"""
    fixer = FixEnterpriseRelationships()
    fixer.fix_relationships()
    print("✅ All enterprise relationships fixed")

if __name__ == "__main__":
    run_relationship_fix()