'use client';

import { useEffect } from 'react';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';

export default function MissionControlPage() {
  // Initialize mock data
  useEffect(() => {
    const init = async () => {
      const { initializeMockData } = await import('@/lib/mock-data');
      initializeMockData();
    };
    init();
  }, []);

  return (
    <div className="h-full p-6">
      <KanbanBoard />
    </div>
  );
}
