'use client';

import { create } from 'zustand';
import { Agent } from '@/types';

interface AgentsState {
  agents: Record<string, Agent>;
  selectedAgent: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setAgents: (agents: Agent[]) => void;
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  removeAgent: (id: string) => void;
  selectAgent: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAgentsStore = create<AgentsState>((set) => ({
  agents: {},
  selectedAgent: null,
  isLoading: false,
  error: null,

  setAgents: (agents) => {
    const agentMap: Record<string, Agent> = {};
    agents.forEach((agent) => {
      agentMap[agent.id] = agent;
    });
    set({ agents: agentMap, isLoading: false, error: null });
  },

  addAgent: (agent) => {
    set((state) => ({
      agents: { ...state.agents, [agent.id]: agent },
    }));
  },

  updateAgent: (id, updates) => {
    set((state) => {
      const agent = state.agents[id];
      if (!agent) return state;
      
      return {
        agents: {
          ...state.agents,
          [id]: { ...agent, ...updates },
        },
      };
    });
  },

  removeAgent: (id) => {
    set((state) => {
      const { [id]: _, ...rest } = state.agents;
      return { agents: rest };
    });
  },

  selectAgent: (id) => {
    set({ selectedAgent: id });
  },

  setLoading: (loading) => {
    set({ isLoading: loading });
  },

  setError: (error) => {
    set({ error, isLoading: false });
  },
}));
