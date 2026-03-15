'use client';

import { create } from 'zustand';

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: string;
  message: string;
  severity: 'info' | 'success' | 'warning' | 'error';
  agent_id?: string | number;
  agent_name?: string;
  metadata?: Record<string, unknown>;
}

interface ActivityState {
  entries: ActivityEvent[];
  isPaused: boolean;
  filter: 'all' | 'info' | 'success' | 'warning' | 'error';
  
  // Actions
  addEntry: (entry: ActivityEvent) => void;
  clear: () => void;
  togglePause: () => void;
  setFilter: (filter: ActivityState['filter']) => void;
  getFilteredEntries: () => ActivityEvent[];
  getRecentEntries: (count: number) => ActivityEvent[];
}

export const useActivityStore = create<ActivityState>((set, get) => ({
  entries: [],
  isPaused: false,
  filter: 'all',

  addEntry: (entry) => {
    const state = get();
    if (state.isPaused) return;
    
    set((s) => ({
      entries: [entry, ...s.entries.slice(0, 199)], // Keep last 200
    }));
  },

  clear: () => {
    set({ entries: [] });
  },

  togglePause: () => {
    set((state) => ({ isPaused: !state.isPaused }));
  },

  setFilter: (filter) => {
    set({ filter });
  },

  getFilteredEntries: () => {
    const { entries, filter } = get();
    if (filter === 'all') return entries;
    return entries.filter((e) => e.severity === filter);
  },

  getRecentEntries: (count: number) => {
    const { entries } = get();
    return entries.slice(0, count);
  },
}));
