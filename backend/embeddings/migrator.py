from typing import List, Dict, Any
from langchain_neo4j import Neo4jGraph
from .orchestrator import EmbeddingOrchestrator
from .validator import EmbeddingValidator
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class EmbeddingMigrator:
    """Handles migration of existing contracts to multi-level embeddings"""
    
    def __init__(self):
        self.graph = Neo4jGraph(
            refresh_schema=False, 
            driver_config={"notifications_min_severity": "OFF"}
        )
        self.orchestrator = EmbeddingOrchestrator()
        self.validator = EmbeddingValidator()
    
    def migrate_existing_contracts(self, batch_size: int = 10) -> Dict[str, Any]:
        """Migrate existing contracts to multi-level embeddings"""
        logger.info("Starting migration of existing contracts...")
        
        # Get contracts that need migration
        contracts_to_migrate = self._get_contracts_needing_migration()
        logger.info(f"Found {len(contracts_to_migrate)} contracts to migrate")
        
        migration_stats = {
            "total_contracts": len(contracts_to_migrate),
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        # Process in batches
        for i in range(0, len(contracts_to_migrate), batch_size):
            batch = contracts_to_migrate[i:i + batch_size]
            
            for contract in batch:
                try:
                    self._migrate_single_contract(contract)
                    migration_stats["successful"] += 1
                    logger.info(f"Successfully migrated contract {contract['file_id']}")
                    
                except Exception as e:
                    migration_stats["failed"] += 1
                    error_msg = f"Failed to migrate contract {contract['file_id']}: {str(e)}"
                    migration_stats["errors"].append(error_msg)
                    logger.error(error_msg)
                
                migration_stats["processed"] += 1
        
        logger.info(f"Migration completed. Success: {migration_stats['successful']}, Failed: {migration_stats['failed']}")
        return migration_stats
    
    def _get_contracts_needing_migration(self) -> List[Dict[str, Any]]:
        """Get contracts that need multi-level embedding migration"""
        query = """
        MATCH (c:Contract)
        WHERE c.document_embedding IS NULL OR c.summary_embedding IS NULL
        RETURN c.file_id as file_id, c.summary as summary
        LIMIT 100
        """
        
        result = self.graph.query(query)
        return [dict(record) for record in result]
    
    def _migrate_single_contract(self, contract: Dict[str, Any]):
        """Migrate a single contract to multi-level embeddings"""
        file_id = contract["file_id"]
        summary = contract.get("summary", "")
        
        if not summary:
            logger.warning(f"Contract {file_id} has no summary, skipping migration")
            return
        
        # Process with orchestrator
        processing_result = self.orchestrator.process_document(
            content=summary,
            metadata={"file_id": file_id, "migration": True}
        )
        
        # Validate results
        all_embeddings = (
            processing_result.document_embeddings + 
            processing_result.clause_embeddings + 
            processing_result.relationship_embeddings
        )
        
        validation_result = self.validator.validate_embeddings(all_embeddings)
        
        if not validation_result.is_valid:
            raise Exception(f"Validation failed: {validation_result.errors}")
        
        # Store embeddings in Neo4j
        self._store_migrated_embeddings(file_id, processing_result)
    
    def _store_migrated_embeddings(self, file_id: str, processing_result):
        """Store migrated embeddings in Neo4j"""
        
        # Update contract with new embeddings
        for doc_embedding in processing_result.document_embeddings:
            if doc_embedding.metadata.get("level") == "document":
                self.graph.query("""
                    MATCH (c:Contract {file_id: $file_id})
                    SET c.document_embedding = $embedding,
                        c.summary_embedding = $embedding
                """, {
                    "file_id": file_id,
                    "embedding": doc_embedding.embedding
                })
            
            elif doc_embedding.metadata.get("level") == "section":
                # Create section node
                section_id = f"{file_id}_section_{doc_embedding.metadata.get('section_index', 0)}"
                self.graph.query("""
                    MATCH (c:Contract {file_id: $file_id})
                    MERGE (s:Section {id: $section_id})
                    SET s.section_type = $section_type,
                        s.content = $content,
                        s.embedding = $embedding,
                        s.order = $order
                    MERGE (c)-[:HAS_SECTION]->(s)
                """, {
                    "file_id": file_id,
                    "section_id": section_id,
                    "section_type": doc_embedding.metadata.get("section_type", "general"),
                    "content": doc_embedding.content,
                    "embedding": doc_embedding.embedding,
                    "order": doc_embedding.metadata.get("section_index", 0)
                })
        
        # Store clause embeddings
        for clause_embedding in processing_result.clause_embeddings:
            clause_id = f"{file_id}_clause_{clause_embedding.metadata.get('start_position', 0)}"
            self.graph.query("""
                MATCH (c:Contract {file_id: $file_id})
                MERGE (cl:Clause {id: $clause_id})
                SET cl.clause_type = $clause_type,
                    cl.content = $content,
                    cl.embedding = $embedding,
                    cl.confidence = $confidence,
                    cl.start_position = $start_position,
                    cl.end_position = $end_position
                MERGE (c)-[:CONTAINS_CLAUSE]->(cl)
            """, {
                "file_id": file_id,
                "clause_id": clause_id,
                "clause_type": clause_embedding.metadata.get("clause_type", "unknown"),
                "content": clause_embedding.content,
                "embedding": clause_embedding.embedding,
                "confidence": clause_embedding.metadata.get("confidence", 0.0),
                "start_position": clause_embedding.metadata.get("start_position", 0),
                "end_position": clause_embedding.metadata.get("end_position", 0)
            })
        
        # Store relationship embeddings
        for rel_embedding in processing_result.relationship_embeddings:
            if rel_embedding.metadata.get("relationship_type") == "PARTY_TO":
                party_name = rel_embedding.metadata.get("party_name", "")
                if party_name:
                    self.graph.query("""
                        MATCH (c:Contract {file_id: $file_id})
                        MATCH (c)<-[r:PARTY_TO]-(p:Party {name: $party_name})
                        SET r.embedding = $embedding,
                            r.context = $context
                    """, {
                        "file_id": file_id,
                        "party_name": party_name,
                        "embedding": rel_embedding.embedding,
                        "context": rel_embedding.content
                    })
    
    def rollback_migration(self, file_ids: List[str] = None):
        """Rollback migration for specific contracts or all"""
        logger.info("Starting migration rollback...")
        
        if file_ids:
            # Rollback specific contracts
            for file_id in file_ids:
                self._rollback_single_contract(file_id)
        else:
            # Rollback all migrated contracts
            self.graph.query("""
                MATCH (c:Contract)
                WHERE c.document_embedding IS NOT NULL
                REMOVE c.document_embedding, c.summary_embedding
            """)
            
            # Remove all sections and clauses
            self.graph.query("MATCH (s:Section) DETACH DELETE s")
            self.graph.query("MATCH (cl:Clause) DETACH DELETE cl")
            
            # Remove relationship embeddings
            self.graph.query("""
                MATCH ()-[r:PARTY_TO]->()
                REMOVE r.embedding, r.context
            """)
        
        logger.info("Migration rollback completed")
    
    def _rollback_single_contract(self, file_id: str):
        """Rollback migration for a single contract"""
        # Remove new embedding properties
        self.graph.query("""
            MATCH (c:Contract {file_id: $file_id})
            REMOVE c.document_embedding, c.summary_embedding
        """, {"file_id": file_id})
        
        # Remove sections
        self.graph.query("""
            MATCH (c:Contract {file_id: $file_id})-[:HAS_SECTION]->(s:Section)
            DETACH DELETE s
        """, {"file_id": file_id})
        
        # Remove clauses
        self.graph.query("""
            MATCH (c:Contract {file_id: $file_id})-[:CONTAINS_CLAUSE]->(cl:Clause)
            DETACH DELETE cl
        """, {"file_id": file_id})
        
        # Remove relationship embeddings
        self.graph.query("""
            MATCH (c:Contract {file_id: $file_id})<-[r:PARTY_TO]-()
            REMOVE r.embedding, r.context
        """, {"file_id": file_id})