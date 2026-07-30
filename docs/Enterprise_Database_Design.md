# Enterprise Database Design for Legal Document Processing System

## 1. Data Versioning & Temporal Tables

### **PostgreSQL Temporal Tables**
```sql
-- Contract version history with temporal support
contracts_history (
    id UUID,
    version_number INTEGER,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    changed_by UUID,
    change_reason TEXT,
    -- all original contract fields
    CONSTRAINT temporal_consistency CHECK (valid_from < valid_to)
);

-- Trigger for automatic versioning
CREATE OR REPLACE FUNCTION create_contract_version()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO contracts_history 
    SELECT OLD.*, OLD.version_number, OLD.updated_at, NOW(), NEW.updated_by, NEW.change_reason;
    NEW.version_number = OLD.version_number + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### **MongoDB Document Versioning**
```json
{
  "contract_id": "uuid",
  "version": 3,
  "parent_version": 2,
  "version_metadata": {
    "created_at": "timestamp",
    "created_by": "user_id",
    "change_type": "amendment|correction|update",
    "approval_status": "pending|approved|rejected",
    "diff_summary": "summary of changes"
  },
  "content": "versioned_chunk_content"
}
```

## 2. Database Partitioning & Sharding

### **Time-Based Partitioning**
```sql
-- Partition audit tables by time for performance
CREATE TABLE processing_audit (
    id UUID,
    contract_id UUID,
    created_at TIMESTAMP,
    operation VARCHAR(50)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE audit_2024_01 PARTITION OF processing_audit
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### **Hash Partitioning for Scale**
```sql
-- Distribute contracts across multiple partitions
CREATE TABLE contracts (
    id UUID PRIMARY KEY,
    file_name VARCHAR(255),
    -- other fields
) PARTITION BY HASH (id);

-- Create hash partitions
CREATE TABLE contracts_0 PARTITION OF contracts FOR VALUES WITH (modulus 4, remainder 0);
CREATE TABLE contracts_1 PARTITION OF contracts FOR VALUES WITH (modulus 4, remainder 1);
```

## 3. Data Lineage & Provenance

### **Neo4j Data Lineage Tracking**
```cypher
// Complete data lineage from source to final output
(OriginalDocument)-[:PROCESSED_BY]->(AIModel)-[:GENERATED]->(ExtractedData)
(ExtractedData)-[:VALIDATED_BY]->(Human)-[:APPROVED_BY]->(LegalExpert)
(ContractV1)-[:AMENDED_TO]->(ContractV2)-[:SUPERSEDES]->(ContractV1)
(Chunk)-[:DERIVED_FROM]->(Section)-[:PART_OF]->(Document)
(Embedding)-[:REPRESENTS]->(Chunk)-[:VALIDATED_AT]->(Timestamp)
```

### **Provenance Metadata**
```json
{
  "data_lineage": {
    "source_document": "original_pdf_hash",
    "processing_pipeline": ["ocr", "chunking", "embedding", "validation"],
    "model_versions": {
      "ocr_model": "v2.1.0",
      "embedding_model": "text-embedding-004",
      "validation_model": "legal-classifier-v1.2"
    },
    "human_reviewers": ["user_123", "legal_expert_456"],
    "confidence_scores": [0.98, 0.95, 0.97]
  }
}
```

## 4. Database Security & Encryption

### **Column-Level Encryption**
```sql
-- Encrypt sensitive contract content
CREATE TABLE contracts (
    id UUID PRIMARY KEY,
    file_name VARCHAR(255),
    encrypted_content BYTEA, -- AES-256 encrypted full text
    content_hash VARCHAR(64), -- SHA-256 for integrity verification
    encryption_key_id UUID REFERENCES encryption_keys(id),
    data_classification VARCHAR(20) CHECK (data_classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','RESTRICTED'))
);

-- Encryption key management
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY,
    key_material BYTEA, -- Encrypted with master key
    algorithm VARCHAR(50) DEFAULT 'AES-256-GCM',
    created_at TIMESTAMP DEFAULT NOW(),
    rotated_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE'
);
```

### **Row-Level Security (RLS)**
```sql
-- Enable RLS for multi-tenant isolation
ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;

-- Tenant-based access policy
CREATE POLICY contract_access_policy ON contracts
    FOR ALL TO application_role
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- Role-based access for different user types
CREATE POLICY legal_team_access ON contracts
    FOR ALL TO legal_role
    USING (data_classification IN ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL'));
```

## 5. Database Backup & Point-in-Time Recovery

### **PostgreSQL PITR Configuration**
```sql
-- WAL configuration for PITR
archive_mode = on
archive_command = 'cp %p /backup/archive/%f'
wal_level = replica
max_wal_senders = 3
checkpoint_completion_target = 0.9

-- Backup retention policies
-- FULL_BACKUP: Daily at 2 AM, retain 30 days
-- INCREMENTAL_BACKUP: Every 4 hours, retain 7 days  
-- WAL_ARCHIVING: Continuous, retain 7 days
```

### **Cross-Database Backup Strategy**
```yaml
backup_schedule:
  postgresql:
    full_backup: "0 2 * * *"  # Daily at 2 AM
    incremental: "0 */4 * * *"  # Every 4 hours
    retention: 30 days
  
  neo4j:
    backup_type: "incremental"
    schedule: "0 3 * * *"  # Daily at 3 AM
    retention: 14 days
  
  mongodb:
    backup_type: "replica_set"
    schedule: "0 1 * * *"  # Daily at 1 AM
    retention: 21 days
```

## 6. Database Performance & Indexing

### **Optimized Indexing Strategy**
```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_contracts_date_type ON contracts (effective_date, contract_type);
CREATE INDEX idx_contracts_tenant_status ON contracts (tenant_id, processing_status);
CREATE INDEX idx_chunks_contract_level ON chunks (contract_id, chunk_level);

-- Partial indexes for active data
CREATE INDEX idx_active_contracts ON contracts (id) 
    WHERE end_date > CURRENT_DATE OR end_date IS NULL;

-- GIN indexes for JSONB queries
CREATE INDEX idx_metadata_gin ON contract_metadata USING GIN (metadata_json);

-- Vector similarity indexes
CREATE INDEX ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
```

### **Query Optimization**
```sql
-- Materialized views for complex aggregations
CREATE MATERIALIZED VIEW contract_analytics AS
SELECT 
    contract_type,
    COUNT(*) as total_contracts,
    AVG(total_amount) as avg_amount,
    DATE_TRUNC('month', effective_date) as month
FROM contracts 
GROUP BY contract_type, DATE_TRUNC('month', effective_date);

-- Refresh strategy
CREATE OR REPLACE FUNCTION refresh_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY contract_analytics;
END;
$$ LANGUAGE plpgsql;
```

## 7. Database Connection Management

### **Connection Pooling Configuration**
```yaml
database_connections:
  postgresql:
    primary:
      host: primary-db.internal
      port: 5432
      max_connections: 100
      pool_size: 20
    
    read_replicas:
      - host: replica1-db.internal
        weight: 50
      - host: replica2-db.internal  
        weight: 50
    
    connection_pool:
      min_size: 10
      max_size: 50
      idle_timeout: 300s
      max_lifetime: 3600s

  mongodb:
    cluster_uri: "mongodb+srv://cluster.mongodb.net"
    max_pool_size: 50
    min_pool_size: 5
    max_idle_time: 300s
```

## 8. Database Monitoring & Performance

### **Performance Monitoring Views**
```sql
-- Slow query identification
CREATE VIEW slow_queries AS
SELECT 
    query,
    mean_time,
    calls,
    total_time,
    (total_time / calls) as avg_time_per_call
FROM pg_stat_statements
WHERE mean_time > 1000  -- queries taking > 1 second
ORDER BY mean_time DESC;

-- Lock contention monitoring
CREATE VIEW lock_contention AS
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype;
```

### **Health Check Metrics**
```sql
-- Database health monitoring
CREATE OR REPLACE FUNCTION database_health_check()
RETURNS TABLE(
    metric_name TEXT,
    metric_value NUMERIC,
    status TEXT,
    threshold NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'connection_count'::TEXT,
        (SELECT count(*) FROM pg_stat_activity)::NUMERIC,
        CASE WHEN (SELECT count(*) FROM pg_stat_activity) > 80 THEN 'WARNING' ELSE 'OK' END,
        100::NUMERIC
    UNION ALL
    SELECT 
        'replication_lag'::TEXT,
        EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))::NUMERIC,
        CASE WHEN EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) > 60 THEN 'CRITICAL' ELSE 'OK' END,
        60::NUMERIC;
END;
$$ LANGUAGE plpgsql;
```

## 9. Data Lifecycle Management

### **Automated Data Archival**
```sql
-- Archive old contracts to separate partition
CREATE TABLE contracts_archive (
    LIKE contracts INCLUDING ALL
) PARTITION BY RANGE (archived_date);

-- Archival procedure
CREATE OR REPLACE FUNCTION archive_old_contracts()
RETURNS void AS $$
BEGIN
    -- Move contracts older than 7 years to archive
    WITH archived_contracts AS (
        DELETE FROM contracts 
        WHERE created_at < NOW() - INTERVAL '7 years'
        RETURNING *
    )
    INSERT INTO contracts_archive 
    SELECT *, NOW() as archived_date FROM archived_contracts;
    
    -- Update statistics
    ANALYZE contracts;
    ANALYZE contracts_archive;
END;
$$ LANGUAGE plpgsql;
```

### **Data Retention Policies**
```sql
-- Automated cleanup procedures
CREATE EXTENSION pg_cron;

-- Schedule regular maintenance tasks
SELECT cron.schedule('archive-contracts', '0 2 1 * *', 'SELECT archive_old_contracts();');
SELECT cron.schedule('cleanup-audit-logs', '0 3 * * 0', 'DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL ''2 years'';');
SELECT cron.schedule('vacuum-analyze', '0 1 * * *', 'VACUUM ANALYZE;');
```

## 10. Database Transactions & ACID Compliance

### **Distributed Transaction Management**
```sql
-- Saga pattern for cross-database consistency
CREATE TABLE transaction_saga (
    saga_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    saga_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'STARTED',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB
);

CREATE TABLE saga_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    saga_id UUID REFERENCES transaction_saga(saga_id),
    step_number INTEGER NOT NULL,
    service_name VARCHAR(50) NOT NULL,
    operation TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    compensation_data JSONB,
    executed_at TIMESTAMP,
    UNIQUE(saga_id, step_number)
);
```

### **Optimistic Locking**
```sql
-- Version-based optimistic locking
ALTER TABLE contracts ADD COLUMN version_lock INTEGER DEFAULT 1;

-- Update with version check
UPDATE contracts 
SET content = ?, version_lock = version_lock + 1
WHERE id = ? AND version_lock = ?;
```

## 11. Database Constraints & Validation

### **Business Rule Constraints**
```sql
-- Date validation constraints
ALTER TABLE contracts ADD CONSTRAINT valid_date_range 
    CHECK (effective_date <= end_date OR end_date IS NULL);

ALTER TABLE contracts ADD CONSTRAINT future_effective_date
    CHECK (effective_date >= '2020-01-01');

-- Amount validation
ALTER TABLE contract_metadata ADD CONSTRAINT positive_amount
    CHECK (total_amount >= 0);

-- Status validation
ALTER TABLE contracts ADD CONSTRAINT valid_status
    CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'ARCHIVED'));
```

### **Cross-Database Referential Integrity**
```sql
-- Trigger to ensure chunk exists before creating embedding
CREATE OR REPLACE FUNCTION validate_chunk_exists()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if chunk exists in MongoDB (via API call or foreign data wrapper)
    IF NOT EXISTS (SELECT 1 FROM mongodb_chunks WHERE chunk_id = NEW.chunk_id) THEN
        RAISE EXCEPTION 'Referenced chunk % does not exist', NEW.chunk_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ensure_chunk_exists
    BEFORE INSERT ON embeddings
    FOR EACH ROW EXECUTE FUNCTION validate_chunk_exists();
```

## 12. Database Compression & Storage Optimization

### **Table Compression**
```sql
-- Enable compression for large tables
ALTER TABLE contracts_archive SET (compression = 'lz4');
ALTER TABLE audit_log SET (compression = 'zstd');

-- Columnar storage for analytics workloads
CREATE EXTENSION citus_columnar;

CREATE TABLE contract_analytics (
    contract_id UUID,
    processing_metrics JSONB,
    created_at TIMESTAMP
) USING columnar;
```

### **Storage Tiering**
```sql
-- Tablespace management for different storage tiers
CREATE TABLESPACE hot_storage LOCATION '/fast_ssd/postgresql';
CREATE TABLESPACE warm_storage LOCATION '/standard_ssd/postgresql';  
CREATE TABLESPACE cold_storage LOCATION '/hdd_storage/postgresql';

-- Move old data to appropriate storage tiers
ALTER TABLE contracts_archive SET TABLESPACE cold_storage;
ALTER TABLE recent_contracts SET TABLESPACE hot_storage;
```

## 13. Change Data Capture (CDC)

### **PostgreSQL Logical Replication**
```sql
-- Enable logical replication for CDC
ALTER SYSTEM SET wal_level = logical;
ALTER SYSTEM SET max_replication_slots = 10;

-- Create publication for contract changes
CREATE PUBLICATION contract_changes FOR TABLE contracts, contract_metadata;

-- Replication slot for external consumers
SELECT pg_create_logical_replication_slot('contract_cdc', 'pgoutput');
```

### **Debezium Configuration**
```json
{
  "name": "contract-cdc-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres-primary.internal",
    "database.port": "5432",
    "database.user": "debezium_user",
    "database.password": "secure_password",
    "database.dbname": "contracts_db",
    "database.server.name": "contract_server",
    "table.include.list": "public.contracts,public.contract_metadata",
    "plugin.name": "pgoutput",
    "transforms": "route",
    "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
    "transforms.route.regex": "([^.]+)\\.([^.]+)\\.([^.]+)",
    "transforms.route.replacement": "$3"
  }
}
```

## 14. Database Testing & Quality Assurance

### **Database Unit Tests**
```sql
-- Test framework for database functions
CREATE EXTENSION pgtap;

-- Test contract validation rules
CREATE OR REPLACE FUNCTION test_contract_validation()
RETURNS SETOF TEXT AS $$
BEGIN
    RETURN NEXT ok(
        (SELECT COUNT(*) FROM contracts WHERE effective_date > end_date) = 0,
        'No contracts should have effective_date after end_date'
    );
    
    RETURN NEXT throws_ok(
        'INSERT INTO contracts (effective_date, end_date) VALUES (''2024-12-31'', ''2024-01-01'')',
        'P0001',
        'Date validation should prevent invalid date ranges'
    );
END;
$$ LANGUAGE plpgsql;
```

### **Performance Regression Testing**
```sql
-- Baseline performance tracking
CREATE TABLE query_performance_baseline (
    query_hash VARCHAR(64) PRIMARY KEY,
    query_text TEXT,
    avg_execution_time INTERVAL,
    max_execution_time INTERVAL,
    baseline_date TIMESTAMP DEFAULT NOW(),
    environment VARCHAR(50)
);

-- Performance regression detection
CREATE OR REPLACE FUNCTION check_performance_regression()
RETURNS TABLE(
    query_hash VARCHAR(64),
    current_avg_time INTERVAL,
    baseline_avg_time INTERVAL,
    regression_factor NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.query_hash,
        s.mean_time * INTERVAL '1 millisecond' as current_avg_time,
        b.avg_execution_time as baseline_avg_time,
        (EXTRACT(EPOCH FROM s.mean_time * INTERVAL '1 millisecond') / 
         EXTRACT(EPOCH FROM b.avg_execution_time)) as regression_factor
    FROM query_performance_baseline b
    JOIN pg_stat_statements s ON s.queryid::text = b.query_hash
    WHERE (s.mean_time * INTERVAL '1 millisecond') > b.avg_execution_time * 1.5;
END;
$$ LANGUAGE plpgsql;
```

## 15. Database Documentation & Metadata

### **Self-Documenting Schema**
```sql
-- Comprehensive table and column documentation
COMMENT ON TABLE contracts IS 'Core contract metadata and document references for legal document processing';
COMMENT ON COLUMN contracts.risk_classification IS 'AI-determined risk level: LOW (standard templates), MEDIUM (custom terms), HIGH (complex agreements)';
COMMENT ON COLUMN contracts.processing_status IS 'Current processing state in the document pipeline';

-- Data dictionary table
CREATE TABLE data_catalog (
    schema_name VARCHAR(100),
    table_name VARCHAR(100),
    column_name VARCHAR(100),
    data_type VARCHAR(50),
    is_nullable BOOLEAN,
    business_definition TEXT,
    data_owner VARCHAR(100),
    sensitivity_level VARCHAR(20),
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (schema_name, table_name, column_name)
);
```

## 16. Database Compliance & Audit

### **Immutable Audit Trail**
```sql
-- Tamper-proof audit logging
CREATE TABLE audit_log (
    id UUID DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id UUID NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id UUID NOT NULL,
    session_id UUID,
    timestamp TIMESTAMP DEFAULT NOW(),
    client_ip INET,
    application_name VARCHAR(100),
    transaction_id BIGINT DEFAULT txid_current(),
    -- Cryptographic integrity
    record_hash VARCHAR(64) GENERATED ALWAYS AS (
        encode(sha256((id || table_name || operation || record_id || timestamp)::bytea), 'hex')
    ) STORED
) WITH (appendonly=true, orientation=column);

-- Prevent modifications to audit log
REVOKE UPDATE, DELETE ON audit_log FROM PUBLIC;
```

### **GDPR Compliance Features**
```sql
-- Data subject rights management
CREATE TABLE data_subject_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_type VARCHAR(20) CHECK (request_type IN ('ACCESS', 'RECTIFICATION', 'ERASURE', 'PORTABILITY')),
    subject_identifier VARCHAR(255) NOT NULL,
    request_date TIMESTAMP DEFAULT NOW(),
    completion_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'PENDING',
    request_details JSONB
);

-- Right to be forgotten implementation
CREATE OR REPLACE FUNCTION anonymize_personal_data(subject_id UUID)
RETURNS void AS $$
BEGIN
    -- Anonymize personal data while preserving business relationships
    UPDATE contracts SET 
        parties = jsonb_set(parties, '{personal_info}', '"[ANONYMIZED]"'::jsonb)
    WHERE parties @> jsonb_build_object('subject_id', subject_id);
    
    -- Log the anonymization
    INSERT INTO audit_log (table_name, operation, record_id, new_values, user_id)
    VALUES ('contracts', 'ANONYMIZE', subject_id, '{"action": "GDPR_ERASURE"}', current_user_id());
END;
$$ LANGUAGE plpgsql;
```

## Implementation Timeline & Considerations

### **Phase 1: Core Enterprise Features (Months 1-2)**
- Data versioning and temporal tables
- Basic partitioning and indexing
- Security and encryption implementation
- Backup and recovery setup

### **Phase 2: Advanced Features (Months 3-4)**
- Change data capture implementation
- Performance optimization and monitoring
- Cross-database transaction management
- Compliance and audit features

### **Phase 3: Optimization & Testing (Months 5-6)**
- Performance regression testing
- Load testing and capacity planning
- Documentation and training
- Production deployment preparation

### **Ongoing Maintenance**
- Regular performance monitoring and optimization
- Security updates and patch management
- Capacity planning and scaling
- Compliance audit preparation

This enterprise database design ensures the legal document processing system meets the highest standards for data integrity, performance, security, and regulatory compliance required in production environments.