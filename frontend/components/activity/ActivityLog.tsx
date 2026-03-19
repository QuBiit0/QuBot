'use client';
import React, { useRef, useEffect, useState } from 'react';
import { useAppStore, ActivityEvent } from '@/store/app.store';

const STATUS_CFG: Record<NonNullable<ActivityEvent['status']>, {
  dot: string;
  badge: string;
  label: string;
  icon: string;
}> = {
  done:        { dot: '#3fb950', badge: 'rgba(63,185,80,0.12)',   label: 'Done',     icon: '✓' },
  completed:   { dot: '#3fb950', badge: 'rgba(63,185,80,0.12)',   label: 'Done',     icon: '✓' },
  working:     { dot: '#f0a500', badge: 'rgba(240,165,0,0.12)',   label: 'Working',  icon: '⟳' },
  in_progress: { dot: '#f0a500', badge: 'rgba(240,165,0,0.12)',   label: 'Working',  icon: '⟳' },
  planning:    { dot: '#58a6ff', badge: 'rgba(88,166,255,0.12)',  label: 'Planning', icon: '◎' },
  pending:     { dot: '#8b949e', badge: 'rgba(139,148,158,0.12)', label: 'Queued',   icon: '·' },
  created:     { dot: '#a371f7', badge: 'rgba(163,113,247,0.12)', label: 'Created',  icon: '+' },
  assigned:    { dot: '#79c0ff', badge: 'rgba(121,192,255,0.12)', label: 'Assigned', icon: '→' },
  failed:      { dot: '#f85149', badge: 'rgba(248,81,73,0.12)',   label: 'Failed',   icon: '✕' },
  error:       { dot: '#f85149', badge: 'rgba(248,81,73,0.12)',   label: 'Error',    icon: '✕' },
  user:        { dot: '#58a6ff', badge: 'rgba(88,166,255,0.12)',  label: 'User',     icon: '↗' },
  idle:        { dot: '#3fb950', badge: 'rgba(63,185,80,0.08)',   label: 'Idle',     icon: '○' },
  offline:     { dot: '#484f58', badge: 'rgba(72,79,88,0.1)',     label: 'Offline',  icon: '—' },
};

const MOCK_EVENTS: ActivityEvent[] = [
  { id: '1', timestamp: '10:49:42', status: 'done',     agentName: 'Lead',    message: 'Task completed — response generated and delivered to user' },
  { id: '2', timestamp: '10:49:13', status: 'working',  agentName: 'Lead',    message: 'Processing request: "Analyze API structure"' },
  { id: '3', timestamp: '10:48:50', status: 'user',     agentName: 'System',  message: 'New user request received via chat' },
  { id: '4', timestamp: '10:44:23', status: 'done',     agentName: 'Backend', message: 'HEARTBEAT_OK — all services responding' },
  { id: '5', timestamp: '10:44:11', status: 'assigned', agentName: 'Lead',    message: 'Task #12 assigned to Backend agent' },
  { id: '6', timestamp: '10:43:50', status: 'created',  agentName: 'System',  message: 'Task #12 created: "Deploy API endpoint"' },
  { id: '7', timestamp: '10:43:19', status: 'working',  agentName: 'Backend', message: 'Initializing FastAPI route — POST /api/v1/agents/' },
  { id: '8', timestamp: '10:42:05', status: 'done',     agentName: 'QA',      message: 'Security scan passed — no critical vulnerabilities' },
  { id: '9', timestamp: '10:41:52', status: 'failed',   agentName: 'Scheduler', message: 'Redis queue timeout — retrying in 5s' },
];

const AGENT_COLORS: Record<string, string> = {
  Lead:      '#a371f7',
  Backend:   '#58a6ff',
  Frontend:  '#f778ba',
  QA:        '#3fb950',
  Scheduler: '#f0a500',
  Content:   '#ff7b72',
  System:    '#8b949e',
};

function getAgentColor(name: string): string {
  return AGENT_COLORS[name] ?? '#79c0ff';
}

