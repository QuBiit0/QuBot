# 🎨 Frontend Implementation TODO

> **Objetivo**: Construir el Mission Control de Qubot — el diferenciador visual vs OpenClaw  
> **Stack**: Next.js 14 + Tailwind + Shadcn/ui + Zustand + TanStack Query + dnd-kit + Konva.js  
> **Tiempo estimado**: 2-3 semanas para MVP

---

## FASE 1: Foundation (Días 1-3)

### 1.1 Project Setup
- [ ] `npx create-next-app@14 frontend --typescript --tailwind --app`
- [ ] Configurar `next.config.js` con `output: 'standalone'`
- [ ] Instalar dependencias:
  ```bash
  npm install zustand @tanstack/react-query @dnd-kit/core @dnd-kit/sortable
  npm install konva react-konva react-konva-utils
  npm install framer-motion lucide-react
  npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
  npm install class-variance-authority clsx tailwind-merge
  ```
- [ ] Setup Shadcn/ui: `npx shadcn-ui@latest init`
- [ ] Crear `frontend/.env.local`:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  NEXT_PUBLIC_WS_URL=ws://localhost:8000
  ```

### 1.2 Type Definitions
- [ ] Crear `frontend/types/index.ts` con interfaces del backend

```typescript
// types/index.ts
export interface Agent {
  id: string;
  name: string;
  status: 'IDLE' | 'WORKING' | 'ERROR' | 'OFFLINE';
  agent_class: AgentClass;
  domain: DomainEnum;
  avatar_config: AvatarConfig;
  current_task_id?: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'BACKLOG' | 'IN_PROGRESS' | 'IN_REVIEW' | 'DONE' | 'FAILED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  assigned_agent_id?: string;
  domain_hint?: DomainEnum;
}

export interface AgentClass {
  id: string;
  name: string;
  domain: DomainEnum;
  description: string;
  default_avatar_config: AvatarConfig;
}

export type DomainEnum = 'TECH' | 'BUSINESS' | 'FINANCE' | 'HR' | 'MARKETING' | 'LEGAL' | 'PERSONAL' | 'OTHER';

export interface AvatarConfig {
  color_primary: string;
  color_secondary: string;
  sprite_id: string;
  icon: string;
}
```

### 1.3 API Client
- [ ] Crear `frontend/lib/api.ts`:

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function api<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// Specific endpoints
export const agentsApi = {
  list: () => api<{ data: Agent[] }>('/agents'),
  get: (id: string) => api<{ data: Agent }>(`/agents/${id}`),
  create: (data: Partial<Agent>) => api<{ data: Agent }>('/agents', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  update: (id: string, data: Partial<Agent>) => api<{ data: Agent }>(`/agents/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
};

