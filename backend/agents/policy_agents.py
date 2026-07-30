"""Policy agents extending existing infrastructure."""

import uuid
from typing import Dict, Any, List
from backend.agents.supervisor.interfaces import IAgent, AgentContext, AgentResult
from backend.infrastructure.chunking.factory import ChunkingFactory
from backend.infrastructure.chunking.storage_service import ChunkingStorageService
from backend.shared.utils.contract_search_tool import graph
from backend.domain.policies.entities import PolicyDocument, PolicyRule, PolicyViolation


class PolicyChunkingAgent(IAgent):
    """Reuses existing chunking infrastructure for policy documents."""
    
    def __init__(self):
        self.chunking_factory = ChunkingFactory()
        self.storage_service = ChunkingStorageService()
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute policy document chunking."""
        try:
            policy_text = context.input_data['policy_text']
            tenant_id = context.input_data['tenant_id']
            policy_name = context.input_data.get('policy_name', 'Unknown Policy')
            
            # Use existing policy chunking strategy
            strategy = self.chunking_factory.create_strategy('policy')
            chunks = strategy.chunk_document(policy_text, {'document_type': 'policy'})
            
            # Store using existing infrastructure
            document_id = f"policy_{tenant_id}_{uuid.uuid4().hex[:8]}"
            
            # Use existing async storage (convert to sync for now)
            import asyncio
            result = asyncio.run(self.storage_service.store_chunks(
                document_id, chunks, {'policy_name': policy_name, 'tenant_id': tenant_id}
            ))
            
            return AgentResult(
                status='success',
                data={
                    'document_id': document_id,
                    'chunks_created': len(chunks),
                    'storage_result': result
                },
                confidence=0.9
            )
            
        except Exception as e:
            return AgentResult(
                status='error',
                data={'error': str(e)},
                confidence=0.0
            )
    
    def get_capabilities(self) -> List[str]:
        return ['policy_chunking', 'document_processing', 'rule_extraction']


class PolicyExtractionAgent(IAgent):
    """Extends existing clause extraction for policy rules."""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Extract policy rules from chunks."""
        try:
            document_id = context.input_data['document_id']
            tenant_id = context.input_data['tenant_id']
            
            # Get chunks using existing storage service
            storage_service = ChunkingStorageService()
            chunks = asyncio.run(storage_service.get_chunks(document_id))
            
            # Extract policy rules from chunks
            policy_rules = []
            for chunk in chunks:
                if chunk.get('chunk_type') == 'policy_rule':
                    rule = PolicyRule(
                        id=f"rule_{uuid.uuid4().hex[:8]}",
                        rule_text=chunk['content'],
                        rule_type=chunk.get('rule_type', 'general'),
                        applies_to=chunk.get('applies_to', ['general']),
                        severity=chunk.get('severity', 'MEDIUM'),
                        section_reference=chunk.get('section_title', 'Unknown'),
                        exceptions=[]
                    )
                    policy_rules.append(rule)
            
            # Store rules in Neo4j using existing graph connection
            self._store_policy_rules(policy_rules, document_id, tenant_id)
            
            return AgentResult(
                status='success',
                data={
                    'rules_extracted': len(policy_rules),
                    'policy_rules': [rule.__dict__ for rule in policy_rules]
                },
                confidence=0.85
            )
            
        except Exception as e:
            return AgentResult(
                status='error',
                data={'error': str(e)},
                confidence=0.0
            )
    
    def _store_policy_rules(self, rules: List[PolicyRule], document_id: str, tenant_id: str):
        """Store policy rules in Neo4j using existing patterns."""
        for rule in rules:
            query = """
            MERGE (p:PolicyDocument {id: $document_id})
            SET p.tenant_id = $tenant_id
            
            CREATE (r:PolicyRule {
                id: $rule_id,
                rule_text: $rule_text,
                rule_type: $rule_type,
                applies_to: $applies_to,
                severity: $severity,
                section_reference: $section_reference,
                created_at: datetime()
            })
            
            CREATE (p)-[:HAS_RULE]->(r)
            """
            
            graph.query(query, {
                'document_id': document_id,
                'tenant_id': tenant_id,
                'rule_id': rule.id,
                'rule_text': rule.rule_text,
                'rule_type': rule.rule_type,
                'applies_to': rule.applies_to,
                'severity': rule.severity,
                'section_reference': rule.section_reference
            })
    
    def get_capabilities(self) -> List[str]:
        return ['policy_extraction', 'rule_identification', 'legal_analysis']


