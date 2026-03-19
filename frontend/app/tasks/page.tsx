'use client';

import { useAgents } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';
import { KanbanBoard } from '@/components/kanban';

export default function TasksPage() {
  // Hydrate stores
  useAgents();
  useTasks();

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 right-1/3 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-purple-600/5 rounded-full blur-[150px]" />
      </div>

      <div className="relative flex-1 flex flex-col p-6 overflow-hidden">
        <KanbanBoard />
      </div>
    </div>
  );
}
