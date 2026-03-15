'use client';

import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Task, PRIORITY_CONFIG, DOMAIN_CONFIG, STATUS_CONFIG } from '@/types';
import { GripVertical, Calendar, User } from 'lucide-react';

interface TaskCardProps {
  task: Task;
  onClick?: (task: Task) => void;
}

export function TaskCard({ task, onClick }: TaskCardProps) {
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
    opacity: isDragging ? 0.5 : 1,
  };

  const priorityConfig = PRIORITY_CONFIG[task.priority];
  const domainConfig = task.domain_hint ? DOMAIN_CONFIG[task.domain_hint] : null;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      onClick={() => onClick?.(task)}
      className="group relative bg-[#0d1117] border border-[#30363d] rounded-lg p-3 
                 hover:border-[#58a6ff] hover:shadow-lg hover:shadow-[#58a6ff]/10
                 transition-all duration-200 cursor-pointer"
    >
      {/* Priority indicator line */}
      <div 
        className="absolute left-0 top-3 bottom-3 w-1 rounded-full"
        style={{ backgroundColor: priorityConfig.color }}
      />

      {/* Drag handle */}
      <div
        {...attributes}
        {...listeners}
        className="absolute right-2 top-2 p-1 opacity-0 group-hover:opacity-100 
                   hover:bg-[#21262d] rounded cursor-grab active:cursor-grabbing transition-opacity"
      >
        <GripVertical className="w-4 h-4 text-[#484f58]" />
      </div>

      {/* Content */}
      <div className="pl-3 pr-6">
        {/* Title */}
        <h4 className="text-[13px] font-medium text-[#c9d1d9] leading-snug mb-2 line-clamp-2">
          {task.title}
        </h4>

        {/* Meta row */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Priority badge */}
          <span
            className="text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide"
            style={{ 
              backgroundColor: `${priorityConfig.color}20`,
              color: priorityConfig.color,
              border: `1px solid ${priorityConfig.color}40`
            }}
          >
            {priorityConfig.label}
          </span>

          {/* Domain badge */}
          {domainConfig && (
            <span
              className="text-[10px] px-1.5 py-0.5 rounded flex items-center gap-1"
              style={{ 
                backgroundColor: `${domainConfig.color}15`,
                color: domainConfig.color,
              }}
            >
              <span>{domainConfig.icon}</span>
              <span className="hidden sm:inline">{domainConfig.label}</span>
            </span>
          )}
        </div>

        {/* Footer info */}
        <div className="flex items-center justify-between mt-3 pt-2 border-t border-[#21262d]">
          {/* Assigned agent */}
          <div className="flex items-center gap-1.5 text-[11px] text-[#8b949e]">
            {task.assigned_agent_name ? (
              <>
                <User className="w-3 h-3" />
                <span className="truncate max-w-[80px]">{task.assigned_agent_name}</span>
              </>
            ) : (
              <span className="text-[#484f58] italic">Unassigned</span>
            )}
          </div>

          {/* Date */}
          <div className="flex items-center gap-1 text-[11px] text-[#6e7681]">
            <Calendar className="w-3 h-3" />
            <span>{formatDate(task.created_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
