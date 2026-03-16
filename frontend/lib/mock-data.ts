import { Agent, Task, ActivityEvent } from '@/types';

export const mockAgents: Agent[] = [
  {
    id: 'agent-1',
    name: 'Alice',
    role: 'Lead Developer',
    domain: 'development',
    description: 'Senior full-stack developer with expertise in React and Node.js',
    state: 'working',
    status: 'WORKING' as const,
    current_task: {
      id: 'task-1',
      title: 'Implement authentication system',
      status: 'IN_PROGRESS',
    },
    config: {
      model: 'gpt-4',
      temperature: 0.7,
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'agent-2',
    name: 'Bob',
    role: 'DevOps Engineer',
    domain: 'devops',
    description: 'Infrastructure and CI/CD specialist',
    state: 'idle',
    status: 'IDLE' as const,
    current_task: null,
    config: {
      model: 'gpt-4',
      temperature: 0.5,
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'agent-3',
    name: 'Carol',
    role: 'UX Designer',
    domain: 'design',
    description: 'Creative designer focused on user experience',
    state: 'thinking',
    status: 'WORKING' as const,
    current_task: {
      id: 'task-2',
      title: 'Design system components',
      status: 'IN_PROGRESS',
    },
    config: {
      model: 'gpt-4',
      temperature: 0.8,
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'agent-4',
    name: 'David',
    role: 'Data Analyst',
    domain: 'analytics',
    description: 'Data scientist specializing in ML and analytics',
    state: 'working',
    status: 'WORKING' as const,
    current_task: {
      id: 'task-3',
      title: 'Analyze user metrics',
      status: 'IN_PROGRESS',
    },
    config: {
      model: 'gpt-4',
      temperature: 0.6,
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'agent-5',
    name: 'Eve',
    role: 'Marketing Specialist',
    domain: 'marketing',
    description: 'Digital marketing and content strategist',
    state: 'talking',
    status: 'IDLE' as const,
    current_task: null,
    config: {
      model: 'gpt-4',
      temperature: 0.9,
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'agent-6',
    name: 'Frank',
    role: 'Product Manager',
    domain: 'product',
    description: 'Product strategist and roadmap planner',
    state: 'idle',
    status: 'IDLE' as const,
    current_task: null,
    config: {
      model: 'gpt-4',
      temperature: 0.7,
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
];

export const mockTasks: Task[] = [
  {
    id: 'task-1',
    title: 'Implement authentication system',
    description: 'Build JWT-based authentication with refresh tokens',
    status: 'IN_PROGRESS',
    priority: 1,
    agentId: 'agent-1',
    assigned_to: { id: 'agent-1', name: 'Alice' },
    tags: ['backend', 'security', 'auth'],
    due_date: '2024-02-01T23:59:59Z',
    created_at: '2024-01-10T10:00:00Z',
    updated_at: '2024-01-15T14:30:00Z',
  },
  {
    id: 'task-2',
    title: 'Design system components',
    description: 'Create reusable UI component library',
    status: 'IN_PROGRESS',
    priority: 2,
    agentId: 'agent-3',
    assigned_to: { id: 'agent-3', name: 'Carol' },
    tags: ['design', 'ui', 'components'],
    due_date: '2024-02-05T23:59:59Z',
    created_at: '2024-01-12T10:00:00Z',
    updated_at: '2024-01-15T11:20:00Z',
  },
  {
    id: 'task-3',
    title: 'Analyze user metrics',
    description: 'Review Q4 user engagement data',
    status: 'IN_PROGRESS',
    priority: 3,
    agentId: 'agent-4',
    assigned_to: { id: 'agent-4', name: 'David' },
    tags: ['analytics', 'data', 'reporting'],
    due_date: '2024-01-25T23:59:59Z',
    created_at: '2024-01-14T10:00:00Z',
    updated_at: '2024-01-15T09:15:00Z',
  },
  {
    id: 'task-4',
    title: 'Setup CI/CD pipeline',
    description: 'Configure GitHub Actions for automated deployment',
    status: 'BACKLOG',
    priority: 2,
    agentId: 'agent-2',
    assigned_to: { id: 'agent-2', name: 'Bob' },
    tags: ['devops', 'cicd', 'automation'],
    due_date: '2024-02-10T23:59:59Z',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'task-5',
    title: 'Write blog post',
    description: 'Article about AI agent collaboration',
    status: 'TODO',
    priority: 4,
    agentId: 'agent-5',
    assigned_to: { id: 'agent-5', name: 'Eve' },
    tags: ['content', 'marketing', 'blog'],
    due_date: '2024-01-30T23:59:59Z',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'task-6',
    title: 'Define product roadmap',
    description: 'Q1 2024 feature planning and prioritization',
    status: 'IN_REVIEW',
    priority: 1,
    agentId: 'agent-6',
    assigned_to: { id: 'agent-6', name: 'Frank' },
    tags: ['product', 'planning', 'roadmap'],
    due_date: '2024-01-20T23:59:59Z',
    created_at: '2024-01-13T10:00:00Z',
    updated_at: '2024-01-15T16:45:00Z',
  },
  {
    id: 'task-7',
    title: 'Update documentation',
    description: 'Refresh API documentation with new endpoints',
    status: 'DONE',
    priority: 3,
    agentId: 'agent-1',
    assigned_to: { id: 'agent-1', name: 'Alice' },
    tags: ['docs', 'api', 'documentation'],
    due_date: '2024-01-18T23:59:59Z',
    created_at: '2024-01-10T10:00:00Z',
    updated_at: '2024-01-14T12:00:00Z',
  },
  {
    id: 'task-8',
    title: 'Optimize database queries',
    description: 'Improve performance of slow queries',
    status: 'BACKLOG',
    priority: 2,
    agentId: undefined,
    assigned_to: null,
    tags: ['backend', 'performance', 'database'],
    due_date: '2024-02-15T23:59:59Z',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
];

export const mockActivityEvents: ActivityEvent[] = [
  {
    id: 'evt-1',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    type: 'task_update',
    message: 'Task "Implement authentication system" moved to IN_PROGRESS',
    severity: 'success',
    agent_id: 'agent-1',
    agent_name: 'Alice',
  },
  {
    id: 'evt-2',
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    type: 'agent_update',
    message: 'Agent Carol is now thinking',
    severity: 'info',
    agent_id: 'agent-3',
    agent_name: 'Carol',
  },
  {
    id: 'evt-3',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    type: 'task_completed',
    message: 'Task "Update documentation" completed',
    severity: 'success',
    agent_id: 'agent-1',
    agent_name: 'Alice',
  },
  {
    id: 'evt-4',
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    type: 'agent_message',
    message: 'Bob: "I\'ll start on the CI/CD pipeline tomorrow"',
    severity: 'info',
    agent_id: 'agent-2',
    agent_name: 'Bob',
  },
  {
    id: 'evt-5',
    timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    type: 'system',
    message: 'System maintenance completed successfully',
    severity: 'info',
  },
  {
    id: 'evt-6',
    timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    type: 'task_update',
    message: 'Task "Define product roadmap" moved to IN_REVIEW',
    severity: 'warning',
    agent_id: 'agent-6',
    agent_name: 'Frank',
  },
  {
    id: 'evt-7',
    timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    type: 'agent_update',
    message: 'Agent David started working on "Analyze user metrics"',
    severity: 'info',
    agent_id: 'agent-4',
    agent_name: 'David',
  },
];

// Initialize stores with mock data
export function initializeMockData() {
  if (typeof window !== 'undefined') {
    const { useAgentsStore } = require('@/store/agents.store');
    const { useTasksStore } = require('@/store/tasks.store');
    const { useActivityStore } = require('@/store/activity.store');

    // Only initialize if stores are empty
    const agentsStore = useAgentsStore.getState();
    const tasksStore = useTasksStore.getState();
    const activityStore = useActivityStore.getState();

    if (Object.keys(agentsStore.agents).length === 0) {
      agentsStore.setAgents(mockAgents);
    }

    if (Object.keys(tasksStore.tasks).length === 0) {
      tasksStore.setTasks(mockTasks);
    }

    if (activityStore.entries.length === 0) {
      mockActivityEvents.forEach((event) => {
        activityStore.addEntry(event);
      });
    }
  }
}
