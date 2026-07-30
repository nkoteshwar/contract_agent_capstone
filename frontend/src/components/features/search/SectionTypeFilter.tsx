import React from 'react';

interface SectionTypeFilterProps {
  selectedTypes: string[];
  onChange: (types: string[]) => void;
  className?: string;
}

export const SectionTypeFilter: React.FC<SectionTypeFilterProps> = ({
  selectedTypes,
  onChange,
  className = ''
}) => {
  const sectionTypes = [
    { value: 'payment', label: 'Payment Terms', description: 'Payment schedules, fees, costs' },
    { value: 'termination', label: 'Termination', description: 'Contract ending conditions' },
    { value: 'liability', label: 'Liability', description: 'Damages, losses, limitations' },
    { value: 'intellectual_property', label: 'Intellectual Property', description: 'IP rights, patents, copyrights' },
    { value: 'confidentiality', label: 'Confidentiality', description: 'Non-disclosure, proprietary info' },
    { value: 'general', label: 'General', description: 'Other contract sections' }
  ];

  const handleTypeToggle = (type: string) => {
    if (selectedTypes.includes(type)) {
      onChange(selectedTypes.filter(t => t !== type));
    } else {
      onChange([...selectedTypes, type]);
    }
  };

  const handleSelectAll = () => {
    onChange(sectionTypes.map(t => t.value));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-slate-700">
          Section Types ({selectedTypes.length} selected)
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleSelectAll}
            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            All
          </button>
          <button
            type="button"
            onClick={handleClearAll}
            className="px-2 py-1 text-xs bg-slate-100 text-slate-700 rounded hover:bg-slate-200"
          >
            None
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {sectionTypes.map((type) => (
          <label
            key={type.value}
            className={`
              flex flex-col p-3 rounded-lg border cursor-pointer transition-all
              ${selectedTypes.includes(type.value)
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-slate-200 bg-white hover:border-slate-300'
              }
            `}
          >
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedTypes.includes(type.value)}
                onChange={() => handleTypeToggle(type.value)}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium text-sm">{type.label}</span>
            </div>
            <span className="text-xs text-slate-500 mt-1 ml-6">{type.description}</span>
          </label>
        ))}
      </div>
    </div>
  );
};