export const tasksApi = {
  list: () => api<{ data: Task[] }>('/tasks'),
  create: (data: Partial<Task>) => api<{ data: Task }>('/tasks', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateStatus: (id: string, status: Task['status']) => api<{ data: Task }>(`/tasks/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  }),
};
```

### 1.4 Zustand Stores
- [ ] Crear `frontend/store/agents.store.ts`:

```typescript
// store/agents.store.ts
import { create } from 'zustand';
import { Agent } from '@/types';

interface AgentsState {
  agents: Record<string, Agent>;
  selectedAgentId: string | null;
  setAgents: (agents: Agent[]) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  selectAgent: (id: string | null) => void;
}

export const useAgentsStore = create<AgentsState>((set) => ({
  agents: {},
  selectedAgentId: null,
  setAgents: (agents) => set({
    agents: agents.reduce((acc, agent) => ({ ...acc, [agent.id]: agent }), {})
  }),
  updateAgent: (id, updates) => set((state) => ({
    agents: { ...state.agents, [id]: { ...state.agents[id], ...updates } }
  })),
  selectAgent: (id) => set({ selectedAgentId: id }),
}));
```

- [ ] Crear `frontend/store/tasks.store.ts`:

```typescript
// store/tasks.store.ts
import { create } from 'zustand';
import { Task } from '@/types';

interface TasksState {
  tasks: Record<string, Task>;
  setTasks: (tasks: Task[]) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  addTask: (task: Task) => void;
}

export const useTasksStore = create<TasksState>((set) => ({
  tasks: {},
  setTasks: (tasks) => set({
    tasks: tasks.reduce((acc, task) => ({ ...acc, [task.id]: task }), {})
  }),
  updateTask: (id, updates) => set((state) => ({
    tasks: { ...state.tasks, [id]: { ...state.tasks[id], ...updates } }
  })),
  addTask: (task) => set((state) => ({
    tasks: { ...state.tasks, [task.id]: task }
  })),
}));
```

- [ ] Crear `frontend/store/activity.store.ts`:

```typescript
// store/activity.store.ts
import { create } from 'zustand';

export interface ActivityEntry {
  id: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  agent_id?: string;
  agent_name?: string;
  task_id?: string;
  task_title?: string;
  timestamp: string;
}

interface ActivityState {
  entries: ActivityEntry[];
  addEntry: (entry: Omit<ActivityEntry, 'id'>) => void;
  clear: () => void;
}

export const useActivityStore = create<ActivityState>((set) => ({
  entries: [],
  addEntry: (entry) => set((state) => ({
    entries: [
      { ...entry, id: crypto.randomUUID() },
      ...state.entries.slice(0, 199),
    ],
  })),
  clear: () => set({ entries: [] }),
}));
```

### 1.5 TanStack Query Hooks
- [ ] Crear `frontend/hooks/useAgents.ts`:

```typescript
// hooks/useAgents.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentsApi } from '@/lib/api';
import { useAgentsStore } from '@/store/agents.store';

export function useAgents() {
  const setAgents = useAgentsStore((s) => s.setAgents);
  
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const response = await agentsApi.list();
      setAgents(response.data);
      return response.data;
    },
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: agentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
```

- [ ] Crear `frontend/hooks/useTasks.ts`:

```typescript
// hooks/useTasks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/lib/api';

export function useTasks() {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const response = await tasksApi.list();
      return response.data;
    },
  });
}

export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      tasksApi.updateStatus(id, status as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}
```

---

## FASE 2: Layout y Navegación (Días 2-3)

### 2.1 Root Layout
- [ ] Crear `frontend/app/layout.tsx`:

```typescript
// app/layout.tsx
import { Inter } from 'next/font/google';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar } from '@/components/layout/Sidebar';
import { ActivityPanel } from '@/components/layout/ActivityPanel';
import { useWebSocket } from '@/hooks/useWebSocket';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

const queryClient = new QueryClient();

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}>
          <div className="flex h-screen bg-slate-950 text-slate-100">
            <Sidebar />
            <main className="flex-1 overflow-hidden">
              {children}
            </main>
            <ActivityPanel />
          </div>
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

### 2.2 Sidebar Component
- [ ] Crear `frontend/components/layout/Sidebar.tsx`:

```typescript
// components/layout/Sidebar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Kanban, 
  Users, 
  MessageSquare, 
  Settings,
  Wrench,
  Sparkles
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Coworking', icon: LayoutDashboard },
  { href: '/mission-control', label: 'Mission Control', icon: Kanban },
  { href: '/agents', label: 'Agents', icon: Users },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/tools', label: 'Tools', icon: Wrench },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-slate-800">
        <Link href="/" className="flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-blue-500" />
          <span className="text-xl font-bold">Qubot</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500">
        <p>Qubot v1.0.0</p>
        <p>Multi-Agent AI Platform</p>
      </div>
    </aside>
  );
}
```

### 2.3 Activity Panel
- [ ] Crear `frontend/components/layout/ActivityPanel.tsx`:

```typescript
// components/layout/ActivityPanel.tsx
'use client';

import { useActivityStore } from '@/store/activity.store';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

const severityColors = {
  info: 'text-slate-300',
  success: 'text-green-400',
  warning: 'text-yellow-400',
  error: 'text-red-400',
};

export function ActivityPanel() {
  const entries = useActivityStore((s) => s.entries);

  return (
    <aside className="w-80 bg-slate-900 border-l border-slate-800 flex flex-col">
      <div className="p-4 border-b border-slate-800">
        <h2 className="font-semibold">Activity Feed</h2>
        <p className="text-xs text-slate-500">Real-time updates</p>
      </div>
      
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-3">
          {entries.length === 0 && (
            <p className="text-sm text-slate-500 text-center py-8">
              No activity yet...
            </p>
          )}
          
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="text-sm p-3 rounded-lg bg-slate-800/50 border border-slate-700"
            >
              <p className={cn('font-medium', severityColors[entry.severity])}>
                {entry.message}
              </p>
              {entry.agent_name && (
                <p className="text-xs text-slate-500 mt-1">
                  via {entry.agent_name}
                </p>
              )}
              <p className="text-xs text-slate-600 mt-1">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </p>
            </div>
          ))}
        </div>
      </ScrollArea>
    </aside>
  );
}
```

---

## FASE 3: Kanban Board (Días 3-5)

### 3.1 Kanban Board Component
- [ ] Crear `frontend/components/kanban/KanbanBoard.tsx`:

```typescript
// components/kanban/KanbanBoard.tsx
'use client';

