import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/shared/ui/card';
import { Badge } from '../components/shared/ui/badge';
import { ArrowRight, Brain, Shield, CheckCircle, AlertTriangle, Zap, Users, FileText, Bot } from 'lucide-react';

export const SupervisorPage: React.FC = () => {
  const [expandedFlows, setExpandedFlows] = useState<Set<string>>(new Set());

  const toggleFlow = (flowId: string) => {
    const newExpanded = new Set(expandedFlows);
    if (newExpanded.has(flowId)) {
      newExpanded.delete(flowId);
    } else {
      newExpanded.add(flowId);
    }
    setExpandedFlows(newExpanded);
  };

  const coordinationFlows = [
    {
      id: 'initialization',
      title: 'Initialization Flow',
      icon: <Brain className="w-6 h-6" />,
      color: 'bg-purple-600',
      description: 'How supervisor initializes and registers agents',
      steps: [
        { name: 'SupervisorFactory', description: 'Creates supervisor instance', icon: <Brain className="w-5 h-5" /> },
        { name: 'AgentFactory', description: 'Creates adapter instances', icon: <Zap className="w-5 h-5" /> },
        { name: 'AgentRegistry', description: 'Registers all agents', icon: <Users className="w-5 h-5" /> },
        { name: 'QualityManager', description: 'Initializes validation strategies', icon: <Shield className="w-5 h-5" /> },
        { name: 'Ready State', description: 'Supervisor ready for coordination', icon: <CheckCircle className="w-5 h-5" /> }
      ]
    },
    {
      id: 'workflow_execution',
      title: 'Workflow Execution Flow',
      icon: <Zap className="w-6 h-6" />,
      color: 'bg-blue-600',
      description: 'Step-by-step agent coordination process',
      steps: [
        { name: 'API Request', description: 'POST /api/supervisor/workflow/execute', icon: <FileText className="w-5 h-5" /> },
        { name: 'PDF Processing', description: 'Extract text and metadata', icon: <FileText className="w-5 h-5" /> },
        { name: 'Clause Extraction', description: 'Extract 41 CUAD clause types', icon: <Bot className="w-5 h-5" /> },
        { name: 'Risk Assessment', description: 'Calculate risk scores', icon: <AlertTriangle className="w-5 h-5" /> },
        { name: 'Quality Validation', description: 'Validate each step output', icon: <Shield className="w-5 h-5" /> },
        { name: 'Result Aggregation', description: 'Combine all agent results', icon: <CheckCircle className="w-5 h-5" /> }
      ]
    },
    {
      id: 'error_handling',
      title: 'Error Handling Flow',
      icon: <Shield className="w-6 h-6" />,
      color: 'bg-red-600',
      description: 'How supervisor handles agent failures',
      steps: [
        { name: 'Agent Failure', description: 'Agent execution fails', icon: <AlertTriangle className="w-5 h-5" /> },
        { name: 'Circuit Breaker', description: 'Detects failure pattern', icon: <Shield className="w-5 h-5" /> },
        { name: 'Retry Manager', description: 'Exponential backoff retry', icon: <Zap className="w-5 h-5" /> },
        { name: 'Recovery Strategy', description: 'Retry/Switch/Degrade/Escalate', icon: <Brain className="w-5 h-5" /> },
        { name: 'Fallback Result', description: 'Graceful degradation', icon: <CheckCircle className="w-5 h-5" /> }
      ]
    },
    {
      id: 'quality_gates',
      title: 'Quality Gate Flow',
      icon: <CheckCircle className="w-6 h-6" />,
      color: 'bg-green-600',
      description: 'Quality validation between agent executions',
      steps: [
        { name: 'Agent Completion', description: 'Agent finishes execution', icon: <Bot className="w-5 h-5" /> },
        { name: 'Strategy Selection', description: 'Get validation strategy', icon: <Brain className="w-5 h-5" /> },
        { name: 'Output Validation', description: 'Validate structure & content', icon: <Shield className="w-5 h-5" /> },
        { name: 'Quality Scoring', description: 'Calculate A-F grade', icon: <CheckCircle className="w-5 h-5" /> },
        { name: 'Gate Decision', description: 'Pass/Fail/Retry decision', icon: <AlertTriangle className="w-5 h-5" /> }
      ]
    }
  ];

  const coordinationBenefits = [
    {
      title: 'Centralized Control',
      description: 'Single point for workflow management and orchestration',
      icon: <Brain className="w-5 h-5 text-purple-600" />,
      color: 'border-purple-200 bg-purple-50'
    },
    {
      title: 'Error Recovery',
      description: 'Automatic retry and fallback strategies for resilience',
      icon: <Shield className="w-5 h-5 text-red-600" />,
      color: 'border-red-200 bg-red-50'
    },
    {
      title: 'Quality Assurance',
      description: 'Validation gates between agents ensure output quality',
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
      color: 'border-green-200 bg-green-50'
    },
    {
      title: 'Shared Context',
      description: 'Agents access previous results through workflow memory',
      icon: <Users className="w-5 h-5 text-blue-600" />,
      color: 'border-blue-200 bg-blue-50'
    },
    {
      title: 'Circuit Protection',
      description: 'Prevents cascade failures with intelligent circuit breakers',
      icon: <Zap className="w-5 h-5 text-yellow-600" />,
      color: 'border-yellow-200 bg-yellow-50'
    },
    {
      title: 'Audit Trail',
      description: 'Complete workflow tracking and logging for compliance',
      icon: <FileText className="w-5 h-5 text-indigo-600" />,
      color: 'border-indigo-200 bg-indigo-50'
    }
  ];

  return (
    <div className="space-y-8">
      <div className="text-center bg-white rounded-lg p-8 shadow-sm border border-slate-200">
        <h1 className="text-3xl font-bold text-slate-800 mb-3">Supervisor Agent</h1>
        <p className="text-lg text-slate-600 max-w-3xl mx-auto">
          Enterprise-grade coordinator that orchestrates multi-agent workflows with error handling, 
          quality validation, and intelligent recovery strategies.
        </p>
      </div>

      {/* Coordination Flows */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-slate-800">Coordination Flows</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {coordinationFlows.map((flow) => (
            <Card 
              key={flow.id}
              className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
                expandedFlows.has(flow.id) ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => toggleFlow(flow.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${flow.color} text-white`}>
                    {flow.icon}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{flow.title}</CardTitle>
                    <p className="text-sm text-slate-600">{flow.description}</p>
                  </div>
                </div>
              </CardHeader>
              
              {expandedFlows.has(flow.id) && (
                <CardContent className="border-t pt-4">
                  <div className="space-y-3">
                    {flow.steps.map((step, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          <div className="p-2 bg-slate-100 rounded-full">
                            {step.icon}
                          </div>
                          <div className="min-w-0 flex-1">
                            <h4 className="font-semibold text-sm text-slate-800">{step.name}</h4>
                            <p className="text-xs text-slate-600">{step.description}</p>
                          </div>
                        </div>
                        {idx < flow.steps.length - 1 && (
                          <ArrowRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        )}
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4 pt-4 border-t">
                    <Badge variant="secondary" className="text-xs">
                      Click to collapse flow details
                    </Badge>
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      </div>

      {/* Coordination Benefits */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-slate-800">Coordination Benefits</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {coordinationBenefits.map((benefit, idx) => (
            <Card key={idx} className={`border ${benefit.color} hover:shadow-md transition-shadow`}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  {benefit.icon}
                  <div>
                    <h3 className="font-semibold text-sm text-slate-800 mb-1">{benefit.title}</h3>
                    <p className="text-xs text-slate-600">{benefit.description}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Architecture Overview */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-600" />
            Supervisor Architecture
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <h3 className="font-semibold mb-3 text-slate-800">SOLID Principles Implementation</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium mb-2 text-slate-700">Design Patterns</h4>
                <div className="space-y-1 text-xs text-slate-600">
                  <div>• Template Method (BaseAdapter)</div>
                  <div>• Strategy Pattern (Validation)</div>
                  <div>• Factory Pattern (Agent creation)</div>
                  <div>• Circuit Breaker (Failure protection)</div>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2 text-slate-700">Agentic AI Patterns</h4>
                <div className="space-y-1 text-xs text-slate-600">
                  <div>• Shared Context (Workflow memory)</div>
                  <div>• Agent Communication (Message bus)</div>
                  <div>• Quality Gates (Inter-agent validation)</div>
                  <div>• Dynamic Discovery (Registry pattern)</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex justify-center">
            <Badge variant="secondary" className="text-xs">
              Enterprise-grade coordination following software engineering best practices
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};