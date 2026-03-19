'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAgentsStore } from '@/store/agents.store';
import { useTasksStore } from '@/store/tasks.store';
import { useAppStore } from '@/store/app.store';
import { useCreateTask } from '@/hooks/useTasks';
import { Task } from '@/types';
import { Cpu, Terminal, Sparkles, MessageSquare, Zap, CheckCircle2, Clock, Network, X, Plus, Loader2 } from 'lucide-react';

interface LocalAgent {
  id: string | number;
  name: string;
  status: string;
  domain?: string;
  current_task_id?: string | null;
}

interface AgentDeskProps {
  agent: LocalAgent;
  x: number;
  y: number;
  isSelected: boolean;
  onClick: () => void;
}

function AgentDeskAnimated({ agent, x, y, isSelected, onClick }: AgentDeskProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'WORKING': return 'rgb(59, 130, 246)';
      case 'ERROR':   return 'rgb(239, 68, 68)';
      case 'IDLE':    return 'rgb(100, 116, 139)';
      case 'DONE':    return 'rgb(34, 197, 94)';
      default:        return 'rgb(100, 116, 139)';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'WORKING': return <Cpu className="w-4 h-4 text-blue-400 animate-pulse" />;
      case 'ERROR':   return <Terminal className="w-4 h-4 text-red-400" />;
      case 'IDLE':    return <Clock className="w-4 h-4 text-slate-400" />;
      case 'DONE':    return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      default:        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const color = getStatusColor(agent.status);
  const isWorking = agent.status === 'WORKING';

  return (
    <div
      onClick={onClick}
      className="absolute transition-all duration-300 hover:z-20 cursor-pointer group"
      style={{ left: x, top: y, transform: `translate(-50%, -50%) scale(${isSelected ? 1.05 : 1})` }}
    >
      <div
        className="absolute inset-0 rounded-[2rem] blur-xl opacity-0 group-hover:opacity-40 transition-opacity duration-500"
        style={{ backgroundColor: color }}
      />
      {isSelected && (
        <div className="absolute inset-0 rounded-[2rem] blur-xl opacity-30 animate-pulse" style={{ backgroundColor: color }} />
      )}

      <div
        className={`relative w-[180px] p-4 bg-slate-900/80 backdrop-blur-md border rounded-[2rem] shadow-2xl flex flex-col items-center transition-all duration-300 ${
          isSelected ? 'border-white/30 shadow-[0_0_30px_rgba(0,0,0,0.5)]' : 'border-white/10 hover:border-white/20'
        }`}
      >
        <div className="relative mb-3">
          <div className="w-16 h-16 rounded-full flex items-center justify-center relative z-10 overflow-hidden bg-slate-800 border-2 border-white/10">
            <div
              className="absolute inset-0 opacity-50"
              style={{ background: `radial-gradient(circle at top left, ${color}, transparent)` }}
            />
            <span className="text-2xl font-bold text-white z-10 tracking-wider">
              {agent.name.substring(0, 2).toUpperCase()}
            </span>
          </div>

          {isWorking && (
            <>
              <div className="absolute inset-[-4px] rounded-full border border-dashed border-blue-400/50 animate-[spin_4s_linear_infinite]" />
              <div className="absolute inset-[-8px] rounded-full border border-dashed border-blue-500/30 animate-[spin_6s_linear_infinite_reverse]" />
            </>
          )}

          <div
            className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center border-2 border-slate-900 z-20 shadow-lg"
            style={{ backgroundColor: 'rgba(15, 23, 42, 0.9)' }}
          >
            {getStatusIcon(agent.status)}
          </div>
        </div>

        <h3 className="text-sm font-semibold text-slate-100 truncate w-full text-center">{agent.name}</h3>
        <span
          className="text-xs font-medium uppercase tracking-wider mt-1 px-2 py-0.5 rounded-full border"
          style={{
            color,
            borderColor: `${color.replace('rgb', 'rgba').replace(')', ', 0.3)')}`,
            backgroundColor: `${color.replace('rgb', 'rgba').replace(')', ', 0.1)')}`,
          }}
        >
          {agent.status}
        </span>

        {agent.current_task_id && (
          <div className="absolute -top-2 -right-2">
            <span className="relative flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-4 w-4 bg-blue-500 border-2 border-slate-900"></span>
            </span>
          </div>
        )}
      </div>

      {isWorking && (
        <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-blue-400 animate-bounce">
          <Sparkles className="w-5 h-5 opacity-70" />
        </div>
      )}
    </div>
  );
}

