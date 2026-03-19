'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useRunTask, useCancelTask } from '@/hooks/useTasks';
import { Task } from '@/types';
import {
  X, Loader2, CheckCircle2, AlertCircle, Clock, User,
  Zap, Flag, Tag, ChevronRight, Activity, Play, Square,
} from 'lucide-react';

interface TaskEvent {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  created_at: string;
  agent_id?: string;
}

interface TaskDetail extends Task {
  events?: TaskEvent[];
}

const PRIORITY_COLOR: Record<string, string> = {
  CRITICAL: 'text-red-400 bg-red-500/10 border-red-500/20',
  HIGH:     'text-orange-400 bg-orange-500/10 border-orange-500/20',
  MEDIUM:   'text-blue-400 bg-blue-500/10 border-blue-500/20',
  LOW:      'text-slate-400 bg-slate-500/10 border-slate-500/20',
};

const STATUS_COLOR: Record<string, string> = {
  BACKLOG:     'text-slate-400 bg-slate-500/10',
  IN_PROGRESS: 'text-amber-400 bg-amber-500/10',
  DONE:        'text-emerald-400 bg-emerald-500/10',
  FAILED:      'text-red-400 bg-red-500/10',
};

const EVENT_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  CREATED:         CheckCircle2,
  ASSIGNED:        User,
  TOOL_CALL:       Zap,
  PROGRESS_UPDATE: Activity,
  COMPLETED:       CheckCircle2,
  FAILED:          AlertCircle,
  COMMENT:         ChevronRight,
};

function EventRow({ event }: { event: TaskEvent }) {
  const Icon = EVENT_ICON[event.type] ?? ChevronRight;
  const isError = event.type === 'FAILED';
  const isSuccess = event.type === 'COMPLETED';

  const summary = (() => {
    if (event.type === 'TOOL_CALL') {
      const p = event.payload;
      return `${p.tool_name ?? 'tool'} → ${p.success ? '✓' : '✗'} (${p.duration_ms ?? 0}ms)`;
    }
    if (event.type === 'ASSIGNED') return `Assigned to agent ${event.payload.agent_name ?? event.agent_id ?? '?'}`;
    if (event.type === 'PROGRESS_UPDATE') return String(event.payload.message ?? '');
    if (event.type === 'COMPLETED') return String(event.payload.summary ?? 'Task completed');
    if (event.type === 'FAILED') return String(event.payload.reason ?? 'Task failed');
    if (event.type === 'CREATED') return 'Task created';
    return JSON.stringify(event.payload).slice(0, 80);
  })();

  return (
    <div className="flex gap-3 py-2">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
        isError ? 'bg-red-500/15' : isSuccess ? 'bg-emerald-500/15' : 'bg-slate-700/60'
      }`}>
        <Icon className={`w-3 h-3 ${isError ? 'text-red-400' : isSuccess ? 'text-emerald-400' : 'text-slate-400'}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-slate-300">{event.type.replace(/_/g, ' ')}</span>
          <span className="text-[10px] text-slate-600 flex-shrink-0">
            {new Date(event.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        </div>
        {summary && (
          <p className="text-xs text-slate-400 mt-0.5 truncate">{summary}</p>
        )}
      </div>
    </div>
  );
}

interface TaskDetailModalProps {
  taskId: string;
  onClose: () => void;
}

export function TaskDetailModal({ taskId, onClose }: TaskDetailModalProps) {
  const runTask = useRunTask();
  const cancelTask = useCancelTask();

  const { data, isLoading, error } = useQuery({
    queryKey: ['task-detail', taskId],
    queryFn: async () => {
      const res = await api.getTask(taskId);
      return res.data as TaskDetail;
    },
    refetchInterval: 5000, // Poll every 5s for live updates when IN_PROGRESS
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-start justify-between px-5 py-4 border-b border-white/5 flex-shrink-0">
          <div className="flex-1 min-w-0 pr-3">
            {isLoading ? (
              <div className="h-5 w-48 bg-slate-700 rounded animate-pulse" />
            ) : (
              <h2 className="text-base font-semibold text-white leading-tight line-clamp-2">
                {data?.title ?? 'Task'}
              </h2>
            )}
          </div>
          {data && data.status === 'IN_PROGRESS' && (
            <button
              onClick={() => cancelTask.mutate(taskId)}
              disabled={cancelTask.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600/80 hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-xs font-medium text-white transition-colors flex-shrink-0"
              title="Cancel task"
            >
              {cancelTask.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Square className="w-3 h-3" />}
              Cancel
            </button>
          )}
          {data && data.status !== 'DONE' && data.status !== 'FAILED' && data.assigned_agent_id && (
            <button
              onClick={() => runTask.mutate(taskId)}
              disabled={runTask.isPending || data.status === 'IN_PROGRESS'}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-xs font-medium text-white transition-colors flex-shrink-0"
              title={data.status === 'IN_PROGRESS' ? 'Already running' : 'Run task'}
            >
              {runTask.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
              Run
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-48 gap-3 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
            Loading task details…
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-48 gap-3 text-red-400">
            <AlertCircle className="w-5 h-5" />
            Failed to load task details.
          </div>
        ) : data ? (
          <div className="flex-1 overflow-y-auto">
            {/* Meta */}
            <div className="px-5 py-4 border-b border-white/5 space-y-3">
              <div className="flex flex-wrap gap-2">
                <span className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border ${PRIORITY_COLOR[data.priority] ?? ''}`}>
                  <Flag className="w-3 h-3" />
                  {data.priority}
                </span>
                <span className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_COLOR[data.status] ?? ''}`}>
                  {data.status === 'IN_PROGRESS' && <Loader2 className="w-3 h-3 animate-spin" />}
                  {data.status.replace('_', ' ')}
                </span>
                {(data.assigned_to?.name ?? data.assigned_agent_name) && (
                  <span className="flex items-center gap-1 text-xs text-slate-400 bg-slate-800 px-2.5 py-1 rounded-full">
                    <User className="w-3 h-3" />
                    {data.assigned_to?.name ?? data.assigned_agent_name}
                  </span>
                )}
                {data.due_date && (
                  <span className="flex items-center gap-1 text-xs text-slate-400 bg-slate-800 px-2.5 py-1 rounded-full">
                    <Clock className="w-3 h-3" />
                    {new Date(data.due_date).toLocaleDateString()}
                  </span>
                )}
              </div>

              {data.description && (
                <p className="text-sm text-slate-400 leading-relaxed">{data.description}</p>
              )}

              {data.tags && data.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {data.tags.map((tag) => (
                    <span key={tag} className="flex items-center gap-1 text-[10px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
                      <Tag className="w-2.5 h-2.5" />
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Execution Timeline */}
            <div className="px-5 py-4">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-white">Execution Timeline</h3>
                <span className="ml-auto text-xs text-slate-500">
                  {data.events?.length ?? 0} events
                </span>
              </div>

              {!data.events || data.events.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">
                  No execution events yet. Start the task to see activity here.
                </p>
              ) : (
                <div className="divide-y divide-white/5">
                  {[...data.events].reverse().map((ev) => (
                    <EventRow key={ev.id} event={ev} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
