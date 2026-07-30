"""
Section Repository with Order Preservation
"""

from typing import List, Dict, Any
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class SectionRepository:
    """Repository for section storage with order preservation"""
    
    def __init__(self):
        from backend.infrastructure.contract_repository import Neo4jContractRepository
        self.repository = Neo4jContractRepository()
    
    def store_sections(self, contract_id: str, sections: List[Dict[str, Any]]) -> bool:
        """Store sections with guaranteed order preservation"""
        try:
            # Sort sections by order to ensure correct sequence
            sorted_sections = sorted(sections, key=lambda x: x['order'])
            
            for section in sorted_sections:
                self._store_single_section(contract_id, section)
            
            logger.info(f"Stored {len(sections)} sections for contract {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store sections: {e}")
            return False
    
    def _store_single_section(self, contract_id: str, section: Dict[str, Any]):
        """Store individual section with order preservation"""
        query = """
        MATCH (c:Contract {file_id: $contract_id})
        CREATE (s:Section {
            section_id: $section_id,
            title: $title,
            content: $content,
            order: $order,
            start_position: $start_position,
            end_position: $end_position,
            section_type: $section_type,
            confidence: $confidence,
            tenant_id: c.tenant_id,
            created_at: datetime()
        })
        CREATE (c)-[:HAS_SECTION {order: $order}]->(s)
        RETURN s.section_id as section_id
        """
        
        self.repository.graph.query(query, {
            "contract_id": contract_id,
            "section_id": section["section_id"],
            "title": section["title"],
            "content": section["content"],
            "order": section["order"],
            "start_position": section.get("start_position", 0),
            "end_position": section.get("end_position", 0),
            "section_type": section["section_type"],
            "confidence": section["confidence"]
        })
    

    
    def get_sections_ordered(self, contract_id: str) -> List[Dict[str, Any]]:
        """Retrieve sections in correct order"""
        query = """
        MATCH (c:Contract {file_id: $contract_id})-[r:HAS_SECTION]->(s:Section)
        RETURN s.section_id as section_id,
               s.title as title,
               s.content as content,
               s.order as order,
               s.start_position as start_position,
               s.end_position as end_position,
               s.section_type as section_type,
               s.confidence as confidence
        ORDER BY s.order ASC
        """
        
        result = self.repository.graph.query(query, {"contract_id": contract_id})
        return [dict(row) for row in result]
    
    def get_section_count(self, contract_id: str) -> int:
        """Get total section count for contract"""
        query = """
        MATCH (c:Contract {file_id: $contract_id})-[:HAS_SECTION]->(s:Section)
        RETURN count(s) as section_count
        """
        
        result = self.repository.graph.query(query, {"contract_id": contract_id})
        return result[0]["section_count"] if result else 0