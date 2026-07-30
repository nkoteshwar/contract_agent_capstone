"""
Document Processor Factory
Factory Pattern for creating different document processors
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.agents.pdf_processing_agent import PDFAgentFactory
from backend.agents.enhanced_pdf_processing_agent import EnhancedPDFAgentFactory
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

class IDocumentProcessor(ABC):
    """Interface for document processors"""
    
    @abstractmethod
    async def process_document(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process document and return results"""
        pass

class BasicDocumentProcessor(IDocumentProcessor):
    """Basic document processor - existing functionality"""
    
    def __init__(self, llm):
        self.llm = llm
        self.agent = PDFAgentFactory.create_agent(llm)
    
    async def process_document(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process document with basic extraction"""
        try:
            state = {
                "file_path": file_path,
                "tenant_id": options.get("tenant_id", "default-tenant"),
                "filename": options.get("filename", ""),
                "extracted_text": None,
                "contract_data": None,
                "processing_result": None
            }
            
            result = await self.agent.ainvoke(state)
            
            return {
                "status": "success",
                "processor_type": "basic",
                "contract_id": result.get("processing_result", {}).get("contract_id"),
                "sections_extracted": 0,
                "clauses_extracted": 0,
                "cuad_classifications": 0
            }
            
        except Exception as e:
            logger.error(f"Basic processing failed: {e}")
            return {
                "status": "error",
                "processor_type": "basic",
                "error": str(e)
            }

class EnhancedDocumentProcessor(IDocumentProcessor):
    """Enhanced document processor with sections"""
    
    def __init__(self, llm):
        self.llm = llm
        self.agent = EnhancedPDFAgentFactory.create_agent(llm, "enhanced")
    
    async def process_document(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process document with section extraction"""
        try:
            state = {
                "file_path": file_path,
                "tenant_id": options.get("tenant_id", "default-tenant"),
                "filename": options.get("filename", ""),
                "extracted_text": None,
                "contract_data": None,
                "processing_result": None,
                "sections": None
            }
            
            result = await self.agent.ainvoke(state)
            
            sections = result.get("sections", [])
            
            return {
                "status": "success",
                "processor_type": "enhanced",
                "contract_id": result.get("processing_result", {}).get("contract_id"),
                "sections_extracted": len(sections),
                "clauses_extracted": 0,
                "cuad_classifications": 0
            }
            
        except Exception as e:
            logger.error(f"Enhanced processing failed: {e}")
            return {
                "status": "error",
                "processor_type": "enhanced",
                "error": str(e)
            }

class FullDocumentProcessor(IDocumentProcessor):
    """Full document processor with sections + clauses + CUAD"""
    
    def __init__(self, llm):
        self.llm = llm
        self.agent = EnhancedPDFAgentFactory.create_agent(llm, "enhanced")
    
    async def process_document(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process document with full extraction pipeline"""
        try:
            state = {
                "file_path": file_path,
                "tenant_id": options.get("tenant_id", "default-tenant"),
                "filename": options.get("filename", ""),
                "extracted_text": None,
                "contract_data": None,
                "processing_result": None,
                "sections": None,
                "clauses": None,
                "cuad_classifications": None
            }
            
            result = await self.agent.ainvoke(state)
            
            sections = result.get("sections", [])
            clauses = result.get("clauses", [])
            cuad_classifications = result.get("cuad_classifications", [])
            
            return {
                "status": "success",
                "processor_type": "full",
                "contract_id": result.get("processing_result", {}).get("contract_id"),
                "sections_extracted": len(sections),
                "clauses_extracted": len(clauses),
                "cuad_classifications": len(cuad_classifications)
            }
            
        except Exception as e:
            logger.error(f"Full processing failed: {e}")
            return {
                "status": "error",
                "processor_type": "full",
                "error": str(e)
            }

class DocumentProcessorFactory:
    """Factory for creating document processors"""
    
    @staticmethod
    def create_processor(processor_type: str, llm) -> IDocumentProcessor:
        """Create document processor based on type"""
        
        if processor_type == "basic":
            return BasicDocumentProcessor(llm)
        elif processor_type == "enhanced":
            return EnhancedDocumentProcessor(llm)
        elif processor_type == "full":
            return FullDocumentProcessor(llm)
        else:
            raise ValueError(f"Unknown processor type: {processor_type}")
    
    @staticmethod
    def get_available_types() -> list:
        """Get available processor types"""
        return ["basic", "enhanced", "full"]
    
    @staticmethod
    def get_processor_capabilities(processor_type: str) -> Dict[str, bool]:
        """Get capabilities of processor type"""
        capabilities = {
            "basic": {
                "contract_analysis": True,
                "section_extraction": False,
                "clause_extraction": False,
                "cuad_classification": False,
                "embeddings": False
            },
            "enhanced": {
                "contract_analysis": True,
                "section_extraction": True,
                "clause_extraction": False,
                "cuad_classification": False,
                "embeddings": True
            },
            "full": {
                "contract_analysis": True,
                "section_extraction": True,
                "clause_extraction": True,
                "cuad_classification": True,
                "embeddings": True
            }
        }
        
        return capabilities.get(processor_type, {})