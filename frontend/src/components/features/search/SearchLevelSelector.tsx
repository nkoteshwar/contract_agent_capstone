import React from 'react';

export type SearchLevel = 'document' | 'section' | 'clause' | 'relationship' | 'all';

interface SearchLevelSelectorProps {
  value: SearchLevel;
  onChange: (level: SearchLevel) => void;
  className?: string;
}

export const SearchLevelSelector: React.FC<SearchLevelSelectorProps> = ({
  value,
  onChange,
  className = ''
}) => {
  const levels = [
    { value: 'document' as SearchLevel, label: 'Document', description: 'Search entire contracts' },
    { value: 'section' as SearchLevel, label: 'Section', description: 'Search contract sections' },
    { value: 'clause' as SearchLevel, label: 'Clause', description: 'Search specific clauses' },
    { value: 'relationship' as SearchLevel, label: 'Relationship', description: 'Search party relationships' },
    { value: 'all' as SearchLevel, label: 'All Levels', description: 'Search across all levels' }
  ];

  return (
    <div className={`space-y-3 ${className}`}>
      <label className="block text-sm font-medium text-slate-700">
        Search Level
      </label>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        {levels.map((level) => (
          <label
            key={level.value}
            className={`
              relative flex flex-col p-3 rounded-lg border cursor-pointer transition-all
              ${value === level.value 
                ? 'border-blue-500 bg-blue-50 text-blue-700' 
                : 'border-slate-200 bg-white hover:border-slate-300'
              }
            `}
          >
            <input
              type="radio"
              name="searchLevel"
              value={level.value}
              checked={value === level.value}
              onChange={(e) => onChange(e.target.value as SearchLevel)}
              className="sr-only"
            />
            <span className="font-medium text-sm">{level.label}</span>
            <span className="text-xs text-slate-500 mt-1">{level.description}</span>
          </label>
        ))}
      </div>
    </div>
  );
};