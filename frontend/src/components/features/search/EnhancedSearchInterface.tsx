import React, { useState } from 'react';
import { SearchLevelSelector, SearchLevel } from './SearchLevelSelector';
import { ClauseTypeFilter } from './ClauseTypeFilter';
import { SectionTypeFilter } from './SectionTypeFilter';
import { Search, Loader2 } from 'lucide-react';

interface EnhancedSearchInterfaceProps {
  onSearch: (searchParams: EnhancedSearchParams) => void;
  isLoading?: boolean;
  className?: string;
}

export interface EnhancedSearchParams {
  searchLevel: SearchLevel;
  query: string;
  clauseTypes: string[];
  sectionTypes: string[];
  parties: string[];
  contractType?: string;
  active?: boolean;
}

export const EnhancedSearchInterface: React.FC<EnhancedSearchInterfaceProps> = ({
  onSearch,
  isLoading = false,
  className = ''
}) => {
  const [searchLevel, setSearchLevel] = useState<SearchLevel>('document');
  const [query, setQuery] = useState('');
  const [clauseTypes, setClauseTypes] = useState<string[]>([]);
  const [sectionTypes, setSectionTypes] = useState<string[]>([]);
  const [parties, setParties] = useState<string[]>([]);
  const [contractType, setContractType] = useState('');
  const [active, setActive] = useState<boolean | undefined>(undefined);

  const handleSearch = () => {
    onSearch({
      searchLevel,
      query: query.trim(),
      clauseTypes,
      sectionTypes,
      parties,
      contractType: contractType.trim() || undefined,
      active
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleSearch();
    }
  };

  return (
    <div className={`space-y-6 bg-white rounded-lg border border-slate-200 p-6 ${className}`}>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-800">Enhanced Contract Search</h3>
        
        {/* Search Level Selector */}
        <SearchLevelSelector
          value={searchLevel}
          onChange={setSearchLevel}
        />

        {/* Search Query */}
        <div className="space-y-2">
          <label htmlFor="search-query" className="block text-sm font-medium text-slate-700">
            Search Query
          </label>
          <div className="relative">
            <input
              id="search-query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter your search query..."
              className="w-full px-4 py-2 pr-10 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              aria-describedby="search-help"
            />
            <Search className="absolute right-3 top-2.5 w-5 h-5 text-slate-400" aria-hidden="true" />
          </div>
          <p id="search-help" className="text-xs text-slate-500">
            Use natural language to search contracts
          </p>
        </div>

        {/* Conditional Filters Based on Search Level */}
        {(searchLevel === 'clause' || searchLevel === 'all') && (
          <ClauseTypeFilter
            selectedTypes={clauseTypes}
            onChange={setClauseTypes}
          />
        )}

        {(searchLevel === 'section' || searchLevel === 'all') && (
          <SectionTypeFilter
            selectedTypes={sectionTypes}
            onChange={setSectionTypes}
          />
        )}

        {/* Additional Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Contract Type */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-700">
              Contract Type
            </label>
            <input
              type="text"
              value={contractType}
              onChange={(e) => setContractType(e.target.value)}
              placeholder="e.g., MSA, SOW, NDA"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Active Status */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-700">
              Contract Status
            </label>
            <select
              value={active === undefined ? '' : active.toString()}
              onChange={(e) => setActive(e.target.value === '' ? undefined : e.target.value === 'true')}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Contracts</option>
              <option value="true">Active Only</option>
              <option value="false">Inactive Only</option>
            </select>
          </div>
        </div>

        {/* Parties Filter */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700">
            Parties (comma-separated)
          </label>
          <input
            type="text"
            value={parties.join(', ')}
            onChange={(e) => setParties(e.target.value.split(',').map(p => p.trim()).filter(p => p))}
            placeholder="e.g., Acme Corp, Tech Solutions Inc"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Search Button */}
        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label={isLoading ? 'Searching contracts...' : 'Search contracts'}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Search Contracts
            </>
          )}
        </button>
      </div>
      
      {/* CUAD Dataset Note */}
      <div className="mt-6 pt-4 border-t border-slate-200">
        <p className="text-xs text-slate-500 text-center">
          <strong>CUAD Dataset:</strong> Contract Understanding Atticus Dataset - 500+ legal contracts with 41 annotated clause types for comprehensive contract analysis.
        </p>
      </div>
    </div>
  );
};