'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useTasksStore } from '@/store/tasks.store';
import { Task, TaskStatus } from '@/types';

export function useTasks() {
  const setTasks = useTasksStore((s) => s.setTasks);
  const setLoading = useTasksStore((s) => s.setLoading);
  const setError = useTasksStore((s) => s.setError);

  return useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      setLoading(true);
      try {
        const response = await api.getTasks();
        setTasks(response.data);
        return response.data;
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Unknown error');
        throw error;
      }
    },
    refetchInterval: 30000,
  });
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ['tasks', id],
    queryFn: async () => {
      const response = await api.getTask(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  const addTask = useTasksStore((s) => s.addTask);

  return useMutation({
    mutationFn: async (data: Partial<Task>) => {
      const response = await api.createTask(data);
      return response.data;
    },
    onSuccess: (data) => {
      addTask(data);
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  const updateTask = useTasksStore((s) => s.updateTask);

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Task> }) => {
      const response = await api.updateTask(id, data);
      return response.data;
    },
    onSuccess: (data) => {
      updateTask(data.id, data);
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['tasks', data.id] });
    },
  });
}

export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();
  const updateTask = useTasksStore((s) => s.updateTask);

  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: TaskStatus }) => {
      const response = await api.updateTaskStatus(id, status);
      return response.data;
    },
    onMutate: async ({ id, status }) => {
      // Optimistic update
      const previousTask = queryClient.getQueryData(['tasks', id]);
      updateTask(id, { status });
      return { previousTask };
    },
    onSuccess: (data) => {
      updateTask(data.id, data);
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousTask) {
        updateTask(variables.id, context.previousTask as Task);
      }
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  const removeTask = useTasksStore((s) => s.removeTask);

  return useMutation({
    mutationFn: api.deleteAgent,
    onSuccess: (_, id) => {
      removeTask(id);
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}
