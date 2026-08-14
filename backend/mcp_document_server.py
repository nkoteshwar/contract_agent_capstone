import json
import logging
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.infrastructure.text_extractors import TextExtractionService
from backend.agents.section_extraction_agent import SectionExtractionAgent
from backend.mcp.decorators import mcp_tool_wrapper
from backend.shared.utils.mcp_logger import get_mcp_logger
from langchain_openai import ChatOpenAI

# Initialize FastMCP server
mcp = FastMCP("ContractDocumentProcessing")
logger = get_mcp_logger("mcp_document_server")

# Services (SOLID: Lazy loading to avoid side-effects on import)
_text_extractor = None
_section_agent = None

def get_text_extractor():
    global _text_extractor
    if _text_extractor is None:
        _text_extractor = TextExtractionService()
    return _text_extractor

def get_section_agent():
    global _section_agent
    if _section_agent is None:
        # Initialize the LLM needed for the agent
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        _section_agent = SectionExtractionAgent(llm, strategy="hybrid")
    return _section_agent

@mcp.tool()
@mcp_tool_wrapper
async def extract_contract_sections(file_path: str, target_sections: Optional[List[str]] = None) -> str:
    """
    Extract text from a raw PDF file, intelligently chunk it into structural sections, 
    and optionally filter for specific sections (e.g., 'Termination', 'Indemnification').
    
    Args:
        file_path: Absolute local path to the PDF file to be processed.
        target_sections: Optional list of section titles to filter by (e.g. ['Termination', 'Terms']). If omitted, returns all sections.
    """
    try:
        logger.info(f"Extracting text from {file_path}")
        # 1. Extract raw text from PDF
        text = get_text_extractor().extract_with_fallback(file_path)
        
        logger.info(f"Extracting sections from text ({len(text)} chars)")
        # 2. Extract structured sections using LLM/Regex Hybrid Agent
        sections = get_section_agent().extract_sections(text, "mcp_temp_extract")
        
        # 3. Filter sections if requested
        filtered_sections = sections
        if target_sections:
            target_lower = [ts.lower() for ts in target_sections]
            filtered_sections = []
            for section in sections:
                title = section.get("title", "").lower()
                # Simple substring match
                if any(t in title for t in target_lower):
                    filtered_sections.append(section)
                    
            logger.info(f"Filtered {len(sections)} down to {len(filtered_sections)} sections matching {target_sections}")
        
        return json.dumps({
            "success": True,
            "total_sections_found": len(sections),
            "sections_returned": len(filtered_sections),
            "sections": filtered_sections
        })
    except Exception as e:
        logger.error(f"Failed to extract sections from {file_path}", e)
        return json.dumps({"success": False, "error": str(e)})

if __name__ == "__main__":
    # Run server via stdio (MCP default)
    mcp.run()
