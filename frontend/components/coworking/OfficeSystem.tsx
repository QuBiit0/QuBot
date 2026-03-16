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
  SPACING_Y: 180,
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

const THEMES = {
  day: {
    wallTop: '#e8eef5', wallBottom: '#d0dae8',
    floorTop: '#f0f4f8', floorBottom: '#e2e8f0',
    windowSky: ['#87CEEB', '#E0F6FF'],
    textColor: '#1a202c', accentColor: '#2563eb',
  },
  sunset: {
    wallTop: '#2d3748', wallBottom: '#1a202c',
    floorTop: '#1e293b', floorBottom: '#0f172a',
    windowSky: ['#ff6b6b', '#ffa502', '#2d3436'],
    textColor: '#f7fafc', accentColor: '#f6ad55',
  },
  night: {
    wallTop: '#0f172a', wallBottom: '#020617',
    floorTop: '#1e293b', floorBottom: '#0f172a',
    windowSky: ['#0a1628', '#1a2a4a', '#0d1a30'],
    textColor: '#e2e8f0', accentColor: '#3b82f6',
  },
};

// ============================================================================
// HOOK PARA POSICIONAMIENTO
// ============================================================================

interface OfficePositions {
  [officeIndex: number]: {
    [agentId: string]: { x: number; y: number };
  };
}

function useAgentPositioning(officeIndex: number) {
  const [customPositions, setCustomPositions] = useState<OfficePositions>({});
  const [isEditMode, setIsEditMode] = useState(false);
  const [draggedAgent, setDraggedAgent] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const saved = localStorage.getItem('qubot_agent_positions');
    if (saved) {
      try {
        setCustomPositions(JSON.parse(saved));
      } catch {
        console.error('Failed to load agent positions');
      }
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
        [draggedAgent]: { x: mouseX - dragOffset.x, y: mouseY - dragOffset.y }
      }
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
        [officeIndex]: {
          ...prev[officeIndex],
          [draggedAgent]: { x: snappedX, y: snappedY }
        }
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
    hasCustomPositions: Object.keys(customPositions[officeIndex] || {}).length > 0
  };
}

// ============================================================================
// FUNCIONES UTILITARIAS
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
    const domainAgents1 = byDomain[domain];
    if (domainAgents1) {
      while (domainAgents1.length > 0 && office1.length < OFFICE_CONFIG.MAX_AGENTS_PER_OFFICE) {
        office1.push(domainAgents1.shift()!);
      }
    }
  }
  if (office1.length > 0) offices.push(office1);

  for (const domain of domains) {
    const domainAgents2 = byDomain[domain];
    if (!domainAgents2) continue;
    while (domainAgents2.length > 0) {
      const office: StoreAgent[] = [];
      while (domainAgents2.length > 0 && office.length < OFFICE_CONFIG.MAX_AGENTS_PER_OFFICE) {
        office.push(domainAgents2.shift()!);
      }
      offices.push(office);
    }
  }
  
  return offices.slice(0, OFFICE_CONFIG.MAX_OFFICES);
}

