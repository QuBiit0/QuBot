'use client';
import React from 'react';
import { useAppStore } from '@/store/app.store';
import { useAgentsStore } from '@/store/agents.store';
import { useTasksStore } from '@/store/tasks.store';

interface CardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent: string;
  icon: React.ReactNode;
}

function Card({ label, value, sub, accent, icon }: CardProps) {
  return (
    <div
      className="relative flex flex-col gap-1 p-3 rounded-xl overflow-hidden"
      style={{
        background:  `linear-gradient(135deg, ${accent}12 0%, ${accent}04 100%)`,
        border:      `1px solid ${accent}25`,
        boxShadow:   `0 0 20px ${accent}08, inset 0 1px 0 ${accent}15`,
      }}
    >
      <div className="flex items-center justify-between mb-0.5">
        <span style={{ color: accent, opacity: 0.85 }}>{icon}</span>
        <div className="w-5 h-5 rounded-md flex items-center justify-center"
          style={{ background: `${accent}15` }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: accent, display: 'block', opacity: 0.7 }} />
        </div>
      </div>
      <div className="text-[20px] font-black leading-none tabular-nums" style={{ color: '#e6edf3' }}>
        {value}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#6b7c99' }}>
          {label}
        </span>
        {sub && (
          <span className="text-[9px] font-semibold" style={{ color: accent }}>
            {sub}
          </span>
        )}
      </div>
      <div
        className="absolute -top-4 -right-4 w-12 h-12 rounded-full blur-xl pointer-events-none"
        style={{ background: accent, opacity: 0.08 }}
      />
    </div>
  );
}

export default function MetricCards() {
  const { metrics, isConnected } = useAppStore();
  const { agents } = useAgentsStore();
  const { tasks } = useTasksStore();

  const agentList    = Object.values(agents);
  const onlineCount  = agentList.filter((a) => a.status !== 'OFFLINE').length;
  const workingCount = agentList.filter((a) => a.status === 'WORKING').length;

  // Derive task counts from store; fall back to WS metrics when store is empty
  const taskList     = Object.values(tasks);
  const storeTotal   = taskList.length;
  const storePending = taskList.filter((t) => t.status === 'BACKLOG' || t.status === 'IN_PROGRESS').length;

  const totalTasks   = storeTotal   > 0 ? storeTotal   : metrics.totalTasks;
  const pendingTasks = storeTotal   > 0 ? storePending : metrics.pendingTasks;
  const activeAgents = agentList.length > 0 ? onlineCount : metrics.activeAgents;

  return (
    <div className="grid grid-cols-2 gap-2 p-3">
      <Card
        label="Pending Tasks"
        value={pendingTasks}
        sub={pendingTasks > 0 ? '↑ pending' : '— idle'}
        accent="#3b6fff"
        icon={<TaskIcon />}
      />
      <Card
        label="Agents Online"
        value={`${onlineCount}/${agentList.length}`}
        sub={workingCount > 0 ? `${workingCount} working` : 'all idle'}
        accent="#a371f7"
        icon={<AgentIcon />}
      />
      <Card
        label="Total Tasks"
        value={totalTasks}
        accent="#58a6ff"
        icon={<TokenIcon />}
      />
      <Card
        label="Active Agents"
        value={activeAgents}
        sub={isConnected ? 'live' : 'offline'}
        accent="#3fb950"
        icon={<CostIcon />}
      />
    </div>
  );
}

function TaskIcon()  { return <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M2 2h12a1 1 0 011 1v10a1 1 0 01-1 1H2a1 1 0 01-1-1V3a1 1 0 011-1zm1 3v1h10V5H3zm0 3v1h7V8H3zm0 3v1h5v-1H3z"/></svg>; }
function AgentIcon() { return <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><circle cx="8" cy="5" r="3"/><path d="M2 14c0-3.314 2.686-6 6-6s6 2.686 6 6H2z"/></svg>; }
function TokenIcon() { return <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1l1.8 3.6L14 5.5l-3 2.9.7 4.1L8 10.4l-3.7 2.1.7-4.1L2 5.5l4.2-.9L8 1z"/></svg>; }
function CostIcon()  { return <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0a8 8 0 100 16A8 8 0 008 0zm.75 11.5v.75a.75.75 0 01-1.5 0v-.75A2.75 2.75 0 014.5 8.75a.75.75 0 011.5 0c0 .69.56 1.25 1.25 1.25h1.5a.75.75 0 000-1.5h-1.5A2.75 2.75 0 014.5 5.75a2.75 2.75 0 012.75-2.75v-.75a.75.75 0 011.5 0v.75a2.75 2.75 0 012.5 2.75.75.75 0 01-1.5 0c0-.69-.56-1.25-1.25-1.25h-1.5a.75.75 0 000 1.5h1.5a2.75 2.75 0 010 5.5z"/></svg>; }
