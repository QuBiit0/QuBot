'use client';

import { useEffect, useRef } from 'react';
import { useAgentsStore } from '@/store/agents.store';
import { useTasksStore } from '@/store/tasks.store';
import { useAppStore } from '@/store/app.store';
import { useActivityStore } from '@/store/activity.store';
import { Task, TaskStatus } from '@/types';

// Backend sends dot-notation event types; map them to our internal uppercase keys.
type BackendEventType =
  | 'task.created' | 'task.updated' | 'task.completed' | 'task.failed' | 'task.assigned'
  | 'agent.status_changed' | 'agent.created' | 'agent.updated'
  | 'tool.executed'
  | 'metrics.updated'
  | 'activity.log'
  | 'system.notification'
  | 'connection.established'
  | string; // fallback

interface BackendMessage {
  type: BackendEventType;
  payload?: Record<string, unknown>;
  timestamp?: string;
  sender_id?: string;
}

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
  const heartbeatInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const isConnecting = useRef(false);
  // Prevents reconnect loop when user explicitly logs out or component unmounts
  const manualDisconnect = useRef(false);

  // Access store actions directly from store state — avoids hook subscriptions
  // that would cause re-renders and re-run effects
  const storeRef = useRef({
    updateAgent: useAgentsStore.getState().updateAgent,
    addTask: useTasksStore.getState().addTask,
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
      useTasksStore.subscribe((s) => {
        storeRef.current.addTask = s.addTask;
        storeRef.current.updateTask = s.updateTask;
      }),
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
  const handleMessage = useRef((raw: BackendMessage) => {
    const { updateAgent, addTask, updateTask, addEntry, updateMetrics } = storeRef.current;
    const payload = raw.payload ?? {};

    switch (raw.type) {
      // ── Agent events ──────────────────────────────────────────────────────
      case 'agent.status_changed':
      case 'agent.created':
      case 'agent.updated': {
        const agentId = payload.agent_id as string | undefined;
        if (agentId) {
          updateAgent(agentId, payload as Parameters<typeof updateAgent>[1]);
          const status = payload.status as string | undefined;
          const agentName = payload.name as string | undefined;
          if (status) {
            addEntry({
              id: `agent-${Date.now()}`,
              timestamp: raw.timestamp ?? new Date().toISOString(),
              type: 'agent_update',
              message: agentName ? `${agentName} → ${status}` : `Agent status → ${status}`,
              severity: status === 'ERROR' ? 'error' : status === 'WORKING' ? 'info' : 'info',
              agent_id: agentId,
            });
          }
        }
        break;
      }

      // ── Task events ───────────────────────────────────────────────────────
      case 'task.created': {
        const taskId = payload.task_id as string | undefined ?? payload.id as string | undefined;
        if (taskId) {
          // New task — add to store (updateTask silently ignores unknown IDs)
          addTask({ ...(payload as unknown as Task), id: taskId });
          addEntry({
            id: `task-${Date.now()}`,
            timestamp: raw.timestamp ?? new Date().toISOString(),
            type: 'task_update',
            message: `New task: ${(payload.title as string | undefined) ?? taskId}`,
            severity: 'info',
          });
        }
        break;
      }

      case 'task.updated':
      case 'task.assigned': {
        const taskId = payload.task_id as string | undefined ?? payload.id as string | undefined;
        if (taskId) {
          updateTask(taskId, payload as Parameters<typeof updateTask>[1]);
        }
        break;
      }

      case 'task.completed': {
        const taskId = payload.task_id as string | undefined ?? payload.id as string | undefined;
        if (taskId) {
          updateTask(taskId, { status: 'DONE' as TaskStatus });
          addEntry({
            id: `task-${Date.now()}`,
            timestamp: raw.timestamp ?? new Date().toISOString(),
            type: 'task_update',
            message: `Task completed: ${(payload.title as string | undefined) ?? taskId}`,
            severity: 'success',
          });
        }
        break;
      }

      case 'task.failed': {
        const taskId = payload.task_id as string | undefined ?? payload.id as string | undefined;
        if (taskId) {
          updateTask(taskId, { status: 'FAILED' as TaskStatus });
          addEntry({
            id: `task-${Date.now()}`,
            timestamp: raw.timestamp ?? new Date().toISOString(),
            type: 'task_update',
            message: `Task failed: ${(payload.title as string | undefined) ?? taskId}`,
            severity: 'error',
          });
        }
        break;
      }

      // ── Activity / system ─────────────────────────────────────────────────
      case 'activity.log': {
        const description = payload.description as string | undefined;
        if (description) {
          addEntry({
            id: `activity-${Date.now()}`,
            timestamp: raw.timestamp ?? new Date().toISOString(),
            type: payload.type as string ?? 'activity',
            message: description,
            severity: (payload.severity as 'info' | 'success' | 'warning' | 'error') ?? 'info',
            agent_id: payload.agent_id as string | undefined,
          });
        }
        break;
      }

      case 'system.notification': {
        addEntry({
          id: `sys-${Date.now()}`,
          timestamp: raw.timestamp ?? new Date().toISOString(),
          type: 'system',
          message: `${payload.title ?? 'System'}: ${payload.message ?? ''}`,
          severity: (payload.level as 'info' | 'success' | 'warning' | 'error') ?? 'info',
        });
        break;
      }

      case 'metrics.updated': {
        if (payload) {
          updateMetrics(payload as Parameters<typeof updateMetrics>[0]);
        }
        break;
      }

      // ── Misc ──────────────────────────────────────────────────────────────
      case 'connection.established':
        // Silently acknowledged
        break;

      default:
        // Legacy / unknown — ignore
        break;
    }
  });

  const stopHeartbeat = useRef(() => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
      heartbeatInterval.current = null;
    }
  });

  const startHeartbeat = useRef(() => {
    stopHeartbeat.current();
    heartbeatInterval.current = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        try { ws.current.send(JSON.stringify({ type: 'ping' })); } catch { /* ignore */ }
      }
    }, 30000); // ping every 30s to keep connection alive
  });

  const attemptReconnect = useRef(() => {
    if (manualDisconnect.current) return;
    if (reconnectAttempts.current >= RECONNECT_CONFIG.maxAttempts) {
      storeRef.current.addEntry({
        id: `ws-${Date.now()}`,
        timestamp: new Date().toISOString(),
        type: 'system',
        message: 'Real-time connection lost. Refresh the page to reconnect.',
        severity: 'error',
      });
      return;
    }

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
        startHeartbeat.current();
      };

      ws.current.onmessage = (event: MessageEvent) => {
        try {
          const data: BackendMessage = JSON.parse(event.data as string);
          handleMessage.current(data);
        } catch {
          // Ignore malformed messages
        }
      };

      ws.current.onclose = () => {
        stopHeartbeat.current();
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

      stopHeartbeat.current();

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