function generatePositionsForOffice(agents: StoreAgent[], width: number, wallH: number) {
  const positions: Array<{ x: number; y: number; agent: StoreAgent }> = [];
  const centerX = width / 2;
  const startY = wallH + 80;
  
  const lead = agents.find(a => a.name?.toLowerCase().includes('lead'));
  const others = agents.filter(a => a.id !== lead?.id);
  
  if (lead) {
    positions.push({
      x: centerX,
      y: startY,
      agent: lead,
    });
  }
  
  const spacingX = OFFICE_CONFIG.SPACING_X;
  const spacingY = OFFICE_CONFIG.SPACING_Y;
  const secondRowY = startY + spacingY + 40;
  
  if (others.length <= 3) {
    const startX = centerX - ((others.length - 1) * spacingX) / 2;
    others.forEach((agent, i) => {
      positions.push({ x: startX + i * spacingX, y: secondRowY, agent });
    });
  } else if (others.length <= 6) {
    const firstRow = Math.min(3, others.length);
    const startX1 = centerX - ((firstRow - 1) * spacingX) / 2;
    for (let i = 0; i < firstRow; i++) {
      positions.push({ x: startX1 + i * spacingX, y: secondRowY, agent: others[i]! });
    }

    const thirdRowY = secondRowY + spacingY;
    const secondRowAgents = others.slice(firstRow);
    const secondRowCount = secondRowAgents.length;
    const startX2 = centerX - ((secondRowCount - 1) * spacingX) / 2;
    secondRowAgents.forEach((agent, i) => {
      positions.push({ x: startX2 + i * spacingX, y: thirdRowY, agent });
    });
  } else {
    const firstRow = 3;
    const startX1 = centerX - ((firstRow - 1) * spacingX) / 2;
    for (let i = 0; i < firstRow; i++) {
      positions.push({ x: startX1 + i * spacingX, y: secondRowY, agent: others[i]! });
    }
    
    const thirdRowY = secondRowY + spacingY;
    const secondRowAgents = others.slice(firstRow);
    const startX2 = centerX - ((4 - 1) * spacingX) / 2;
    secondRowAgents.forEach((agent, i) => {
      positions.push({ x: startX2 + i * spacingX, y: thirdRowY, agent });
    });
  }
  
  return positions;
}

// ============================================================================
// COMPONENTES VISUALES
// ============================================================================

function Floor({ width, height, theme, showGrid }: { width: number; height: number; theme: TimeOfDay; showGrid?: boolean }) {
  const colors = THEMES[theme];
  return (
    <g>
      <defs>
        <linearGradient id="floorGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={colors.floorTop} />
          <stop offset="100%" stopColor={colors.floorBottom} />
        </linearGradient>
        <pattern id="floorGrid" width="50" height="30" patternUnits="userSpaceOnUse">
          <rect width="50" height="30" fill="url(#floorGrad)" />
          <path d="M0 0 L50 0 M0 0 L0 30" stroke={theme === 'day' ? '#cbd5e1' : '#1e293b'} strokeWidth="0.5" opacity="0.3" />
        </pattern>
        <pattern id="editGrid" width={OFFICE_CONFIG.GRID_SIZE} height={OFFICE_CONFIG.GRID_SIZE} patternUnits="userSpaceOnUse">
          <rect width={OFFICE_CONFIG.GRID_SIZE} height={OFFICE_CONFIG.GRID_SIZE} fill="transparent" />
          <circle cx={2} cy={2} r={1} fill={theme === 'day' ? '#94a3b8' : '#475569'} opacity="0.4" />
        </pattern>
      </defs>
      <rect width={width} height={height} fill="url(#floorGrid)" />
      {showGrid && <rect width={width} height={height} fill="url(#editGrid)" opacity="0.3" />}
    </g>
  );
}

function BackWall({ width, height, theme }: { width: number; height: number; theme: TimeOfDay }) {
  const colors = THEMES[theme];
  const wallH = height * 0.18;
  
  return (
    <g>
      <defs>
        <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={colors.wallTop} />
          <stop offset="100%" stopColor={colors.wallBottom} />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={width} height={wallH} fill="url(#wallGrad)" />
      <rect x={0} y={wallH - 4} width={width} height={4} fill={theme === 'day' ? '#94a3b8' : '#1e293b'} />
    </g>
  );
}

