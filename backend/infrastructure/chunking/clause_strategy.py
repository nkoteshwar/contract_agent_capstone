"""Clause-boundary detection chunking strategy for legal documents."""

import re
from typing import List, Dict, Any
from .base_strategy import IChunkingStrategy as ChunkingStrategy


class ClauseStrategy(ChunkingStrategy):
    """Chunks text based on legal clause boundaries and patterns."""
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List:
        """Compatibility method for existing interface."""
        chunks = self.chunk_text(content, metadata)
        # Convert to expected format
        results = []
        for chunk in chunks:
            result = type('ChunkResult', (), {
                'chunk_id': f"chunk_{chunk.get('chunk_index', 0)}",
                'content': chunk['content'],
                'chunk_type': chunk.get('chunk_type', 'clause'),
                'start_pos': chunk.get('start_position', 0),
                'end_pos': chunk.get('end_position', 0),
                'confidence': chunk.get('quality_score', 0.8)
            })()
            results.append(result)
        return results
    
    def get_chunk_size(self) -> int:
        """Return the target chunk size."""
        return self.max_chunk_size
    """Chunks text based on legal clause boundaries and patterns."""
    
    def __init__(self, min_chunk_size: int = 200, max_chunk_size: int = 800):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Legal clause patterns
        self.clause_patterns = [
            r'(?:PROVIDED|WHEREAS|THEREFORE|FURTHERMORE|NOTWITHSTANDING|IN CONSIDERATION)',
            r'(?:shall|will|must|may|should)\s+(?:not\s+)?(?:be|have|do|provide|ensure|maintain)',
            r'(?:Party|Parties|Company|Contractor|Client|Vendor)\s+(?:agrees?|acknowledges?|represents?)',
            r'(?:In the event|If|Unless|Except|Subject to)',
            r'(?:This Agreement|The Contract|These Terms)',
        ]
        
        # Clause ending patterns
        self.clause_endings = [
            r'[.;]\s*(?=\n|$)',  # Period or semicolon at line end
            r'[.]\s*(?=[A-Z])',  # Period followed by capital letter
        ]
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Chunk text by clause boundaries."""
        clauses = self._identify_clauses(text)
        
        if not clauses:
            return self._fallback_sentence_chunk(text, metadata)
        
        # Group small clauses together
        chunks = self._group_clauses(clauses, text)
        
        return self._add_overlap(chunks, text, metadata)
    
    def _identify_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Identify clause boundaries in legal text."""
        sentences = re.split(r'[.!?]+\s+', text)
        clauses = []
        current_clause = []
        current_start = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Find sentence position in original text
            sent_start = text.find(sentence, current_start)
            sent_end = sent_start + len(sentence)
            
            # Check if sentence starts a new clause
            is_clause_start = any(re.search(pattern, sentence, re.IGNORECASE) 
                                for pattern in self.clause_patterns)
            
            if is_clause_start and current_clause:
                # Finalize previous clause
                clause_content = ' '.join(current_clause)
                clauses.append({
                    'content': clause_content,
                    'start_position': current_start,
                    'end_position': current_start + len(clause_content),
                    'chunk_type': 'clause',
                    'size': len(clause_content)
                })
                
                # Start new clause
                current_clause = [sentence]
                current_start = sent_start
            else:
                current_clause.append(sentence)
            
            # Update position for next search
            current_start = sent_end
        
        # Add final clause
        if current_clause:
            clause_content = ' '.join(current_clause)
            clauses.append({
                'content': clause_content,
                'start_position': current_start,
                'end_position': len(text),
                'chunk_type': 'clause',
                'size': len(clause_content)
            })
        
        return clauses
    
    def _group_clauses(self, clauses: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Group small clauses together to meet minimum chunk size."""
        chunks = []
        current_group = []
        current_size = 0
        
        for clause in clauses:
            clause_size = clause['size']
            
            # If adding this clause exceeds max size, finalize current group
            if current_group and current_size + clause_size > self.max_chunk_size:
                chunks.append(self._create_grouped_chunk(current_group))
                current_group = [clause]
                current_size = clause_size
            else:
                current_group.append(clause)
                current_size += clause_size
                
                # If group meets minimum size and clause is complete, consider finalizing
                if current_size >= self.min_chunk_size:
                    # Check if next clause would exceed max size
                    next_clause_idx = clauses.index(clause) + 1
                    if (next_clause_idx < len(clauses) and 
                        current_size + clauses[next_clause_idx]['size'] > self.max_chunk_size):
                        chunks.append(self._create_grouped_chunk(current_group))
                        current_group = []
                        current_size = 0
        
        # Add final group
        if current_group:
            chunks.append(self._create_grouped_chunk(current_group))
        
        return chunks
    
    def _create_grouped_chunk(self, clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a chunk from grouped clauses."""
        if not clauses:
            return {}
        
        content = ' '.join(clause['content'] for clause in clauses)
        return {
            'content': content,
            'start_position': clauses[0]['start_position'],
            'end_position': clauses[-1]['end_position'],
            'chunk_type': 'clause_group',
            'size': len(content),
            'clause_count': len(clauses)
        }
    
    def _fallback_sentence_chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to sentence-based chunking when no clauses detected."""
        sentences = re.split(r'[.!?]+\s+', text)
        chunks = []
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if current_size + len(sentence) > self.max_chunk_size and current_chunk:
                chunk_content = ' '.join(current_chunk)
                chunks.append({
                    'content': chunk_content,
                    'start_position': start_pos,
                    'end_position': start_pos + len(chunk_content),
                    'chunk_type': 'sentence_fallback',
                    'size': len(chunk_content)
                })
                current_chunk = [sentence]
                current_size = len(sentence)
                start_pos += len(chunk_content) + 1
            else:
                current_chunk.append(sentence)
                current_size += len(sentence) + 1
        
        # Add final chunk
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunks.append({
                'content': chunk_content,
                'start_position': start_pos,
                'end_position': len(text),
                'chunk_type': 'sentence_fallback',
                'size': len(chunk_content)
            })
        
        return chunks
    
    def _add_overlap(self, chunks: List[Dict[str, Any]], text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add clause-aware overlap between chunks."""
        if len(chunks) <= 1:
            return chunks
        
        overlap_ratio = 0.25  # 25% overlap for clause-based chunks to preserve legal context
        
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Calculate overlap size
            overlap_size = int(len(current_chunk['content']) * overlap_ratio)
            
            # Add overlap from end of current chunk
            current_end = current_chunk['content'][-overlap_size:]
            next_chunk['content'] = current_end + " " + next_chunk['content']
            next_chunk['has_overlap'] = True
            next_chunk['overlap_size'] = overlap_size
        
        return chunks