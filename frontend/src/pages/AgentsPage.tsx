import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/shared/ui/card';
import { Badge } from '../components/shared/ui/badge';
import { agents, getAgentTools, agentPatterns } from '../data/agents';
import { CheckCircle, Clock, XCircle } from 'lucide-react';

const getPatternIcon = (status: string) => {
  switch (status) {
    case 'implemented': return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'partial': return <Clock className="w-4 h-4 text-yellow-500" />;
    case 'missing': return <XCircle className="w-4 h-4 text-red-500" />;
    default: return null;
  }
};

export const AgentsPage: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'agents' | 'patterns'>('agents');

  return (
    <div className="space-y-6">
      <div className="flex gap-4 border-b">
        <button
          onClick={() => setActiveTab('agents')}
          className={`pb-2 px-1 border-b-2 transition-colors ${
            activeTab === 'agents' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-600'
          }`}
        >
          Agent Architecture
        </button>
        <button
          onClick={() => setActiveTab('patterns')}
          className={`pb-2 px-1 border-b-2 transition-colors ${
            activeTab === 'patterns' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-600'
          }`}
        >
          AI Agent Patterns
        </button>
      </div>

      {activeTab === 'agents' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <Card 
              key={agent.id}
              className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
                selectedAgent === agent.id ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${agent.color} text-white`}>
                    {agent.icon}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <Badge variant="secondary" className="text-xs">{agent.role}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600 mb-4">{agent.description}</p>
                
                {selectedAgent === agent.id && (
                  <div className="space-y-4 border-t pt-4">
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Capabilities</h4>
                      <div className="flex flex-wrap gap-1">
                        {agent.capabilities.map((cap, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">{cap}</Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-slate-700">Input:</span>
                        <p className="text-slate-600">{agent.input}</p>
                      </div>
                      <div>
                        <span className="font-medium text-slate-700">Output:</span>
                        <p className="text-slate-600">{agent.output}</p>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Tools Used</h4>
                      <div className="bg-slate-50 rounded p-2 text-xs text-slate-600">
                        {getAgentTools(agent.id)}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'patterns' && (
        <div className="space-y-4">
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2">AI Agent Pattern Implementation Status</h3>
            <p className="text-sm text-slate-600">Overview of implemented and missing AI agent patterns in the contract intelligence system.</p>
          </div>
          
          {agentPatterns.map((pattern, idx) => (
            <Card key={idx} className="">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  {getPatternIcon(pattern.status)}
                  <div className="flex-1">
                    <CardTitle className="text-base">{pattern.name}</CardTitle>
                    <Badge 
                      variant={pattern.status === 'implemented' ? 'default' : pattern.status === 'partial' ? 'secondary' : 'destructive'}
                      className="text-xs mt-1"
                    >
                      {pattern.status.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600 mb-3">{pattern.description}</p>
                
                {pattern.location && (
                  <div className="mb-3">
                    <span className="font-medium text-xs text-slate-700">Location: </span>
                    <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">{pattern.location}</code>
                  </div>
                )}
                
                {pattern.justification && (
                  <div className="bg-slate-50 rounded p-3 text-sm">
                    <span className="font-medium text-slate-700">Implementation Notes: </span>
                    <p className="text-slate-600 mt-1">{pattern.justification}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};