function WhiteboardLogo({ width, wallH, theme, officeNumber }: { width: number; wallH: number; theme: TimeOfDay; officeNumber: number }) {
  const colors = THEMES[theme];
  const isDay = theme === 'day';
  
  return (
    <g transform={`translate(${width / 2}, ${wallH * 0.5})`}>
      <defs>
        {/* Marco de madera */}
        <linearGradient id="woodFrame" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={isDay ? '#8B4513' : '#5c3a1e'} />
          <stop offset="50%" stopColor={isDay ? '#A0522D' : '#6b4423'} />
          <stop offset="100%" stopColor={isDay ? '#8B4513' : '#5c3a1e'} />
        </linearGradient>
        {/* Pizarra blanca */}
        <linearGradient id="whiteboard" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={isDay ? '#f8fafc' : '#e2e8f0'} />
          <stop offset="100%" stopColor={isDay ? '#f1f5f9' : '#cbd5e1'} />
        </linearGradient>
        {/* Sombra */}
        <filter id="boardShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="3" stdDeviation="4" floodOpacity="0.3"/>
        </filter>
      </defs>
      
      {/* Marco de madera */}
      <rect x={-110} y={-35} width={220} height={70} rx={4} fill="url(#woodFrame)" filter="url(#boardShadow)" />
      
      {/* Pizarra blanca interior */}
      <rect x={-105} y={-30} width={210} height={60} rx={2} fill="url(#whiteboard)" stroke="#94a3b8" strokeWidth="0.5" />
      
      {/* Borde metálico */}
      <rect x={-107} y={-32} width={214} height={64} rx={3} fill="none" stroke={isDay ? '#64748b' : '#475569'} strokeWidth="1" opacity="0.5" />
      
      {/* Texto QUBOT */}
      <text x={0} y={-2} textAnchor="middle" fontSize={22} fontWeight="bold" 
        fill={isDay ? '#1e293b' : '#0f172a'}
        style={{ fontFamily: 'system-ui, sans-serif', letterSpacing: '2px' }}>QUBOT</text>
      
      {/* Subtítulo AI OFFICE */}
      <text x={0} y={16} textAnchor="middle" fontSize={10} fill={isDay ? '#64748b' : '#475569'} letterSpacing={3}
        style={{ fontFamily: 'system-ui, sans-serif' }}>AI OFFICE {officeNumber > 1 ? `#${officeNumber}` : ''}</text>
      
      {/* Estante para marcadores */}
      <rect x={-105} y={28} width={210} height={8} rx={1} fill={isDay ? '#e2e8f0' : '#cbd5e1'} />
      
      {/* Marcadores de colores */}
      <rect x={-90} y={26} width={4} height={6} rx={1} fill="#ef4444" />
      <rect x={-82} y={26} width={4} height={6} rx={1} fill="#3b82f6" />
      <rect x={-74} y={26} width={4} height={6} rx={1} fill="#22c55e" />
      <rect x={70} y={26} width={4} height={6} rx={1} fill="#f59e0b" />
      
      {/* Borrador */}
      <rect x={80} y={25} width={16} height={5} rx={1} fill="#94a3b8" />
    </g>
  );
}

function Windows({ width, wallH, theme }: { width: number; wallH: number; theme: TimeOfDay }) {
  const colors = THEMES[theme];
  const windowW = 80;
  const windowH = wallH * 0.55;
  
  return (
    <g>
      <defs>
        <linearGradient id="windowSky" x1="0" y1="0" x2="0" y2="1">
          {colors.windowSky.map((color, i) => (
            <stop key={i} offset={`${(i / (colors.windowSky.length - 1)) * 100}%`} stopColor={color} />
          ))}
        </linearGradient>
      </defs>
      
      {/* Ventana izquierda - posición ajustada para no tapar */}
      <g transform={`translate(35, ${wallH * 0.2})`}>
        <rect width={windowW} height={windowH} rx={2} fill="url(#windowSky)" 
          stroke={theme === 'day' ? '#64748b' : '#1e3a6e'} strokeWidth="2" />
        <line x1={windowW/2} y1={0} x2={windowW/2} y2={windowH} 
          stroke={theme === 'day' ? '#64748b' : '#1e3a6e'} strokeWidth="2" />
        <line x1={0} y1={windowH/2} x2={windowW} y2={windowH/2} 
          stroke={theme === 'day' ? '#64748b' : '#1e3a6e'} strokeWidth="2" />
      </g>
      
      {/* Ventana derecha - posición ajustada */}
      <g transform={`translate(${width - 115}, ${wallH * 0.2})`}>
        <rect width={windowW} height={windowH} rx={2} fill="url(#windowSky)" 
          stroke={theme === 'day' ? '#64748b' : '#1e3a6e'} strokeWidth="2" />
        <line x1={windowW/2} y1={0} x2={windowW/2} y2={windowH} 
          stroke={theme === 'day' ? '#64748b' : '#1e3a6e'} strokeWidth="2" />
        <line x1={0} y1={windowH/2} x2={windowW} y2={windowH/2} 
          stroke={theme === 'day' ? '#64748b' : '#1e3a6e'} strokeWidth="2" />
      </g>
    </g>
  );
}

