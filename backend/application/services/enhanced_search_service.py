from typing import Dict
from backend.domain.search_entities import SearchLevel, SearchParams, SearchResult
from backend.shared.utils.search_strategies import (
    SearchStrategy, 
    DocumentSearchStrategy, 
    ClauseSearchStrategy, 
    SectionSearchStrategy, 
    RelationshipSearchStrategy
)

class EnhancedSearchService:
    """Unified search service using Dependency Inversion principle"""
    
    def __init__(self):
        self._strategies: Dict[SearchLevel, SearchStrategy] = {
            SearchLevel.DOCUMENT: DocumentSearchStrategy(),
            SearchLevel.CLAUSE: ClauseSearchStrategy(),
            SearchLevel.SECTION: SectionSearchStrategy(),
            SearchLevel.RELATIONSHIP: RelationshipSearchStrategy()
        }
    
    def search(self, params: SearchParams) -> SearchResult:
        """Execute search using appropriate strategy"""
        if params.search_level == SearchLevel.ALL:
            return self._search_all_levels(params)
        
        strategy = self._strategies.get(params.search_level)
        if not strategy:
            raise ValueError(f"Unsupported search level: {params.search_level}")
        
        return strategy.execute(params)
    
    def _search_all_levels(self, params: SearchParams) -> SearchResult:
        """Combine results from all search levels"""
        all_results = {}
        total_count = 0
        
        for level, strategy in self._strategies.items():
            if level != SearchLevel.ALL:
                level_params = SearchParams(
                    search_level=level,
                    query=params.query,
                    clause_types=params.clause_types if level == SearchLevel.CLAUSE else None,
                    section_types=params.section_types if level == SearchLevel.SECTION else None,
                    parties=params.parties if level == SearchLevel.RELATIONSHIP else None
                )
                result = strategy.execute(level_params)
                all_results[level.value] = result.items
                total_count += result.total_count
        
        return SearchResult(
            total_count=total_count,
            items=[all_results],
            search_metadata={"search_level": "all", "query": params.query}
        )