import { DndContext, DragEndEvent, DragOverlay, closestCenter } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useState } from 'react';
import { Task } from '@/types';
import { useTasks, useUpdateTaskStatus } from '@/hooks/useTasks';
import { useTasksStore } from '@/store/tasks.store';
import { KanbanColumn } from './KanbanColumn';
import { TaskCard } from './TaskCard';

const COLUMNS = [
  { id: 'BACKLOG', label: 'Backlog', color: 'slate' },
  { id: 'IN_PROGRESS', label: 'In Progress', color: 'blue' },
  { id: 'IN_REVIEW', label: 'In Review', color: 'yellow' },
  { id: 'DONE', label: 'Done', color: 'green' },
] as const;

export function KanbanBoard() {
  const { data: tasks, isLoading } = useTasks();
  const updateStatus = useUpdateTaskStatus();
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    
    if (!over) return;
    
    const taskId = active.id as string;
    const newStatus = over.id as Task['status'];
    const oldStatus = active.data.current?.status as Task['status'];
    
    if (newStatus === oldStatus) return;
    
    // Optimistic update
    useTasksStore.getState().updateTask(taskId, { status: newStatus });
    
    try {
      await updateStatus.mutateAsync({ id: taskId, status: newStatus });
    } catch {
      // Revert on error
      useTasksStore.getState().updateTask(taskId, { status: oldStatus });
    }
    
    setActiveTask(null);
  };

  if (isLoading) {
    return <div className="p-8">Loading...</div>;
  }

  const tasksByColumn = COLUMNS.reduce((acc, col) => {
    acc[col.id] = tasks?.filter((t) => t.status === col.id) || [];
    return acc;
  }, {} as Record<string, Task[]>);

  return (
    <div className="h-full p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Mission Control</h1>
        <p className="text-slate-400">Manage your team's tasks</p>
      </div>

      <DndContext
        collisionDetection={closestCenter}
        onDragStart={(e) => setActiveTask(e.active.data.current as Task)}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 h-[calc(100%-100px)] overflow-x-auto">
          {COLUMNS.map((column) => (
            <KanbanColumn
              key={column.id}
              id={column.id}
              label={column.label}
              color={column.color}
              tasks={tasksByColumn[column.id]}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask ? <TaskCard task={activeTask} isOverlay /> : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
```

### 3.2 Kanban Column
- [ ] Crear `frontend/components/kanban/KanbanColumn.tsx`:

```typescript
// components/kanban/KanbanColumn.tsx
'use client';

import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { Task } from '@/types';
import { TaskCard } from './TaskCard';
import { cn } from '@/lib/utils';

interface KanbanColumnProps {
  id: string;
  label: string;
  color: 'slate' | 'blue' | 'yellow' | 'green';
  tasks: Task[];
}

const colorClasses = {
  slate: 'border-slate-700 bg-slate-900/50',
  blue: 'border-blue-700/50 bg-blue-900/20',
  yellow: 'border-yellow-700/50 bg-yellow-900/20',
  green: 'border-green-700/50 bg-green-900/20',
};

export function KanbanColumn({ id, label, color, tasks }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex flex-col w-80 min-w-80 rounded-xl border-2 transition-colors',
        colorClasses[color],
        isOver && 'border-blue-500 bg-blue-900/30'
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{label}</h3>
          <span className="text-xs bg-slate-800 px-2 py-1 rounded-full">
            {tasks.length}
          </span>
        </div>
      </div>

      {/* Tasks */}
      <SortableContext
        items={tasks.map((t) => t.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="flex-1 p-3 space-y-3 overflow-y-auto">
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}
```

### 3.3 Task Card
- [ ] Crear `frontend/components/kanban/TaskCard.tsx`:

```typescript
// components/kanban/TaskCard.tsx
'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Task } from '@/types';
import { cn } from '@/lib/utils';
import { AlertCircle, Clock, User } from 'lucide-react';

interface TaskCardProps {
  task: Task;
  isOverlay?: boolean;
}

const priorityColors = {
  LOW: 'bg-slate-700',
  MEDIUM: 'bg-blue-700',
  HIGH: 'bg-yellow-700',
  CRITICAL: 'bg-red-700',
};

const domainIcons: Record<string, string> = {
  TECH: '💻',
  FINANCE: '💰',
  MARKETING: '📢',
  HR: '👥',
  LEGAL: '⚖️',
  BUSINESS: '💼',
  PERSONAL: '🏠',
};

export function TaskCard({ task, isOverlay }: TaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id, data: task });

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
        'bg-slate-800 rounded-lg p-4 border border-slate-700 cursor-grab',
        'hover:border-slate-600 transition-colors',
        isDragging && 'opacity-50 rotate-2',
        isOverlay && 'shadow-xl rotate-3 cursor-grabbing'
      )}
    >
      {/* Priority bar */}
      <div className={cn('h-1 w-12 rounded-full mb-3', priorityColors[task.priority])} />

      {/* Title */}
      <h4 className="font-medium mb-2 line-clamp-2">{task.title}</h4>

      {/* Meta */}
      <div className="flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <span>{domainIcons[task.domain_hint || 'TECH']}</span>
          <span className="bg-slate-700 px-2 py-0.5 rounded">
            {task.priority}
          </span>
        </div>
        
        {task.assigned_agent_id ? (
          <div className="flex items-center gap-1">
            <User className="w-3 h-3" />
            <span>Assigned</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-yellow-500">
            <AlertCircle className="w-3 h-3" />
            <span>Unassigned</span>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## FASE 4: WebSocket Real-time (Días 5-6)

### 4.1 WebSocket Client
- [ ] Crear `frontend/lib/websocket.ts`:

```typescript
// lib/websocket.ts
let ws: WebSocket | null = null;
const listeners: Map<string, ((event: any) => void)[]> = new Map();

export function connect(token: string): WebSocket {
  if (ws?.readyState === WebSocket.OPEN) return ws;

  const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws?token=${token}`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected');
    // Auto-subscribe
    subscribe('kanban');
    subscribe('global');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      const handlers = listeners.get(data.type) || [];
      handlers.forEach((handler) => handler(data));
      
      // Wildcard listeners
      const wildcards = listeners.get('*') || [];
      wildcards.forEach((handler) => handler(data));
    } catch (e) {
      console.error('WS parse error:', e);
    }
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected, reconnecting...');
    setTimeout(() => connect(token), 3000);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  return ws;
}

export function subscribe(channel: string, agentId?: string, taskId?: string) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  
  const msg: any = { action: 'subscribe', channel };
  if (agentId) msg.agent_id = agentId;
  if (taskId) msg.task_id = taskId;
  
  ws.send(JSON.stringify(msg));
}

export function on(eventType: string, handler: (event: any) => void) {
  if (!listeners.has(eventType)) listeners.set(eventType, []);
  listeners.get(eventType)!.push(handler);
}

export function off(eventType: string, handler: (event: any) => void) {
  const handlers = listeners.get(eventType) || [];
  const idx = handlers.indexOf(handler);
  if (idx > -1) handlers.splice(idx, 1);
}
```

### 4.2 WebSocket Hook
- [ ] Crear `frontend/hooks/useWebSocket.ts`:

```typescript
// hooks/useWebSocket.ts
'use client';

import { useEffect } from 'react';
import { connect, on } from '@/lib/websocket';
import { useActivityStore } from '@/store/activity.store';
import { useAgentsStore } from '@/store/agents.store';
import { useTasksStore } from '@/store/tasks.store';

export function useWebSocket() {
  const addActivity = useActivityStore((s) => s.addEntry);
  const updateAgent = useAgentsStore((s) => s.updateAgent);
  const updateTask = useTasksStore((s) => s.updateTask);

  useEffect(() => {
    const token = localStorage.getItem('token') || 'dev-token';
    connect(token);

    // Activity feed
    on('activity_feed', (event) => {
      addActivity(event.payload);
    });

    // Agent status changes
    on('agent_status_changed', (event) => {
      updateAgent(event.payload.agent_id, {
        status: event.payload.new_status,
        current_task_id: event.payload.current_task_id,
      });
    });

    // Task status changes
    on('task_status_changed', (event) => {
      updateTask(event.payload.task_id, {
        status: event.payload.new_status,
        assigned_agent_id: event.payload.assigned_agent_id,
      });
    });

    return () => {
      // Cleanup listeners on unmount
    };
  }, [addActivity, updateAgent, updateTask]);
}
```

---

## FASE 5: Coworking Office (Días 6-10)

### 5.1 Coworking Canvas
- [ ] Crear `frontend/components/coworking/CoworkingCanvas.tsx`:

```typescript
// components/coworking/CoworkingCanvas.tsx
'use client';

import { useEffect, useRef, useState } from 'react';
import { Stage, Layer } from 'react-konva';
import { useAgentsStore } from '@/store/agents.store';
import { OfficeFloor } from './OfficeFloor';
import { DeskGrid } from './DeskGrid';

export function CoworkingCanvas() {
  const agents = useAgentsStore((s) => Object.values(s.agents));
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });
    
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="w-full h-full bg-slate-950 relative">
      <Stage
        width={dimensions.width}
        height={dimensions.height}
      >
        <Layer>
          <OfficeFloor width={dimensions.width} height={dimensions.height} />
        </Layer>
        
        <Layer>
          <DeskGrid
            agents={agents}
            canvasWidth={dimensions.width}
            canvasHeight={dimensions.height}
            onAgentClick={setSelectedAgentId}
          />
        </Layer>
      </Stage>

      {/* Selected Agent Panel */}
      {selectedAgentId && (
        <AgentDetailPanel
          agentId={selectedAgentId}
          onClose={() => setSelectedAgentId(null)}
        />
      )}
    </div>
  );
}
```

### 5.2 Office Floor
- [ ] Crear `frontend/components/coworking/OfficeFloor.tsx`:

```typescript
// components/coworking/OfficeFloor.tsx
import { Rect, Group } from 'react-konva';

