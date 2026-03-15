'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAgentsStore } from '@/store/agents.store';
import { Agent } from '@/types';

export function useAgents() {
  const setAgents = useAgentsStore((s) => s.setAgents);
  const setLoading = useAgentsStore((s) => s.setLoading);
  const setError = useAgentsStore((s) => s.setError);

  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      setLoading(true);
      try {
        const response = await api.getAgents();
        setAgents(response.data);
        return response.data;
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Unknown error');
        throw error;
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useAgent(id: string) {
  return useQuery({
    queryKey: ['agents', id],
    queryFn: async () => {
      const response = await api.getAgent(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  const addAgent = useAgentsStore((s) => s.addAgent);

  return useMutation({
    mutationFn: async (data: Partial<Agent>) => {
      const response = await api.createAgent(data);
      return response.data;
    },
    onSuccess: (data) => {
      addAgent(data);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();
  const updateAgent = useAgentsStore((s) => s.updateAgent);

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Agent> }) => {
      const response = await api.updateAgent(id, data);
      return response.data;
    },
    onSuccess: (data) => {
      updateAgent(data.id, data);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['agents', data.id] });
    },
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  const removeAgent = useAgentsStore((s) => s.removeAgent);

  return useMutation({
    mutationFn: api.deleteAgent,
    onSuccess: (_, id) => {
      removeAgent(id);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
