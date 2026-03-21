'use client';
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useAgentsStore } from '@/store/agents.store';
import { Agent as StoreAgent } from '@/types';
import { AgentDesk } from './AgentDesk';

// ============================================================================
// CONFIGURACIÓN DEL SISTEMA
// ============================================================================

const OFFICE_CONFIG = {
  MAX_AGENTS_PER_OFFICE: 8,
  MAX_OFFICES: 10,
  SPACING_Y: 185,
  SPACING_X: 200,
  GRID_SIZE: 40,
};

type TimeOfDay = 'day' | 'night' | 'sunset';

function getTimeOfDay(): TimeOfDay {
  const hour = new Date().getHours();
  if (hour >= 6 && hour < 17) return 'day';
  if (hour >= 17 && hour < 20) return 'sunset';
  return 'night';
}

// Premium design tokens per theme
const PREMIUM_THEMES = {
  day: {
    isDark: false,
    bg0: '#eef2f7', bg1: '#e2e8f2',
    wall0: '#dde4ef', wall1: '#ccd3e0',
    floor0: '#eaf0f8', floor1: '#dde5f0',
    tileStroke: '#c8d4e4',
    accent: '#3b82f6', accentGlow: 'rgba(59,130,246,0.3)',
    secondary: '#6366f1',
    ceilLight0: '#93c5fd', ceilLight1: '#bfdbfe',
    borderDefault: '#c8d4e4', borderAccent: 'rgba(59,130,246,0.25)',
    textPrimary: '#1e293b', textMuted: '#64748b',
    glass: 'rgba(241,245,249,0.88)', glassBorder: 'rgba(100,116,139,0.3)',
    junctionNeon: '#60a5fa',
    windowSky: ['#bfdbfe', '#e0f2fe'],
    serverGlow: '#22c55e',
  },
  sunset: {
    isDark: true,
    bg0: '#0f0a1a', bg1: '#080612',
    wall0: '#110d1e', wall1: '#0b0913',
    floor0: '#0d0a17', floor1: '#070510',
    tileStroke: '#18122a',
    accent: '#f59e0b', accentGlow: 'rgba(245,158,11,0.35)',
    secondary: '#ef4444',
    ceilLight0: '#f59e0b', ceilLight1: '#fcd34d',
    borderDefault: '#2d1f3d', borderAccent: 'rgba(245,158,11,0.25)',
    textPrimary: '#f7fafc', textMuted: '#94a3b8',
    glass: 'rgba(8,4,16,0.88)', glassBorder: 'rgba(245,158,11,0.25)',
    junctionNeon: '#f59e0b',
    windowSky: ['#020208', '#160510', '#4a0c02'],
    serverGlow: '#6366f1',
  },
  night: {
    isDark: true,
    bg0: '#060912', bg1: '#030608',
    wall0: '#080d17', wall1: '#04080f',
    floor0: '#060912', floor1: '#040710',
    tileStroke: '#0d1628',
    accent: '#6366f1', accentGlow: 'rgba(99,102,241,0.35)',
    secondary: '#8b5cf6',
    ceilLight0: '#6366f1', ceilLight1: '#a78bfa',
    borderDefault: '#1a2535', borderAccent: 'rgba(99,102,241,0.22)',
    textPrimary: '#e2e8f0', textMuted: '#475569',
    glass: 'rgba(6,9,18,0.88)', glassBorder: 'rgba(99,102,241,0.22)',
    junctionNeon: '#6366f1',
    windowSky: ['#020408', '#04080f', '#060b1a'],
    serverGlow: '#10b981',
  },
};

// ============================================================================
// HOOK PARA POSICIONAMIENTO (unchanged)
// ============================================================================

interface OfficePositions {
  [officeIndex: number]: { [agentId: string]: { x: number; y: number } };
}

function useAgentPositioning(officeIndex: number) {
  const [customPositions, setCustomPositions] = useState<OfficePositions>({});
  const [isEditMode, setIsEditMode] = useState(false);
  const [draggedAgent, setDraggedAgent] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const saved = localStorage.getItem('qubot_agent_positions');
    if (saved) {
      try { setCustomPositions(JSON.parse(saved)); } catch { /* ignore */ }
    }
  }, []);

  const startDrag = useCallback((agentId: string, mouseX: number, mouseY: number, agentX: number, agentY: number) => {
    setDraggedAgent(agentId);
    setDragOffset({ x: mouseX - agentX, y: mouseY - agentY });
  }, []);

  const drag = useCallback((mouseX: number, mouseY: number) => {
    if (!draggedAgent || !isEditMode) return;
    setCustomPositions(prev => ({
      ...prev,
      [officeIndex]: {
        ...prev[officeIndex],
        [draggedAgent]: { x: mouseX - dragOffset.x, y: mouseY - dragOffset.y },
      },
    }));
  }, [draggedAgent, dragOffset, isEditMode, officeIndex]);

  const endDrag = useCallback(() => {
    if (!draggedAgent) return;
    setCustomPositions(prev => {
      const currentPos = prev[officeIndex]?.[draggedAgent];
      if (!currentPos) return prev;
      const snappedX = Math.round(currentPos.x / OFFICE_CONFIG.GRID_SIZE) * OFFICE_CONFIG.GRID_SIZE;
      const snappedY = Math.round(currentPos.y / OFFICE_CONFIG.GRID_SIZE) * OFFICE_CONFIG.GRID_SIZE;
      const updated = {
        ...prev,
        [officeIndex]: { ...prev[officeIndex], [draggedAgent]: { x: snappedX, y: snappedY } },
      };
      localStorage.setItem('qubot_agent_positions', JSON.stringify(updated));
      return updated;
    });
    setDraggedAgent(null);
  }, [draggedAgent, officeIndex]);

  const resetPositions = useCallback(() => {
    const updated = { ...customPositions };
    delete updated[officeIndex];
    setCustomPositions(updated);
    localStorage.setItem('qubot_agent_positions', JSON.stringify(updated));
  }, [customPositions, officeIndex]);

  const getPosition = useCallback((agentId: string, defaultX: number, defaultY: number) => {
    const custom = customPositions[officeIndex]?.[agentId];
    return custom || { x: defaultX, y: defaultY };
  }, [customPositions, officeIndex]);

  return {
    isEditMode, setIsEditMode, draggedAgent,
    startDrag, drag, endDrag, resetPositions, getPosition,
    hasCustomPositions: Object.keys(customPositions[officeIndex] || {}).length > 0,
  };
}

