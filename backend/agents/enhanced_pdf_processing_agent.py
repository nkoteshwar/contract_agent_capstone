"""
Enhanced PDF Processing Agent with Section and Clause Extraction
Chain of Responsibility Pattern for complete document processing
"""

from backend.agents.pdf_processing_agent import get_pdf_processing_agent
from backend.agents.section_extraction_agent import SectionExtractionAgent
from backend.agents.clause_extraction_agent import ClauseExtractionAgent
from backend.agents.cuad_classifier_agent import CUADClassifierAgent
from backend.infrastructure.section_repository import SectionRepository
from backend.infrastructure.clause_repository import ClauseRepository
from backend.agents.pdf_state import PDFProcessingState
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

def get_enhanced_pdf_processing_agent(llm):
    """Create enhanced PDF processing agent with section/clause extraction"""
    
    # Get base agent
    base_agent = get_pdf_processing_agent(llm)
    
    # Initialize enhanced services
    section_extractor = SectionExtractionAgent(llm, strategy="hybrid")
    clause_extractor = ClauseExtractionAgent(llm, strategy="regex")
    cuad_classifier = CUADClassifierAgent(llm, strategy="hybrid")
    section_repo = SectionRepository()
    clause_repo = ClauseRepository()
    
    def extract_sections_node(state: PDFProcessingState) -> PDFProcessingState:
        """Extract sections from processed contract"""
        contract_data = state.get("contract_data")
        if not contract_data or not contract_data.is_contract:
            return state
        
        try:
            contract_id = state.get("processing_result", {}).get("contract_id")
            if not contract_id:
                return state
            
            # Extract sections
            sections = section_extractor.extract_sections(
                contract_data.full_text, 
                contract_id
            )
            
            if sections:
                # Store sections
                section_repo.store_sections(contract_id, sections)
                logger.info(f"Extracted and stored {len(sections)} sections")
                
                return {**state, "sections": sections}
            
            return state
            
        except Exception as e:
            logger.error(f"Section extraction failed: {e}")
            return state
    
    def extract_clauses_node(state: PDFProcessingState) -> PDFProcessingState:
        """Extract clauses from sections"""
        sections = state.get("sections", [])
        if not sections:
            return state
        
        try:
            all_clauses = []
            
            for section in sections:
                # Extract clauses from section
                clauses = clause_extractor.extract_clauses_from_section(section)
                all_clauses.extend(clauses)
            
            if all_clauses:
                # Store clauses
                clause_repo.store_clauses(all_clauses)
                
                # Classify with CUAD
                classifications = cuad_classifier.classify_clauses_batch(all_clauses)
                if classifications:
                    clause_repo.store_cuad_classifications(classifications)
                
                # Generate embeddings
                from backend.infrastructure.embedding_service import EmbeddingService
                embedding_service = EmbeddingService()
                embedding_service.generate_section_embeddings(sections)
                embedding_service.generate_clause_embeddings(all_clauses)
                
                logger.info(f"Extracted {len(all_clauses)} clauses, {len(classifications)} CUAD classifications, generated embeddings")
                
                return {**state, "clauses": all_clauses, "cuad_classifications": classifications}
            
            return state
            
        except Exception as e:
            logger.error(f"Clause extraction failed: {e}")
            return state
    
    # Extend base agent with new nodes
    from langgraph.graph import StateGraph, END
    
    builder = StateGraph(PDFProcessingState)
    
    # Add base nodes
    builder.add_node("extract_text", base_agent.get_node("extract_text"))
    builder.add_node("analyze_contract", base_agent.get_node("analyze_contract"))
    builder.add_node("store_contract", base_agent.get_node("store_contract"))
    
    # Add enhanced nodes
    builder.add_node("extract_sections", extract_sections_node)
    builder.add_node("extract_clauses", extract_clauses_node)
    
    # Build enhanced flow
    builder.add_edge("extract_text", "analyze_contract")
    builder.add_edge("analyze_contract", "store_contract")
    builder.add_edge("store_contract", "extract_sections")
    builder.add_edge("extract_sections", "extract_clauses")
    builder.add_edge("extract_clauses", END)
    
    return builder.compile()

class EnhancedPDFAgentFactory:
    """Factory for creating enhanced PDF processing agents"""
    
    @staticmethod
    def create_agent(llm, agent_type: str = "enhanced"):
        """Create enhanced PDF processing agent"""
        
        if agent_type == "enhanced":
            return get_enhanced_pdf_processing_agent(llm)
        elif agent_type == "basic":
            return get_pdf_processing_agent(llm)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    @staticmethod
    def get_available_types():
        """Get list of available agent types"""
        return ["basic", "enhanced"]