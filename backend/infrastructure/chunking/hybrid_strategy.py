"""Hybrid chunking strategy combining multiple approaches."""

from typing import List, Dict, Any
from .base_strategy import IChunkingStrategy as ChunkingStrategy
from .sentence_strategy import SentenceAdaptiveStrategy as SentenceStrategy
from .paragraph_strategy import ParagraphStrategy
from .section_strategy import SectionStrategy
from .clause_strategy import ClauseStrategy


class HybridStrategy(ChunkingStrategy):
    """Combines multiple chunking strategies for optimal results."""
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List:
        """Compatibility method for existing interface."""
        chunks = self.chunk_text(content, metadata)
        # Convert to expected format
        results = []
        for chunk in chunks:
            result = type('ChunkResult', (), {
                'chunk_id': f"chunk_{chunk.get('chunk_index', 0)}",
                'content': chunk['content'],
                'chunk_type': chunk.get('chunk_type', 'hybrid'),
                'start_pos': chunk.get('start_position', 0),
                'end_pos': chunk.get('end_position', 0),
                'confidence': chunk.get('quality_score', 0.8)
            })()
            results.append(result)
        return results
    
    def get_chunk_size(self) -> int:
        """Return the target chunk size."""
        return self.max_chunk_size
    """Combines multiple chunking strategies for optimal results."""
    
    def __init__(self, min_chunk_size: int = 400, max_chunk_size: int = 1000):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Initialize all strategies
        self.section_strategy = SectionStrategy(min_chunk_size, max_chunk_size)
        self.clause_strategy = ClauseStrategy(min_chunk_size//2, max_chunk_size)
        self.paragraph_strategy = ParagraphStrategy(min_chunk_size, max_chunk_size)
        self.sentence_strategy = SentenceStrategy(min_chunk_size, max_chunk_size)
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Apply hybrid chunking strategy based on document analysis."""
        # Analyze document to determine best approach
        doc_analysis = self._analyze_document(text)
        
        # Choose primary strategy based on analysis
        if doc_analysis['has_sections'] and doc_analysis['section_count'] >= 3:
            primary_chunks = self.section_strategy.chunk_text(text, metadata)
            primary_strategy = 'section'
        elif doc_analysis['has_clauses'] and doc_analysis['clause_density'] > 0.3:
            primary_chunks = self.clause_strategy.chunk_text(text, metadata)
            primary_strategy = 'clause'
        elif doc_analysis['paragraph_count'] >= 5:
            primary_chunks = self.paragraph_strategy.chunk_text(text, metadata)
            primary_strategy = 'paragraph'
        else:
            primary_chunks = self.sentence_strategy.chunk_text(text, metadata)
            primary_strategy = 'sentence'
        
        # Refine chunks that are too large or too small
        refined_chunks = self._refine_chunks(primary_chunks, text, primary_strategy)
        
        # Add hybrid metadata
        for chunk in refined_chunks:
            chunk['primary_strategy'] = primary_strategy
            chunk['hybrid_processed'] = True
            chunk['document_analysis'] = doc_analysis
        
        return refined_chunks
    
    def _analyze_document(self, text: str) -> Dict[str, Any]:
        """Analyze document structure to determine optimal chunking strategy."""
        import re
        
        # Section analysis
        section_patterns = [
            r'^(?:ARTICLE|Article|SECTION|Section)\s+[IVX\d]+',
            r'^\d+\.\s+[A-Z][^.]*[.:]',
            r'^[A-Z][A-Z\s]{10,}:?\s*$'
        ]
        section_matches = sum(1 for pattern in section_patterns 
                            for _ in re.finditer(pattern, text, re.MULTILINE))
        
        # Clause analysis
        clause_patterns = [
            r'(?:PROVIDED|WHEREAS|THEREFORE|FURTHERMORE)',
            r'(?:shall|will|must|may)\s+(?:not\s+)?(?:be|have|do)',
            r'(?:Party|Parties|Company)\s+(?:agrees?|acknowledges?)'
        ]
        clause_matches = sum(1 for pattern in clause_patterns 
                           for _ in re.finditer(pattern, text, re.IGNORECASE))
        
        # Paragraph analysis
        paragraphs = len(re.split(r'\n\s*\n', text))
        
        # Sentence analysis
        sentences = len(re.split(r'[.!?]+\s+', text))
        
        return {
            'has_sections': section_matches >= 2,
            'section_count': section_matches,
            'has_clauses': clause_matches >= 3,
            'clause_density': clause_matches / max(sentences, 1),
            'paragraph_count': paragraphs,
            'sentence_count': sentences,
            'document_length': len(text),
            'avg_paragraph_length': len(text) / max(paragraphs, 1)
        }
    
    def _refine_chunks(self, chunks: List[Dict[str, Any]], text: str, primary_strategy: str) -> List[Dict[str, Any]]:
        """Refine chunks that are too large or too small."""
        refined_chunks = []
        
        for chunk in chunks:
            chunk_size = chunk['size']
            
            if chunk_size < self.min_chunk_size:
                # Chunk too small - try to merge with next or expand
                refined_chunks.append(self._expand_small_chunk(chunk, text))
            elif chunk_size > self.max_chunk_size:
                # Chunk too large - split using secondary strategy
                split_chunks = self._split_large_chunk(chunk, primary_strategy)
                refined_chunks.extend(split_chunks)
            else:
                # Chunk size is good
                refined_chunks.append(chunk)
        
        # Merge adjacent small chunks
        return self._merge_small_adjacent_chunks(refined_chunks)
    
    def _expand_small_chunk(self, chunk: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Expand small chunks by adding surrounding context."""
        start_pos = chunk['start_position']
        end_pos = chunk['end_position']
        
        # Try to expand backwards and forwards
        expansion_size = (self.min_chunk_size - chunk['size']) // 2
        
        new_start = max(0, start_pos - expansion_size)
        new_end = min(len(text), end_pos + expansion_size)
        
        # Adjust to sentence boundaries
        if new_start > 0:
            # Find previous sentence boundary
            prev_text = text[new_start:start_pos]
            sentence_end = prev_text.rfind('.')
            if sentence_end != -1:
                new_start = new_start + sentence_end + 1
        
        if new_end < len(text):
            # Find next sentence boundary
            next_text = text[end_pos:new_end]
            sentence_end = next_text.find('.')
            if sentence_end != -1:
                new_end = end_pos + sentence_end + 1
        
        expanded_content = text[new_start:new_end].strip()
        
        return {
            **chunk,
            'content': expanded_content,
            'start_position': new_start,
            'end_position': new_end,
            'size': len(expanded_content),
            'expanded': True
        }
    
    def _split_large_chunk(self, chunk: Dict[str, Any], primary_strategy: str) -> List[Dict[str, Any]]:
        """Split large chunks using secondary strategy."""
        content = chunk['content']
        
        # Choose secondary strategy different from primary
        if primary_strategy == 'section':
            secondary_chunks = self.paragraph_strategy.chunk_text(content)
        elif primary_strategy == 'paragraph':
            secondary_chunks = self.sentence_strategy.chunk_text(content)
        else:
            secondary_chunks = self.sentence_strategy.chunk_text(content)
        
        # Adjust positions relative to original text
        base_start = chunk['start_position']
        for sec_chunk in secondary_chunks:
            sec_chunk['start_position'] += base_start
            sec_chunk['end_position'] += base_start
            sec_chunk['parent_chunk_type'] = chunk.get('chunk_type', 'unknown')
            sec_chunk['split_from_large'] = True
        
        return secondary_chunks
    
    def _merge_small_adjacent_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge adjacent chunks that are both small."""
        if len(chunks) <= 1:
            return chunks
        
        merged_chunks = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # Check if current and next chunk are both small
            if (i + 1 < len(chunks) and 
                current_chunk['size'] < self.min_chunk_size and 
                chunks[i + 1]['size'] < self.min_chunk_size and
                current_chunk['size'] + chunks[i + 1]['size'] <= self.max_chunk_size):
                
                # Merge chunks
                next_chunk = chunks[i + 1]
                merged_content = current_chunk['content'] + "\n\n" + next_chunk['content']
                
                merged_chunk = {
                    'content': merged_content,
                    'start_position': current_chunk['start_position'],
                    'end_position': next_chunk['end_position'],
                    'chunk_type': 'merged',
                    'size': len(merged_content),
                    'merged_from': [current_chunk.get('chunk_type'), next_chunk.get('chunk_type')],
                    'merged_count': 2
                }
                
                merged_chunks.append(merged_chunk)
                i += 2  # Skip next chunk as it's been merged
            else:
                merged_chunks.append(current_chunk)
                i += 1
        
        return merged_chunks