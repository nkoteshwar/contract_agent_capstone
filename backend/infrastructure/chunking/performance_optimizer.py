"""Performance optimization using Singleton pattern."""

import asyncio
import hashlib
from typing import Dict, Any, List, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor


@dataclass
class CacheEntry:
    """Cache entry for document analysis results."""
    analysis_result: Dict[str, Any]
    document_hash: str
    timestamp: float


class PerformanceOptimizer:
    """Singleton performance optimizer for chunking operations."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.analysis_cache = DocumentAnalysisCache()
        self.parallel_processor = ParallelChunkProcessor()
        self.deduplicator = ChunkDeduplicator()
    
    async def optimize_chunking_pipeline(self, text: str, chunks: List[Dict[str, Any]], 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize entire chunking pipeline."""
        # Step 1: Check cache for document analysis
        doc_hash = self._calculate_text_hash(text)
        cached_analysis = self.analysis_cache.get_cached_analysis(doc_hash)
        
        # Step 2: Parallel processing if many chunks
        if len(chunks) > 10:
            chunks = await self.parallel_processor.process_chunks_parallel(chunks, context)
        
        # Step 3: Deduplicate chunks
        chunks = self.deduplicator.remove_duplicates(chunks)
        
        return {
            'optimized_chunks': chunks,
            'used_cache': cached_analysis is not None,
            'parallel_processed': len(chunks) > 10,
            'duplicates_removed': self.deduplicator.last_duplicate_count
        }
    
    def _calculate_text_hash(self, text: str) -> str:
        """Calculate hash for text caching."""
        return hashlib.md5(text.encode()).hexdigest()


