"""Paragraph-based chunking strategy for legal documents."""

import re
from typing import List, Dict, Any
from .base_strategy import IChunkingStrategy as ChunkingStrategy


class ParagraphStrategy(ChunkingStrategy):
    """Chunks text based on paragraph boundaries with legal document awareness."""
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List:
        """Compatibility method for existing interface."""
        chunks = self.chunk_text(content, metadata)
        # Convert to expected format
        results = []
        for chunk in chunks:
            result = type('ChunkResult', (), {
                'chunk_id': f"chunk_{chunk.get('chunk_index', 0)}",
                'content': chunk['content'],
                'chunk_type': chunk.get('chunk_type', 'paragraph'),
                'start_pos': chunk.get('start_position', 0),
                'end_pos': chunk.get('end_position', 0),
                'confidence': chunk.get('quality_score', 0.8)
            })()
            results.append(result)
        return results
    
    def get_chunk_size(self) -> int:
        """Return the target chunk size."""
        return self.max_chunk_size
    """Chunks text based on paragraph boundaries with legal document awareness."""
    
    def __init__(self, min_chunk_size: int = 300, max_chunk_size: int = 1200):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Chunk text by paragraph boundaries."""
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text.strip())
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for i, paragraph in enumerate(paragraphs):
            # Calculate positions
            para_start = text.find(paragraph, current_start)
            para_end = para_start + len(paragraph)
            
            # If adding this paragraph exceeds max size, finalize current chunk
            if current_chunk and len(current_chunk) + len(paragraph) > self.max_chunk_size:
                chunks.append(self._create_chunk(current_chunk, current_start, para_start - 1))
                current_chunk = paragraph
                current_start = para_start
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    current_start = para_start
            
            # Update position for next search
            current_start = para_end
        
        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, current_start, len(text)))
        
        return self._add_overlap(chunks, text, metadata)
    
    def _create_chunk(self, content: str, start_pos: int, end_pos: int) -> Dict[str, Any]:
        """Create chunk with metadata."""
        return {
            'content': content.strip(),
            'start_position': start_pos,
            'end_position': end_pos,
            'chunk_type': 'paragraph',
            'size': len(content)
        }
    
    def _add_overlap(self, chunks: List[Dict[str, Any]], text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add context-aware overlap between chunks."""
        if len(chunks) <= 1:
            return chunks
        
        # Determine overlap ratio based on document size
        doc_size = len(text)
        overlap_ratio = 0.3 if doc_size > 10000 else 0.15  # 30% for large, 15% for small
        
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Calculate overlap size
            overlap_size = int(len(current_chunk['content']) * overlap_ratio)
            
            # Add overlap from end of current chunk to beginning of next
            current_end = current_chunk['content'][-overlap_size:]
            next_chunk['content'] = current_end + "\n\n" + next_chunk['content']
            next_chunk['has_overlap'] = True
            next_chunk['overlap_size'] = overlap_size
        
        return chunks