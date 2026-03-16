'use client';

import { KanbanBoard } from '@/components/kanban/KanbanBoard';
import { useAgents } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';

export default function MissionControlPage() {
  useAgents();
  useTasks();

  return (
    <div className="h-full p-6">
      <KanbanBoard />
    </div>
  );
}
