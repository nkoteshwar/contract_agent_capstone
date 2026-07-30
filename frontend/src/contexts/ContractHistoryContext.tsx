import React, { createContext, useContext, useState, useEffect } from 'react';

interface ContractRecord {
  contract_id: string;
  filename: string;
  upload_date: string;
  model_used: string;
  analysis_completed: boolean;
  risk_score?: number;
  risk_level?: string;
  analysis_results?: any; // Cache analysis results
}

interface ContractHistoryContextType {
  contracts: ContractRecord[];
  addContract: (contract: ContractRecord) => void;
  updateContract: (contract_id: string, updates: Partial<ContractRecord>) => void;
  getContract: (contract_id: string) => ContractRecord | undefined;
  clearHistory: () => void;
  selectedContractId: string | null;
  setSelectedContract: (contract_id: string | null) => void;
}

const ContractHistoryContext = createContext<ContractHistoryContextType | undefined>(undefined);

export const ContractHistoryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [contracts, setContracts] = useState<ContractRecord[]>([]);
  const [selectedContractId, setSelectedContractId] = useState<string | null>(null);

  // Load from localStorage on mount with validation
  useEffect(() => {
    const saved = localStorage.getItem('contract_history');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Validate contract data structure
        const validContracts = parsed.filter((contract: any) =>
          contract.contract_id &&
          contract.filename &&
          contract.upload_date &&
          contract.model_used !== undefined &&
          contract.analysis_completed !== undefined
        );
        setContracts(validContracts);

        // Clean up localStorage if we filtered out invalid contracts
        if (validContracts.length !== parsed.length) {
          localStorage.setItem('contract_history', JSON.stringify(validContracts));
        }
      } catch (e) {
        // removed console error
        localStorage.removeItem('contract_history'); // Clear corrupted data
      }
    }
  }, []);

  // Save to localStorage whenever contracts change with error handling
  useEffect(() => {
    try {
      localStorage.setItem('contract_history', JSON.stringify(contracts));
    } catch (e) {
      // removed console error
      // If localStorage is full, remove oldest contracts
      if (contracts.length > 10) {
        const trimmed = contracts.slice(0, 10);
        setContracts(trimmed);
      }
    }
  }, [contracts]);

  const addContract = (contract: ContractRecord) => {
    setContracts(prev => {
      // Remove existing contract with same ID if it exists
      const filtered = prev.filter(c => c.contract_id !== contract.contract_id);
      return [contract, ...filtered]; // Add new contract at the beginning
    });
  };

  const updateContract = (contract_id: string, updates: Partial<ContractRecord>) => {
    setContracts(prev =>
      prev.map(contract =>
        contract.contract_id === contract_id
          ? { ...contract, ...updates }
          : contract
      )
    );
  };

  const setSelectedContract = (contract_id: string | null) => {
    setSelectedContractId(contract_id);
  };

  const getContract = (contract_id: string) => {
    return contracts.find(c => c.contract_id === contract_id);
  };

  const clearHistory = () => {
    setContracts([]);
    localStorage.removeItem('contract_history');
  };

  return (
    <ContractHistoryContext.Provider value={{
      contracts,
      addContract,
      updateContract,
      getContract,
      clearHistory,
      selectedContractId,
      setSelectedContract
    }}>
      {children}
    </ContractHistoryContext.Provider>
  );
};

export const useContractHistory = () => {
  const context = useContext(ContractHistoryContext);
  if (!context) {
    throw new Error('useContractHistory must be used within ContractHistoryProvider');
  }
  return context;
};