// ============================================================================
// FUNCIONES UTILITARIAS (unchanged)
// ============================================================================

function classifyAgent(agent: StoreAgent): string {
  const domain = (agent.domain || agent.role || '').toLowerCase();
  const name = (agent.name || '').toLowerCase();
  if (agent.name?.toLowerCase().includes('lead')) return 'lead';
  if (name.includes('front') || name.includes('back') || name.includes('database')) return 'tech';
  if (name.includes('devops') || name.includes('security')) return 'ops';
  if (name.includes('ml') || name.includes('data')) return 'data';
  if (name.includes('content')) return 'creative';
  if (domain.includes('tech') || domain.includes('dev')) return 'tech';
  if (domain.includes('ops') || domain.includes('security')) return 'ops';
  if (domain.includes('data') || domain.includes('ml')) return 'data';
  return 'tech';
}

function distributeAgentsIntoOffices(agents: StoreAgent[]): StoreAgent[][] {
  const offices: StoreAgent[][] = [];
  const lead = agents.find(a => a.name?.toLowerCase().includes('lead'));
  const others = agents.filter(a => a.id !== lead?.id);
  const byDomain: Record<string, StoreAgent[]> = {};
  others.forEach(agent => {
    const domain = classifyAgent(agent);
    if (!byDomain[domain]) byDomain[domain] = [];
    byDomain[domain].push(agent);
  });
  const office1: StoreAgent[] = [];
  if (lead) office1.push(lead);
  const domains = Object.keys(byDomain);
  for (const domain of domains) {
    const da = byDomain[domain];
    if (da) while (da.length > 0 && office1.length < OFFICE_CONFIG.MAX_AGENTS_PER_OFFICE) office1.push(da.shift()!);
  }
  if (office1.length > 0) offices.push(office1);
  for (const domain of domains) {
    const da = byDomain[domain];
    if (!da) continue;
    while (da.length > 0) {
      const office: StoreAgent[] = [];
      while (da.length > 0 && office.length < OFFICE_CONFIG.MAX_AGENTS_PER_OFFICE) office.push(da.shift()!);
      offices.push(office);
    }
  }
  return offices.slice(0, OFFICE_CONFIG.MAX_OFFICES);
}

function generatePositionsForOffice(agents: StoreAgent[], width: number, wallH: number) {
  const positions: Array<{ x: number; y: number; agent: StoreAgent }> = [];
  const centerX = width / 2;
  const startY = wallH + 90;
  const lead = agents.find(a => a.name?.toLowerCase().includes('lead'));
  const others = agents.filter(a => a.id !== lead?.id);
  if (lead) positions.push({ x: centerX, y: startY, agent: lead });
  const spacingX = OFFICE_CONFIG.SPACING_X;
  const spacingY = OFFICE_CONFIG.SPACING_Y;
  const secondRowY = startY + spacingY + 40;
  if (others.length <= 3) {
    const startX = centerX - ((others.length - 1) * spacingX) / 2;
    others.forEach((agent, i) => positions.push({ x: startX + i * spacingX, y: secondRowY, agent }));
  } else if (others.length <= 6) {
    const firstRow = Math.min(3, others.length);
    const startX1 = centerX - ((firstRow - 1) * spacingX) / 2;
    for (let i = 0; i < firstRow; i++) positions.push({ x: startX1 + i * spacingX, y: secondRowY, agent: others[i]! });
    const thirdRowY = secondRowY + spacingY;
    const secondRowAgents = others.slice(firstRow);
    const startX2 = centerX - ((secondRowAgents.length - 1) * spacingX) / 2;
    secondRowAgents.forEach((agent, i) => positions.push({ x: startX2 + i * spacingX, y: thirdRowY, agent }));
  } else {
    const firstRow = 3;
    const startX1 = centerX - ((firstRow - 1) * spacingX) / 2;
    for (let i = 0; i < firstRow; i++) positions.push({ x: startX1 + i * spacingX, y: secondRowY, agent: others[i]! });
    const thirdRowY = secondRowY + spacingY;
    const secondRowAgents = others.slice(firstRow);
    const startX2 = centerX - ((4 - 1) * spacingX) / 2;
    secondRowAgents.forEach((agent, i) => positions.push({ x: startX2 + i * spacingX, y: thirdRowY, agent }));
  }
  return positions;
}

// ============================================================================
// PREMIUM VISUAL COMPONENTS
// ============================================================================

