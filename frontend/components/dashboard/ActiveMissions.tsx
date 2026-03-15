'use client';
import React from 'react';
import { useTasksStore } from '@/store/tasks.store';
import { Task, TaskStatus } from '@/types';
import { useAgentsStore } from '@/store/agents.store';

const STATUS_CFG: Record<TaskStatus, { label: string; color: string; bg: string }> = {
  BACKLOG:     { label: 'Backlog',     color: '#6b7c99', bg: 'rgba(107,124,153,0.1)' },
  TODO:        { label: 'Todo',        color: '#8b949e', bg: 'rgba(139,148,158,0.1)' },
  IN_PROGRESS: { label: 'In Progress', color: '#f0a500', bg: 'rgba(240,165,0,0.1)'   },
  IN_REVIEW:   { label: 'In Review',   color: '#58a6ff', bg: 'rgba(88,166,255,0.1)'  },
  DONE:        { label: 'Done',        color: '#3fb950', bg: 'rgba(63,185,80,0.1)'   },
};

const PRIORITY_CFG = [
  { label: 'Low',      color: '#484f58' },
  { label: 'Med',      color: '#f0a500' },
  { label: 'High',     color: '#f85149' },
  { label: 'Critical', color: '#ff7b72' },
];

const AGENT_COLORS: Record<string, string> = {
  Lead:      '#a371f7',
  Backend:   '#58a6ff',
  Frontend:  '#f778ba',
  QA:        '#3fb950',
  Scheduler: '#f0a500',
  Content:   '#ff7b72',
};
function agentColor(name: string) { return AGENT_COLORS[name] ?? '#79c0ff'; }

function MissionCard({ task, agentName }: { task: Task; agentName?: string }) {
  const st = STATUS_CFG[task.status] ?? STATUS_CFG.BACKLOG;
  const pr = PRIORITY_CFG[task.priority] ?? PRIORITY_CFG[0];
  const aColor = agentName ? agentColor(agentName) : '#8b949e';

  return (
    <div
      className="mx-3 mb-2 p-2.5 rounded-xl transition-all"
      style={{
        background: 'rgba(10,15,30,0.6)',
        border:     '1px solid rgba(255,255,255,0.05)',
        boxShadow:  'inset 0 1px 0 rgba(255,255,255,0.03)',
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(59,111,255,0.2)')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)')}
    >
      {/* Title row */}
      <div className="flex items-start gap-2 mb-2">
        {/* Priority dot */}
        <span className="mt-1 w-2 h-2 rounded-full flex-shrink-0" style={{ background: pr.color }} />
        <span className="text-[12px] font-semibold leading-tight flex-1 min-w-0" style={{ color: '#c9d1d9' }}>
          {task.title.length > 42 ? task.title.slice(0, 42) + '…' : task.title}
        </span>
      </div>

      {/* Footer row */}
      <div className="flex items-center gap-1.5 pl-4">
        {/* Status */}
        <span
          className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md"
          style={{ color: st.color, background: st.bg }}
        >
          {st.label}
        </span>

        {/* Priority */}
        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-md"
          style={{ color: pr.color, background: `${pr.color}12` }}>
          {pr.label}
        </span>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Agent */}
        {agentName && (
          <span
            className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md"
            style={{ color: aColor, background: `${aColor}15`, border: `1px solid ${aColor}20` }}
          >
            {agentName}
          </span>
        )}
      </div>

      {/* Progress bar for in_progress/planning */}
      {(task.status === 'IN_PROGRESS') && (
        <div className="mt-2 ml-4 h-0.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
          <div
            className="h-full rounded-full"
            style={{
              width:      '65%',
              background: `linear-gradient(90deg, ${st.color}80, ${st.color})`,
              boxShadow:  `0 0 6px ${st.color}50`,
            }}
          />
        </div>
      )}
    </div>
  );
}

export default function ActiveMissions() {
  const { tasks } = useTasksStore();
  const { agents } = useAgentsStore();

  const taskList = Object.values(tasks);
  // Active tasks first (planning/in_progress), then pending, then done
  const sorted = [...taskList].sort((a, b) => {
    const order: Record<TaskStatus, number> = {
      IN_PROGRESS: 0, IN_REVIEW: 1, TODO: 2, BACKLOG: 3, DONE: 4,
    };
    return (order[a.status] ?? 9) - (order[b.status] ?? 9);
  }).slice(0, 8);

  const activeCnt = taskList.filter(t => t.status === 'IN_PROGRESS').length;

  return (
    <div className="flex flex-col" style={{ minHeight: 0 }}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 flex-shrink-0 border-b"
        style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
        <div className="flex items-center gap-2">
          <span className="text-[12px] font-bold" style={{ color: '#e6edf3', letterSpacing: '-0.2px' }}>
            Missions
          </span>
          {activeCnt > 0 && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full animate-pulse"
              style={{ background: 'rgba(240,165,0,0.15)', color: '#f0a500' }}>
              {activeCnt} active
            </span>
          )}
        </div>
        <span className="text-[10px] font-mono" style={{ color: '#484f58' }}>
          {taskList.length} total
        </span>
      </div>

      {/* List */}
      <div className="overflow-y-auto py-2" style={{ maxHeight: 220 }}>
        {sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 gap-1.5">
            <span style={{ fontSize: 22 }}>🚀</span>
            <span style={{ color: '#484f58', fontSize: 11 }}>No missions yet</span>
            <span style={{ color: '#2d4060', fontSize: 10 }}>Use the chat to create tasks</span>
          </div>
        ) : (
          sorted.map(task => (
            <MissionCard
              key={task.id}
              task={task}
              agentName={task.agentId ? agents[task.agentId]?.name : undefined}
            />
          ))
        )}
      </div>
    </div>
  );
}
