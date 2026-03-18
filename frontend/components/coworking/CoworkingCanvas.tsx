'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useAgentsStore } from '@/store/agents.store';
import { useAppStore } from '@/store/app.store';
import { Cpu, Terminal, Sparkles, MessageSquare, Zap, CheckCircle2, Clock, Network } from 'lucide-react';

interface LocalAgent {
  id: string | number;
  name: string;
  status: string;
  domain?: string;
  current_task_id?: string | null;
}

interface AgentDeskProps {
  agent: LocalAgent;
  x: number;
  y: number;
  isSelected: boolean;
  onClick: () => void;
}

function AgentDeskAnimated({ agent, x, y, isSelected, onClick }: AgentDeskProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'WORKING': return 'rgb(59, 130, 246)'; // Blue
      case 'ERROR': return 'rgb(239, 68, 68)';    // Red
      case 'IDLE': return 'rgb(100, 116, 139)';   // Slate
      case 'DONE': return 'rgb(34, 197, 94)';     // Green
      default: return 'rgb(100, 116, 139)';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'WORKING': return <Cpu className="w-4 h-4 text-blue-400 animate-pulse" />;
      case 'ERROR': return <Terminal className="w-4 h-4 text-red-400" />;
      case 'IDLE': return <Clock className="w-4 h-4 text-slate-400" />;
      case 'DONE': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      default: return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const color = getStatusColor(agent.status);
  const isWorking = agent.status === 'WORKING';

  return (
    <div
      onClick={onClick}
      className={`absolute transition-all duration-300 hover:z-20 cursor-pointer group`}
      style={{
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${isSelected ? 1.05 : 1})`,
      }}
    >
      {/* Glow Effect / Desk Aura */}
      <div 
        className="absolute inset-0 rounded-[2rem] blur-xl opacity-0 group-hover:opacity-40 transition-opacity duration-500"
        style={{ backgroundColor: color }}
      />
      {isSelected && (
        <div 
          className="absolute inset-0 rounded-[2rem] blur-xl opacity-30 animate-pulse"
          style={{ backgroundColor: color }}
        />
      )}

      {/* Main Desk Container */}
      <div 
        className={`relative w-[180px] p-4 bg-slate-900/80 backdrop-blur-md border rounded-[2rem] shadow-2xl flex flex-col items-center transition-all duration-300
          ${isSelected ? 'border-white/30 shadow-[0_0_30px_rgba(0,0,0,0.5)]' : 'border-white/10 hover:border-white/20'}`}
      >
        {/* Animated Avatar */}
        <div className="relative mb-3">
          <div className="w-16 h-16 rounded-full flex items-center justify-center relative z-10 overflow-hidden bg-slate-800 border-2 border-white/10">
            {/* Sprite gradient background */}
            <div 
              className="absolute inset-0 opacity-50"
              style={{
                background: `radial-gradient(circle at top left, ${color}, transparent)`
              }}
            />
            {/* Initial */}
            <span className="text-2xl font-bold text-white z-10 tracking-wider">
              {agent.name.substring(0, 2).toUpperCase()}
            </span>
          </div>
          
          {/* Orbital rings */}
          {isWorking && (
            <>
              <div className="absolute inset-[-4px] rounded-full border border-dashed border-blue-400/50 animate-[spin_4s_linear_infinite]" />
              <div className="absolute inset-[-8px] rounded-full border border-dashed border-blue-500/30 animate-[spin_6s_linear_infinite_reverse]" />
            </>
          )}

          {/* Status Badge Indicator */}
          <div 
            className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center border-2 border-slate-900 z-20 shadow-lg"
            style={{ backgroundColor: 'rgba(15, 23, 42, 0.9)' }}
          >
            {getStatusIcon(agent.status)}
          </div>
        </div>

        {/* Info */}
        <h3 className="text-sm font-semibold text-slate-100 truncate w-full text-center">
          {agent.name}
        </h3>
        <span 
          className="text-xs font-medium uppercase tracking-wider mt-1 px-2 py-0.5 rounded-full border"
          style={{ 
            color: color, 
            borderColor: `${color.replace('rgb', 'rgba').replace(')', ', 0.3)')}`,
            backgroundColor: `${color.replace('rgb', 'rgba').replace(')', ', 0.1)')}` 
          }}
        >
          {agent.status}
        </span>
        
        {/* Current Task Ping */}
        {agent.current_task_id && (
          <div className="absolute -top-2 -right-2">
            <span className="relative flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-4 w-4 bg-blue-500 border-2 border-slate-900"></span>
            </span>
          </div>
        )}
      </div>

      {/* Floating Sparkles when working */}
      {isWorking && (
        <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-blue-400 animate-bounce">
          <Sparkles className="w-5 h-5 opacity-70" />
        </div>
      )}
    </div>
  );
}

export function CoworkingCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [selectedAgent, setSelectedAgent] = useState<string | number | null>(null);
  
  const agents = useAgentsStore((s) => Object.values(s.agents));
  const isConnected = useAppStore((s) => s.isConnected);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    updateDimensions();
    // small delay to ensure container is fully rendered in flex box
    const timeout = setTimeout(updateDimensions, 100);
    window.addEventListener('resize', updateDimensions);
    
    return () => {
      clearTimeout(timeout);
      window.removeEventListener('resize', updateDimensions);
    };
  }, []);

  const getDeskPositions = useCallback(() => {
    if (dimensions.width === 0) return [];
    
    // Create a beautiful staggered grid / hexagonal-like layout
    // instead of a boring square grid.
    const nodes = agents.length;
    if (nodes === 0) return [];

    const cols = Math.max(1, Math.ceil(Math.sqrt(nodes)));
    const rows = Math.ceil(nodes / cols);
    
    // Margins to not clip elements
    const paddingX = 150;
    const paddingY = 150;
    
    const usableWidth = dimensions.width - paddingX * 2;
    const usableHeight = dimensions.height - paddingY * 2;

    const cellW = usableWidth / Math.max(1, cols - 1);
    const cellH = usableHeight / Math.max(1, rows - 1);
    
    return agents.map((agent, i) => {
      const c = i % cols;
      const r = Math.floor(i / cols);
      
      // Stagger odd rows
      const xOffset = (r % 2 !== 0 && cols > 1) ? cellW / 2 : 0;
      
      const baseX = nodes === 1 ? dimensions.width / 2 : paddingX + (c * cellW) + xOffset;
      const baseY = nodes === 1 ? dimensions.height / 2 : paddingY + (r * cellH);
      
      // Prevent off-screen pushing due to stagger
      const finalX = Math.min(Math.max(baseX, paddingX), dimensions.width - paddingX);

      return {
        agent,
        x: finalX,
        y: baseY,
      };
    });
  }, [agents, dimensions]);

  if (dimensions.width === 0) return null;

  const positions = getDeskPositions();
  const selectedAgentData = selectedAgent ? agents.find(a => a.id === selectedAgent) : null;

  return (
    <div
      ref={containerRef}
      className="w-full h-full relative bg-[url('/grid-bg.svg')] bg-center bg-repeat"
      style={{
        backgroundSize: '40px 40px',
        backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)'
      }}
    >
      {/* Top HUD */}
      <div className="absolute top-6 flex justify-between w-full px-6 pointer-events-none z-10">
        <div className="flex items-center gap-3 px-4 py-2 bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-full shadow-lg">
          <div className="relative flex h-3 w-3">
            {isConnected && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
            <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            {isConnected ? 'Core Online' : 'Core Offline'}
          </span>
        </div>

        <div className="flex items-center gap-3 px-4 py-2 bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-full shadow-lg">
          <Network className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            {agents.length} Active Node{agents.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Agents Rendering */}
      {positions.map(({ agent, x, y }) => (
        <AgentDeskAnimated
          key={agent.id}
          agent={agent}
          x={x}
          y={y}
          isSelected={selectedAgent === agent.id}
          onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
        />
      ))}

      {/* Selected Agent Inspector */}
      {selectedAgentData && (
        <div className="absolute right-6 bottom-6 w-96 bg-slate-900/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] p-6 z-30 animate-in slide-in-from-right-8 fade-in duration-300">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-600/20 border border-blue-500/50 flex items-center justify-center">
                <span className="text-xl font-bold text-blue-400">
                  {selectedAgentData.name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white leading-tight">{selectedAgentData.name}</h3>
                <p className="text-sm text-slate-400 mt-1 uppercase tracking-wider font-semibold">
                  {selectedAgentData.domain || 'General Purpose'}
                </p>
              </div>
            </div>
            <button 
              onClick={() => setSelectedAgent(null)}
              className="p-1 rounded-full hover:bg-white/10 text-slate-400 transition-colors"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>

          <div className="space-y-4 mb-8">
            <div className="bg-slate-800/50 rounded-lg p-3 border border-white/5 flex justify-between items-center">
              <span className="text-xs text-slate-400 uppercase font-semibold">Status</span>
              <span className={`text-sm font-medium ${selectedAgentData.status === 'WORKING' ? 'text-blue-400' : 'text-slate-300'}`}>
                {selectedAgentData.status}
              </span>
            </div>
            
            {selectedAgentData.current_task_id ? (
              <div className="bg-blue-900/20 rounded-lg p-3 border border-blue-500/20">
                <span className="text-xs text-blue-300/70 uppercase font-semibold block mb-1">Active Task</span>
                <span className="text-sm text-blue-300 font-mono break-all line-clamp-2">
                  {selectedAgentData.current_task_id}
                </span>
              </div>
            ) : (
              <div className="bg-slate-800/50 rounded-lg p-3 border border-white/5">
                <span className="text-xs text-slate-400 uppercase font-semibold block mb-1">Active Task</span>
                <span className="text-sm text-slate-500 italic">No task assigned</span>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <button className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl py-3 text-sm font-semibold transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:shadow-[0_0_30px_rgba(37,99,235,0.5)]">
              <Zap className="w-4 h-4" />
              Assign Task
            </button>
            <button className="flex-1 flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white rounded-xl py-3 text-sm font-semibold transition-all">
              <MessageSquare className="w-4 h-4" />
              Direct Chat
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