interface OfficeFloorProps {
  width: number;
  height: number;
}

export function OfficeFloor({ width, height }: OfficeFloorProps) {
  const TILE_SIZE = 48;
  const tiles = [];

  // Checkerboard pattern
  for (let row = 0; row * TILE_SIZE < height; row++) {
    for (let col = 0; col * TILE_SIZE < width; col++) {
      tiles.push(
        <Rect
          key={`${row}-${col}`}
          x={col * TILE_SIZE}
          y={row * TILE_SIZE}
          width={TILE_SIZE}
          height={TILE_SIZE}
          fill={(row + col) % 2 === 0 ? '#0f172a' : '#1e293b'}
        />
      );
    }
  }

  return <Group>{tiles}</Group>;
}
```

### 5.3 Desk Grid con Agentes
- [ ] Crear `frontend/components/coworking/DeskGrid.tsx`:

```typescript
// components/coworking/DeskGrid.tsx
import { Agent } from '@/types';
import { AgentDesk } from './AgentDesk';

interface DeskGridProps {
  agents: Agent[];
  canvasWidth: number;
  canvasHeight: number;
  onAgentClick: (id: string) => void;
}

export function DeskGrid({ agents, canvasWidth, canvasHeight, onAgentClick }: DeskGridProps) {
  const cols = Math.ceil(Math.sqrt(agents.length));
  const rows = Math.ceil(agents.length / cols);
  
  const cellW = canvasWidth / (cols + 1);
  const cellH = canvasHeight / (rows + 1);

  return (
    <>
      {agents.map((agent, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        const x = cellW * (col + 1);
        const y = cellH * (row + 1);

        return (
          <AgentDesk
            key={agent.id}
            agent={agent}
            x={x}
            y={y}
            onClick={() => onAgentClick(agent.id)}
          />
        );
      })}
    </>
  );
}
```

### 5.4 Agent Desk
- [ ] Crear `frontend/components/coworking/AgentDesk.tsx`:

```typescript
// components/coworking/AgentDesk.tsx
import { Group, Rect, Circle, Text } from 'react-konva';
import { Agent } from '@/types';

