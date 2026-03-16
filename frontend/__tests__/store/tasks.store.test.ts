/**
 * Unit tests for tasks store
 */
import { useTasksStore } from '@/store/tasks.store';
import type { Task, TaskStatus } from '@/types';

const makeTask = (overrides: Partial<Task> = {}): Task => ({
  id: Math.random().toString(36).slice(2),
  title: 'Test Task',
  status: 'BACKLOG' as TaskStatus,
  priority: 'MEDIUM' as Task['priority'],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  tags: [],
  ...overrides,
});

describe('useTasksStore', () => {
  beforeEach(() => {
    useTasksStore.setState({ tasks: {}, selectedTask: null, isLoading: false, error: null });
  });

  describe('setTasks', () => {
    it('converts array to map by id', () => {
      const tasks = [makeTask({ id: 'a' }), makeTask({ id: 'b' })];
      useTasksStore.getState().setTasks(tasks);
      const state = useTasksStore.getState();
      expect(state.tasks['a']).toBeDefined();
      expect(state.tasks['b']).toBeDefined();
      expect(Object.keys(state.tasks)).toHaveLength(2);
    });

    it('clears loading and error', () => {
      useTasksStore.setState({ isLoading: true, error: 'old error' });
      useTasksStore.getState().setTasks([]);
      const state = useTasksStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe('addTask', () => {
    it('adds task to the map', () => {
      const task = makeTask({ id: 'new-task' });
      useTasksStore.getState().addTask(task);
      expect(useTasksStore.getState().tasks['new-task']).toEqual(task);
    });
  });

  describe('updateTask', () => {
    it('merges updates into existing task', () => {
      const task = makeTask({ id: 't1', title: 'Old' });
      useTasksStore.setState({ tasks: { t1: task } });
      useTasksStore.getState().updateTask('t1', { title: 'New' });
      expect(useTasksStore.getState().tasks['t1']!.title).toBe('New');
    });

    it('is a no-op for nonexistent task', () => {
      useTasksStore.getState().updateTask('ghost', { title: 'x' });
      expect(useTasksStore.getState().tasks['ghost']).toBeUndefined();
    });
  });

  describe('removeTask', () => {
    it('removes task from the map', () => {
      const task = makeTask({ id: 'rm' });
      useTasksStore.setState({ tasks: { rm: task } });
      useTasksStore.getState().removeTask('rm');
      expect(useTasksStore.getState().tasks['rm']).toBeUndefined();
    });
  });

  describe('moveTask', () => {
    it('updates task status', () => {
      const task = makeTask({ id: 'mv', status: 'BACKLOG' as TaskStatus });
      useTasksStore.setState({ tasks: { mv: task } });
      useTasksStore.getState().moveTask('mv', 'IN_PROGRESS' as TaskStatus);
      expect(useTasksStore.getState().tasks['mv']!.status).toBe('IN_PROGRESS');
    });

    it('is a no-op for nonexistent task', () => {
      useTasksStore.getState().moveTask('ghost', 'DONE' as TaskStatus);
      expect(useTasksStore.getState().tasks['ghost']).toBeUndefined();
    });
  });

  describe('selectTask', () => {
    it('sets selectedTask', () => {
      useTasksStore.getState().selectTask('t1');
      expect(useTasksStore.getState().selectedTask).toBe('t1');
    });

    it('clears selectedTask when null', () => {
      useTasksStore.setState({ selectedTask: 't1' });
      useTasksStore.getState().selectTask(null);
      expect(useTasksStore.getState().selectedTask).toBeNull();
    });
  });

  describe('setLoading / setError', () => {
    it('setLoading updates isLoading', () => {
      useTasksStore.getState().setLoading(true);
      expect(useTasksStore.getState().isLoading).toBe(true);
    });

    it('setError sets error and clears loading', () => {
      useTasksStore.setState({ isLoading: true });
      useTasksStore.getState().setError('boom');
      expect(useTasksStore.getState().error).toBe('boom');
      expect(useTasksStore.getState().isLoading).toBe(false);
    });
  });
});