type ThemeTokens = typeof PREMIUM_THEMES['night'];

function PremiumFloor({ width, height, t, showGrid }: { width: number; height: number; t: ThemeTokens; showGrid?: boolean }) {
  return (
    <g>
      <defs>
        <linearGradient id="floorBase" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.floor0} />
          <stop offset="100%" stopColor={t.floor1} />
        </linearGradient>
        <pattern id="tilePat" width="70" height="70" patternUnits="userSpaceOnUse">
          <rect width="70" height="70" fill="none" />
          <rect width="70" height="70" fill="none" stroke={t.tileStroke} strokeWidth="0.8" />
          <rect x="3" y="3" width="64" height="64" fill="none" stroke={t.tileStroke} strokeWidth="0.25" opacity="0.5" />
        </pattern>
        <radialGradient id="floorAmb1" cx="30%" cy="55%" r="40%">
          <stop offset="0%" stopColor={t.accent} stopOpacity={t.isDark ? 0.05 : 0.04} />
          <stop offset="100%" stopColor="transparent" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="floorAmb2" cx="70%" cy="60%" r="35%">
          <stop offset="0%" stopColor={t.secondary} stopOpacity={t.isDark ? 0.04 : 0.03} />
          <stop offset="100%" stopColor="transparent" stopOpacity="0" />
        </radialGradient>
        <pattern id="editGrid" width={OFFICE_CONFIG.GRID_SIZE} height={OFFICE_CONFIG.GRID_SIZE} patternUnits="userSpaceOnUse">
          <rect width={OFFICE_CONFIG.GRID_SIZE} height={OFFICE_CONFIG.GRID_SIZE} fill="transparent" />
          <circle cx={2} cy={2} r={1.2} fill={t.accent} opacity="0.5" />
        </pattern>
      </defs>
      <rect width={width} height={height} fill="url(#floorBase)" />
      <rect width={width} height={height} fill="url(#tilePat)" />
      <rect width={width} height={height} fill="url(#floorAmb1)" />
      <rect width={width} height={height} fill="url(#floorAmb2)" />
      {showGrid && <rect width={width} height={height} fill="url(#editGrid)" opacity="0.5" />}
    </g>
  );
}

function PremiumBackWall({ width, height, t }: { width: number; height: number; t: ThemeTokens }) {
  const wallH = height * 0.18;
  return (
    <g>
      <defs>
        <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.wall0} />
          <stop offset="100%" stopColor={t.wall1} />
        </linearGradient>
        <linearGradient id="ceilLightGradL" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.ceilLight0} stopOpacity="0.5" />
          <stop offset="100%" stopColor={t.ceilLight0} stopOpacity="0" />
        </linearGradient>
        <linearGradient id="ceilLightGradR" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.ceilLight1} stopOpacity="0.5" />
          <stop offset="100%" stopColor={t.ceilLight1} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Main wall */}
      <rect x={0} y={0} width={width} height={wallH} fill="url(#wallGrad)" />

      {/* Ceiling light strips */}
      <rect x={width * 0.14} y={0} width={width * 0.24} height={4} rx={2}
        fill={t.ceilLight0} opacity={t.isDark ? 0.9 : 0.6} />
      <rect x={width * 0.14} y={4} width={width * 0.24} height={40}
        fill="url(#ceilLightGradL)" opacity="0.12" />

      <rect x={width * 0.62} y={0} width={width * 0.24} height={4} rx={2}
        fill={t.ceilLight1} opacity={t.isDark ? 0.9 : 0.6} />
      <rect x={width * 0.62} y={4} width={width * 0.24} height={40}
        fill="url(#ceilLightGradR)" opacity="0.12" />

      {/* Wall/floor junction panel */}
      <rect x={0} y={wallH - 5} width={width} height={5}
        fill={t.isDark ? '#0c1422' : '#b8c4d8'} />
      {/* Neon trim line */}
      <rect x={0} y={wallH - 5} width={width} height={1.5}
        fill={t.junctionNeon} opacity={t.isDark ? 0.5 : 0.35} />
    </g>
  );
}

