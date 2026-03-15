'use client';

import { Wrench, GitBranch, Database, Cloud, Shield, Zap } from 'lucide-react';

const tools = [
  {
    name: 'Git Integration',
    description: 'Connect with GitHub, GitLab, and Bitbucket repositories',
    icon: GitBranch,
    status: 'available',
    color: 'bg-orange-500',
  },
  {
    name: 'Database Tools',
    description: 'Query and manage databases with AI assistance',
    icon: Database,
    status: 'available',
    color: 'bg-emerald-500',
  },
  {
    name: 'Cloud Services',
    description: 'Deploy and manage cloud resources',
    icon: Cloud,
    status: 'coming_soon',
    color: 'bg-sky-500',
  },
  {
    name: 'Security Scanner',
    description: 'Automated security vulnerability detection',
    icon: Shield,
    status: 'coming_soon',
    color: 'bg-red-500',
  },
  {
    name: 'Performance Profiler',
    description: 'Analyze and optimize application performance',
    icon: Zap,
    status: 'coming_soon',
    color: 'bg-yellow-500',
  },
];

export default function ToolsPage() {
  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Tools & Integrations</h1>
        <p className="text-slate-400">Extend your agents with powerful integrations</p>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tools.map((tool) => {
          const Icon = tool.icon;
          return (
            <div
              key={tool.name}
              className="p-6 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl ${tool.color}`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                {tool.status === 'coming_soon' && (
                  <span className="px-2 py-1 bg-slate-800 rounded-full text-xs text-slate-400">
                    Coming Soon
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-lg mb-2">{tool.name}</h3>
              <p className="text-slate-400 text-sm">{tool.description}</p>
              {tool.status === 'available' && (
                <button className="mt-4 w-full py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors">
                  Configure
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
