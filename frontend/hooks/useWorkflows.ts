'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi, Workflow, WorkflowNode, WorkflowEdge } from '@/lib/api';

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await workflowsApi.getAll();
      return response.data as Workflow[];
    },
  });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: ['workflows', id],
    queryFn: async () => {
      const response = await workflowsApi.getById(id);
      return response.data as Workflow;
    },
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      workflowsApi.create({ ...data, nodes: [], edges: [] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useSaveWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      nodes,
      edges,
      name,
    }: {
      id: string;
      nodes: WorkflowNode[];
      edges: WorkflowEdge[];
      name?: string;
    }) => workflowsApi.update(id, { nodes, edges, ...(name ? { name } : {}) }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflows', id] });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workflowsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}
