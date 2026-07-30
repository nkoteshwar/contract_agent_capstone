from typing import List, Dict, Any
from backend.shared.utils.gemini_embedding_service import embedding
from langchain_text_splitters import RecursiveCharacterTextSplitter
from . import EmbeddingStrategy

class DocumentEmbeddingStrategy(EmbeddingStrategy):
    """Strategy for generating document-level embeddings"""
    
    def __init__(self):
        self.embeddings = embedding
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=8000,  # Larger chunks for document-level context
            chunk_overlap=400,
            separators=["\n\n", "\n", ". ", " "]
        )
    
    def generate_embedding(self, content: str, metadata: Dict[str, Any] = None) -> List[float]:
        """Generate embedding for full document content"""
        # For very large documents, create a representative summary
        if len(content) > 10000:
            chunks = self.text_splitter.split_text(content)
            # Take first and last chunks plus middle chunk for representation
            representative_text = " ".join([
                chunks[0],
                chunks[len(chunks)//2] if len(chunks) > 2 else "",
                chunks[-1] if len(chunks) > 1 else ""
            ])
            content = representative_text
        
        return self.embeddings.embed_query(content)
    
    def get_embedding_dimension(self) -> int:
        return 1536  # Google text-embedding-004 dimension