interface AgentDeskProps {
  agent: Agent;
  x: number;
  y: number;
  onClick: () => void;
}

const statusColors = {
  IDLE: '#94a3b8',
  WORKING: '#22c55e',
  ERROR: '#ef4444',
  OFFLINE: '#6b7280',
};

const domainIcons: Record<string, string> = {
  TECH: '💻',
  FINANCE: '💰',
  MARKETING: '📢',
  HR: '👥',
  LEGAL: '⚖️',
  BUSINESS: '💼',
  PERSONAL: '🏠',
  OTHER: '🔧',
};

export function AgentDesk({ agent, x, y, onClick }: AgentDeskProps) {
  const isWorking = agent.status === 'WORKING';
  const isError = agent.status === 'ERROR';
  const isOffline = agent.status === 'OFFLINE';

  return (
    <Group x={x} y={y} onClick={onClick} onTap={onClick}>
      {/* Desk */}
      <Rect
        x={-40}
        y={-20}
        width={80}
        height={40}
        fill="#334155"
        cornerRadius={4}
        stroke="#475569"
        strokeWidth={2}
      />
      
      {/* Monitor */}
      <Rect
        x={-15}
        y={-45}
        width={30}
        height={25}
        fill={isWorking ? '#1e40af' : '#1f2937'}
        cornerRadius={2}
        shadowColor={isWorking ? '#3b82f6' : undefined}
        shadowBlur={isWorking ? 15 : 0}
      />

      {/* Agent avatar placeholder */}
      <Circle
        x={0}
        y={-60}
        radius={20}
        fill={agent.avatar_config?.color_primary || '#3b82f6'}
        stroke={statusColors[agent.status]}
        strokeWidth={3}
        opacity={isOffline ? 0.4 : 1}
      />

      {/* Status dot */}
      <Circle
        x={15}
        y={-75}
        radius={5}
        fill={statusColors[agent.status]}
        shadowColor={isWorking ? '#22c55e' : undefined}
        shadowBlur={isWorking ? 8 : 0}
      />

      {/* Domain icon */}
      <Text
        x={-10}
        y={-70}
        text={domainIcons[agent.domain] || '🔧'}
        fontSize={16}
      />

      {/* Agent name */}
      <Text
        x={-50}
        y={25}
        width={100}
        text={agent.name}
        fontSize={11}
        fill="white"
        align="center"
      />

      {/* Error indicator */}
      {isError && (
        <Text
          x={-25}
          y={-95}
          text="⚠️"
          fontSize={20}
        />
      )}
    </Group>
  );
}
```

---

## FASE 6: Agent Management (Días 8-10)

### 6.1 Agent List Page
- [ ] Crear `frontend/app/agents/page.tsx`:

```typescript
// app/agents/page.tsx
'use client';

