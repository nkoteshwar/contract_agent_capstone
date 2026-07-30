export const getWorkflowBadgeText = (key: string): string => {
  const badgeTexts: Record<string, string> = {
    'storage': 'Automatic: Happens when you upload any document',
    'production_storage': 'Production: Enhanced workflow with tenant isolation & versioning',
    'chat': 'Try it: Go to Contract Search',
    'search': 'Try it: Use enhanced search with granular filters',
    'orchestration': 'Automatic: Multi-level embedding generation',
    'production_orchestration': 'Production: Enhanced embedding pipeline with fine-tuning & validation',
    'analysis': 'Try it: Upload PDF → Click Analyze'
  };
  return badgeTexts[key] || 'Available';
};

export const formatAgentName = (name: string): string => {
  return name.replace(/Agent$/, '').trim();
};

export const getStepTextColor = (step: { isNew?: boolean; isEnhanced?: boolean }): string => {
  if (step.isNew || step.isEnhanced) return 'text-red-600';
  return 'text-slate-800';
};