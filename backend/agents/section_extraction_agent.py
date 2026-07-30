"""
Section Extraction Agent
Strategy Pattern + Observer Pattern for document section extraction
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)

@dataclass
class Section:
    """Section data model with order preservation"""
    title: str
    content: str
    order: int
    start_position: int  # Character position in original text
    end_position: int    # End character position
    section_type: str = "general"
    confidence: float = 1.0

class ISectionExtractionStrategy(ABC):
    """Strategy interface for section extraction"""
    
    @abstractmethod
    def extract_sections(self, text: str) -> List[Section]:
        """Extract sections from text"""
        pass

class RegexSectionExtractor(ISectionExtractionStrategy):
    """Fast regex-based section extraction"""
    
    def extract_sections(self, text: str) -> List[Section]:
        """Extract sections using regex patterns"""
        sections = []
        
        # Common section patterns
        patterns = [
            r'^\s*(\d+\.?\s+[A-Z][^.\n]{10,50})\s*$',  # Numbered sections
            r'^\s*([A-Z][A-Z\s]{5,30})\s*$',           # ALL CAPS sections
            r'^\s*(ARTICLE\s+[IVX\d]+[^.\n]{5,30})\s*$' # Article sections
        ]
        
        lines = text.split('\n')
        current_section = None
        content_buffer = []
        order = 0
        
        for line in lines:
            is_section_header = False
            
            for pattern in patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    # Save previous section
                    if current_section:
                        sections.append(Section(
                            title=current_section,
                            content='\n'.join(content_buffer).strip(),
                            order=order,
                            start_position=0,  # Will be calculated properly
                            end_position=0,    # Will be calculated properly
                            confidence=0.8
                        ))
                        order += 1
                    
                    # Start new section
                    current_section = line.strip()
                    content_buffer = []
                    is_section_header = True
                    break
            
            if not is_section_header and current_section:
                content_buffer.append(line)
        
        # Add final section
        if current_section and content_buffer:
            sections.append(Section(
                title=current_section,
                content='\n'.join(content_buffer).strip(),
                order=order,
                start_position=0,  # Will be calculated properly
                end_position=0,    # Will be calculated properly
                confidence=0.8
            ))
        
        return sections

class LLMSectionExtractor(ISectionExtractionStrategy):
    """LLM-based intelligent section extraction"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def extract_sections(self, text: str) -> List[Section]:
        """Extract sections using LLM analysis"""
        # Truncate for LLM processing
        analysis_text = text[:6000] if len(text) > 6000 else text
        
        prompt = f"""
        Analyze this contract and identify major sections. Return a JSON list of sections:
        
        {analysis_text}
        
        Format: [{{"title": "Section Title", "start_marker": "text snippet", "type": "recitals|definitions|terms|termination|general"}}]
        
        Focus on major structural sections, not individual clauses.
        """
        
        try:
            response = self.llm.invoke(prompt)
            # Parse LLM response and extract sections
            # Implementation would parse JSON and map to text
            return self._parse_llm_response(response.content, text)
        except Exception as e:
            logger.error(f"LLM section extraction failed: {e}")
            return []
    
    def _parse_llm_response(self, response: str, full_text: str) -> List[Section]:
        """Parse LLM response and map to actual text sections"""
        # Simplified implementation - would need proper JSON parsing
        return []

class HybridSectionExtractor(ISectionExtractionStrategy):
    """Hybrid approach combining regex and LLM"""
    
    def __init__(self, llm):
        self.regex_extractor = RegexSectionExtractor()
        self.llm_extractor = LLMSectionExtractor(llm)
    
    def extract_sections(self, text: str) -> List[Section]:
        """Use regex first, LLM for validation/enhancement"""
        regex_sections = self.regex_extractor.extract_sections(text)
        
        if len(regex_sections) >= 3:  # Good regex extraction
            return regex_sections
        else:  # Fallback to LLM
            return self.llm_extractor.extract_sections(text)

class SectionExtractionAgent:
    """Main section extraction agent using Strategy pattern"""
    
    def __init__(self, llm, strategy: str = "hybrid"):
        self.llm = llm
        self.strategy = self._create_strategy(strategy)
        self.observers = []
    
    def _create_strategy(self, strategy_type: str) -> ISectionExtractionStrategy:
        """Factory method for strategy creation"""
        if strategy_type == "regex":
            return RegexSectionExtractor()
        elif strategy_type == "llm":
            return LLMSectionExtractor(self.llm)
        elif strategy_type == "hybrid":
            return HybridSectionExtractor(self.llm)
        else:
            raise ValueError(f"Unknown strategy: {strategy_type}")
    
    def add_observer(self, observer):
        """Observer pattern for progress tracking"""
        self.observers.append(observer)
    
    def _notify_observers(self, event: str, data: Any):
        """Notify observers of extraction progress"""
        for observer in self.observers:
            observer.on_section_extraction_event(event, data)
    
    def extract_sections(self, text: str, contract_id: str) -> List[Dict[str, Any]]:
        """Extract sections and return as dictionaries for storage"""
        try:
            self._notify_observers("extraction_started", {"contract_id": contract_id})
            
            sections = self.strategy.extract_sections(text)
            
            # Sort sections by order to ensure correct sequence
            sections = sorted(sections, key=lambda x: x.order)
            
            # Convert to storage format
            section_dicts = []
            for section in sections:
                section_dict = {
                    "section_id": f"{contract_id}_section_{section.order:03d}",
                    "title": section.title,
                    "content": section.content,
                    "order": section.order,
                    "start_position": section.start_position,
                    "end_position": section.end_position,
                    "section_type": section.section_type,
                    "confidence": section.confidence,
                    "contract_id": contract_id
                }
                section_dicts.append(section_dict)
            
            self._notify_observers("extraction_completed", {
                "contract_id": contract_id,
                "sections_found": len(sections)
            })
            
            return section_dicts
            
        except Exception as e:
            self._notify_observers("extraction_failed", {
                "contract_id": contract_id,
                "error": str(e)
            })
            logger.error(f"Section extraction failed for {contract_id}: {e}")
            return []

class SectionExtractionObserver:
    """Observer for section extraction events"""
    
    def on_section_extraction_event(self, event: str, data: Dict[str, Any]):
        """Handle section extraction events"""
        logger.info(f"Section extraction event: {event} - {data}")