// ============================================================================
// DECORACIONES
// ============================================================================

function WallClock({ x, y, theme }: { x: number; y: number; theme: TimeOfDay }) {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);
  
  // Hora actual correcta
  const hours = time.getHours();
  const minutes = time.getMinutes();
  const seconds = time.getSeconds();
  
  // Ángulos correctos para las manecillas
  const hourAngle = ((hours % 12) * 30) + (minutes * 0.5) - 90;
  const minuteAngle = (minutes * 6) - 90;
  const secondAngle = (seconds * 6) - 90;
  
  return (
    <g transform={`translate(${x}, ${y})`}>
      {/* Marco del reloj */}
      <circle cx={0} cy={0} r={26} fill={theme === 'day' ? '#f8fafc' : '#1e293b'} 
        stroke={theme === 'day' ? '#cbd5e1' : '#334155'} strokeWidth="2" />
      <circle cx={0} cy={0} r={22} fill="none" 
        stroke={theme === 'day' ? '#e2e8f0' : '#1e293b'} strokeWidth="1" />
      
      {/* Marcadores de hora */}
      {[...Array(12)].map((_, i) => (
        <line
          key={i}
          x1={0}
          y1={i % 3 === 0 ? -18 : -20}
          x2={0}
          y2={-22}
          stroke={theme === 'day' ? '#64748b' : '#94a3b8'}
          strokeWidth={i % 3 === 0 ? 2 : 1}
          transform={`rotate(${i * 30})`}
        />
      ))}
      
      {/* Manecilla de horas - corregida */}
      <line
        x1={0} y1={0}
        x2={12} y2={0}
        stroke={theme === 'day' ? '#1e293b' : '#e2e8f0'}
        strokeWidth="3"
        strokeLinecap="round"
        transform={`rotate(${hourAngle})`}
      />
      
      {/* Manecilla de minutos - corregida */}
      <line
        x1={0} y1={0}
        x2={18} y2={0}
        stroke={theme === 'day' ? '#475569' : '#cbd5e1'}
        strokeWidth="2"
        strokeLinecap="round"
        transform={`rotate(${minuteAngle})`}
      />
      
      {/* Manecilla de segundos - corregida */}
      <line
        x1={0} y1={0}
        x2={20} y2={0}
        stroke="#ef4444"
        strokeWidth="1"
        strokeLinecap="round"
        transform={`rotate(${secondAngle})`}
      />
      
      {/* Centro */}
      <circle cx={0} cy={0} r={3} fill={theme === 'day' ? '#1e293b' : '#e2e8f0'} />
      <circle cx={0} cy={0} r={1.5} fill="#ef4444" />
    </g>
  );
}

function Bookshelf({ x, y, theme }: { x: number; y: number; theme: TimeOfDay }) {
  const bookColors = ['#8B4513', '#654321', '#4a3728', '#2d1f16', '#1a4a6e', '#3d5c5c'];
  
  return (
    <g transform={`translate(${x}, ${y})`}>
      <defs>
        <linearGradient id="woodGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={theme === 'day' ? '#5c4033' : '#1a1510'} />
          <stop offset="50%" stopColor={theme === 'day' ? '#8b6914' : '#2d2418'} />
          <stop offset="100%" stopColor={theme === 'day' ? '#5c4033' : '#1a1510'} />
        </linearGradient>
      </defs>
      
      <rect x={0} y={0} width={50} height={80} rx={2} fill="url(#woodGrad)" 
        stroke={theme === 'day' ? '#3d3020' : '#0d0a05'} strokeWidth="1" />
      
      <rect x={2} y={25} width={46} height={2} fill={theme === 'day' ? '#4a3728' : '#1a1208'} />
      <rect x={2} y={52} width={46} height={2} fill={theme === 'day' ? '#4a3728' : '#1a1208'} />
      
      {/* Libros con animación */}
      {[0, 1, 2].map((shelf) => (
        <g key={shelf}>
          {Array.from({ length: 4 }).map((_, i) => {
            const h = 18 + ((shelf * 4 + i) % 3) * 3;
            const w = 8;
            const bookX = 5 + i * 11;
            const bookY = 24 + shelf * 27 - h;
            return (
              <rect 
                key={i} 
                x={bookX} 
                y={bookY} 
                width={w} 
                height={h} 
                fill={bookColors[(shelf * 4 + i) % bookColors.length]} 
                stroke="#000" 
                strokeWidth="0.3">
                <animate 
                  attributeName="y" 
                  values={`${bookY};${bookY - 1};${bookY}`} 
                  dur={`${3 + Math.random() * 2}s`} 
                  repeatCount="indefinite" />
              </rect>
            );
          })}
        </g>
      ))}
      
      <ellipse cx={25} cy={82} rx={25} ry={3} fill="#000" opacity="0.2" />
    </g>
  );
}

