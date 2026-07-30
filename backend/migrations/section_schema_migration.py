"""
Section Schema Migration
Creates Section nodes and HAS_SECTION relationships with order preservation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.infrastructure.contract_repository import Neo4jContractRepository
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class SectionSchemaMigration:
    """Migration for section storage with order preservation"""
    
    def __init__(self):
        self.repository = Neo4jContractRepository()
    
    def migrate(self):
        """Apply section schema migration"""
        try:
            self._create_section_indexes()
            self._create_sample_sections()
            logger.info("Section schema migration completed")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def _create_section_indexes(self):
        """Create indexes for Section nodes and relationships"""
        queries = [
            "CREATE INDEX section_order IF NOT EXISTS FOR (s:Section) ON (s.order)",
            "CREATE INDEX section_position IF NOT EXISTS FOR (s:Section) ON (s.start_position)",
            "CREATE INDEX section_contract IF NOT EXISTS FOR (s:Section) ON (s.contract_id)",
            "CREATE INDEX section_tenant IF NOT EXISTS FOR (s:Section) ON (s.tenant_id)",
            "CREATE INDEX section_type IF NOT EXISTS FOR (s:Section) ON (s.section_type)"
        ]
        
        for query in queries:
            try:
                self.repository.graph.query(query)
                print(f"✅ Created index: {query.split('FOR')[0].split('INDEX')[1].strip()}")
            except Exception as e:
                print(f"⚠️ Index may already exist: {e}")
    
    def _create_sample_sections(self):
        """Create sample sections for testing"""
        # Get a sample contract
        contract_query = "MATCH (c:Contract) RETURN c.file_id as contract_id LIMIT 1"
        contract_result = self.repository.graph.query(contract_query)
        
        if not contract_result:
            print("⚠️ No contracts found for sample sections")
            return
        
        contract_id = contract_result[0]["contract_id"]
        
        # Create sample sections with order
        sections = [
            {
                "title": "Definitions",
                "content": "Sample definitions section content...",
                "order": 0,
                "start_position": 100,
                "end_position": 500,
                "section_type": "definitions"
            },
            {
                "title": "Terms and Conditions", 
                "content": "Sample terms section content...",
                "order": 1,
                "start_position": 501,
                "end_position": 1200,
                "section_type": "terms"
            },
            {
                "title": "Termination",
                "content": "Sample termination section content...",
                "order": 2,
                "start_position": 1201,
                "end_position": 1800,
                "section_type": "termination"
            }
        ]
        
        for section in sections:
            section_query = """
            MATCH (c:Contract {file_id: $contract_id})
            CREATE (s:Section {
                section_id: $section_id,
                title: $title,
                content: $content,
                order: $order,
                start_position: $start_position,
                end_position: $end_position,
                section_type: $section_type,
                confidence: 0.95,
                contract_id: $contract_id,
                tenant_id: c.tenant_id,
                created_at: datetime()
            })
            CREATE (c)-[:HAS_SECTION {order: $order, sequence: $order}]->(s)
            RETURN s.section_id as section_id
            """
            
            try:
                result = self.repository.graph.query(section_query, {
                    "contract_id": contract_id,
                    "section_id": f"{contract_id}_section_{section['order']:03d}",
                    "title": section["title"],
                    "content": section["content"],
                    "order": section["order"],
                    "start_position": section["start_position"],
                    "end_position": section["end_position"],
                    "section_type": section["section_type"]
                })
                
                print(f"✅ Created section: {section['title']} (order: {section['order']})")
                
            except Exception as e:
                print(f"⚠️ Section creation failed: {e}")
    
    def verify_migration(self):
        """Verify migration was successful"""
        try:
            # Check section count
            section_result = self.repository.graph.query("MATCH (s:Section) RETURN count(s) as count")
            section_count = section_result[0]["count"] if section_result else 0
            
            # Check relationship count
            rel_result = self.repository.graph.query("MATCH ()-[r:HAS_SECTION]->() RETURN count(r) as count")
            rel_count = rel_result[0]["count"] if rel_result else 0
            
            # Check order preservation
            order_result = self.repository.graph.query("""
                MATCH (c:Contract)-[r:HAS_SECTION]->(s:Section)
                RETURN s.order as section_order, r.order as rel_order
                ORDER BY s.order ASC
                LIMIT 5
            """)
            
            print(f"✅ Migration verification:")
            print(f"   - Section nodes: {section_count}")
            print(f"   - HAS_SECTION relationships: {rel_count}")
            print(f"   - Order preservation: {len(order_result)} sections with order")
            
            if order_result:
                print("   - Sample orders:")
                for row in order_result:
                    print(f"     Section order: {row['section_order']}, Relationship order: {row['rel_order']}")
            
            return section_count > 0 and rel_count > 0
            
        except Exception as e:
            print(f"❌ Migration verification failed: {e}")
            return False

def run_migration():
    """Run the section schema migration"""
    migration = SectionSchemaMigration()
    migration.migrate()
    
    if migration.verify_migration():
        print("✅ Section schema migration completed successfully")
    else:
        print("❌ Migration verification failed")

if __name__ == "__main__":
    run_migration()