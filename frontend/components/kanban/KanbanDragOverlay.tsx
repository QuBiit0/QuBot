'use client';

import { Task } from '@/types';
import { cn, formatTime } from '@/lib/utils';
import { User, Clock } from 'lucide-react';

interface KanbanDragOverlayProps {
  task: Task;
}

const priorityColors: Record<string, string> = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-orange-500',
  MEDIUM: 'bg-yellow-500',
  LOW: 'bg-blue-500',
};

export function KanbanDragOverlay({ task }: KanbanDragOverlayProps) {
  return (
    <div
      className={cn(
        'p-4 rounded-lg border cursor-grabbing shadow-2xl',
        'bg-slate-800 border-blue-500 rotate-3 scale-105'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="font-medium text-sm leading-tight">{task.title}</h4>
        <div
          className={cn(
            'w-2 h-2 rounded-full flex-shrink-0',
            priorityColors[task.priority]
          )}
        />
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
          {task.assigned_to && (
            <div className="flex items-center gap-1">
              <User className="w-3 h-3" />
              <span className="truncate max-w-[80px]">{task.assigned_to.name}</span>
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