function HolographicDisplay({ width, wallH, t, officeNumber }: { width: number; wallH: number; t: ThemeTokens; officeNumber: number }) {
  return (
    <g transform={`translate(${width / 2}, ${wallH * 0.5})`}>
      <defs>
        <linearGradient id="dispBg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.isDark ? '#0d1117' : '#f8fafc'} />
          <stop offset="100%" stopColor={t.isDark ? '#06090e' : '#f1f5f9'} />
        </linearGradient>
        <linearGradient id="dispBorder" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={t.accent} />
          <stop offset="50%" stopColor={t.secondary} />
          <stop offset="100%" stopColor={t.accent} />
        </linearGradient>
        <filter id="dispGlow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Outer ambient glow */}
      {t.isDark && (
        <rect x={-128} y={-48} width={256} height={96} rx={10}
          fill={t.accent} opacity="0.04" filter="url(#dispGlow)" />
      )}

      {/* Main panel */}
      <rect x={-120} y={-42} width={240} height={84} rx={7}
        fill="url(#dispBg)" stroke="url(#dispBorder)" strokeWidth="1.5" />

      {/* Inner panel inset */}
      <rect x={-116} y={-38} width={232} height={76} rx={5}
        fill="none" stroke={t.isDark ? t.accent + '18' : t.accent + '22'} strokeWidth="0.8" />

      {/* Corner brackets */}
      <path d={`M-110,-30 L-110,-38 L-102,-38`} fill="none" stroke={t.accent} strokeWidth="1.5" opacity="0.85" />
      <path d={`M110,-30 L110,-38 L102,-38`} fill="none" stroke={t.accent} strokeWidth="1.5" opacity="0.85" />
      <path d={`M-110,30 L-110,38 L-102,38`} fill="none" stroke={t.secondary} strokeWidth="1.5" opacity="0.85" />
      <path d={`M110,30 L110,38 L102,38`} fill="none" stroke={t.secondary} strokeWidth="1.5" opacity="0.85" />

      {/* Scan line animation */}
      {t.isDark && (
        <rect x={-116} y={-38} width={232} height={2} rx={1}
          fill={t.accent} opacity="0.25">
          <animate attributeName="y" values="-38;36;-38" dur="5s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.25;0;0.25" dur="5s" repeatCount="indefinite" />
        </rect>
      )}

      {/* QUBOT logotype */}
      <text x={0} y={2} textAnchor="middle" fontSize={26} fontWeight={800}
        fill={t.isDark ? '#e2e8f0' : '#1e293b'}
        style={{ fontFamily: 'system-ui, -apple-system, sans-serif', letterSpacing: '5px' }}>
        QUBOT
      </text>

      {/* Accent underline */}
      <rect x={-35} y={7} width={70} height={1.5} rx={1}
        fill={t.accent} opacity="0.75" />

      {/* Subtitle */}
      <text x={0} y={24} textAnchor="middle" fontSize={8.5}
        fill={t.accent}
        style={{ fontFamily: 'system-ui, sans-serif', letterSpacing: '7px' }}>
        AI OFFICE{officeNumber > 1 ? ` #${officeNumber}` : ''}
      </text>

      {/* Status indicator dot */}
      <circle cx={-92} cy={-24} r={3.5} fill="#10b981" opacity="0.9">
        <animate attributeName="opacity" values="0.9;0.3;0.9" dur="2s" repeatCount="indefinite" />
      </circle>
      <text x={-85} y={-20} fontSize={7} fill={t.textMuted}
        style={{ fontFamily: 'monospace' }}>SYS.ONLINE</text>
    </g>
  );
}

function PremiumWindows({ width, wallH, t }: { width: number; wallH: number; t: ThemeTokens }) {
  const windowW = 92;
  const windowH = wallH * 0.62;

  // Deterministic city buildings
  const buildings = [
    { x: 0,  w: 16, h: 58 },
    { x: 19, w: 11, h: 42 },
    { x: 33, w: 22, h: 68 },
    { x: 58, w: 9,  h: 32 },
    { x: 70, w: 15, h: 52 },
  ];

  const renderWindow = (offsetX: number) => {
    const gradId = `winSky${Math.round(offsetX)}`;
    const clipId = `winClip${Math.round(offsetX)}`;
    return (
      <g key={offsetX} transform={`translate(${offsetX}, ${wallH * 0.17})`}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            {t.windowSky.map((color, i) => (
              <stop key={i}
                offset={`${(i / (t.windowSky.length - 1)) * 100}%`}
                stopColor={color} />
            ))}
          </linearGradient>
          <clipPath id={clipId}>
            <rect width={windowW} height={windowH} rx={4} />
          </clipPath>
        </defs>

        {/* Sky background */}
        <rect width={windowW} height={windowH} rx={4} fill={`url(#${gradId})`} />

        <g clipPath={`url(#${clipId})`}>
          {/* Stars (dark only) */}
          {t.isDark && [
            { x: 8, y: 6 }, { x: 22, y: 4 }, { x: 45, y: 10 },
            { x: 68, y: 5 }, { x: 82, y: 14 }, { x: 36, y: 3 }, { x: 58, y: 8 },
          ].map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={0.9} fill="#ffffff" opacity="0.55">
              <animate attributeName="opacity" values="0.55;0.15;0.55"
                dur={`${1.8 + i * 0.4}s`} repeatCount="indefinite" />
            </circle>
          ))}

          {/* City silhouette */}
          {buildings.map((b, i) => (
            <g key={i}>
              <rect x={b.x} y={windowH - b.h} width={b.w} height={b.h}
                fill={t.isDark ? '#0a1628' : '#94a3b8'} />
              {/* Building windows at night */}
              {t.isDark && Array.from({ length: Math.floor(b.h / 9) }).map((_, row) =>
                Array.from({ length: Math.floor(b.w / 5) }).map((_, col) => {
                  const lit = (i * 11 + row * 5 + col * 7) % 3 !== 0;
                  return lit ? (
                    <rect key={`${row}-${col}`}
                      x={b.x + 2 + col * 5} y={windowH - b.h + 5 + row * 9}
                      width={2.5} height={3.5}
                      fill={[(i * 3 + row) % 2 === 0 ? '#fde68a' : '#bfdbfe'][0]}
                      opacity="0.65" />
                  ) : null;
                })
              )}
            </g>
          ))}

          {/* Moon (night) */}
          {t.isDark && (
            <circle cx={windowW * 0.78} cy={windowH * 0.22} r={7} fill="#fef3c7" opacity="0.88">
              <animate attributeName="r" values="7;7.5;7" dur="4s" repeatCount="indefinite" />
            </circle>
          )}

          {/* Sun (day) */}
          {!t.isDark && (
            <circle cx={windowW * 0.72} cy={windowH * 0.28} r={10} fill="#fde68a" opacity="0.9">
              <animate attributeName="r" values="10;11;10" dur="3s" repeatCount="indefinite" />
            </circle>
          )}
        </g>

        {/* Window frame */}
        <rect width={windowW} height={windowH} rx={4} fill="none"
          stroke={t.isDark ? '#1e3a6e' : '#94a3b8'} strokeWidth="2" />
        {/* Dividers */}
        <line x1={windowW / 2} y1={0} x2={windowW / 2} y2={windowH}
          stroke={t.isDark ? '#1e3a6e' : '#94a3b8'} strokeWidth="1.5" />
        <line x1={0} y1={windowH / 2} x2={windowW} y2={windowH / 2}
          stroke={t.isDark ? '#1e3a6e' : '#94a3b8'} strokeWidth="1.5" />
        {/* Glass reflection sheen */}
        <rect x={4} y={4} width={windowW * 0.3} height={windowH - 8} rx={2}
          fill="white" opacity="0.025" />
      </g>
    );
  };

  return (
    <g>
      {renderWindow(28)}
      {renderWindow(width - 120)}
    </g>
  );
}

