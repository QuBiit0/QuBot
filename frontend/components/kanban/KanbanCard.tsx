'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Task } from '@/types';
import { cn, formatTime } from '@/lib/utils';
import { Clock, User } from 'lucide-react';

interface KanbanCardProps {
  task: Task;
}

const priorityColors = {
  1: 'bg-red-500',
  2: 'bg-orange-500',
  3: 'bg-yellow-500',
  4: 'bg-blue-500',
  5: 'bg-slate-500',
};

const priorityLabels = {
  1: 'Critical',
  2: 'High',
  3: 'Medium',
  4: 'Low',
  5: 'Trivial',
};

export function KanbanCard({ task }: KanbanCardProps) {
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
        'p-4 rounded-lg border cursor-move transition-all hover:shadow-lg',
        isDragging
          ? 'opacity-50 rotate-3 scale-105 bg-slate-800 border-blue-500'
          : 'bg-slate-800 border-slate-700 hover:border-slate-600'
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
          title={priorityLabels[task.priority]}
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