import { useAgents } from '@/hooks/useAgents';
import { useAgentsStore } from '@/store/agents.store';
import { AgentCard } from '@/components/agents/AgentCard';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import Link from 'next/link';

export default function AgentsPage() {
  const { isLoading } = useAgents();
  const agents = useAgentsStore((s) => Object.values(s.agents));

  if (isLoading) {
    return <div className="p-8">Loading agents...</div>;
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Agents</h1>
          <p className="text-slate-400">Manage your AI team</p>
        </div>
        <Link href="/agents/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Create Agent
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  );
}
```

### 6.2 Agent Card
- [ ] Crear `frontend/components/agents/AgentCard.tsx`:

```typescript
// components/agents/AgentCard.tsx
import { Agent } from '@/types';
import Link from 'next/link';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { User, Cpu } from 'lucide-react';

interface AgentCardProps {
  agent: Agent;
}

const statusColors = {
  IDLE: 'bg-slate-600',
  WORKING: 'bg-green-600',
  ERROR: 'bg-red-600',
  OFFLINE: 'bg-gray-600',
};

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <Link href={`/agents/${agent.id}`}>
      <Card className="hover:border-blue-500 transition-colors cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
                style={{ backgroundColor: agent.avatar_config?.color_primary || '#3b82f6' }}
              >
                {agent.avatar_config?.icon || '🤖'}
              </div>
              <div>
                <h3 className="font-semibold">{agent.name}</h3>
                <p className="text-sm text-slate-500">{agent.agent_class?.name}</p>
              </div>
            </div>
            <Badge className={cn(statusColors[agent.status])}>
              {agent.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <div className="flex items-center gap-1">
              <User className="w-4 h-4" />
              <span>{agent.domain}</span>
            </div>
            {agent.current_task_id && (
              <div className="flex items-center gap-1 text-blue-400">
                <Cpu className="w-4 h-4" />
                <span>Working...</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
```

---

## 🎯 Checklist de Finalización

### MVP Core (Días 1-7)
- [ ] Next.js setup con todas las dependencias
- [ ] Type definitions completos
- [ ] API client funcional
- [ ] Zustand stores implementados
- [ ] TanStack Query hooks funcionando
- [ ] Sidebar navigation
- [ ] Activity panel live
- [ ] Kanban board con drag & drop
- [ ] WebSocket conexión y eventos

### Visual Features (Días 6-10)
- [ ] Coworking canvas renderizando
- [ ] Office floor tiles
-- [ ] Agent desks visibles
- [ ] Agent status animations
- [ ] Agent list page
- [ ] Agent detail view
- [ ] Agent creation wizard (básico)

### Polish (Día 10+)
- [ ] Loading states
- [ ] Error handling
- [ ] Empty states
- [ ] Responsive design
- [ ] Animaciones con Framer Motion
- [ ] Dark mode consistente

---

## 🚀 Éxito = Kanban funcional + Coworking office visible

**Métricas:**
- [ ] Poder crear tareas desde UI
- [ ] Drag & drop entre columnas
- [ ] Ver agentes en el canvas
- [ ] Activity feed con eventos reales
- [ ] Navegación fluida entre páginas

**Cuando esté listo:** Qubot será visualmente SUPERIOR a OpenClaw.
