'use client';

import { create } from 'zustand';
import { Task, TaskStatus } from '@/types';

interface TasksState {
  tasks: Record<string, Task>;
  selectedTask: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  removeTask: (id: string) => void;
  moveTask: (taskId: string, newStatus: TaskStatus) => void;
  selectTask: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useTasksStore = create<TasksState>((set) => ({
  tasks: {},
  selectedTask: null,
  isLoading: false,
  error: null,

  setTasks: (tasks) => {
    const taskMap: Record<string | number, Task> = {};
    tasks.forEach((task) => {
      taskMap[task.id] = task;
    });
    set({ tasks: taskMap, isLoading: false, error: null });
  },

  addTask: (task) => {
    set((state) => ({
      tasks: { ...state.tasks, [task.id]: task },
    }));
  },

  updateTask: (id, updates) => {
    set((state) => {
      const task = state.tasks[id];
      if (!task) return state;
      
      return {
        tasks: {
          ...state.tasks,
          [id]: { ...task, ...updates },
        },
      };
    });
  },

  removeTask: (id) => {
    set((state) => {
      const { [id]: _, ...rest } = state.tasks;
      return { tasks: rest };
    });
  },

  moveTask: (taskId, newStatus) => {
    set((state) => {
      const task = state.tasks[taskId];
      if (!task) return state;
      
      return {
        tasks: {
          ...state.tasks,
          [taskId]: { ...task, status: newStatus },
        },
      };
    });
  },

  selectTask: (id) => {
    set({ selectedTask: id });
  },

  setLoading: (loading) => {
    set({ isLoading: loading });
  },

  setError: (error) => {
    set({ error, isLoading: false });
  },
}));
