'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { CoworkingCanvas } from '@/components/coworking/CoworkingCanvas';
import { useAgents } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';
import { Network, Activity, Cpu, Grid, Users, CheckCircle, Clock, AlertCircle, Zap, Server, ChevronRight, Circle } from 'lucide-react';
import { api } from '@/lib/api';

const WorkflowBuilderVisual = dynamic(
  () => import('@/components/workflow/WorkflowBuilderVisual').then((m) => m.WorkflowBuilderVisual),
  { ssr: false }
);

interface Agent {
  id: string;
  name: string;
  status: string;
  current_task?: string;
}

interface Task {
  id: string;
  title: string;
  status: string;
  priority?: string;
}

interface ActivityItem {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  agent?: string;
}

function StatCard({ icon: Icon, label, value, color, sublabel }: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string;
  sublabel?: string;
}) {
  return (
    <div className="rounded-xl p-4 flex items-center gap-3"
      style={{ background: 'rgba(6,9,18,0.88)', border: `1px solid ${color}20` }}>
      <div className="w-12 h-12 rounded-lg flex items-center justify-center"
        style={{ background: `${color}15` }}>
        <Icon className="w-6 h-6" style={{ color }} />
      </div>
      <div>
        <div className="text-[24px] font-bold" style={{ color }}>{value}</div>
        <div className="text-[12px] font-medium" style={{ color: 'rgba(255,255,255,0.6)' }}>{label}</div>
        {sublabel && <div className="text-[10px]" style={{ color: 'rgba(255,255,255,0.35)' }}>{sublabel}</div>}
      </div>
    </div>
  );
}

