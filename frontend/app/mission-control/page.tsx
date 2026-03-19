'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { CoworkingCanvas } from '@/components/coworking/CoworkingCanvas';

const WorkflowBuilderVisual = dynamic(
  () => import('@/components/workflow/WorkflowBuilderVisual').then((m) => m.WorkflowBuilderVisual),
  { ssr: false }
);
import { useAgents } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';
import { Network, Activity, Cpu, Grid } from 'lucide-react';

export default function MissionControlPage() {
  useAgents();
  useTasks();

  const [activeTab, setActiveTab] = useState<'coworking' | 'workflow'>('coworking');

  return (
    <div className="h-full flex flex-col bg-slate-950 text-white overflow-hidden relative">
      
      {/* Background Ambient Glows */}
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] pointer-events-none" />

      {/* Header */}
      <div className="flex-none p-6 border-b border-white/10 z-10 relative bg-slate-950/50 backdrop-blur-xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
              Mission Control
            </h1>
            <p className="text-slate-400 mt-1">
              Real-time multi-agent orchestration and workflow monitoring.
            </p>
          </div>
          <div className="flex space-x-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-700 hover:border-slate-500 rounded-lg text-sm transition-all shadow-lg hover:shadow-blue-500/20">
              <Network className="w-4 h-4 text-blue-400" />
              <span>Network Status</span>
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)]">
              <Cpu className="w-4 h-4" />
              <span>Deploy Agent</span>
            </button>
          </div>
        </div>

        {/* Custom Premium Tabs */}
        <div className="flex space-x-2 bg-slate-900/50 p-1 rounded-xl w-max border border-white/5 shadow-inner">
          <button
            onClick={() => setActiveTab('coworking')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${
              activeTab === 'coworking'
                ? 'bg-slate-800 text-blue-400 shadow-[0_2px_10px_rgba(0,0,0,0.5)] border border-slate-700/50'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Activity className="w-4 h-4" />
            Coworking View
          </button>
          <button
            onClick={() => setActiveTab('workflow')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${
              activeTab === 'workflow'
                ? 'bg-slate-800 text-indigo-400 shadow-[0_2px_10px_rgba(0,0,0,0.5)] border border-slate-700/50'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Grid className="w-4 h-4" />
            Workflow Builder
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden relative z-10">
        <div
          className={`absolute inset-0 transition-all duration-500 transform ${
            activeTab === 'coworking' ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8 pointer-events-none'
          }`}
        >
          <CoworkingCanvas />
        </div>
        
        <div
          className={`absolute inset-0 transition-all duration-500 transform ${
            activeTab === 'workflow' ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8 pointer-events-none'
          }`}
        >
          <WorkflowBuilderVisual />
        </div>
      </div>

    </div>
  );
}
