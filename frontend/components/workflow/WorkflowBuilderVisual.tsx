'use client';

import { useState } from 'react';
import { Play, Plus, Search, Settings2, ShieldAlert, FileText, Database, Check } from 'lucide-react';

export function WorkflowBuilderVisual() {
  const [activeNode, setActiveNode] = useState<number | null>(1);

  const nodes = [
    { id: 1, type: 'trigger', x: 50, y: 150, title: 'User Input', icon: <Search className="w-5 h-5 text-indigo-400" />, status: 'completed' },
    { id: 2, type: 'agent', x: 300, y: 150, title: 'Planner Agent', icon: <Database className="w-5 h-5 text-blue-400" />, status: 'active' },
    { id: 3, type: 'agent', x: 550, y: 50, title: 'Coder Agent', icon: <FileText className="w-5 h-5 text-emerald-400" />, status: 'pending' },
    { id: 4, type: 'agent', x: 550, y: 250, title: 'Reviewer Agent', icon: <ShieldAlert className="w-5 h-5 text-rose-400" />, status: 'pending' },
    { id: 5, type: 'output', x: 800, y: 150, title: 'Final Review', icon: <Check className="w-5 h-5 text-amber-400" />, status: 'pending' },
  ];

  const edges = [
    { from: 1, to: 2, animated: true },
    { from: 2, to: 3, animated: true },
    { from: 2, to: 4, animated: false },
    { from: 3, to: 5, animated: false },
    { from: 4, to: 5, animated: false },
  ];

  return (
    <div className="w-full h-full relative bg-slate-950 flex">
      {/* Sidebar Tooling */}
      <div className="w-72 bg-slate-900/50 backdrop-blur-md border-r border-white/10 flex flex-col z-20">
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <h2 className="text-white font-semibold">Nodes</h2>
          <button className="p-1.5 bg-blue-600/20 text-blue-400 rounded-md hover:bg-blue-600/40 transition-colors">
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="p-4 flex-1 overflow-y-auto space-y-3">
          {/* Draggable templates */}
          <div className="p-3 bg-slate-800/50 border border-slate-700/50 rounded-xl cursor-grab hover:border-blue-500/50 transition-colors flex items-center gap-3">
            <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-lg"><Search className="w-4 h-4" /></div>
            <div><p className="text-sm text-white font-medium">Input Trigger</p><p className="text-xs text-slate-400">Webhook / Msg.</p></div>
          </div>
          <div className="p-3 bg-slate-800/50 border border-slate-700/50 rounded-xl cursor-grab hover:border-blue-500/50 transition-colors flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg"><Database className="w-4 h-4" /></div>
            <div><p className="text-sm text-white font-medium">LLM Task</p><p className="text-xs text-slate-400">Prompt execution</p></div>
          </div>
          <div className="p-3 bg-slate-800/50 border border-slate-700/50 rounded-xl cursor-grab hover:border-blue-500/50 transition-colors flex items-center gap-3">
            <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-lg"><Check className="w-4 h-4" /></div>
            <div><p className="text-sm text-white font-medium">Conditional</p><p className="text-xs text-slate-400">If/Else routing</p></div>
          </div>
        </div>
        <div className="p-4 border-t border-white/5 bg-slate-900 shadow-[0_-10px_30px_rgba(0,0,0,0.5)]">
          <button className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg flex justify-center items-center gap-2 font-medium shadow-[0_0_15px_rgba(37,99,235,0.4)] transition-all">
            <Play className="w-4 h-4 fill-current" />
            Run Workflow
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 relative overflow-hidden bg-[url('/grid-bg.svg')] bg-[length:40px_40px] bg-center shadow-inner" style={{ backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)' }}>
        
        {/* SVG Edges */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
          <defs>
            <linearGradient id="edge-active" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgb(59, 130, 246)" stopOpacity="0.2" />
              <stop offset="100%" stopColor="rgb(59, 130, 246)" stopOpacity="1" />
            </linearGradient>
          </defs>
          {edges.map((edge, i) => {
            const start = nodes.find(n => n.id === edge.from)!;
            const end = nodes.find(n => n.id === edge.to)!;
            const path = `M ${start.x + 200} ${start.y + 40} C ${start.x + 240} ${start.y + 40}, ${end.x - 40} ${end.y + 40}, ${end.x} ${end.y + 40}`;
            
            return (
              <g key={i}>
                <path d={path} fill="none" strokeWidth="3" stroke={edge.animated ? "url(#edge-active)" : "rgba(255,255,255,0.1)"} className="transition-all duration-500" />
                {edge.animated && (
                  <circle r="4" fill="rgb(96, 165, 250)">
                    <animateMotion dur="2s" repeatCount="indefinite" path={path} />
                  </circle>
                )}
              </g>
            );
          })}
        </svg>

        {/* Nodes */}
        {nodes.map(node => (
          <div 
            key={node.id}
            onClick={() => setActiveNode(node.id)}
            className={`absolute w-[200px] bg-slate-900/90 backdrop-blur-xl border rounded-2xl p-4 cursor-pointer transition-all duration-300 z-10
              ${activeNode === node.id ? 'border-blue-500 shadow-[0_0_30px_rgba(59,130,246,0.3)] scale-105' : 'border-white/10 hover:border-white/20'}`}
            style={{ left: node.x, top: node.y }}
          >
            {node.status === 'active' && (
              <div className="absolute -inset-1 rounded-2xl border border-blue-400/50 animate-pulse pointer-events-none" />
            )}
            <div className="flex justify-between items-center mb-3">
              <div className={`p-2 rounded-xl ${node.status === 'active' ? 'bg-blue-500/20' : 'bg-slate-800'}`}>
                {node.icon}
              </div>
              <Settings2 className="w-4 h-4 text-slate-500 hover:text-white transition-colors" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">{node.title}</h3>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              {node.status === 'completed' && <span className="text-emerald-400">Completed</span>}
              {node.status === 'active' && <span className="text-blue-400 animate-pulse">Running...</span>}
              {node.status === 'pending' && <span className="text-slate-500">Pending</span>}
            </p>

            {/* In/Out Connectors */}
            <div className="absolute -left-3 top-1/2 -translate-y-1/2 w-3 h-6 bg-slate-800 border-y border-r border-white/20 rounded-r-md flex items-center justify-center">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-500" />
            </div>
            <div className="absolute -right-3 top-1/2 -translate-y-1/2 w-3 h-6 bg-slate-800 border-y border-l border-white/20 rounded-l-md flex items-center justify-center">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