function PremiumClock({ x, y, t }: { x: number; y: number; t: ThemeTokens }) {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const hours = time.getHours();
  const minutes = time.getMinutes();
  const seconds = time.getSeconds();
  const hourAngle   = ((hours % 12) * 30) + (minutes * 0.5) - 90;
  const minuteAngle = (minutes * 6) - 90;
  const secondAngle = (seconds * 6) - 90;

  return (
    <g transform={`translate(${x}, ${y})`}>
      <defs>
        <linearGradient id="clockFace" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.isDark ? '#0d1117' : '#f8fafc'} />
          <stop offset="100%" stopColor={t.isDark ? '#060912' : '#f1f5f9'} />
        </linearGradient>
      </defs>
      {/* Outer accent ring */}
      <circle cx={0} cy={0} r={25} fill="none"
        stroke={t.accent} strokeWidth="1" opacity="0.35" />
      {/* Face */}
      <circle cx={0} cy={0} r={22} fill="url(#clockFace)"
        stroke={t.borderDefault} strokeWidth="1.5" />
      {/* Hour markers */}
      {[...Array(12)].map((_, i) => {
        const isMain = i % 3 === 0;
        return (
          <line key={i} x1={0} y1={isMain ? -14 : -17} x2={0} y2={-20}
            stroke={isMain ? t.accent : (t.isDark ? '#1e2d40' : '#94a3b8')}
            strokeWidth={isMain ? 2 : 1}
            transform={`rotate(${i * 30})`} />
        );
      })}
      {/* Hour hand */}
      <line x1={0} y1={2.5} x2={0} y2={-10}
        stroke={t.isDark ? '#e2e8f0' : '#1e293b'}
        strokeWidth="2.5" strokeLinecap="round"
        transform={`rotate(${hourAngle})`} />
      {/* Minute hand */}
      <line x1={0} y1={3} x2={0} y2={-15}
        stroke={t.isDark ? '#94a3b8' : '#475569'}
        strokeWidth="1.5" strokeLinecap="round"
        transform={`rotate(${minuteAngle})`} />
      {/* Second hand */}
      <line x1={0} y1={3.5} x2={0} y2={-17}
        stroke={t.accent}
        strokeWidth="1" strokeLinecap="round"
        transform={`rotate(${secondAngle})`} />
      {/* Center hub */}
      <circle cx={0} cy={0} r={3}
        fill={t.isDark ? '#0d1117' : '#f1f5f9'}
        stroke={t.accent} strokeWidth="1.5" />
      <circle cx={0} cy={0} r={1.5} fill={t.accent} />
    </g>
  );
}

