"""
Database schema updates for Phase 2 and Phase 3 features
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.infrastructure.contract_repository import Neo4jContractRepository
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class Phase2Phase3SchemaMigration:
    """Database schema migration for Phase 2 and Phase 3 features"""
    
    def __init__(self):
        self.repository = Neo4jContractRepository()
    
    def migrate_schema(self):
        """Apply all Phase 2 and Phase 3 schema changes"""
        try:
            self._add_cuad_analysis_fields()
            self._create_feedback_indexes()
            self._add_performance_tracking()
            logger.info("Phase 2/3 schema migration completed successfully")
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            raise
    
    def _add_cuad_analysis_fields(self):
        """Add CUAD analysis fields to Contract nodes"""
        queries = [
            # Add CUAD analysis status fields
            """
            MATCH (c:Contract)
            SET c.cuad_analysis_status = COALESCE(c.cuad_analysis_status, 'pending'),
                c.deviation_count = COALESCE(c.deviation_count, 0),
                c.jurisdiction_detected = COALESCE(c.jurisdiction_detected, 'unknown'),
                c.industry_detected = COALESCE(c.industry_detected, 'general'),
                c.precedent_matches = COALESCE(c.precedent_matches, 0),
                c.semantic_analysis_enabled = COALESCE(c.semantic_analysis_enabled, true),
                c.cache_enabled = COALESCE(c.cache_enabled, true),
                c.performance_optimized = COALESCE(c.performance_optimized, true)
            """,
            
            # Create indexes for performance
            "CREATE INDEX contract_cuad_status IF NOT EXISTS FOR (c:Contract) ON (c.cuad_analysis_status)",
            "CREATE INDEX contract_jurisdiction IF NOT EXISTS FOR (c:Contract) ON (c.jurisdiction_detected)",
            "CREATE INDEX contract_industry IF NOT EXISTS FOR (c:Contract) ON (c.industry_detected)",
        ]
        
        for query in queries:
            try:
                self.repository.graph.query(query)
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Query failed (may already exist): {e}")
    
    def _create_feedback_indexes(self):
        """Create indexes for feedback and learning system"""
        queries = [
            # Create LegalDecision node constraints and indexes
            "CREATE CONSTRAINT legal_decision_id IF NOT EXISTS FOR (d:LegalDecision) REQUIRE d.decision_id IS UNIQUE",
            "CREATE INDEX legal_decision_contract IF NOT EXISTS FOR (d:LegalDecision) ON (d.contract_id)",
            "CREATE INDEX legal_decision_clause_type IF NOT EXISTS FOR (d:LegalDecision) ON (d.clause_type)",
            "CREATE INDEX legal_decision_timestamp IF NOT EXISTS FOR (d:LegalDecision) ON (d.decision_timestamp)",
            
            # Create LearnedPattern nodes for pattern storage
            """
            MERGE (p:LearnedPattern {pattern_id: 'sample_pattern'})
            SET p.pattern_type = 'approval',
                p.clause_type = 'payment',
                p.confidence = 0.8,
                p.usage_count = 0,
                p.success_rate = 0.0,
                p.created_at = datetime()
            """,
            
            "CREATE INDEX learned_pattern_type IF NOT EXISTS FOR (p:LearnedPattern) ON (p.pattern_type)",
            "CREATE INDEX learned_pattern_clause IF NOT EXISTS FOR (p:LearnedPattern) ON (p.clause_type)",
        ]
        
        for query in queries:
            try:
                self.repository.graph.query(query)
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Query failed (may already exist): {e}")
    
    def _add_performance_tracking(self):
        """Add performance tracking fields"""
        queries = [
            # Add performance metrics to contracts
            """
            MATCH (c:Contract)
            SET c.analysis_duration_ms = COALESCE(c.analysis_duration_ms, 0),
                c.cache_hit_rate = COALESCE(c.cache_hit_rate, 0.0),
                c.phase_used = COALESCE(c.phase_used, 'phase1'),
                c.performance_score = COALESCE(c.performance_score, 0.0),
                c.last_optimized = COALESCE(c.last_optimized, datetime())
            """,
            
            # Create PerformanceMetric nodes for detailed tracking
            """
            MERGE (pm:PerformanceMetric {metric_id: 'sample_metric'})
            SET pm.operation = 'cuad_analysis',
                pm.duration_ms = 1000.0,
                pm.success = true,
                pm.timestamp = datetime(),
                pm.phase_used = 'phase3'
            """,
            
            "CREATE INDEX performance_operation IF NOT EXISTS FOR (pm:PerformanceMetric) ON (pm.operation)",
            "CREATE INDEX performance_timestamp IF NOT EXISTS FOR (pm:PerformanceMetric) ON (pm.timestamp)",
        ]
        
        for query in queries:
            try:
                self.repository.graph.query(query)
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Query failed (may already exist): {e}")
    
    def verify_migration(self) -> bool:
        """Verify that migration was successful"""
        try:
            # Check if new fields exist
            result = self.repository.graph.query("""
                MATCH (c:Contract)
                RETURN c.cuad_analysis_status as status,
                       c.performance_optimized as optimized,
                       c.cache_enabled as cached
                LIMIT 1
            """)
            
            if result and len(result) > 0:
                contract = result[0]
                has_cuad_fields = contract.get('status') is not None
                has_performance_fields = contract.get('optimized') is not None
                
                logger.info(f"Migration verification: CUAD fields={has_cuad_fields}, Performance fields={has_performance_fields}")
                return has_cuad_fields and has_performance_fields
            
            return False
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return False

def run_migration():
    """Run the Phase 2/3 schema migration"""
    migration = Phase2Phase3SchemaMigration()
    migration.migrate_schema()
    
    if migration.verify_migration():
        print("✅ Phase 2/3 schema migration completed successfully")
    else:
        print("❌ Phase 2/3 schema migration verification failed")

if __name__ == "__main__":
    run_migration()