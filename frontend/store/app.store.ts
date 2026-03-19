'use client';

import { create } from 'zustand';

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type?: string;
  message: string;
  severity?: 'info' | 'success' | 'warning' | 'error';
  status?: 'done' | 'completed' | 'working' | 'in_progress' | 'planning' | 'pending' | 'created' | 'assigned' | 'failed' | 'error' | 'user' | 'idle' | 'offline';
  agent_id?: string | number;
  /** @deprecated use agent_name */
  agentName?: string;
  agent_name?: string;
  metadata?: Record<string, unknown>;
}

interface AppState {
  isConnected: boolean;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error';
  metrics: {
    cpu: number;
    memory: number;
    activeAgents: number;
    pendingTasks: number;
    totalTasks: number;
  };
  activityLog: ActivityEvent[];
  
  // Actions
  setConnected: (connected: boolean) => void;
  setConnectionState: (state: AppState['connectionState']) => void;
  addActivityEvent: (event: ActivityEvent) => void;
  updateMetrics: (metrics: Partial<AppState['metrics']>) => void;
  clearActivityLog: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  isConnected: false,
  connectionState: 'disconnected',
  metrics: {
    cpu: 0,
    memory: 0,
    activeAgents: 0,
    pendingTasks: 0,
    totalTasks: 0,
  },
  activityLog: [],

  setConnected: (connected) => {
    set({ 
      isConnected: connected,
      connectionState: connected ? 'connected' : 'disconnected'
    });
  },

  setConnectionState: (state) => {
    set({ 
      connectionState: state,
      isConnected: state === 'connected'
    });
  },

  addActivityEvent: (event) => {
    set((state) => ({
      activityLog: [event, ...state.activityLog.slice(0, 99)], // Keep last 100
    }));
  },

  updateMetrics: (metrics) => {
    set((state) => ({
      metrics: { ...state.metrics, ...metrics },
    }));
  },

  clearActivityLog: () => {
    set({ activityLog: [] });
  },
}));
