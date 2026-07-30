"""Document analysis pipeline using Chain of Responsibility pattern."""

import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class DocumentAnalyzer(ABC):
    """Base class for document analysis components."""
    
    def __init__(self):
        self._next_analyzer: Optional['DocumentAnalyzer'] = None
    
    def set_next(self, analyzer: 'DocumentAnalyzer') -> 'DocumentAnalyzer':
        """Set the next analyzer in the chain."""
        self._next_analyzer = analyzer
        return analyzer
    
    def analyze(self, text: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document and pass to next analyzer."""
        result = self._analyze(text, analysis_result)
        
        if self._next_analyzer:
            return self._next_analyzer.analyze(text, result)
        
        return result
    
    @abstractmethod
    def _analyze(self, text: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform specific analysis."""
        pass


class SectionHeaderDetector(DocumentAnalyzer):
    """Detects legal section headers and structure."""
    
    def __init__(self):
        super().__init__()
        self.section_patterns = [
            (r'^(?:ARTICLE|Article)\s+([IVX\d]+)[.\s]+(.*)', 'article'),
            (r'^(?:SECTION|Section)\s+([IVX\d]+)[.\s]+(.*)', 'section'),
            (r'^(\d+)\.\s+([A-Z][^.]*[.:]?)', 'numbered_section'),
            (r'^([A-Z][A-Z\s]{10,}):?\s*$', 'caps_header'),
            (r'^([A-Z][a-z\s]{5,}):?\s*$', 'title_header'),
        ]
    
    def _analyze(self, text: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Detect section headers and structure."""
        lines = text.split('\n')
        sections = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            for pattern, section_type in self.section_patterns:
                match = re.match(pattern, line_stripped)
                if match:
                    sections.append({
                        'line_number': i,
                        'type': section_type,
                        'header': line_stripped,
                        'identifier': match.group(1) if match.groups() else '',
                        'title': match.group(2) if len(match.groups()) > 1 else '',
                        'position': text.find(line_stripped)
                    })
                    break
        
        analysis_result.update({
            'sections': sections,
            'section_count': len(sections),
            'has_hierarchical_structure': len(sections) >= 3,
            'section_types': list(set(s['type'] for s in sections))
        })
        
        return analysis_result


class ClauseBoundaryDetector(DocumentAnalyzer):
    """Detects legal clause boundaries and patterns."""
    
    def __init__(self):
        super().__init__()
        self.clause_starters = [
            r'(?:PROVIDED\s+THAT|PROVIDED\s+HOWEVER)',
            r'(?:WHEREAS|THEREFORE|FURTHERMORE|NOTWITHSTANDING)',
            r'(?:IN\s+CONSIDERATION\s+OF|SUBJECT\s+TO)',
            r'(?:The\s+(?:Party|Parties|Company|Contractor))',
            r'(?:This\s+Agreement|The\s+Contract|These\s+Terms)',
            r'(?:In\s+the\s+event|If\s+and\s+when|Unless\s+otherwise)',
        ]
        
        self.obligation_patterns = [
            r'(?:shall|will|must|agrees?\s+to)\s+(?:not\s+)?(?:be|have|do|provide|ensure|maintain)',
            r'(?:is\s+required\s+to|is\s+obligated\s+to|undertakes\s+to)',
            r'(?:represents\s+and\s+warrants|acknowledges\s+that)',
        ]
    
    def _analyze(self, text: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Detect clause boundaries and legal patterns."""
        sentences = re.split(r'[.!?]+\s+', text)
        clauses = []
        obligations = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check for clause starters
            for pattern in self.clause_starters:
                if re.search(pattern, sentence, re.IGNORECASE):
                    clauses.append({
                        'sentence_index': i,
                        'type': 'clause_starter',
                        'pattern': pattern,
                        'content': sentence[:100] + '...' if len(sentence) > 100 else sentence,
                        'position': text.find(sentence)
                    })
                    break
            
            # Check for obligations
            for pattern in self.obligation_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    obligations.append({
                        'sentence_index': i,
                        'type': 'obligation',
                        'pattern': pattern,
                        'content': sentence[:100] + '...' if len(sentence) > 100 else sentence,
                        'position': text.find(sentence)
                    })
                    break
        
        clause_density = len(clauses) / max(len(sentences), 1)
        obligation_density = len(obligations) / max(len(sentences), 1)
        
        analysis_result.update({
            'clauses': clauses,
            'obligations': obligations,
            'clause_count': len(clauses),
            'obligation_count': len(obligations),
            'clause_density': clause_density,
            'obligation_density': obligation_density,
            'is_legal_document': clause_density > 0.1 or obligation_density > 0.05
        })
        
        return analysis_result


class ParagraphStructureAnalyzer(DocumentAnalyzer):
    """Analyzes paragraph structure and legal formatting."""
    
    def _analyze(self, text: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze paragraph structure and formatting."""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Analyze paragraph characteristics
        paragraph_lengths = [len(p) for p in paragraphs]
        avg_paragraph_length = sum(paragraph_lengths) / max(len(paragraph_lengths), 1)
        
        # Detect numbered/lettered paragraphs
        numbered_paragraphs = []
        lettered_paragraphs = []
        
        for i, para in enumerate(paragraphs):
            # Check for numbered paragraphs
            if re.match(r'^\d+\.\s+', para):
                numbered_paragraphs.append(i)
            
            # Check for lettered paragraphs
            if re.match(r'^\([a-z]\)\s+', para):
                lettered_paragraphs.append(i)
        
        # Detect indentation patterns
        indented_paragraphs = []
        for i, para in enumerate(paragraphs):
            lines = para.split('\n')
            if any(line.startswith('    ') or line.startswith('\t') for line in lines):
                indented_paragraphs.append(i)
        
        analysis_result.update({
            'paragraphs': paragraphs,
            'paragraph_count': len(paragraphs),
            'avg_paragraph_length': avg_paragraph_length,
            'numbered_paragraphs': numbered_paragraphs,
            'lettered_paragraphs': lettered_paragraphs,
            'indented_paragraphs': indented_paragraphs,
            'has_structured_paragraphs': len(numbered_paragraphs) > 2 or len(lettered_paragraphs) > 2,
            'paragraph_lengths': paragraph_lengths
        })
        
        return analysis_result


class ContractFormatHandler(DocumentAnalyzer):
    """Handles contract-specific formatting and structure."""
    
    def __init__(self):
        super().__init__()
        self.contract_indicators = [
            r'(?:AGREEMENT|CONTRACT|TERMS\s+AND\s+CONDITIONS)',
            r'(?:PARTY|PARTIES|CONTRACTOR|CLIENT|VENDOR)',
            r'(?:EFFECTIVE\s+DATE|TERM\s+OF\s+AGREEMENT)',
            r'(?:CONSIDERATION|PAYMENT|COMPENSATION)',
            r'(?:TERMINATION|BREACH|DEFAULT)',
            r'(?:GOVERNING\s+LAW|JURISDICTION|DISPUTE)',
        ]
        
        self.document_sections = [
            r'(?:RECITALS|BACKGROUND|PREAMBLE)',
            r'(?:DEFINITIONS|INTERPRETATION)',
            r'(?:SCOPE\s+OF\s+WORK|SERVICES|DELIVERABLES)',
            r'(?:PAYMENT\s+TERMS|FEES|COMPENSATION)',
            r'(?:CONFIDENTIALITY|NON-DISCLOSURE)',
            r'(?:INTELLECTUAL\s+PROPERTY|IP\s+RIGHTS)',
            r'(?:LIMITATION\s+OF\s+LIABILITY|INDEMNIFICATION)',
            r'(?:TERMINATION|EXPIRATION)',
            r'(?:GENERAL\s+PROVISIONS|MISCELLANEOUS)',
        ]
    
    def _analyze(self, text: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze contract-specific formatting and structure."""
        # Count contract indicators
        contract_matches = 0
        for pattern in self.contract_indicators:
            contract_matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Identify document sections
        found_sections = []
        for pattern in self.document_sections:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found_sections.append({
                    'section': pattern,
                    'match': match.group(),
                    'position': match.start()
                })
        
        # Detect signature blocks
        signature_patterns = [
            r'(?:SIGNATURE|EXECUTED|SIGNED)',
            r'(?:By:\s*_+|Signature:\s*_+)',
            r'(?:Date:\s*_+|Date\s+Signed)',
        ]
        
        signature_indicators = 0
        for pattern in signature_patterns:
            signature_indicators += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Calculate contract probability
        contract_probability = min(1.0, (contract_matches * 0.2 + 
                                       len(found_sections) * 0.1 + 
                                       signature_indicators * 0.3))
        
        analysis_result.update({
            'contract_indicators': contract_matches,
            'document_sections': found_sections,
            'signature_indicators': signature_indicators,
            'contract_probability': contract_probability,
            'is_contract': contract_probability > 0.5,
            'document_type': self._determine_document_type(contract_probability, found_sections)
        })
        
        return analysis_result
    
    def _determine_document_type(self, contract_prob: float, sections: List[Dict]) -> str:
        """Determine the type of legal document."""
        if contract_prob > 0.7:
            return 'contract'
        elif contract_prob > 0.4:
            return 'legal_agreement'
        elif any('POLICY' in s['match'].upper() for s in sections):
            return 'policy_document'
        elif any('TERMS' in s['match'].upper() for s in sections):
            return 'terms_of_service'
        else:
            return 'general_document'


def create_document_analysis_pipeline() -> DocumentAnalyzer:
    """Create the complete document analysis pipeline."""
    section_detector = SectionHeaderDetector()
    clause_detector = ClauseBoundaryDetector()
    paragraph_analyzer = ParagraphStructureAnalyzer()
    contract_handler = ContractFormatHandler()
    
    # Chain the analyzers
    section_detector.set_next(clause_detector).set_next(paragraph_analyzer).set_next(contract_handler)
    
    return section_detector


def analyze_document(text: str) -> Dict[str, Any]:
    """Analyze document using the complete pipeline."""
    pipeline = create_document_analysis_pipeline()
    initial_analysis = {
        'document_length': len(text),
        'word_count': len(text.split()),
        'line_count': len(text.split('\n'))
    }
    
    return pipeline.analyze(text, initial_analysis)