function ActivityFeed({ items }: { items: ActivityItem[] }) {
  const getIcon = (type: string) => {
    switch (type) {
      case 'task_completed': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'agent_spawned': return <Zap className="w-4 h-4 text-purple-400" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'tool_call': return <Server className="w-4 h-4 text-blue-400" />;
      default: return <Circle className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {items.map((item, i) => (
        <div key={item.id} className="flex items-start gap-3 p-3 rounded-lg"
          style={{ background: 'rgba(0,0,0,0.3)' }}>
          <div className="mt-0.5">{getIcon(item.type)}</div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.7)' }}>
              {item.message}
            </p>
            <div className="flex items-center gap-2 mt-1">
              {item.agent && (
                <span className="text-[10px] px-1.5 py-0.5 rounded"
                  style={{ background: 'rgba(168,85,247,0.15)', color: '#a855f7' }}>
                  {item.agent}
                </span>
              )}
              <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                {item.timestamp}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function SystemHealth() {
  const [health, setHealth] = useState({
    backend: 'online',
    database: 'online',
    redis: 'offline',
    mcp: 'online',
  });

  return (
    <div className="flex flex-col gap-3">
      {Object.entries(health).map(([service, status]) => (
        <div key={service} className="flex items-center justify-between p-2 rounded-lg"
          style={{ background: 'rgba(0,0,0,0.2)' }}>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full"
              style={{ background: status === 'online' ? '#22c55e' : '#ef4444', boxShadow: status === 'online' ? '0 0 8px #22c55e' : '0 0 8px #ef4444' }} />
            <span className="text-[12px]" style={{ color: 'rgba(255,255,255,0.6)' }}>
              {service.charAt(0).toUpperCase() + service.slice(1)}
            </span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded"
            style={{
              background: status === 'online' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
              color: status === 'online' ? '#22c55e' : '#ef4444',
            }}>
            {status}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function MissionControlPage() {
  useAgents();
  useTasks();

  const [activeTab, setActiveTab] = useState<'coworking' | 'workflow'>('coworking');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);

  useEffect(() => {
    api.get<{ data: Agent[] }>('/agents')
      .then(res => setAgents(res.data ?? []))
      .catch(() => {});

    api.get<{ data: Task[] }>('/tasks?limit=20')
      .then(res => setTasks(res.data ?? []))
      .catch(() => {});

    setActivities([
      { id: '1', type: 'task_completed', message: 'Code review completed for PR #42', agent: 'DevAgent', timestamp: '2m ago' },
      { id: '2', type: 'agent_spawned', message: 'New subagent spawned for data analysis', agent: 'Orchestrator', timestamp: '5m ago' },
      { id: '3', type: 'tool_call', message: 'web_search executed: "latest AI news"', agent: 'ResearchBot', timestamp: '8m ago' },
      { id: '4', type: 'task_completed', message: 'Database migration verified', agent: 'DBAgent', timestamp: '12m ago' },
      { id: '5', type: 'error', message: 'API rate limit exceeded, retrying...', agent: 'APIBot', timestamp: '15m ago' },
    ]);
  }, []);

  const stats = {
    totalAgents: agents.length,
    activeAgents: agents.filter(a => a.status === 'working').length,
    idleAgents: agents.filter(a => a.status === 'idle').length,
    totalTasks: tasks.length,
    completedTasks: tasks.filter(t => t.status === 'completed').length,
    pendingTasks: tasks.filter(t => t.status === 'pending').length,
    inProgressTasks: tasks.filter(t => t.status === 'in_progress').length,
  };

  return (
    <div className="h-full flex flex-col overflow-hidden relative" style={{ background: 'linear-gradient(180deg, #060912 0%, #0a0f1a 100%)' }}>
      
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[600px] h-[600px] bg-purple-600/8 rounded-full blur-[150px] pointer-events-none" />

      <div className="flex-none p-4 border-b z-10 relative" style={{ borderColor: 'rgba(255,255,255,0.05)', background: 'rgba(6,9,24,0.8)', backdropFilter: 'blur(12px)' }}>
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'rgba(255,255,255,0.92)' }}>Mission Control</h1>
            <p className="text-[13px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
              Real-time multi-agent orchestration and workflow monitoring
            </p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium transition-all"
              style={{ background: 'rgba(6,9,18,0.88)', border: '1px solid rgba(99,102,241,0.2)', color: 'rgba(255,255,255,0.7)' }}>
              <Network className="w-4 h-4 text-blue-400" />
              Network Status
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold transition-all"
              style={{ background: 'linear-gradient(135deg,#3b82f6,#6366f1)', color: '#fff' }}>
              <Cpu className="w-4 h-4" />
              Deploy Agent
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-4">
          <StatCard icon={Users} label="Total Agents" value={stats.totalAgents} color="#6366f1" />
          <StatCard icon={Activity} label="Active" value={stats.activeAgents} color="#22c55e" sublabel="working now" />
          <StatCard icon={Clock} label="Pending Tasks" value={stats.pendingTasks} color="#f59e0b" />
          <StatCard icon={CheckCircle} label="Completed" value={stats.completedTasks} color="#3b82f6" />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('coworking')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium transition-all"
            style={{
              background: activeTab === 'coworking' ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
              color: activeTab === 'coworking' ? '#6366f1' : 'rgba(255,255,255,0.5)',
              border: activeTab === 'coworking' ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent',
            }}
          >
            <Activity className="w-4 h-4" />
            Coworking View
          </button>
          <button
            onClick={() => setActiveTab('workflow')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium transition-all"
            style={{
              background: activeTab === 'workflow' ? 'rgba(168,85,247,0.2)' : 'rgba(255,255,255,0.05)',
              color: activeTab === 'workflow' ? '#a855f7' : 'rgba(255,255,255,0.5)',
              border: activeTab === 'workflow' ? '1px solid rgba(168,85,247,0.3)' : '1px solid transparent',
            }}
          >
            <Grid className="w-4 h-4" />
            Workflow Builder
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden relative z-10">
        <div className="flex-1 overflow-hidden">
          <div className={`h-full transition-all duration-500 ${activeTab === 'coworking' ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <CoworkingCanvas />
          </div>
          <div className={`h-full transition-all duration-500 ${activeTab === 'workflow' ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <WorkflowBuilderVisual />
          </div>
        </div>

        <div className="w-80 border-l shrink-0 overflow-y-auto p-4 flex flex-col gap-4"
          style={{ borderColor: 'rgba(255,255,255,0.05)', background: 'rgba(6,9,18,0.5)' }}>
          
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[13px] font-semibold" style={{ color: 'rgba(255,255,255,0.8)' }}>System Health</h3>
              <button className="text-[11px] flex items-center gap-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
                Refresh <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            <SystemHealth />
          </div>

          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[13px] font-semibold" style={{ color: 'rgba(255,255,255,0.8)' }}>Recent Activity</h3>
              <button className="text-[11px] px-2 py-0.5 rounded" style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1' }}>
                View All
              </button>
            </div>
            <ActivityFeed items={activities} />
          </div>

          <div>
            <h3 className="text-[13px] font-semibold mb-3" style={{ color: 'rgba(255,255,255,0.8)' }}>Quick Stats</h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 rounded-lg" style={{ background: 'rgba(0,0,0,0.3)' }}>
                <div className="text-[18px] font-bold text-purple-400">{stats.inProgressTasks}</div>
                <div className="text-[10px]" style={{ color: 'rgba(255,255,255,0.4)' }}>In Progress</div>
              </div>
              <div className="p-3 rounded-lg" style={{ background: 'rgba(0,0,0,0.3)' }}>
                <div className="text-[18px] font-bold text-gray-400">{stats.idleAgents}</div>
                <div className="text-[10px]" style={{ color: 'rgba(255,255,255,0.4)' }}>Idle Agents</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