function Plant({ x, y, theme, type = 'tall' }: { x: number; y: number; theme: TimeOfDay; type?: 'tall' | 'bush' }) {
  const potColor = theme === 'day' ? '#8b4513' : '#5c3a1e';
  const leafColors = ['#22c55e', '#16a34a', '#15803d', '#4ade80'];
  
  if (type === 'bush') {
    return (
      <g transform={`translate(${x}, ${y})`}>
        <path d="M-20 40 L-15 60 L15 60 L20 40 Z" fill={potColor} />
        <ellipse cx={0} cy={40} rx={20} ry={5} fill={theme === 'day' ? '#a0522d' : '#4a3728'} />
        <circle cx={-10} cy={25} r={15} fill={leafColors[0]} />
        <circle cx={10} cy={25} r={15} fill={leafColors[1]} />
        <circle cx={0} cy={10} r={18} fill={leafColors[2]} />
        <circle cx={-5} cy={20} r={12} fill={leafColors[3]} />
        <circle cx={8} cy={18} r={10} fill={leafColors[0]} />
      </g>
    );
  }
  
  // Tall plant - más compacta
  return (
    <g transform={`translate(${x}, ${y})`}>
      <path d="M-15 50 L-12 70 L12 70 L15 50 Z" fill={potColor} />
      <ellipse cx={0} cy={50} rx={15} ry={3} fill={theme === 'day' ? '#a0522d' : '#4a3728'} />
      <line x1={-3} y1={50} x2={-5} y2={15} stroke={leafColors[2]} strokeWidth="3" strokeLinecap="round" />
      <line x1={3} y1={50} x2={5} y2={10} stroke={leafColors[2]} strokeWidth="3" strokeLinecap="round" />
      <line x1={0} y1={50} x2={0} y2={0} stroke={leafColors[2]} strokeWidth="3" strokeLinecap="round" />
      <ellipse cx={-8} cy={20} rx={6} ry={12} fill={leafColors[0]} transform="rotate(-20)" />
      <ellipse cx={8} cy={15} rx={6} ry={12} fill={leafColors[1]} transform="rotate(20)" />
      <ellipse cx={0} cy={-5} rx={5} ry={10} fill={leafColors[3]} />
    </g>
  );
}