// ─── Assign Task Modal ────────────────────────────────────────────────────────

interface AssignTaskModalProps {
  agentId: string | number;
  agentName: string;
  onClose: () => void;
}

function AssignTaskModal({ agentId, agentName, onClose }: AssignTaskModalProps) {
  const createTask = useCreateTask();
  const [form, setForm] = useState({
    title: '',
    description: '',
    priority: 'MEDIUM' as Task['priority'],
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;

    createTask.mutate(
      {
        title: form.title.trim(),
        description: form.description.trim() || undefined,
        priority: form.priority,
        status: 'IN_PROGRESS',
        assigned_agent_id: String(agentId),
      },
      { onSuccess: onClose },
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-sm bg-slate-900 border border-white/10 rounded-2xl shadow-[0_0_60px_rgba(0,0,0,0.5)] overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
          <div>
            <h2 className="text-base font-semibold text-white">Assign Task</h2>
            <p className="text-xs text-slate-400 mt-0.5">to <span className="text-blue-400 font-medium">{agentName}</span></p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Task Title *</label>
            <input
              autoFocus
              type="text"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="What should this agent do?"
              required
              className="w-full px-3 py-2.5 bg-slate-800 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Optional details..."
              rows={2}
              className="w-full px-3 py-2.5 bg-slate-800 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Priority</label>
            <select
              value={form.priority}
              onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value as Task['priority'] }))}
              className="w-full px-3 py-2.5 bg-slate-800 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-white/10 rounded-xl text-sm font-medium text-slate-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!form.title.trim() || createTask.isPending}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-medium text-white transition-colors"
            >
              {createTask.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              Assign
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Canvas ──────────────────────────────────────────────────────────────

export function CoworkingCanvas() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [selectedAgent, setSelectedAgent] = useState<string | number | null>(null);
  const [assignTarget, setAssignTarget] = useState<{ id: string | number; name: string } | null>(null);

  const agents = useAgentsStore((s) => Object.values(s.agents));
  const tasks = useTasksStore((s) => s.tasks);
  const isConnected = useAppStore((s) => s.isConnected);

  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };
    update();
    const t = setTimeout(update, 100);
    window.addEventListener('resize', update);
    return () => { clearTimeout(t); window.removeEventListener('resize', update); };
  }, []);

  const getDeskPositions = useCallback(() => {
    if (dimensions.width === 0) return [];
    const count = agents.length;
    if (count === 0) return [];

    const cols = Math.max(1, Math.ceil(Math.sqrt(count)));
    const rows = Math.ceil(count / cols);
    const padX = 150, padY = 150;
    const usableW = dimensions.width - padX * 2;
    const usableH = dimensions.height - padY * 2;
    const cellW = usableW / Math.max(1, cols - 1);
    const cellH = usableH / Math.max(1, rows - 1);

    return agents.map((agent, i) => {
      const c = i % cols;
      const r = Math.floor(i / cols);
      const xOff = r % 2 !== 0 && cols > 1 ? cellW / 2 : 0;
      const baseX = count === 1 ? dimensions.width / 2 : padX + c * cellW + xOff;
      const baseY = count === 1 ? dimensions.height / 2 : padY + r * cellH;
      return { agent, x: Math.min(Math.max(baseX, padX), dimensions.width - padX), y: baseY };
    });
  }, [agents, dimensions]);

  if (dimensions.width === 0) return null;

  const positions = getDeskPositions();
  const selectedAgentData = selectedAgent != null ? agents.find((a) => a.id === selectedAgent) : null;

  // Resolve active task title for the inspector
  const activeTask: Task | null = selectedAgentData?.current_task_id
    ? tasks[selectedAgentData.current_task_id] ?? null
    : null;

  return (
    <div
      ref={containerRef}
      className="w-full h-full relative bg-center bg-repeat"
      style={{
        backgroundSize: '40px 40px',
        backgroundImage:
          'linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)',
      }}
    >
      {/* HUD */}
      <div className="absolute top-6 flex justify-between w-full px-6 pointer-events-none z-10">
        <div className="flex items-center gap-3 px-4 py-2 bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-full shadow-lg">
          <div className="relative flex h-3 w-3">
            {isConnected && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
            <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            {isConnected ? 'Core Online' : 'Core Offline'}
          </span>
        </div>
        <div className="flex items-center gap-3 px-4 py-2 bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-full shadow-lg">
          <Network className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            {agents.length} Active Node{agents.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Agent desks */}
      {positions.map(({ agent, x, y }) => (
        <AgentDeskAnimated
          key={agent.id}
          agent={agent}
          x={x}
          y={y}
          isSelected={selectedAgent === agent.id}
          onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
        />
      ))}

      {/* Agent Inspector Panel */}
      {selectedAgentData && (
        <div className="absolute right-6 bottom-6 w-80 bg-slate-900/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] p-5 z-30 animate-in slide-in-from-right-8 fade-in duration-300">
          {/* Header */}
          <div className="flex items-start justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-full bg-blue-600/20 border border-blue-500/50 flex items-center justify-center">
                <span className="text-lg font-bold text-blue-400">
                  {selectedAgentData.name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <h3 className="text-base font-bold text-white leading-tight">{selectedAgentData.name}</h3>
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mt-0.5">
                  {selectedAgentData.domain || 'General Purpose'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setSelectedAgent(null)}
              className="p-1.5 rounded-full hover:bg-white/10 text-slate-400 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Details */}
          <div className="space-y-2.5 mb-5">
            <div className="bg-slate-800/50 rounded-lg p-3 border border-white/5 flex justify-between items-center">
              <span className="text-xs text-slate-400 uppercase font-semibold">Status</span>
              <span className={`text-sm font-medium ${selectedAgentData.status === 'WORKING' ? 'text-blue-400' : 'text-slate-300'}`}>
                {selectedAgentData.status}
              </span>
            </div>

            <div className={`rounded-lg p-3 border ${activeTask ? 'bg-blue-900/20 border-blue-500/20' : 'bg-slate-800/50 border-white/5'}`}>
              <span className="text-xs text-slate-400 uppercase font-semibold block mb-1">Active Task</span>
              {activeTask ? (
                <span className="text-sm text-blue-300 font-medium line-clamp-2">{activeTask.title}</span>
              ) : (
                <span className="text-sm text-slate-500 italic">No task assigned</span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2.5">
            <button
              onClick={() => setAssignTarget({ id: selectedAgentData.id, name: selectedAgentData.name })}
              className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl py-2.5 text-sm font-semibold transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)]"
            >
              <Zap className="w-4 h-4" />
              Assign Task
            </button>
            <button
              onClick={() => router.push('/chat')}
              className="flex-1 flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white rounded-xl py-2.5 text-sm font-semibold transition-all"
            >
              <MessageSquare className="w-4 h-4" />
              Direct Chat
            </button>
          </div>
        </div>
      )}

      {/* Assign Task Modal */}
      {assignTarget && (
        <AssignTaskModal
          agentId={assignTarget.id}
          agentName={assignTarget.name}
          onClose={() => setAssignTarget(null)}
        />
      )}
    </div>
  );
}
