'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Task } from '@/types';
import { cn, formatTime } from '@/lib/utils';
import { Clock, User, ExternalLink } from 'lucide-react';

interface KanbanCardProps {
  task: Task;
  onDetail?: (task: Task) => void;
}

const priorityColors: Record<string, string> = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-orange-500',
  MEDIUM: 'bg-yellow-500',
  LOW: 'bg-blue-500',
};

const priorityLabels: Record<string, string> = {
  CRITICAL: 'Critical',
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
};

export function KanbanCard({ task, onDetail }: KanbanCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        'group p-4 rounded-lg border cursor-move transition-all hover:shadow-lg',
        isDragging
          ? 'opacity-50 rotate-3 scale-105 bg-slate-800 border-blue-500'
          : 'bg-slate-800 border-slate-700 hover:border-slate-600'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="font-medium text-sm leading-tight flex-1">{task.title}</h4>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <div
            className={cn('w-2 h-2 rounded-full', priorityColors[task.priority])}
            title={priorityLabels[task.priority]}
          />
          {onDetail && (
            <button
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => { e.stopPropagation(); onDetail(task); }}
              className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-white/10 text-slate-500 hover:text-white transition-all"
              title="View details"
            >
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Description */}
      {task.description && (
        <p className="text-xs text-slate-400 mb-3 line-clamp-2">
          {task.description}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-2">
          {(task.assigned_to?.name ?? task.assigned_agent_name) && (
            <div className="flex items-center gap-1">
              <User className="w-3 h-3" />
              <span className="truncate max-w-[80px]">{task.assigned_to?.name ?? task.assigned_agent_name}</span>
            </div>
          )}
        </div>
        
        {task.due_date && (
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{formatTime(task.due_date)}</span>
          </div>
        )}
      </div>

      {/* Tags */}
      {task.tags && task.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {task.tags.map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 bg-slate-700 rounded text-[10px] text-slate-300"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