function PremiumBookshelf({ x, y, t }: { x: number; y: number; t: ThemeTokens }) {
  const bookColors = ['#6366f1', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#14b8a6'];
  return (
    <g transform={`translate(${x}, ${y})`}>
      <rect x={0} y={0} width={52} height={88} rx={3}
        fill={t.isDark ? '#0c1018' : '#f1f5f9'}
        stroke={t.borderDefault} strokeWidth="1.5" />
      {/* Shelves */}
      <rect x={3} y={27} width={46} height={2} fill={t.isDark ? '#1a2535' : '#94a3b8'} />
      <rect x={3} y={56} width={46} height={2} fill={t.isDark ? '#1a2535' : '#94a3b8'} />
      {/* Books - deterministic heights */}
      {[0, 1, 2].map(shelf => (
        <g key={shelf}>
          {Array.from({ length: 5 }).map((_, i) => {
            const heights = [18, 21, 16, 22, 19];
            const h = heights[(shelf * 5 + i) % heights.length]!;
            const color = bookColors[(shelf * 5 + i) % bookColors.length]!;
            return (
              <rect key={i}
                x={5 + i * 9} y={26 + shelf * 29 - h}
                width={7} height={h} rx={1}
                fill={color} opacity={t.isDark ? 0.72 : 0.6} />
            );
          })}
        </g>
      ))}
      <ellipse cx={26} cy={90} rx={24} ry={3} fill="#000" opacity="0.12" />
    </g>
  );
}

function PremiumPlant({ x, y, t, type = 'tall' }: { x: number; y: number; t: ThemeTokens; type?: 'tall' | 'bush' }) {
  const pot = t.isDark ? '#0c1018' : '#e2e8f0';
  const potStroke = t.isDark ? '#1a2535' : '#94a3b8';

  if (type === 'bush') {
    return (
      <g transform={`translate(${x}, ${y})`}>
        <rect x={-15} y={44} width={30} height={18} rx={4} fill={pot} stroke={potStroke} strokeWidth="1" />
        <rect x={-13} y={40} width={26} height={6} rx={2} fill={t.isDark ? '#111f30' : '#cbd5e1'} />
        <circle cx={-8} cy={28} r={14} fill="#065f46" opacity="0.92" />
        <circle cx={8}  cy={28} r={14} fill="#047857" opacity="0.92" />
        <circle cx={0}  cy={16} r={16} fill="#059669" opacity="0.88" />
        <circle cx={-4} cy={24} r={10} fill="#10b981" opacity="0.6" />
        <circle cx={7}  cy={21} r={9}  fill="#10b981" opacity="0.5" />
      </g>
    );
  }

  return (
    <g transform={`translate(${x}, ${y})`}>
      <rect x={-12} y={52} width={24} height={18} rx={4} fill={pot} stroke={potStroke} strokeWidth="1" />
      <rect x={-10} y={48} width={20} height={6} rx={2} fill={t.isDark ? '#111f30' : '#cbd5e1'} />
      <path d="M0 52 C-2 38 -9 26 -14 10" fill="none" stroke="#065f46" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M0 52 C2 32 11 22 9 5"    fill="none" stroke="#047857" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M0 52 C0 36 0 20 0 2"     fill="none" stroke="#059669" strokeWidth="2.5" strokeLinecap="round" />
      <ellipse cx={-11} cy={22} rx={8} ry={15} fill="#10b981" opacity="0.78" transform="rotate(-22,-11,22)" />
      <ellipse cx={11}  cy={16} rx={8} ry={15} fill="#059669" opacity="0.78" transform="rotate(22,11,16)" />
      <ellipse cx={0}   cy={4}  rx={6} ry={11} fill="#34d399" opacity="0.68" />
    </g>
  );
}

function PremiumServerRack({ x, y, t }: { x: number; y: number; t: ThemeTokens }) {
  return (
    <g transform={`translate(${x}, ${y})`}>
      <defs>
        <linearGradient id="rackBody" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={t.isDark ? '#060912' : '#e2e8f0'} />
          <stop offset="100%" stopColor={t.isDark ? '#0c1018' : '#f1f5f9'} />
        </linearGradient>
      </defs>
      {/* Body */}
      <rect width={38} height={112} rx={4} fill="url(#rackBody)"
        stroke={t.borderDefault} strokeWidth="1.5" />
      {/* Accent border glow */}
      <rect width={38} height={112} rx={4} fill="none"
        stroke={t.accent} strokeWidth="0.5" opacity="0.3" />
      {/* Units */}
      {Array.from({ length: 5 }).map((_, i) => (
        <g key={i} transform={`translate(3, ${8 + i * 21})`}>
          <rect width={32} height={17} rx={2}
            fill={t.isDark ? '#060912' : '#e8eef8'}
            stroke={t.isDark ? '#1a2535' : '#cbd5e1'} strokeWidth="0.5" />
          {/* LED */}
          <circle cx={27} cy={8.5} r={2.5}
            fill={i % 2 === 0 ? t.serverGlow : t.accent}>
            <animate attributeName="opacity" values="1;0.25;1"
              dur={`${1.3 + i * 0.25}s`} repeatCount="indefinite" />
          </circle>
          {/* Drive slots */}
          {[0, 1, 2].map(j => (
            <rect key={j} x={4 + j * 6} y={5.5} width={4} height={6} rx={1}
              fill={t.isDark ? '#0c1828' : '#cbd5e1'}
              stroke={t.isDark ? '#1a2535' : '#94a3b8'} strokeWidth="0.3" />
          ))}
        </g>
      ))}
      {/* Shadow */}
      <ellipse cx={19} cy={114} rx={18} ry={4} fill="#000" opacity="0.18" />
    </g>
  );
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

export default function OfficeSystem() {
  const agentRecord = useAgentsStore(state => state.agents);
  const agents = useMemo(() => Object.values(agentRecord), [agentRecord]);

  const [currentOffice, setCurrentOffice] = useState(0);
  const [dimensions, setDimensions] = useState({ width: 800, height: 450 });
  const [currentTime, setCurrentTime] = useState('');
  const [theme, setTheme] = useState<TimeOfDay>('night');
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const {
    isEditMode, setIsEditMode, draggedAgent,
    startDrag, drag, endDrag, resetPositions, getPosition, hasCustomPositions,
  } = useAgentPositioning(currentOffice);

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      // Use local timezone explicitly with 24-hour format
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const seconds = String(now.getSeconds()).padStart(2, '0');
      setCurrentTime(`${hours}:${minutes}:${seconds}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    setTheme(getTimeOfDay());
    const id = setInterval(() => setTheme(getTimeOfDay()), 60000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };
    const ro = new ResizeObserver(update);
    if (containerRef.current) ro.observe(containerRef.current);
    update();
    return () => ro.disconnect();
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent, agentId: string, agentX: number, agentY: number) => {
    if (!isEditMode) return;
    e.preventDefault();
    const rect = containerRef.current?.getBoundingClientRect();
    if (rect) startDrag(agentId, e.clientX - rect.left, e.clientY - rect.top, agentX, agentY);
  }, [isEditMode, startDrag]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isEditMode || !draggedAgent) return;
    const rect = containerRef.current?.getBoundingClientRect();
    if (rect) drag(e.clientX - rect.left, e.clientY - rect.top);
  }, [isEditMode, draggedAgent, drag]);

  const handleMouseUp = useCallback(() => endDrag(), [endDrag]);

  const offices = useMemo(() => {
    const mockAgents = agents.length > 0 ? agents : [
      { id: 1, name: 'Lead',     role: 'Command Center', domain: 'management', status: 'busy' },
      { id: 2, name: 'Frontend', role: 'UI Architect',   domain: 'tech',       status: 'busy' },
      { id: 3, name: 'Backend',  role: 'API Engineer',   domain: 'tech',       status: 'busy' },
      { id: 4, name: 'Database', role: 'Data Architect', domain: 'tech',       status: 'idle' },
      { id: 5, name: 'DevOps',   role: 'SRE Engineer',   domain: 'ops',        status: 'busy' },
      { id: 6, name: 'Security', role: 'SecOps',         domain: 'ops',        status: 'idle' },
      { id: 7, name: 'ML',       role: 'AI Engineer',    domain: 'data',       status: 'idle' },
      { id: 8, name: 'Content',  role: 'Tech Writer',    domain: 'creative',   status: 'OFFLINE' },
    ];
    return distributeAgentsIntoOffices(mockAgents as StoreAgent[]);
  }, [agents]);

  const t = PREMIUM_THEMES[theme];
  const currentAgents = offices[currentOffice] || [];
  const wallH = dimensions.height * 0.18;

  const agentPositions = useMemo(() => {
    const basePositions = generatePositionsForOffice(currentAgents, dimensions.width, wallH);
    return basePositions.map(({ x, y, agent }) => ({
      agent,
      ...getPosition(String(agent.id), x, y),
    }));
  }, [currentAgents, dimensions.width, wallH, getPosition]);

  const onlineCount = currentAgents.filter(a => a.status !== 'OFFLINE').length;

  const themeIcon = { day: '☀️', sunset: '🌅', night: '🌙' }[theme];

  return (
    <div
      ref={containerRef}
      className="w-full h-full relative overflow-hidden rounded-xl"
      style={{
        background: `linear-gradient(180deg, ${t.bg0} 0%, ${t.bg1} 100%)`,
      }}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* ========== SVG BACKGROUND CANVAS ========== */}
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        style={{ position: 'absolute', top: 0, left: 0, display: 'block',
          cursor: isEditMode ? (draggedAgent ? 'grabbing' : 'grab') : 'default' }}
      >
        <PremiumFloor width={dimensions.width} height={dimensions.height} t={t} showGrid={isEditMode} />
        <PremiumBackWall width={dimensions.width} height={dimensions.height} t={t} />
        <HolographicDisplay width={dimensions.width} wallH={wallH} t={t} officeNumber={currentOffice + 1} />
        <PremiumWindows width={dimensions.width} wallH={wallH} t={t} />
        <PremiumClock x={dimensions.width * 0.76} y={wallH * 0.5} t={t} />
        <PremiumBookshelf x={22} y={wallH + 28} t={t} />
        <PremiumPlant x={86} y={wallH + 52} t={t} type="tall" />
        <PremiumServerRack x={dimensions.width - 60} y={wallH + 26} t={t} />
        <PremiumPlant x={dimensions.width - 108} y={wallH + 72} t={t} type="bush" />

        {/* Edit mode grid overlay */}
        {isEditMode && (
          <g opacity="0.18">
            {Array.from({ length: Math.ceil(dimensions.width / OFFICE_CONFIG.GRID_SIZE) }).map((_, i) => (
              <line key={`v${i}`}
                x1={i * OFFICE_CONFIG.GRID_SIZE} y1={wallH}
                x2={i * OFFICE_CONFIG.GRID_SIZE} y2={dimensions.height}
                stroke={t.accent} strokeWidth="0.5" strokeDasharray="3,3" />
            ))}
            {Array.from({ length: Math.ceil((dimensions.height - wallH) / OFFICE_CONFIG.GRID_SIZE) }).map((_, i) => (
              <line key={`h${i}`}
                x1={0} y1={wallH + i * OFFICE_CONFIG.GRID_SIZE}
                x2={dimensions.width} y2={wallH + i * OFFICE_CONFIG.GRID_SIZE}
                stroke={t.accent} strokeWidth="0.5" strokeDasharray="3,3" />
            ))}
          </g>
        )}
      </svg>

      {/* ========== AGENT HTML OVERLAY ========== */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        {agentPositions.map(({ x, y, agent }) => (
          <div
            key={agent.id}
            style={{
              pointerEvents: 'auto',
              opacity: draggedAgent === String(agent.id) ? 0.65 : 1,
              cursor: isEditMode ? 'grab' : 'pointer',
              transition: 'opacity 0.15s ease',
            }}
            onMouseDown={(e) => handleMouseDown(e, String(agent.id), x, y)}
          >
            <AgentDesk
              agent={agent}
              x={x}
              y={y}
              isLead={agent.name?.toLowerCase().includes('lead')}
              onClick={() => {}}
            />
          </div>
        ))}
      </div>

      {/* ========== HEADER BAR — glassmorphism ========== */}
      <div className="absolute top-3 left-3 right-3 z-30 flex justify-between items-center">

        {/* LIVE + clock */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 14px', borderRadius: 10,
          background: t.glass,
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          border: `1px solid ${t.glassBorder}`,
          boxShadow: '0 4px 20px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04)',
        }}>
          <span className="animate-pulse" style={{
            width: 7, height: 7, borderRadius: '50%',
            background: '#10b981',
            boxShadow: '0 0 8px rgba(16,185,129,0.8)',
            flexShrink: 0,
            display: 'block',
          }} />
          <span style={{ fontSize: 11, fontWeight: 700, color: t.textPrimary, letterSpacing: '0.06em' }}>
            LIVE
          </span>
          <span style={{ width: 1, height: 12, background: t.borderDefault, flexShrink: 0 }} />
          <span style={{ fontSize: 11, fontFamily: 'monospace', color: t.textMuted, letterSpacing: '0.04em' }}>
            {currentTime}
          </span>
        </div>

        {/* Office tabs */}
        {offices.length > 1 && (
          <div style={{ display: 'flex', gap: 4 }}>
            {offices.map((office, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentOffice(idx)}
                style={{
                  padding: '5px 12px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                  cursor: 'pointer', outline: 'none',
                  background: currentOffice === idx
                    ? t.accent
                    : t.glass,
                  backdropFilter: currentOffice === idx ? 'none' : 'blur(14px)',
                  WebkitBackdropFilter: currentOffice === idx ? 'none' : 'blur(14px)',
                  color: currentOffice === idx ? '#fff' : t.textMuted,
                  border: `1px solid ${currentOffice === idx ? t.accent : t.glassBorder}`,
                  boxShadow: currentOffice === idx
                    ? `0 0 16px ${t.accentGlow}`
                    : '0 4px 20px rgba(0,0,0,0.3)',
                  transition: 'all 0.2s ease',
                }}
              >
                Office {idx + 1}
                <span style={{ opacity: 0.65, marginLeft: 4 }}>({office.length})</span>
              </button>
            ))}
          </div>
        )}

        {/* Edit layout button */}
        <button
          onClick={() => setIsEditMode(!isEditMode)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '6px 14px', borderRadius: 10, fontSize: 11, fontWeight: 600,
            cursor: 'pointer', outline: 'none',
            background: isEditMode ? t.accent : t.glass,
            backdropFilter: isEditMode ? 'none' : 'blur(14px)',
            WebkitBackdropFilter: isEditMode ? 'none' : 'blur(14px)',
            color: isEditMode ? '#fff' : t.textMuted,
            border: `1px solid ${isEditMode ? t.accent : t.glassBorder}`,
            boxShadow: isEditMode
              ? `0 0 18px ${t.accentGlow}`
              : '0 4px 20px rgba(0,0,0,0.3)',
            transition: 'all 0.2s ease',
          }}
        >
          <span>{isEditMode ? '✓' : '⊹'}</span>
          <span>{isEditMode ? 'Done' : 'Layout'}</span>
        </button>
      </div>

      {/* Edit mode hint */}
      {isEditMode && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 pointer-events-none z-30"
          style={{
            padding: '5px 16px', borderRadius: 8, fontSize: 10, fontWeight: 500,
            background: t.isDark ? 'rgba(99,102,241,0.12)' : 'rgba(59,130,246,0.1)',
            border: `1px solid ${t.accent}44`,
            color: t.accent,
            backdropFilter: 'blur(10px)',
            letterSpacing: '0.04em',
          }}>
          ⊹ Drag agents · Grid {OFFICE_CONFIG.GRID_SIZE}px snap
        </div>
      )}

      {/* ========== FOOTER BAR — glassmorphism ========== */}
      <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">

        {/* Agent count */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '5px 14px', borderRadius: 10,
          background: t.glass,
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          border: `1px solid ${t.glassBorder}`,
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
            background: onlineCount === currentAgents.length
              ? '#10b981'
              : onlineCount > 0 ? '#f59e0b' : '#f43f5e',
            boxShadow: `0 0 8px ${onlineCount === currentAgents.length
              ? 'rgba(16,185,129,0.7)' : 'rgba(245,158,11,0.6)'}`,
          }} />
          <span style={{ fontSize: 11, color: t.textMuted }}>
            <span style={{ fontWeight: 700, color: t.textPrimary }}>
              {onlineCount}/{currentAgents.length}
            </span>
            {' '}agents online
          </span>
          {offices.length > 1 && (
            <>
              <span style={{ width: 1, height: 12, background: t.borderDefault }} />
              <span style={{ fontSize: 10, color: t.textMuted, fontFamily: 'monospace' }}>
                {currentOffice + 1}/{offices.length}
              </span>
            </>
          )}
        </div>

        {/* Center: reset button in edit mode */}
        {isEditMode && hasCustomPositions && (
          <button onClick={resetPositions}
            style={{
              padding: '5px 14px', borderRadius: 10, fontSize: 11, fontWeight: 600,
              cursor: 'pointer', outline: 'none',
              background: 'rgba(244,63,94,0.12)',
              border: '1px solid rgba(244,63,94,0.35)',
              color: '#f43f5e',
              backdropFilter: 'blur(10px)',
              transition: 'all 0.2s ease',
            } as React.CSSProperties}>
            ↺ Reset Layout
          </button>
        )}

        {/* Theme indicator */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '5px 12px', borderRadius: 10,
          background: t.glass,
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          border: `1px solid ${t.glassBorder}`,
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
          fontSize: 11, color: t.textMuted,
        }}>
          <span>{themeIcon}</span>
          <span style={{ textTransform: 'capitalize', letterSpacing: '0.04em' }}>{theme}</span>
        </div>
      </div>
    </div>
  );
}
