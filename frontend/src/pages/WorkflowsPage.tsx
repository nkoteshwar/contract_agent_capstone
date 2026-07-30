import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/shared/ui/card';
import { Badge } from '../components/shared/ui/badge';
import { ArrowRight } from 'lucide-react';
import { workflows } from '../data/workflows.tsx';
import { getWorkflowBadgeText, getStepTextColor } from '../utils/documentation';

export const WorkflowsPage: React.FC = () => {
  const [activeWorkflows, setActiveWorkflows] = useState<Set<string>>(new Set());

  const toggleWorkflow = (key: string) => {
    const newActiveWorkflows = new Set(activeWorkflows);
    if (newActiveWorkflows.has(key)) {
      newActiveWorkflows.delete(key);
    } else {
      newActiveWorkflows.add(key);
    }
    setActiveWorkflows(newActiveWorkflows);
  };

  return (
    <div className="space-y-8">
      <div className="text-center bg-white rounded-lg p-8 shadow-sm border border-slate-200">
        <h1 className="text-3xl font-bold text-slate-800 mb-3">AI Workflows</h1>
        <p className="text-lg text-slate-600 max-w-3xl mx-auto">
          Multi-agent workflows that orchestrate contract processing and analysis.
        </p>
      </div>

      <div className="space-y-6">
        {Object.entries(workflows).map(([key, workflow]) => (
          <Card 
            key={key} 
            className={`overflow-hidden cursor-pointer transition-all duration-200 ${
              activeWorkflows.has(key) ? 'ring-2 ring-blue-500 shadow-lg' : 'hover:shadow-md'
            }`}
            onClick={() => toggleWorkflow(key)}
          >
            <CardHeader className="bg-slate-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500 text-white rounded-lg">
                    {workflow.icon}
                  </div>
                  <div>
                    <CardTitle className="text-xl">{workflow.title}</CardTitle>
                    <p className="text-slate-600">{workflow.description}</p>
                  </div>
                </div>
                <Badge variant="outline">Click to expand</Badge>
              </div>
            </CardHeader>
            {activeWorkflows.has(key) && (
              <CardContent className="p-6 border-t">
                <div className="flex items-center justify-between">
                  {workflow.steps.map((step, idx) => (
                    <React.Fragment key={idx}>
                      <div className="flex flex-col items-center text-center max-w-32">
                        <div className="p-3 bg-slate-100 rounded-full mb-2 hover:bg-blue-100 transition-colors">
                          {step.icon}
                        </div>
                        <h4 className={`font-semibold text-sm mb-1 ${getStepTextColor(step)}`}>
                          {step.agent}
                        </h4>
                        <p className="text-xs text-slate-600 mb-2">{step.description}</p>
                        <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded border">
                          {step.tech}
                        </div>
                      </div>
                      {idx < workflow.steps.length - 1 && (
                        <ArrowRight className="w-5 h-5 text-slate-400 mx-2 animate-pulse" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
                
                <div className="mt-6 pt-4 border-t">
                  <div className="flex justify-center">
                    <Badge variant="secondary">
                      {getWorkflowBadgeText(key)}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};