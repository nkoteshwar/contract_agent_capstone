"""Legal chunking facade using Facade and Adapter patterns."""

from typing import Dict, Any, List
from .document_analyzer import analyze_document


class LegalChunkingFacade:
    """Facade that provides unified interface for legal document chunking."""
    
    def __init__(self):
        self.section_adapter = SectionHeaderAdapter()
        self.contract_adapter = ContractFormattingAdapter()
        self.paragraph_adapter = ParagraphStructureAdapter()
    
    def prepare_legal_context(self, text: str, doc_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare comprehensive legal context for chunking strategies."""
        if doc_analysis is None:
            doc_analysis = analyze_document(text)
        
        # Adapt analysis results for chunking strategies
        legal_context = {
            'is_legal_document': doc_analysis.get('is_legal_document', False),
            'document_type': doc_analysis.get('document_type', 'unknown'),
            'section_headers': self.section_adapter.extract_section_headers(doc_analysis),
            'contract_formatting': self.contract_adapter.extract_formatting_rules(doc_analysis),
            'paragraph_structure': self.paragraph_adapter.extract_structure_info(doc_analysis),
            'legal_patterns': self._extract_legal_patterns(doc_analysis)
        }
        
        return legal_context
    
    def _extract_legal_patterns(self, doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract legal patterns for chunking optimization."""
        return {
            'clause_density': doc_analysis.get('clause_density', 0),
            'obligation_density': doc_analysis.get('obligation_density', 0),
            'section_count': doc_analysis.get('section_count', 0),
            'has_hierarchical_structure': doc_analysis.get('has_hierarchical_structure', False)
        }


class SectionHeaderAdapter:
    """Adapts section analysis results for section chunking strategy."""
    
    def extract_section_headers(self, doc_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract section headers in format suitable for chunking."""
        sections = doc_analysis.get('sections', [])
        
        adapted_sections = []
        for section in sections:
            adapted_sections.append({
                'header': section.get('header', ''),
                'type': section.get('type', 'unknown'),
                'position': section.get('position', 0),
                'line_number': section.get('line_number', 0),
                'identifier': section.get('identifier', ''),
                'title': section.get('title', ''),
                'is_major_section': section.get('type') in ['article', 'section', 'numbered_section']
            })
        
        return adapted_sections
    
    def get_section_boundaries(self, sections: List[Dict[str, Any]], text: str) -> List[int]:
        """Get section boundary positions for chunking."""
        boundaries = []
        
        for section in sections:
            if section.get('position', 0) > 0:
                boundaries.append(section['position'])
        
        return sorted(boundaries)


class ContractFormattingAdapter:
    """Adapts contract formatting analysis for chunking strategies."""
    
    def extract_formatting_rules(self, doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contract formatting rules for chunking."""
        contract_probability = doc_analysis.get('contract_probability', 0)
        document_sections = doc_analysis.get('document_sections', [])
        
        formatting_rules = {
            'is_contract': contract_probability > 0.5,
            'contract_probability': contract_probability,
            'has_signature_blocks': doc_analysis.get('signature_indicators', 0) > 0,
            'standard_sections': self._identify_standard_sections(document_sections),
            'formatting_patterns': self._extract_formatting_patterns(doc_analysis)
        }
        
        return formatting_rules
    
    def _identify_standard_sections(self, document_sections: List[Dict[str, Any]]) -> List[str]:
        """Identify standard contract sections."""
        standard_sections = []
        
        section_keywords = {
            'definitions': ['DEFINITIONS', 'INTERPRETATION'],
            'scope': ['SCOPE', 'SERVICES', 'DELIVERABLES'],
            'payment': ['PAYMENT', 'FEES', 'COMPENSATION'],
            'confidentiality': ['CONFIDENTIALITY', 'NON-DISCLOSURE'],
            'ip': ['INTELLECTUAL PROPERTY', 'IP RIGHTS'],
            'liability': ['LIABILITY', 'INDEMNIFICATION'],
            'termination': ['TERMINATION', 'EXPIRATION'],
            'general': ['GENERAL PROVISIONS', 'MISCELLANEOUS']
        }
        
        for section in document_sections:
            section_text = section.get('match', '').upper()
            for category, keywords in section_keywords.items():
                if any(keyword in section_text for keyword in keywords):
                    standard_sections.append(category)
                    break
        
        return list(set(standard_sections))
    
    def _extract_formatting_patterns(self, doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract formatting patterns for chunking optimization."""
        return {
            'has_numbered_sections': any(s.get('type') == 'numbered_section' 
                                       for s in doc_analysis.get('sections', [])),
            'has_lettered_paragraphs': len(doc_analysis.get('lettered_paragraphs', [])) > 0,
            'has_indented_content': len(doc_analysis.get('indented_paragraphs', [])) > 0,
            'average_paragraph_length': doc_analysis.get('avg_paragraph_length', 0)
        }


class ParagraphStructureAdapter:
    """Adapts paragraph structure analysis for paragraph chunking strategy."""
    
    def extract_structure_info(self, doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract paragraph structure information for chunking."""
        return {
            'paragraph_count': doc_analysis.get('paragraph_count', 0),
            'avg_paragraph_length': doc_analysis.get('avg_paragraph_length', 0),
            'numbered_paragraphs': doc_analysis.get('numbered_paragraphs', []),
            'lettered_paragraphs': doc_analysis.get('lettered_paragraphs', []),
            'indented_paragraphs': doc_analysis.get('indented_paragraphs', []),
            'has_structured_paragraphs': doc_analysis.get('has_structured_paragraphs', False),
            'paragraph_boundaries': self._calculate_paragraph_boundaries(doc_analysis)
        }
    
    def _calculate_paragraph_boundaries(self, doc_analysis: Dict[str, Any]) -> List[int]:
        """Calculate paragraph boundary positions."""
        paragraphs = doc_analysis.get('paragraphs', [])
        boundaries = []
        
        current_pos = 0
        for paragraph in paragraphs:
            boundaries.append(current_pos)
            current_pos += len(paragraph) + 2  # Add space for paragraph break
        
        return boundaries


class LegalChunkingEnhancer:
    """Enhances existing chunking strategies with legal intelligence."""
    
    def __init__(self, facade: LegalChunkingFacade):
        self.facade = facade
    
    def enhance_section_strategy(self, strategy, text: str, legal_context: Dict[str, Any]):
        """Enhance section strategy with legal intelligence."""
        section_headers = legal_context.get('section_headers', [])
        
        # Override section patterns with detected headers
        if section_headers:
            strategy.detected_sections = section_headers
            strategy.use_detected_sections = True
    
    def enhance_clause_strategy(self, strategy, text: str, legal_context: Dict[str, Any]):
        """Enhance clause strategy with contract-specific patterns."""
        contract_formatting = legal_context.get('contract_formatting', {})
        
        # Add contract-specific clause patterns
        if contract_formatting.get('is_contract', False):
            strategy.contract_mode = True
            strategy.enhanced_patterns = self._get_contract_clause_patterns()
    
    def enhance_paragraph_strategy(self, strategy, text: str, legal_context: Dict[str, Any]):
        """Enhance paragraph strategy with structure awareness."""
        paragraph_structure = legal_context.get('paragraph_structure', {})
        
        # Use detected paragraph boundaries
        if paragraph_structure.get('paragraph_boundaries'):
            strategy.paragraph_boundaries = paragraph_structure['paragraph_boundaries']
            strategy.use_detected_boundaries = True
    
    def _get_contract_clause_patterns(self) -> List[str]:
        """Get enhanced clause patterns for contracts."""
        return [
            r'(?:The\s+(?:Company|Contractor|Client|Vendor))\s+(?:shall|will|agrees?\s+to)',
            r'(?:This\s+Agreement|The\s+Contract)\s+(?:shall|will)',
            r'(?:Upon|In\s+the\s+event\s+of|If)\s+.*(?:breach|default|termination)',
            r'(?:Payment|Compensation|Fees)\s+(?:shall|will)\s+be',
            r'(?:Confidential|Proprietary)\s+(?:Information|Data)',
            r'(?:Intellectual\s+Property|IP)\s+(?:rights|ownership)',
            r'(?:Limitation\s+of\s+)?Liability',
            r'(?:Indemnification|Hold\s+harmless)',
            r'(?:Governing\s+Law|Jurisdiction)',
            r'(?:Force\s+Majeure|Acts?\s+of\s+God)'
        ]