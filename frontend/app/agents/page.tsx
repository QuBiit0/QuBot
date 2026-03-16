'use client';

import { useState, useEffect } from 'react';
import { useAgents } from '@/hooks/useAgents';
import { useAgentsStore } from '@/store/agents.store';
import { useCreateAgent } from '@/hooks/useAgents';
import { AgentWizard } from '@/components/wizard/AgentWizard';
import { PageLoader, ErrorMessage, EmptyState, toast } from '@/components/ui';
import { Plus, User, MoreVertical, Cpu, Activity, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

const domainColors: Record<string, string> = {
  development: 'bg-emerald-500',
  design: 'bg-pink-500',
  marketing: 'bg-purple-500',
  sales: 'bg-orange-500',
  support: 'bg-cyan-500',
  analytics: 'bg-indigo-500',
  product: 'bg-sky-500',
  devops: 'bg-lime-500',
};

const stateColors: Record<string, string> = {
  idle: 'text-slate-400',
  working: 'text-emerald-400',
  thinking: 'text-amber-400',
  talking: 'text-blue-400',
};

export default function AgentsPage() {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const { isLoading, error, refetch } = useAgents();
  const agents = useAgentsStore((s) => Object.values(s.agents));
  const createAgent = useCreateAgent();

  // Initialize mock data
  useEffect(() => {
    const init = async () => {
      const { initializeMockData } = await import('@/lib/mock-data');
      initializeMockData();
    };
    init();
  }, []);

  const handleCreateAgent = (agentData: Parameters<typeof createAgent.mutate>[0]) => {
    createAgent.mutate(agentData, {
      onSuccess: () => {
        toast.success('Agent created', `${agentData.name} has been added to your team`);
        setIsWizardOpen(false);
      },
      onError: (error) => {
        toast.error('Failed to create agent', error.message);
      },
    });
  };

  if (isLoading) {
    return <PageLoader />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load agents"
        message={error.message}
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Agents</h1>
          <p className="text-slate-400">Manage your AI workforce</p>
        </div>
        <button
          onClick={() => setIsWizardOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Agent
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Total Agents"
          value={agents.length}
          icon={<User className="w-5 h-5" />}
        />
        <StatCard
          label="Active"
          value={agents.filter((a) => a.state === 'working').length}
          icon={<Activity className="w-5 h-5" />}
          color="emerald"
        />
        <StatCard
          label="Idle"
          value={agents.filter((a) => a.state === 'idle').length}
          icon={<Cpu className="w-5 h-5" />}
          color="slate"
        />
        <StatCard
          label="Domains"
          value={new Set(agents.map((a) => a.domain)).size}
          icon={<Users className="w-5 h-5" />}
          color="purple"
        />
      </div>

      {/* Agents Grid */}
      <div className="flex-1 overflow-y-auto">
        {agents.length === 0 ? (
          <EmptyState
            icon={<User className="w-8 h-8 text-slate-500" />}
            title="No agents yet"
            description="Create your first AI agent to get started with Qubot"
            action={
              <button
                onClick={() => setIsWizardOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
              >
                <Plus className="w-4 h-4" />
                Create Agent
              </button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg',
                        domainColors[agent.domain?.toLowerCase() ?? ''] || 'bg-blue-500'
                      )}
                    >
                      {agent.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-semibold">{agent.name}</h3>
                      <p className="text-sm text-slate-400">{agent.role}</p>
                    </div>
                  </div>
                  <button className="p-1.5 text-slate-500 hover:text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Domain</span>
                    <span className="capitalize">{agent.domain}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Status</span>
                    <span className={cn('capitalize', stateColors[agent.state])}>
                      {agent.state}
                    </span>
                  </div>
                  {agent.current_task && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Current Task</span>
                      <span className="truncate max-w-[120px]">
                        {agent.current_task.title}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2 mt-4 pt-4 border-t border-slate-800">
                  <button className="flex-1 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
                    Assign Task
                  </button>
                  <button className="flex-1 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
                    Chat
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Agent Creation Wizard */}
      <AgentWizard
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onCreate={handleCreateAgent}
      />
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  color = 'blue',
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  color?: 'blue' | 'emerald' | 'slate' | 'purple';
}) {
  const colorClasses = {
    blue: 'bg-blue-500/10 text-blue-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    slate: 'bg-slate-500/10 text-slate-400',
    purple: 'bg-purple-500/10 text-purple-400',
  };

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
      <div className="flex items-center justify-between mb-2">
        <span className="text-slate-400 text-sm">{label}</span>
        <span className={cn('p-2 rounded-lg', colorClasses[color])}>
          {icon}
        </span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
