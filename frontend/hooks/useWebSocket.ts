'use client';

import { useEffect, useRef, useCallback } from 'react';
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
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const isConnecting = useRef(false);
  
  const updateAgent = useAgentsStore((s) => s.updateAgent);
  const updateTask = useTasksStore((s) => s.updateTask);
  const setConnected = useAppStore((s) => s.setConnected);
  const setConnectionState = useAppStore((s) => s.setConnectionState);
  const updateMetrics = useAppStore((s) => s.updateMetrics);
  const addActivityEntry = useActivityStore((s) => s.addEntry);

  const connect = useCallback(() => {
    if (isConnecting.current || ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    isConnecting.current = true;
    setConnectionState('connecting');

    try {
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        console.log('[WebSocket] Connected');
        reconnectAttempts.current = 0;
        setConnected(true);
        setConnectionState('connected');
        isConnecting.current = false;
      };

      ws.current.onmessage = (event: MessageEvent) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          handleMessage(data);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.current.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setConnected(false);
        setConnectionState('disconnected');
        isConnecting.current = false;
        attemptReconnect();
      };

      ws.current.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        setConnectionState('error');
        isConnecting.current = false;
      };
    } catch (error) {
      console.error('[WebSocket] Failed to connect:', error);
      setConnectionState('error');
      isConnecting.current = false;
      attemptReconnect();
    }
  }, [setConnected, setConnectionState]);

  const attemptReconnect = useCallback(() => {
    if (reconnectAttempts.current >= RECONNECT_CONFIG.maxAttempts) {
      console.log('[WebSocket] Max reconnect attempts reached');
      return;
    }

    const delay = Math.min(
      RECONNECT_CONFIG.initialDelay * Math.pow(RECONNECT_CONFIG.multiplier, reconnectAttempts.current),
      RECONNECT_CONFIG.maxDelay
    );
    
    // Add jitter
    const jitteredDelay = delay * (1 + (Math.random() * 2 - 1) * RECONNECT_CONFIG.jitter);

    console.log(`[WebSocket] Reconnecting in ${Math.round(jitteredDelay)}ms (attempt ${reconnectAttempts.current + 1})`);

    reconnectTimeout.current = setTimeout(() => {
      reconnectAttempts.current++;
      connect();
    }, jitteredDelay);
  }, [connect]);

  const handleMessage = useCallback((data: WebSocketMessage) => {
    switch (data.type) {
      case 'AGENT_UPDATE':
        if (data.id && data.payload) {
          updateAgent(data.id, data.payload);
          
          // Add activity entry for significant state changes
          const payload = data.payload as { state?: string; name?: string };
          if (payload.state) {
            addActivityEntry({
              id: `agent-${Date.now()}`,
              timestamp: new Date().toISOString(),
              type: 'agent_update',
              message: `${payload.name || 'Agent'} is now ${payload.state}`,
              severity: 'info',
              agent_id: data.id,
              agent_name: payload.name,
            });
          }
        }
        break;

      case 'TASK_UPDATE':
        if (data.id && data.payload) {
          updateTask(data.id, data.payload);
          
          const payload = data.payload as { status?: TaskStatus; title?: string };
          if (payload.status) {
            addActivityEntry({
              id: `task-${Date.now()}`,
              timestamp: new Date().toISOString(),
              type: 'task_update',
              message: `Task "${payload.title}" moved to ${payload.status}`,
              severity: 'success',
            });
          }
        }
        break;

      case 'ACTIVITY_EVENT':
        if (data.payload) {
          const event = data.payload as {
            message: string;
            severity?: 'info' | 'success' | 'warning' | 'error';
            agent_id?: string | number;
            agent_name?: string;
          };
          addActivityEntry({
            id: `activity-${Date.now()}`,
            timestamp: new Date().toISOString(),
            type: data.type,
            message: event.message,
            severity: event.severity || 'info',
            agent_id: event.agent_id,
            agent_name: event.agent_name,
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

      default:
        console.log('[WebSocket] Unknown message type:', data.type);
    }
  }, [updateAgent, updateTask, addActivityEntry, updateMetrics]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    
    setConnected(false);
    setConnectionState('disconnected');
  }, [setConnected, setConnectionState]);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);
}
