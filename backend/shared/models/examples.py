"""
Usage examples for the shared models module.
Demonstrates integration with existing agent patterns and SOLID principles.
"""

from backend.shared.models import (
    AgentContext, AgentResult, AgentStatus,
    EnhancedAgentContext, CUADDeviation, DeviationType,
    JurisdictionInfo, PrecedentMatch
)


def example_basic_agent_usage():
    """Example of basic agent model usage following existing patterns"""
    
    # Create agent context (follows existing intelligence_state pattern)
    context = AgentContext(
        input_data={
            'tenant_id': 'company_123',
            'clauses': [
                {'clause_type': 'Payment Terms', 'content': 'Payment due in 60 days'},
                {'clause_type': 'Liability', 'content': 'Unlimited liability'}
            ],
            'contract_type': 'service_agreement'
        },
        contract_text="Sample contract text...",
        workflow_context={'workflow_id': 'wf_001'}
    )
    
    # Add clauses using existing pattern
    context.add_clause({
        'clause_type': 'Termination',
        'content': 'Immediate termination allowed',
        'risk_level': 'HIGH'
    })
    
    # Create successful result
    result = AgentResult.success(
        data={
            'violations_found': 2,
            'policies_checked': 5,
            'violations': [
                {'severity': 'CRITICAL', 'issue': 'Payment terms exceed policy'},
                {'severity': 'CRITICAL', 'issue': 'Unlimited liability exposure'}
            ]
        },
        execution_time=1.5
    )
    
    return context, result


def example_cuad_mitigation_usage():
    """Example of CUAD mitigation features using enhanced models"""
    
    # Create enhanced context for CUAD mitigation
    context = EnhancedAgentContext(
        input_data={'contract_text': 'Sample contract with merged clauses...'},
        company_policies={
            'payment_terms': {'max_days': 45},
            'liability_cap': {'multiplier': 1}
        }
    )
    
    # Add CUAD deviation (merged clause detection)
    deviation = CUADDeviation(
        deviation_type=DeviationType.MERGED_CLAUSE,
        description="Liability, indemnification, and insurance in one clause",
        location="Section 8.1",
        risk_level="MEDIUM",
        mitigation_strategy="Extract individual concepts for separate analysis",
        confidence_score=0.85
    )
    context.add_deviation(deviation)
    
    # Add jurisdiction information
    jurisdiction = JurisdictionInfo(
        country="United States",
        state_province="California",
        applicable_laws=["CCPA", "California Civil Code"],
        compliance_requirements={
            'data_protection': {'ccpa_compliance': True},
            'employment': {'at_will_employment': True}
        }
    )
    context.set_jurisdiction(jurisdiction)
    
    # Add precedent match
    precedent = PrecedentMatch(
        contract_id="MSA-2023-001",
        similarity_score=0.92,
        clause_text="Similar liability clause from precedent",
        approval_status="approved_with_conditions",
        business_context="Similar technology services engagement"
    )
    context.add_precedent_match(precedent)
    
    return context


def example_policy_api_integration():
    """Example showing how this integrates with the policy_api.py"""
    
    # This is how policy_api.py would use the models
    context = AgentContext(
        input_data={
            'tenant_id': 'company_123',
            'clauses': [{'clause_type': 'Payment', 'content': 'Net 60 payment terms'}],
            'contract_type': 'general'
        }
    )
    
    # Simulate agent execution
    result = AgentResult(
        status=AgentStatus.SUCCESS,
        data={
            'violations_found': 1,
            'policies_checked': 3,
            'violations': [
                {
                    'clause_type': 'Payment Terms',
                    'issue': 'Exceeds company policy (Net 30 preferred)',
                    'severity': 'CRITICAL'
                }
            ]
        },
        processing_complete=True
    )
    
    return {
        'success': True,
        'compliance_check': {
            'violations_found': result.data['violations_found'],
            'policies_checked': result.data['policies_checked'],
            'violations': result.data['violations']
        }
    }


if __name__ == "__main__":
    # Test basic usage
    basic_context, basic_result = example_basic_agent_usage()
    print(f"Basic agent result: {basic_result.status}")
    
    # Test CUAD mitigation
    enhanced_context = example_cuad_mitigation_usage()
    print(f"CUAD deviations detected: {len(enhanced_context.cuad_deviations)}")
    
    # Test policy API integration
    policy_response = example_policy_api_integration()
    print(f"Policy API response: {policy_response['success']}")