class DocumentAnalysisCache:
    """Caches document analysis results by document type and characteristics."""
    
    def __init__(self, max_cache_size: int = 100):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_cache_size = max_cache_size
        self.hit_count = 0
        self.miss_count = 0
    
    def get_cached_analysis(self, document_hash: str) -> Dict[str, Any]:
        """Get cached analysis result."""
        if document_hash in self.cache:
            self.hit_count += 1
            return self.cache[document_hash].analysis_result
        
        self.miss_count += 1
        return None
    
    def cache_analysis(self, document_hash: str, analysis_result: Dict[str, Any]):
        """Cache analysis result."""
        import time
        
        # Clean cache if full
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()
        
        self.cache[document_hash] = CacheEntry(
            analysis_result=analysis_result,
            document_hash=document_hash,
            timestamp=time.time()
        )
    
    def _evict_oldest(self):
        """Evict oldest cache entry."""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
        del self.cache[oldest_key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / max(total_requests, 1)
        
        return {
            'cache_size': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }


class ParallelChunkProcessor:
    """Processes chunks in parallel for large documents."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_chunks_parallel(self, chunks: List[Dict[str, Any]], 
                                    context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process chunks in parallel batches."""
        if len(chunks) <= 5:
            return chunks  # Not worth parallelizing
        
        # Split into batches
        batch_size = max(2, len(chunks) // self.max_workers)
        batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
        
        # Process batches in parallel
        loop = asyncio.get_event_loop()
        tasks = []
        
        for batch in batches:
            task = loop.run_in_executor(
                self.executor,
                self._process_batch,
                batch,
                context
            )
            tasks.append(task)
        
        # Wait for all batches to complete
        processed_batches = await asyncio.gather(*tasks)
        
        # Flatten results
        processed_chunks = []
        for batch in processed_batches:
            processed_chunks.extend(batch)
        
        return processed_chunks
    
    def _process_batch(self, batch: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single batch of chunks."""
        processed_batch = []
        
        for chunk in batch:
            # Add processing optimizations
            processed_chunk = self._optimize_chunk(chunk, context)
            processed_batch.append(processed_chunk)
        
        return processed_batch
    
    def _optimize_chunk(self, chunk: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize individual chunk."""
        # Add performance optimizations
        chunk['processed_parallel'] = True
        
        # Optimize content if needed
        content = chunk.get('content', '')
        if len(content) > 2000:  # Large chunk
            chunk['content'] = self._optimize_large_content(content)
        
        return chunk
    
    def _optimize_large_content(self, content: str) -> str:
        """Optimize large content for better processing."""
        # Remove excessive whitespace
        import re
        content = re.sub(r'\s+', ' ', content)
        
        # Remove redundant punctuation
        content = re.sub(r'[.]{3,}', '...', content)
        
        return content.strip()


class ChunkDeduplicator:
    """Removes duplicate chunks from high overlap scenarios."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.last_duplicate_count = 0
    
    def remove_duplicates(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate chunks based on content similarity."""
        if len(chunks) <= 1:
            return chunks
        
        unique_chunks = []
        duplicate_count = 0
        
        for chunk in chunks:
            if not self._is_duplicate(chunk, unique_chunks):
                unique_chunks.append(chunk)
            else:
                duplicate_count += 1
        
        self.last_duplicate_count = duplicate_count
        return unique_chunks
    
    def _is_duplicate(self, chunk: Dict[str, Any], existing_chunks: List[Dict[str, Any]]) -> bool:
        """Check if chunk is duplicate of existing chunks."""
        chunk_content = chunk.get('content', '')
        
        for existing_chunk in existing_chunks:
            existing_content = existing_chunk.get('content', '')
            
            # Calculate similarity
            similarity = self._calculate_similarity(chunk_content, existing_content)
            
            if similarity >= self.similarity_threshold:
                return True
        
        return False
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate content similarity using simple word overlap."""
        if not content1 or not content2:
            return 0.0
        
        # Normalize content
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / max(union, 1)
    
    def remove_high_overlap_duplicates(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove chunks with excessive overlap."""
        if len(chunks) <= 1:
            return chunks
        
        filtered_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Check overlap with previous chunk
            if i > 0:
                prev_chunk = chunks[i - 1]
                overlap_ratio = self._calculate_overlap_ratio(chunk, prev_chunk)
                
                # Skip if overlap is too high
                if overlap_ratio > 0.8:
                    continue
            
            filtered_chunks.append(chunk)
        
        return filtered_chunks
    
    def _calculate_overlap_ratio(self, chunk1: Dict[str, Any], chunk2: Dict[str, Any]) -> float:
        """Calculate overlap ratio between two chunks."""
        content1 = chunk1.get('content', '')
        content2 = chunk2.get('content', '')
        
        if not content1 or not content2:
            return 0.0
        
        # Find common substring
        shorter = content1 if len(content1) < len(content2) else content2
        longer = content2 if len(content1) < len(content2) else content1
        
        # Simple overlap detection
        max_overlap = 0
        for i in range(len(shorter)):
            for j in range(i + 1, len(shorter) + 1):
                substring = shorter[i:j]
                if len(substring) > max_overlap and substring in longer:
                    max_overlap = len(substring)
        
        return max_overlap / max(len(shorter), 1)


# Singleton access function
def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the singleton performance optimizer instance."""
    return PerformanceOptimizer()


# Performance monitoring
class PerformanceMonitor:
    """Monitors chunking performance metrics."""
    
    def __init__(self):
        self.processing_times = []
        self.chunk_counts = []
        self.optimization_stats = {}
    
    def record_processing_time(self, processing_time: float, chunk_count: int):
        """Record processing performance."""
        self.processing_times.append(processing_time)
        self.chunk_counts.append(chunk_count)
    
    def record_optimization_stats(self, stats: Dict[str, Any]):
        """Record optimization statistics."""
        for key, value in stats.items():
            if key not in self.optimization_stats:
                self.optimization_stats[key] = []
            self.optimization_stats[key].append(value)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        if not self.processing_times:
            return {'error': 'No performance data recorded'}
        
        avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        avg_chunk_count = sum(self.chunk_counts) / len(self.chunk_counts)
        
        return {
            'average_processing_time': avg_processing_time,
            'average_chunk_count': avg_chunk_count,
            'total_documents_processed': len(self.processing_times),
            'optimization_stats': self.optimization_stats,
            'performance_trend': 'improving' if len(self.processing_times) > 1 and 
                               self.processing_times[-1] < self.processing_times[0] else 'stable'
        }