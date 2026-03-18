'use client';

import { useState } from 'react';
import { useAgents, useCreateAgent } from '@/hooks/useAgents';
import { useAgentsStore } from '@/store/agents.store';
import { AgentWizard } from '@/components/wizard/AgentWizard';
import { PageLoader, ErrorMessage, EmptyState, toast } from '@/components/ui';
import { Plus, User, MoreVertical, Cpu, Activity, Users, Settings, Zap, ArrowRight, ShieldCheck } from 'lucide-react';

export default function AgentsPage() {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const { isLoading, error, refetch } = useAgents();
  const agents = useAgentsStore((s) => Object.values(s.agents));
  const createAgent = useCreateAgent();

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

  if (isLoading) return <PageLoader />;
  if (error) return <ErrorMessage title="Failed to load agents" message={error.message} onRetry={() => refetch()} />;

  const activeAgents = agents.filter((a) => a.state === 'working').length;
  const idleAgents = agents.filter((a) => a.state === 'idle').length;
  const totalDomains = new Set(agents.map((a) => a.domain)).size;

  return (
    <div className="h-full flex flex-col p-6 bg-slate-950 text-slate-200 relative overflow-hidden">
      {/* Premium Background Elements */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[800px] h-[800px] bg-indigo-600/10 rounded-full blur-[150px] pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between mb-8 relative z-10">
        <div>
          <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 tracking-tight">
            Agent Dashboard
          </h1>
          <p className="text-slate-400 mt-2 font-medium">Manage and deploy your autonomous AI workforce</p>
        </div>
        <button
          onClick={() => setIsWizardOpen(true)}
          className="group relative flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold text-white transition-all shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:shadow-[0_0_30px_rgba(37,99,235,0.6)] hover:-translate-y-0.5"
        >
          <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-400 to-indigo-500 opacity-0 group-hover:opacity-20 transition-opacity" />
          <Plus className="w-5 h-5" />
          Deploy New Agent
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8 relative z-10">
        <StatCard label="Total Agents" value={agents.length} icon={<User className="w-6 h-6" />} color="blue" />
        <StatCard label="Active Nodes" value={activeAgents} icon={<Activity className="w-6 h-6" />} color="emerald" pulse />
        <StatCard label="Idle Nodes" value={idleAgents} icon={<Cpu className="w-6 h-6" />} color="slate" />
        <StatCard label="Active Domains" value={totalDomains} icon={<Users className="w-6 h-6" />} color="purple" />
      </div>

      {/* Agents Grid */}
      <div className="flex-1 overflow-y-auto relative z-10 pr-2 custom-scrollbar">
        {agents.length === 0 ? (
          <EmptyState
            icon={<ShieldCheck className="w-12 h-12 text-blue-500/50" />}
            title="Core Database Empty"
            description="Initialize your first agent to bootstrap the Qubot system."
            action={
              <button
                onClick={() => setIsWizardOpen(true)}
                className="mt-4 flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl font-medium transition-all"
              >
                <Zap className="w-4 h-4 text-blue-400" />
                Initialize Agent
              </button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-6">
            {agents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        )}
      </div>

      <AgentWizard isOpen={isWizardOpen} onClose={() => setIsWizardOpen(false)} onCreate={handleCreateAgent} />
    </div>
  );
}

function StatCard({ label, value, icon, color = 'blue', pulse = false }: any) {
  const colorMap: any = {
    blue: 'from-blue-500/20 to-blue-600/5 border-blue-500/30 text-blue-400',
    emerald: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/30 text-emerald-400',
    slate: 'from-slate-500/20 to-slate-600/5 border-slate-500/30 text-slate-400',
    purple: 'from-purple-500/20 to-purple-600/5 border-purple-500/30 text-purple-400',
  };

  return (
    <div className={`relative p-6 rounded-2xl bg-gradient-to-br border backdrop-blur-sm ${colorMap[color]} shadow-lg overflow-hidden group hover:border-opacity-50 transition-all`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-slate-300 font-medium uppercase tracking-wider text-xs">{label}</span>
        <div className={`p-2 rounded-xl bg-slate-950/50 shadow-inner ${pulse ? 'animate-pulse' : ''}`}>
          {icon}
        </div>
      </div>
      <div className="flex items-end gap-3">
        <p className="text-4xl font-extrabold text-white">{value}</p>
        <div className="h-2 flex-1 bg-slate-900 rounded-full overflow-hidden mb-1.5 opacity-50">
          <div className={`h-full w-full bg-current rounded-full ${pulse ? 'opacity-100' : 'opacity-30'}`} />
        </div>
      </div>
    </div>
  );
}

function AgentCard({ agent }: any) {
  const isWorking = agent.state === 'working';
  
  return (
    <div className={`group relative p-5 bg-slate-900/60 backdrop-blur-md border rounded-2xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl flex flex-col justify-between ${isWorking ? 'border-blue-500/50 shadow-[0_5px_30px_rgba(59,130,246,0.15)]' : 'border-white/10 hover:border-white/20'}`}>
      {/* Top Section */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-white font-bold text-2xl shadow-inner border border-white/10 ${isWorking ? 'bg-gradient-to-br from-blue-500 to-indigo-600' : 'bg-slate-800'}`}>
              {agent.name.charAt(0).toUpperCase()}
            </div>
            {isWorking && (
              <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500 border-2 border-slate-900"></span>
              </span>
            )}
          </div>
          <div>
            <h3 className="font-bold text-lg text-white group-hover:text-blue-400 transition-colors">{agent.name}</h3>
            <p className="text-sm text-slate-400 font-medium">{agent.role}</p>
          </div>
        </div>
        <button className="p-2 text-slate-500 hover:text-white bg-slate-800/0 hover:bg-slate-800 rounded-lg transition-all opacity-0 group-hover:opacity-100">
          <Settings className="w-4 h-4" />
        </button>
      </div>

      {/* Middle Specs */}
      <div className="space-y-3 p-4 bg-slate-950/50 rounded-xl border border-white/5 mb-5 flex-1">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500 font-medium">Domain</span>
          <span className="px-2.5 py-1 bg-slate-800 border border-slate-700 rounded-md text-xs font-semibold capitalize text-slate-300">{agent.domain || 'General'}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500 font-medium">Status</span>
          <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide border ${isWorking ? 'bg-blue-500/10 text-blue-400 border-blue-500/30' : 'bg-slate-800 text-slate-400 border-transparent'}`}>
            {agent.state}
          </span>
        </div>
        {agent.current_task && (
          <div className="pt-2 mt-2 border-t border-slate-800/50">
            <span className="text-xs text-slate-500 font-medium uppercase block mb-1">Active Workflow</span>
            <span className="text-sm text-blue-300 truncate block font-mono bg-blue-500/5 px-2 py-1 rounded border border-blue-500/10">
              {agent.current_task.title}
            </span>
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="flex gap-3">
        <button className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all ${isWorking ? 'bg-slate-800 text-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]'}`}>
          <Zap className="w-4 h-4" />
          Assign
        </button>
        <button className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 hover:border-slate-500 rounded-xl text-sm font-semibold transition-all">
          Interact
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
