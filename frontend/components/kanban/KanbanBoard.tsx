'use client';

import { useMemo, useState } from 'react';
import { DndContext, DragOverlay, useSensor, useSensors, PointerSensor, DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import { Task, TaskStatus } from '@/types';
import { useTasksStore } from '@/store/tasks.store';
import { useUpdateTaskStatus, useCreateTask } from '@/hooks/useTasks';
import { useAgentsStore } from '@/store/agents.store';
import { KanbanColumn } from './KanbanColumn';
import { KanbanCard } from './KanbanCard';
import { KanbanDragOverlay } from './KanbanDragOverlay';
import { X, Plus, Loader2, Search, Filter } from 'lucide-react';
import { TaskDetailModal } from './TaskDetailModal';

const columns: { id: TaskStatus; title: string; color: string }[] = [
  { id: 'BACKLOG',     title: 'Backlog',      color: 'bg-slate-700' },
  { id: 'IN_PROGRESS', title: 'In Progress',  color: 'bg-yellow-600' },
  { id: 'FAILED',      title: 'Failed',       color: 'bg-red-600'   },
  { id: 'DONE',        title: 'Done',         color: 'bg-green-600' },
];

// ─── New Task Modal ───────────────────────────────────────────────────────────

interface NewTaskModalProps {
  onClose: () => void;
}

function NewTaskModal({ onClose }: NewTaskModalProps) {
  const createTask = useCreateTask();
  const agents = Object.values(useAgentsStore((s) => s.agents));

  const [form, setForm] = useState({
    title: '',
    description: '',
    priority: 'MEDIUM' as Task['priority'],
    status: 'BACKLOG' as TaskStatus,
    assigned_agent_id: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;

    createTask.mutate(
      {
        title: form.title.trim(),
        description: form.description.trim() || undefined,
        priority: form.priority,
        status: form.status,
        assigned_agent_id: form.assigned_agent_id || undefined,
      },
      { onSuccess: onClose },
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-slate-900 border border-white/10 rounded-2xl shadow-[0_0_60px_rgba(0,0,0,0.5)] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
          <h2 className="text-base font-semibold text-white">New Task</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Title *</label>
            <input
              autoFocus
              type="text"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="Task title..."
              required
              className="w-full px-3 py-2.5 bg-slate-800 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Optional description..."
              rows={3}
              className="w-full px-3 py-2.5 bg-slate-800 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors resize-none"
            />
          </div>

          {/* Row: Priority + Status */}
          <div className="grid grid-cols-2 gap-3">
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
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as TaskStatus }))}
                className="w-full px-3 py-2.5 bg-slate-800 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
              >
                {columns.map((col) => (
                  <option key={col.id} value={col.id}>{col.title}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Assign to agent */}
          {agents.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Assign to Agent</label>
              <select
                value={form.assigned_agent_id}
                onChange={(e) => setForm((f) => ({ ...f, assigned_agent_id: e.target.value }))}
                className="w-full px-3 py-2.5 bg-slate-800 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
              >
                <option value="">Unassigned</option>
                {agents.map((a) => (
                  <option key={a.id} value={String(a.id)}>{a.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
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
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-medium text-white transition-colors shadow-[0_0_15px_rgba(37,99,235,0.3)]"
            >
              {createTask.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Board ───────────────────────────────────────────────────────────────

export function KanbanBoard() {
  const tasks = useTasksStore((s) => Object.values(s.tasks));
  const agents = Object.values(useAgentsStore((s) => s.agents));
  const updateTaskStatus = useUpdateTaskStatus();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [showNewTask, setShowNewTask] = useState(false);
  const [search, setSearch] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<Task['priority'] | 'ALL'>('ALL');
  const [agentFilter, setAgentFilter] = useState<string>('ALL');
  const [detailTaskId, setDetailTaskId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  // Map task id → its column (used to resolve card drops)
  const taskColumnMap = useMemo<Record<string, TaskStatus>>(() => {
    const map: Record<string, TaskStatus> = {};
    tasks.forEach((t) => { map[t.id] = t.status; });
    return map;
  }, [tasks]);

  // Filtered tasks (search + priority + agent)
  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        t.title.toLowerCase().includes(q) ||
        t.description?.toLowerCase().includes(q) ||
        t.assigned_agent_name?.toLowerCase().includes(q);
      const matchPriority = priorityFilter === 'ALL' || t.priority === priorityFilter;
      const matchAgent =
        agentFilter === 'ALL' ||
        (agentFilter === 'UNASSIGNED' ? !t.assigned_agent_id : t.assigned_agent_id === agentFilter);
      return matchSearch && matchPriority && matchAgent;
    });
  }, [tasks, search, priorityFilter, agentFilter]);

  const tasksByStatus = useMemo(() => {
    const grouped: Record<TaskStatus, Task[]> = {
      BACKLOG: [], IN_PROGRESS: [], FAILED: [], DONE: [],
    };
    filteredTasks.forEach((task) => { grouped[task.status]?.push(task); });
    return grouped;
  }, [filteredTasks]);

  const activeTask = useMemo(() => tasks.find((t) => t.id === activeId), [activeId, tasks]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) { setActiveId(null); return; }

    const taskId = active.id as string;
    let targetStatus: TaskStatus | null = null;

    // Case 1: dropped directly on a column
    if (columns.some((col) => col.id === over.id)) {
      targetStatus = over.id as TaskStatus;
    }
    // Case 2: dropped on another card — use that card's current column
    else if (taskColumnMap[over.id as string]) {
      targetStatus = taskColumnMap[over.id as string] ?? null;
    }

    if (targetStatus) {
      const task = tasks.find((t) => t.id === taskId);
      if (task && task.status !== targetStatus) {
        updateTaskStatus.mutate({ id: taskId, status: targetStatus });
      }
    }

    setActiveId(null);
  };

  const hasFilters = search || priorityFilter !== 'ALL' || agentFilter !== 'ALL';

  return (
    <div className="flex flex-col h-full">
      {/* Board Header */}
      <div className="flex-none mb-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-2xl font-bold text-white">Tasks</h1>
            <p className="text-slate-400 text-sm mt-0.5">
              {filteredTasks.length} of {tasks.length} tasks
              {hasFilters && ' (filtered)'}
            </p>
          </div>
          <button
            onClick={() => setShowNewTask(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium text-white text-sm transition-colors shadow-[0_0_15px_rgba(37,99,235,0.3)]"
          >
            <Plus className="w-4 h-4" />
            New Task
          </button>
        </div>

        {/* Filter Bar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 group-focus-within:text-blue-400 transition-colors pointer-events-none" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tasks…"
              className="pl-8 pr-3 py-1.5 bg-slate-900/60 border border-white/10 focus:border-blue-500/40 rounded-lg text-xs text-slate-200 placeholder:text-slate-500 outline-none transition-colors w-44"
            />
          </div>

          {/* Priority filter */}
          <div className="flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            {(['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                  priorityFilter === p
                    ? p === 'ALL' ? 'bg-blue-600 text-white'
                      : p === 'CRITICAL' ? 'bg-red-600 text-white'
                      : p === 'HIGH' ? 'bg-orange-600 text-white'
                      : p === 'MEDIUM' ? 'bg-blue-600 text-white'
                      : 'bg-slate-600 text-white'
                    : 'bg-slate-900/60 border border-white/5 text-slate-400 hover:text-white'
                }`}
              >
                {p === 'ALL' ? 'All Priority' : p}
              </button>
            ))}
          </div>

          {/* Agent filter */}
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-900/60 border border-white/10 rounded-lg text-xs text-slate-300 outline-none focus:border-blue-500/40 transition-colors"
          >
            <option value="ALL">All Agents</option>
            <option value="UNASSIGNED">Unassigned</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>

          {/* Clear filters */}
          {hasFilters && (
            <button
              onClick={() => { setSearch(''); setPriorityFilter('ALL'); setAgentFilter('ALL'); }}
              className="flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 border border-white/5 text-slate-400 hover:text-white rounded-lg text-xs transition-colors"
            >
              <X className="w-3 h-3" /> Clear
            </button>
          )}
        </div>
      </div>

      {/* Kanban Board */}
      <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-4 h-full min-w-max">
            {columns.map((column) => (
              <KanbanColumn
                key={column.id}
                id={column.id}
                title={column.title}
                color={column.color}
                tasks={tasksByStatus[column.id]}
                onDetail={(t) => setDetailTaskId(t.id)}
              />
            ))}
          </div>
        </div>

        <DragOverlay>
          {activeTask ? <KanbanDragOverlay task={activeTask} /> : null}
        </DragOverlay>
      </DndContext>

      {/* New Task Modal */}
      {showNewTask && <NewTaskModal onClose={() => setShowNewTask(false)} />}

      {/* Task Detail Modal */}
      {detailTaskId && (
        <TaskDetailModal taskId={detailTaskId} onClose={() => setDetailTaskId(null)} />
      )}
    </div>
  );
}
