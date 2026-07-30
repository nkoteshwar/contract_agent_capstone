import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface ClauseTypeFilterProps {
  selectedTypes: string[];
  onChange: (types: string[]) => void;
  className?: string;
}

export const ClauseTypeFilter: React.FC<ClauseTypeFilterProps> = ({
  selectedTypes,
  onChange,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const cuadClauseTypes = [
    "Document Name", "Parties", "Agreement Date", "Effective Date", "Expiration Date",
    "Renewal Term", "Notice Period To Terminate Renewal", "Governing Law", 
    "Most Favored Nation", "Non-Compete", "Exclusivity", "No-Solicit Of Customers",
    "No-Solicit Of Employees", "Non-Disparagement", "Termination For Convenience",
    "Rofr/Rofo/Rofn", "Change Of Control", "Anti-Assignment", "Revenue/Customer Sharing",
    "Price Restrictions", "Minimum Commitment", "Volume Restriction", "IP Ownership Assignment",
    "Joint IP Ownership", "License Grant", "Non-Transferable License", "Affiliate License-Licensor",
    "Affiliate License-Licensee", "Unlimited/All-You-Can-Eat-License", "Irrevocable Or Perpetual License",
    "Source Code Escrow", "Post-Termination Services", "Audit Rights", "Uncapped Liability",
    "Cap On Liability", "Liquidated Damages", "Warranty Duration", "Insurance",
    "Covenant Not To Sue", "Third Party Beneficiary", "Escrow"
  ];

  const handleTypeToggle = (type: string) => {
    if (selectedTypes.includes(type)) {
      onChange(selectedTypes.filter(t => t !== type));
    } else {
      onChange([...selectedTypes, type]);
    }
  };

  const handleSelectAll = () => {
    onChange(cuadClauseTypes);
  };

  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-slate-700">
          CUAD Clause Types ({selectedTypes.length} selected)
        </label>
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center text-sm text-blue-600 hover:text-blue-700"
        >
          {isExpanded ? (
            <>Hide <ChevronUp className="w-4 h-4 ml-1" /></>
          ) : (
            <>Show <ChevronDown className="w-4 h-4 ml-1" /></>
          )}
        </button>
      </div>

      {isExpanded && (
        <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
          <div className="flex gap-2 mb-3">
            <button
              type="button"
              onClick={handleSelectAll}
              className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            >
              Select All
            </button>
            <button
              type="button"
              onClick={handleClearAll}
              className="px-3 py-1 text-xs bg-slate-100 text-slate-700 rounded hover:bg-slate-200"
            >
              Clear All
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-60 overflow-y-auto">
            {cuadClauseTypes.map((type) => (
              <label
                key={type}
                className="flex items-center space-x-2 p-2 rounded hover:bg-white cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedTypes.includes(type)}
                  onChange={() => handleTypeToggle(type)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700">{type}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};