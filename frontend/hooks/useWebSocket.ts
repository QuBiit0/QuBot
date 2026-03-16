'use client';

import { useEffect, useRef } from 'react';
import { useAgentsStore } from '@/store/agents.store';
import { useTasksStore } from '@/store/tasks.store';
import { useAppStore } from '@/store/app.store';
import { useActivityStore } from '@/store/activity.store';
import { WebSocketMessage, TaskStatus } from '@/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

const RECONNECT_CONFIG = {
  initialDelay: 1000,
  maxDelay: 30000,
  multiplier: 2,
  jitter: 0.1,
  maxAttempts: 10,
};

export function useWebSocket() {
  // All state in refs to avoid stale closure issues and prevent effect re-runs
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isConnecting = useRef(false);
  // Prevents reconnect loop when user explicitly logs out or component unmounts
  const manualDisconnect = useRef(false);

  // Access store actions directly from store state — avoids hook subscriptions
  // that would cause re-renders and re-run effects
  const storeRef = useRef({
    updateAgent: useAgentsStore.getState().updateAgent,
    updateTask: useTasksStore.getState().updateTask,
    setConnected: useAppStore.getState().setConnected,
    setConnectionState: useAppStore.getState().setConnectionState,
    updateMetrics: useAppStore.getState().updateMetrics,
    addEntry: useActivityStore.getState().addEntry,
  });

  // Keep store action refs up to date (actions are stable, but this handles edge cases)
  useEffect(() => {
    const unsubs = [
      useAgentsStore.subscribe((s) => { storeRef.current.updateAgent = s.updateAgent; }),
      useTasksStore.subscribe((s) => { storeRef.current.updateTask = s.updateTask; }),
      useAppStore.subscribe((s) => {
        storeRef.current.setConnected = s.setConnected;
        storeRef.current.setConnectionState = s.setConnectionState;
        storeRef.current.updateMetrics = s.updateMetrics;
      }),
      useActivityStore.subscribe((s) => { storeRef.current.addEntry = s.addEntry; }),
    ];
    return () => unsubs.forEach((u) => u());
  }, []);

  // Defined as refs so connect/attemptReconnect can call each other without
  // circular useCallback dependency issues
  const handleMessage = useRef((data: WebSocketMessage) => {
    const { updateAgent, updateTask, addEntry, updateMetrics } = storeRef.current;

    switch (data.type) {
      case 'AGENT_UPDATE':
        if (data.id && data.payload) {
          updateAgent(data.id, data.payload as Parameters<typeof updateAgent>[1]);
          const p = data.payload as { state?: string; name?: string };
          if (p.state) {
            addEntry({
              id: `agent-${Date.now()}`,
              timestamp: new Date().toISOString(),
              type: 'agent_update',
              message: `${p.name ?? 'Agent'} is now ${p.state}`,
              severity: 'info',
              agent_id: data.id,
              agent_name: p.name,
            });
          }
        }
        break;

      case 'TASK_UPDATE':
        if (data.id && data.payload) {
          updateTask(data.id as string, data.payload as Parameters<typeof updateTask>[1]);
          const p = data.payload as { status?: TaskStatus; title?: string };
          if (p.status) {
            addEntry({
              id: `task-${Date.now()}`,
              timestamp: new Date().toISOString(),
              type: 'task_update',
              message: `Task "${p.title ?? ''}" moved to ${p.status}`,
              severity: 'success',
            });
          }
        }
        break;

      case 'ACTIVITY_EVENT':
        if (data.payload) {
          const e = data.payload as {
            message: string;
            severity?: 'info' | 'success' | 'warning' | 'error';
            agent_id?: string | number;
            agent_name?: string;
          };
          addEntry({
            id: `activity-${Date.now()}`,
            timestamp: new Date().toISOString(),
            type: data.type,
            message: e.message,
            severity: e.severity ?? 'info',
            agent_id: e.agent_id,
            agent_name: e.agent_name,
          });
        }
        break;

      case 'METRICS_UPDATE':
        if (data.payload) {
          updateMetrics(data.payload as Parameters<typeof updateMetrics>[0]);
        }
        break;

      case 'PING':
        ws.current?.send(JSON.stringify({ type: 'PONG' }));
        break;
    }
  });

  const attemptReconnect = useRef(() => {
    if (manualDisconnect.current) return;
    if (reconnectAttempts.current >= RECONNECT_CONFIG.maxAttempts) return;

    const base = RECONNECT_CONFIG.initialDelay *
      Math.pow(RECONNECT_CONFIG.multiplier, reconnectAttempts.current);
    const delay = Math.min(base, RECONNECT_CONFIG.maxDelay);
    const jitter = delay * (1 + (Math.random() * 2 - 1) * RECONNECT_CONFIG.jitter);

    reconnectTimeout.current = setTimeout(() => {
      reconnectAttempts.current++;
      connect.current();
    }, jitter);
  });

  const connect = useRef(() => {
    if (manualDisconnect.current) return;
    if (isConnecting.current || ws.current?.readyState === WebSocket.OPEN) return;

    isConnecting.current = true;
    storeRef.current.setConnectionState('connecting');

    // Attach auth token as query parameter for backend WS auth
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const url = token ? `${WS_URL}?token=${encodeURIComponent(token)}` : WS_URL;

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        reconnectAttempts.current = 0;
        storeRef.current.setConnected(true);
        storeRef.current.setConnectionState('connected');
        isConnecting.current = false;
      };

      ws.current.onmessage = (event: MessageEvent) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data as string);
          handleMessage.current(data);
        } catch {
          // Ignore malformed messages
        }
      };

      ws.current.onclose = () => {
        storeRef.current.setConnected(false);
        storeRef.current.setConnectionState('disconnected');
        isConnecting.current = false;
        attemptReconnect.current();
      };

      ws.current.onerror = () => {
        storeRef.current.setConnectionState('error');
        isConnecting.current = false;
      };
    } catch {
      storeRef.current.setConnectionState('error');
      isConnecting.current = false;
      attemptReconnect.current();
    }
  });

  useEffect(() => {
    manualDisconnect.current = false;
    connect.current();

    return () => {
      // Mark as intentional so onclose doesn't trigger reconnect
      manualDisconnect.current = true;

      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }

      if (ws.current) {
        // Remove onclose before closing so reconnect doesn't trigger
        ws.current.onclose = null;
        ws.current.close();
        ws.current = null;
      }

      storeRef.current.setConnected(false);
      storeRef.current.setConnectionState('disconnected');
    };
  }, []); // Single lifecycle — intentionally empty deps
}