function LogRow({ event, isNew }: { event: ActivityEvent; isNew?: boolean }) {
  const cfg = STATUS_CFG[event.status ?? 'working'] ?? STATUS_CFG['working']!;
  const agentColor = getAgentColor(event.agentName ?? event.agent_name ?? '');
  const [expanded, setExpanded] = useState(false);
  const isLong = event.message.length > 60;

  return (
    <div
      className="group flex items-start gap-2 py-1.5 px-3 border-b transition-colors"
      style={{
        borderColor: '#1a2035',
        background: isNew ? 'rgba(88,166,255,0.04)' : 'transparent',
        cursor: isLong ? 'pointer' : 'default',
      }}
      onClick={() => isLong && setExpanded(e => !e)}
    >
      {/* Status dot */}
      <div className="mt-1 flex-shrink-0 flex items-center justify-center w-4 h-4 rounded-full"
        style={{ background: cfg.badge }}>
        <span style={{ color: cfg.dot, fontSize: '9px', fontWeight: 700, lineHeight: 1 }}>
          {cfg.icon}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span style={{ color: '#484f58', fontSize: '9px', fontFamily: 'monospace', flexShrink: 0 }}>
            {event.timestamp}
          </span>
          {/* Status badge */}
          <span
            className="px-1 rounded text-[9px] font-semibold flex-shrink-0"
            style={{ background: cfg.badge, color: cfg.dot }}
          >
            {cfg.label}
          </span>
          {/* Agent badge */}
          <span
            className="px-1.5 rounded text-[9px] font-semibold flex-shrink-0"
            style={{ background: `${agentColor}18`, color: agentColor, border: `1px solid ${agentColor}30` }}
          >
            {event.agentName ?? event.agent_name}
          </span>
        </div>
        <p
          className="text-[10.5px] leading-[1.4]"
          style={{
            color: '#8b949e',
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitBoxOrient: 'vertical',
            WebkitLineClamp: expanded ? 10 : 1,
          } as React.CSSProperties}
        >
          {event.message}
        </p>
      </div>

      {/* Expand chevron */}
      {isLong && (
        <span className="flex-shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ color: '#484f58', fontSize: '10px' }}>
          {expanded ? '▲' : '▼'}
        </span>
      )}
    </div>
  );
}

export default function ActivityLog() {
  const { activityLog, isConnected } = useAppStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [newEventIds, setNewEventIds] = useState<Set<string>>(new Set());
  const prevLenRef = useRef(activityLog.length);

  useEffect(() => {
    if (activityLog.length > prevLenRef.current && activityLog.length > 0) {
      const newId = activityLog[0]!.id;
      setNewEventIds(s => new Set([...s, newId]));
      setTimeout(() => setNewEventIds(s => { const n = new Set(s); n.delete(newId); return n; }), 2000);
      if (scrollRef.current) scrollRef.current.scrollTop = 0;
    }
    prevLenRef.current = activityLog.length;
  }, [activityLog.length]);

  const events = activityLog.length > 0 ? activityLog : MOCK_EVENTS;
  const totalCount = activityLog.length > 0 ? activityLog.length : '—';

  const statusCounts = events.reduce<Record<string, number>>((acc, e) => {
    const key = e.status ?? 'working';
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full" style={{ background: 'transparent' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 flex-shrink-0 border-b" style={{ borderColor: '#1a2035' }}>
        <div className="flex items-center gap-2">
          <span className="text-[12px] font-semibold" style={{ color: '#e6edf3' }}>Activity Log</span>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold border"
            style={isConnected
              ? { background: 'rgba(63,185,80,0.1)', borderColor: 'rgba(63,185,80,0.3)', color: '#3fb950' }
              : { background: 'rgba(72,79,88,0.15)', borderColor: '#30363d', color: '#484f58' }}>
            <span className={`w-1 h-1 rounded-full flex-shrink-0 ${isConnected ? 'animate-pulse' : ''}`}
              style={{ background: isConnected ? '#3fb950' : '#484f58' }} />
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Mini status breakdown */}
          {statusCounts.done && (
            <span style={{ fontSize: '10px', color: STATUS_CFG['done']!.dot }}>
              {statusCounts.done} done
            </span>
          )}
          <span style={{ color: '#484f58', fontSize: '11px', fontFamily: 'monospace' }}>
            {typeof totalCount === 'number' ? totalCount.toLocaleString() : totalCount} events
          </span>
        </div>
      </div>

      {/* Events */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {events.map((event) => (
          <LogRow key={event.id} event={event} isNew={newEventIds.has(event.id)} />
        ))}
        {events.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-2 py-12">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm"
              style={{ background: '#161b22', border: '1px solid #21262d', color: '#484f58' }}>
              ⌛
            </div>
            <span style={{ color: '#484f58', fontSize: '12px' }}>Waiting for events…</span>
          </div>
        )}
      </div>
    </div>
  );
}