class PolicyComplianceAgent(IAgent):
    """Extends existing policy compliance for dynamic policy loading."""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Check contract compliance against stored policies."""
        try:
            tenant_id = context.input_data['tenant_id']
            contract_clauses = context.input_data['clauses']
            contract_type = context.input_data.get('contract_type', 'general')
            
            # Load policies from database
            policies = self._load_tenant_policies(tenant_id, contract_type)
            
            # Check compliance using existing patterns
            violations = []
            for clause in contract_clauses:
                clause_violations = self._check_clause_compliance(clause, policies)
                violations.extend(clause_violations)
            
            return AgentResult(
                status='success',
                data={
                    'violations_found': len(violations),
                    'violations': [v.__dict__ for v in violations],
                    'policies_checked': len(policies)
                },
                confidence=0.9
            )
            
        except Exception as e:
            return AgentResult(
                status='error',
                data={'error': str(e)},
                confidence=0.0
            )
    
    def _load_tenant_policies(self, tenant_id: str, contract_type: str = None) -> List[PolicyRule]:
        """Load policies from Neo4j using existing patterns."""
        query = """
        MATCH (p:PolicyDocument {tenant_id: $tenant_id})-[:HAS_RULE]->(r:PolicyRule)
        WHERE $contract_type IN r.applies_to OR 'general' IN r.applies_to
        RETURN r.id as id, r.rule_text as rule_text, r.rule_type as rule_type,
               r.applies_to as applies_to, r.severity as severity,
               r.section_reference as section_reference
        """
        
        result = graph.query(query, {
            'tenant_id': tenant_id,
            'contract_type': contract_type or 'general'
        })
        
        policies = []
        for record in result:
            policy = PolicyRule(
                id=record['id'],
                rule_text=record['rule_text'],
                rule_type=record['rule_type'],
                applies_to=record['applies_to'],
                severity=record['severity'],
                section_reference=record['section_reference']
            )
            policies.append(policy)
        
        return policies
    
    def _check_clause_compliance(self, clause: Dict[str, Any], policies: List[PolicyRule]) -> List[PolicyViolation]:
        """Check single clause against policies."""
        violations = []
        clause_content = clause.get('content', '').lower()
        clause_type = clause.get('type', 'general')
        
        for policy in policies:
            if clause_type not in policy.applies_to and 'general' not in policy.applies_to:
                continue
            
            violation = self._evaluate_policy_rule(clause, policy)
            if violation:
                violations.append(violation)
        
        return violations
    
    def _evaluate_policy_rule(self, clause: Dict[str, Any], policy: PolicyRule) -> PolicyViolation:
        """Evaluate clause against specific policy rule."""
        clause_content = clause.get('content', '').lower()
        rule_text = policy.rule_text.lower()
        
        # Simple rule evaluation logic (can be enhanced with LLM)
        if policy.rule_type == 'prohibited':
            # Check for prohibited terms
            prohibited_terms = ['unlimited liability', 'immediate termination', 'no notice']
            for term in prohibited_terms:
                if term in clause_content and term in rule_text:
                    return PolicyViolation(
                        policy_rule_id=policy.id,
                        clause_content=clause.get('content', ''),
                        violation_type='prohibited_term',
                        severity=policy.severity,
                        message=f"Clause contains prohibited term: {term}",
                        recommendation=f"Remove or modify '{term}' to comply with policy",
                        confidence=0.8
                    )
        
        elif policy.rule_type == 'mandatory':
            # Check for missing mandatory terms
            mandatory_terms = ['liability cap', 'notice period', 'governing law']
            for term in mandatory_terms:
                if term in rule_text and term not in clause_content:
                    return PolicyViolation(
                        policy_rule_id=policy.id,
                        clause_content=clause.get('content', ''),
                        violation_type='missing_mandatory',
                        severity=policy.severity,
                        message=f"Clause missing mandatory term: {term}",
                        recommendation=f"Add '{term}' to comply with policy",
                        confidence=0.7
                    )
        
        return None
    
    def get_capabilities(self) -> List[str]:
        return ['policy_compliance', 'violation_detection', 'risk_assessment']