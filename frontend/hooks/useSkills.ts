'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface Skill {
  id: string;
  name: string;
  description?: string;
  code?: string;
  language: 'python' | 'javascript';
  created_by?: string;
  is_public: boolean;
  is_official: boolean;
  version: string;
  usage_count: number;
  rating_average: number;
  rating_count: number;
  parameters: SkillParameter[];
  created_at: string;
  updated_at: string;
}

export interface SkillParameter {
  id?: string;
  name: string;
  param_type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description?: string;
  required: boolean;
  default_value?: any;
}

export interface AgentSkill {
  id: string;
  agent_id: string;
  skill_id: string;
  skill_name: string;
  skill_description?: string;
  is_enabled: boolean;
  permission_level: 'READ_ONLY' | 'READ_WRITE' | 'DANGEROUS';
  use_count: number;
  last_used_at?: string;
  config: Record<string, any>;
}

export function useSkills(filters?: { public_only?: boolean; search?: string; language?: string }) {
  return useQuery({
    queryKey: ['skills', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.public_only) params.append('public_only', 'true');
      if (filters?.search) params.append('search', filters.search);
      if (filters?.language) params.append('language', filters.language);
      
      const response = await api.get<Skill[]>(`/skills?${params.toString()}`);
      return response;
    },
  });
}

export function useSkill(id: string) {
  return useQuery({
    queryKey: ['skills', id],
    queryFn: async () => {
      const response = await api.get<Skill>(`/skills/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateSkill() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: Partial<Skill>) => {
      const response = await api.post<Skill>('/skills', data);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });
}

export function useUpdateSkill() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Skill> }) => {
      const response = await api.patch<Skill>(`/skills/${id}`, data);
      return response;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['skills', variables.id] });
    },
  });
}

export function useDeleteSkill() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/skills/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });
}

export function useExecuteSkill() {
  return useMutation({
    mutationFn: async ({ 
      skillId, 
      parameters, 
      timeout = 30 
    }: { 
      skillId: string; 
      parameters: Record<string, any>; 
      timeout?: number;
    }) => {
      const response = await api.post<{
        success: boolean;
        result?: any;
        error?: string;
        execution_time_ms: number;
      }>(`/skills/${skillId}/execute`, { parameters, timeout });
      return response;
    },
  });
}

// Agent Skills
export function useAgentSkills(agentId: string) {
  return useQuery({
    queryKey: ['agent-skills', agentId],
    queryFn: async () => {
      const response = await api.get<AgentSkill[]>(`/skills/agent/${agentId}/skills`);
      return response;
    },
    enabled: !!agentId,
  });
}

export function useAssignSkillToAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ 
      agentId, 
      skillId, 
      config = {},
      permission_level = 'READ_WRITE'
    }: { 
      agentId: string; 
      skillId: string; 
      config?: Record<string, any>;
      permission_level?: string;
    }) => {
      const response = await api.post<AgentSkill>(`/skills/agent/${agentId}/skills`, {
        skill_id: skillId,
        config,
        permission_level,
      });
      return response;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agent-skills', variables.agentId] });
    },
  });
}

export function useRemoveSkillFromAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ agentId, agentSkillId }: { agentId: string; agentSkillId: string }) => {
      await api.delete(`/skills/agent/${agentId}/skills/${agentSkillId}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agent-skills', variables.agentId] });
    },
  });
}