function ServerRack({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x}, ${y})`}>
      <rect width={35} height={100} rx={3} fill="#0d1117" stroke="#1e3a6e" strokeWidth="2" />
      {Array.from({ length: 5 }).map((_, i) => (
        <g key={i} transform={`translate(4, ${10 + i * 18})`}>
          <rect width={27} height={14} rx={2} fill="#111926" stroke="#1e2d45" />
          <circle cx={20} cy={7} r={2} fill={i % 2 === 0 ? "#3fb950" : "#58a6ff"}>
            <animate attributeName="opacity" values="1;0.3;1" dur={`${1.5 + i * 0.2}s`} repeatCount="indefinite" />
          </circle>
        </g>
      ))}
      <ellipse cx={17} cy={102} rx={17} ry={3} fill="#000" opacity="0.2" />
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
  
  const { isEditMode, setIsEditMode, draggedAgent, startDrag, drag, endDrag, resetPositions, getPosition, hasCustomPositions } = useAgentPositioning(currentOffice);

  // Hora actual
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  // Tema día/noche
  useEffect(() => {
    setTheme(getTimeOfDay());
    const interval = setInterval(() => setTheme(getTimeOfDay()), 60000);
    return () => clearInterval(interval);
  }, []);

  // Resize observer
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

  // Mouse handlers
  const handleMouseDown = useCallback((e: React.MouseEvent, agentId: string, agentX: number, agentY: number) => {
    if (!isEditMode) return;
    e.preventDefault();
    const rect = svgRef.current?.getBoundingClientRect();
    if (rect) startDrag(agentId, e.clientX - rect.left, e.clientY - rect.top, agentX, agentY);
  }, [isEditMode, startDrag]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isEditMode || !draggedAgent) return;
    const rect = svgRef.current?.getBoundingClientRect();
    if (rect) drag(e.clientX - rect.left, e.clientY - rect.top);
  }, [isEditMode, draggedAgent, drag]);

  const handleMouseUp = useCallback(() => endDrag(), [endDrag]);

  const offices = useMemo(() => {
    const mockAgents = agents.length > 0 ? agents : [
      { id: 1, name: 'Lead', role: 'Command Center', domain: 'management', status: 'busy' },
      { id: 2, name: 'Frontend', role: 'UI Architect', domain: 'tech', status: 'busy' },
      { id: 3, name: 'Backend', role: 'API Engineer', domain: 'tech', status: 'busy' },
      { id: 4, name: 'Database', role: 'Data Architect', domain: 'tech', status: 'idle' },
      { id: 5, name: 'DevOps', role: 'SRE Engineer', domain: 'ops', status: 'busy' },
      { id: 6, name: 'Security', role: 'SecOps', domain: 'ops', status: 'idle' },
      { id: 7, name: 'ML', role: 'AI Engineer', domain: 'data', status: 'idle' },
      { id: 8, name: 'Content', role: 'Tech Writer', domain: 'creative', status: 'OFFLINE' },
    ];
    return distributeAgentsIntoOffices(mockAgents as StoreAgent[]);
  }, [agents]);

  const currentAgents = offices[currentOffice] || [];
  const wallH = dimensions.height * 0.18;
  const colors = THEMES[theme];
  
  const agentPositions = useMemo(() => {
    const basePositions = generatePositionsForOffice(currentAgents, dimensions.width, wallH);
    return basePositions.map(({ x, y, agent }) => ({
      agent,
      ...getPosition(String(agent.id), x, y)
    }));
  }, [currentAgents, dimensions.width, wallH, getPosition]);

  const onlineCount = currentAgents.filter(a => a.status !== 'OFFLINE').length;

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full relative overflow-hidden rounded-xl flex flex-col"
      style={{ 
        background: theme === 'day' 
          ? 'linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%)'
          : 'linear-gradient(180deg, #0f172a 0%, #020617 100%)',
      }}
    >
      {/* ========== HEADER INFO BAR - ENCIMA DE TODO ========== */}
      <div className="absolute top-3 left-3 right-3 z-30 flex justify-between items-center">
        {/* LIVE indicator + hora digital */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs"
          style={{ 
            background: theme === 'day' ? 'rgba(255,255,255,0.95)' : 'rgba(9,14,26,0.95)', 
            borderColor: theme === 'day' ? '#cbd5e1' : '#1e3a6e',
          }}>
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="font-medium" style={{ color: theme === 'day' ? '#1e293b' : '#e2e8f0' }}>LIVE</span>
          <span className="text-gray-400">|</span>
          <span className="font-mono" style={{ color: theme === 'day' ? '#475569' : '#94a3b8' }}>{currentTime}</span>
        </div>

        {/* Tabs de oficinas - centrados */}
        {offices.length > 1 && (
          <div className="flex gap-1">
            {offices.map((office, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentOffice(idx)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                style={{
                  background: currentOffice === idx 
                    ? (theme === 'day' ? '#3b82f6' : '#1e3a6e')
                    : (theme === 'day' ? 'rgba(255,255,255,0.8)' : 'rgba(15,23,42,0.8)'),
                  color: currentOffice === idx ? '#fff' : (theme === 'day' ? '#475569' : '#94a3b8'),
                  border: `1px solid ${currentOffice === idx ? '#3b82f6' : theme === 'day' ? '#cbd5e1' : '#1e293b'}`,
                }}
              >
                Office {idx + 1}
                <span className="ml-1 opacity-70">({office.length})</span>
              </button>
            ))}
          </div>
        )}

        {/* Edit Layout button */}
        <button
          onClick={() => setIsEditMode(!isEditMode)}
          className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2"
          style={{
            background: isEditMode 
              ? (theme === 'day' ? '#3b82f6' : '#2563eb')
              : (theme === 'day' ? 'rgba(255,255,255,0.95)' : 'rgba(9,14,26,0.95)'),
            color: isEditMode ? '#fff' : (theme === 'day' ? '#475569' : '#8b949e'),
            border: `1px solid ${isEditMode ? '#3b82f6' : theme === 'day' ? '#cbd5e1' : '#1e3a6e'}`,
          }}
        >
          <span>{isEditMode ? '✓' : '✎'}</span>
          <span>{isEditMode ? 'Done' : 'Edit Layout'}</span>
        </button>
      </div>

      {/* ========== CANVAS SVG ========== */}
      <svg 
        ref={svgRef}
        width={dimensions.width} 
        height={dimensions.height} 
        className="block flex-1"
        style={{ cursor: isEditMode ? (draggedAgent ? 'grabbing' : 'grab') : 'default' }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          <filter id="blur" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" />
          </filter>
        </defs>
        
        {/* Fondo */}
        <Floor width={dimensions.width} height={dimensions.height} theme={theme} showGrid={isEditMode} />
        <BackWall width={dimensions.width} height={dimensions.height} theme={theme} />
        
        {/* Logo centrado en la pared */}
        <WhiteboardLogo width={dimensions.width} wallH={wallH} theme={theme} officeNumber={currentOffice + 1} />
        
        {/* Ventanas - posiciones ajustadas */}
        <Windows width={dimensions.width} wallH={wallH} theme={theme} />
        
        {/* Reloj de pared - POSICIÓN CORREGIDA (entre ventana y borde) */}
        <WallClock x={dimensions.width - 50} y={wallH * 0.5} theme={theme} />
        
        {/* Librería - posición ajustada */}
        <Bookshelf x={25} y={wallH + 30} theme={theme} />
        
        {/* Planta junto a librería - POSICIÓN AJUSTADA */}
        <Plant x={90} y={wallH + 55} theme={theme} type="tall" />
        
        {/* Server rack */}
        <ServerRack x={dimensions.width - 60} y={wallH + 30} />
        
        {/* Planta junto a server - POSICIÓN AJUSTADA */}
        <Plant x={dimensions.width - 110} y={wallH + 75} theme={theme} type="bush" />
        
        {/* Grid overlay */}
        {isEditMode && (
          <g opacity="0.2">
            {Array.from({ length: Math.ceil(dimensions.width / OFFICE_CONFIG.GRID_SIZE) }).map((_, i) => (
              <line key={`v${i}`} x1={i * OFFICE_CONFIG.GRID_SIZE} y1={wallH} x2={i * OFFICE_CONFIG.GRID_SIZE} y2={dimensions.height}
                stroke={theme === 'day' ? '#94a3b8' : '#475569'} strokeWidth="0.5" strokeDasharray="2,2" />
            ))}
            {Array.from({ length: Math.ceil((dimensions.height - wallH) / OFFICE_CONFIG.GRID_SIZE) }).map((_, i) => (
              <line key={`h${i}`} x1={0} y1={wallH + i * OFFICE_CONFIG.GRID_SIZE} x2={dimensions.width} y2={wallH + i * OFFICE_CONFIG.GRID_SIZE}
                stroke={theme === 'day' ? '#94a3b8' : '#475569'} strokeWidth="0.5" strokeDasharray="2,2" />
            ))}
          </g>
        )}
        
        {/* Agentes */}
        {agentPositions.map(({ x, y, agent }) => (
          <g key={agent.id} onMouseDown={(e) => handleMouseDown(e, String(agent.id), x, y)}
            style={{ cursor: isEditMode ? 'grab' : 'pointer', opacity: draggedAgent === String(agent.id) ? 0.7 : 1 }}>
            <AgentDesk agent={agent} x={x} y={y} isLead={agent.name?.toLowerCase().includes('lead')} onClick={() => {}} />
            {isEditMode && (
              <rect 
                x={x - (agent.name?.toLowerCase().includes('lead') ? 52 : 45)} 
                y={y - (agent.name?.toLowerCase().includes('lead') ? 52 : 45)} 
                width={agent.name?.toLowerCase().includes('lead') ? 104 : 90} 
                height={agent.name?.toLowerCase().includes('lead') ? 104 : 90} 
                fill="none"
                stroke={theme === 'day' ? '#3b82f6' : '#60a5fa'} 
                strokeWidth="2" 
                strokeDasharray="4,2" 
                rx="8"
                opacity={draggedAgent === String(agent.id) ? 1 : 0.5} 
              />
            )}
          </g>
        ))}
      </svg>

      {/* ========== FOOTER INFO ========== */}
      <div className="absolute bottom-3 left-3 flex items-center gap-3 px-4 py-2 rounded-xl border"
        style={{ 
          background: theme === 'day' ? 'rgba(255,255,255,0.95)' : 'rgba(9,14,26,0.95)', 
          borderColor: theme === 'day' ? '#cbd5e1' : '#1e3a6e',
        }}>
        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ 
          background: onlineCount === currentAgents.length ? '#3fb950' : onlineCount > 0 ? '#f0a500' : '#f85149'
        }} />
        <span className="text-xs" style={{ color: theme === 'day' ? '#475569' : '#8b949e' }}>
          <span className="font-semibold" style={{ color: theme === 'day' ? '#1e293b' : '#e6edf3' }}>
            {onlineCount}/{currentAgents.length}
          </span>
          <span className="ml-1">agents</span>
        </span>
        {offices.length > 1 && (
          <span className="text-xs px-2 py-0.5 rounded" 
            style={{ background: theme === 'day' ? '#e2e8f0' : '#1e293b', color: theme === 'day' ? '#64748b' : '#94a3b8' }}>
            Office {currentOffice + 1}/{offices.length}
          </span>
        )}
      </div>

      {/* Theme indicator */}
      <div className="absolute bottom-3 right-3 flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs"
        style={{ 
          background: theme === 'day' ? 'rgba(255,255,255,0.95)' : 'rgba(9,14,26,0.95)', 
          borderColor: theme === 'day' ? '#cbd5e1' : '#1e3a6e',
          color: theme === 'day' ? '#475569' : '#8b949e',
        }}>
        <span>{theme === 'day' ? '☀️' : theme === 'sunset' ? '🌅' : '🌙'}</span>
        <span className="capitalize">{theme} Mode</span>
      </div>

      {/* Reset button en modo edición */}
      {isEditMode && hasCustomPositions && (
        <button onClick={resetPositions}
          className="absolute bottom-3 left-1/2 transform -translate-x-1/2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
          style={{
            background: theme === 'day' ? 'rgba(239,68,68,0.1)' : 'rgba(239,68,68,0.2)',
            color: '#ef4444',
            border: `1px solid ${theme === 'day' ? '#fca5a5' : '#ef4444'}`,
          }}>
          Reset Positions
        </button>
      )}

      {/* Instrucciones modo edición */}
      {isEditMode && (
        <div className="absolute top-12 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg text-xs text-center pointer-events-none"
          style={{
            background: theme === 'day' ? 'rgba(59,130,246,0.1)' : 'rgba(59,130,246,0.2)',
            color: theme === 'day' ? '#1d4ed8' : '#60a5fa',
            border: `1px solid ${theme === 'day' ? '#93c5fd' : '#3b82f6'}`,
          }}>
          🖱️ Drag agents • Grid snap {OFFICE_CONFIG.GRID_SIZE}px
        </div>
      )}
    </div>
  );
}
