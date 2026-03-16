'use client';

import { useMemo, useState } from 'react';
import { useDndContext, DndContext, DragOverlay, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { Task, TaskStatus } from '@/types';
import { cn } from '@/lib/utils';
import { useTasksStore } from '@/store/tasks.store';
import { useUpdateTaskStatus } from '@/hooks/useTasks';
import { KanbanColumn } from './KanbanColumn';
import { KanbanCard } from './KanbanCard';
import { KanbanDragOverlay } from './KanbanDragOverlay';

const columns: { id: TaskStatus; title: string; color: string }[] = [
  { id: 'BACKLOG', title: 'Backlog', color: 'bg-slate-700' },

  { id: 'IN_PROGRESS', title: 'In Progress', color: 'bg-yellow-600' },
  { id: 'FAILED', title: 'Failed', color: 'bg-red-600' },
  { id: 'DONE', title: 'Done', color: 'bg-green-600' },
];

export function KanbanBoard() {
  const tasks = useTasksStore((s) => Object.values(s.tasks));
  const updateTaskStatus = useUpdateTaskStatus();
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 }
    })
  );

  const tasksByStatus = useMemo(() => {
    const grouped: Record<TaskStatus, Task[]> = {
      BACKLOG: [],

      IN_PROGRESS: [],
      FAILED: [],
      DONE: [],
    };
    tasks.forEach((task) => {
      grouped[task.status].push(task);
    });
    return grouped;
  }, [tasks]);

  const activeTask = useMemo(
    () => tasks.find((t) => t.id === activeId),
    [activeId, tasks]
  );

  const handleDragStart = (event: any) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = (event: any) => {
    const { active, over } = event;
    
    if (!over) {
      setActiveId(null);
      return;
    }

    const taskId = active.id as string;
    const newStatus = over.id as TaskStatus;

    // Check if dropped on a column
    if (columns.some((col) => col.id === newStatus)) {
      const task = tasks.find((t) => t.id === taskId);
      if (task && task.status !== newStatus) {
        updateTaskStatus.mutate({ id: taskId, status: newStatus });
      }
    }

    setActiveId(null);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Board Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Mission Control</h1>
          <p className="text-slate-400">Manage and track all tasks across your team</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors">
          + New Task
        </button>
      </div>

      {/* Kanban Board */}
      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-4 h-full min-w-max">
            {columns.map((column) => (
              <KanbanColumn
                key={column.id}
                id={column.id}
                title={column.title}
                color={column.color}
                tasks={tasksByStatus[column.id]}
              />
            ))}
          </div>
        </div>

        {/* Drag Overlay */}
        <DragOverlay>
          {activeTask ? (
            <KanbanDragOverlay task={activeTask} />
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
