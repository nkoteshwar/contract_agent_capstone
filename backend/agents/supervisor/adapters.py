from typing import Dict, Any
from .base_adapter import BaseAgentAdapter, AgentConfig
from .interfaces import AgentContext, AgentResult
from ...llm_manager import LLMManager

class PDFProcessingAdapter(BaseAgentAdapter):
    def __init__(self, config: AgentConfig, llm_manager: LLMManager):
        super().__init__(config)
        self.llm_manager = llm_manager
        
    def prepare_input(self, context: AgentContext) -> Dict[str, Any]:
        return {
            "file_path": context.input_data.get("file_path"),
            "filename": context.input_data.get("filename", ""),
            "tenant_id": context.input_data.get("tenant_id", "default-tenant")
        }
    
    def call_agent(self, input_data: Dict[str, Any]) -> Any:
        # Use existing PDF processing logic
        from ...application.services.document_processing_service import DocumentServiceFactory
        service = DocumentServiceFactory.create_service(self.llm_manager)
        
        from ...domain.entities import DocumentProcessingRequest
        request = DocumentProcessingRequest(
            file_path=input_data["file_path"],
            filename=input_data["filename"],
            tenant_id=input_data.get("tenant_id", "default-tenant"),
            processing_options={"model": "gemini-2.5-flash"}
        )
        
        return service.process_pdf_upload(request)
    
    def format_output(self, raw_result: Any) -> AgentResult:
        return AgentResult(
            status=raw_result.get("status", "success"),
            data={
                "text_content": raw_result.get("final_result", ""),
                "contract_id": raw_result.get("contract_id"),
                "metadata": {"processing_complete": True}
            },
            confidence=0.8
        )

class ClauseExtractionAdapter(BaseAgentAdapter):
    def __init__(self, config: AgentConfig, llm_manager: LLMManager):
        super().__init__(config)
        self.llm_manager = llm_manager
        
    def prepare_input(self, context: AgentContext) -> Dict[str, Any]:
        pdf_result = context.workflow_context.get_agent_result("pdf-processing")
        return {
            "contract_id": pdf_result.data.get("contract_id") if pdf_result else context.input_data.get("contract_id"),
            "text_content": pdf_result.data.get("text_content") if pdf_result else ""
        }
    
    def call_agent(self, input_data: Dict[str, Any]) -> Any:
        from ...application.services.contract_intelligence_service import ContractIntelligenceServiceFactory
        service = ContractIntelligenceServiceFactory.create_service(self.llm_manager)
        
        contract_id = input_data["contract_id"]
        if contract_id:
            return service.analyze_contract_by_id(contract_id, "gemini-2.5-flash")
        else:
            return {"clauses": [], "status": "no_contract_id"}
    
    def format_output(self, raw_result: Any) -> AgentResult:
        if hasattr(raw_result, 'clauses'):
            clauses_data = [
                {
                    "clause_type": clause.clause_type,
                    "content": clause.content,
                    "confidence_score": clause.confidence_score
                }
                for clause in raw_result.clauses
            ]
            confidence = sum(c["confidence_score"] for c in clauses_data) / len(clauses_data) if clauses_data else 0.0
        else:
            clauses_data = []
            confidence = 0.0
            
        return AgentResult(
            status="success",
            data={"clauses": clauses_data},
            confidence=confidence
        )

class RiskAssessmentAdapter(BaseAgentAdapter):
    def __init__(self, config: AgentConfig, llm_manager: LLMManager):
        super().__init__(config)
        self.llm_manager = llm_manager
        
    def prepare_input(self, context: AgentContext) -> Dict[str, Any]:
        clause_result = context.workflow_context.get_agent_result("clause-extraction")
        pdf_result = context.workflow_context.get_agent_result("pdf-processing")
        
        return {
            "contract_id": pdf_result.data.get("contract_id") if pdf_result else None,
            "clauses": clause_result.data.get("clauses", []) if clause_result else []
        }
    
    def call_agent(self, input_data: Dict[str, Any]) -> Any:
        from ...application.services.contract_intelligence_service import ContractIntelligenceServiceFactory
        service = ContractIntelligenceServiceFactory.create_service(self.llm_manager)
        
        contract_id = input_data["contract_id"]
        if contract_id:
            return service.analyze_contract_by_id(contract_id, "gemini-2.5-flash")
        else:
            return {"risk_assessment": None}
    
    def format_output(self, raw_result: Any) -> AgentResult:
        if hasattr(raw_result, 'risk_assessment') and raw_result.risk_assessment:
            risk_data = {
                "risk_score": raw_result.risk_assessment.overall_risk_score,
                "risk_level": raw_result.risk_assessment.risk_level,
                "critical_issues": raw_result.risk_assessment.critical_issues,
                "recommendations": raw_result.risk_assessment.recommendations
            }
            confidence = 0.8
        else:
            risk_data = {"risk_score": 50, "risk_level": "MEDIUM", "critical_issues": [], "recommendations": []}
            confidence = 0.3
            
        return AgentResult(
            status="success",
            data=risk_data,
            confidence=confidence
        )