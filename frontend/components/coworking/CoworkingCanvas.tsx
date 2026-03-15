'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useAgentsStore } from '@/store/agents.store';
import { useAppStore } from '@/store/app.store';

// Dynamically import Konva components to avoid SSR issues
const Stage = dynamic(() => import('react-konva').then(mod => mod.Stage), { ssr: false });
const Layer = dynamic(() => import('react-konva').then(mod => mod.Layer), { ssr: false });

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

// Simple desk component using HTML instead of Konva for now
function AgentDeskHTML({ agent, x, y, isSelected, onClick }: AgentDeskProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'WORKING': return '#10b981';
      case 'ERROR': return '#ef4444';
      case 'IDLE': return '#64748b';
      default: return '#64748b';
    }
  };

  return (
    <div
      onClick={onClick}
      style={{
        position: 'absolute',
        left: x - 40,
        top: y - 30,
        width: 80,
        height: 60,
        backgroundColor: '#1e293b',
        border: isSelected ? '3px solid #3b82f6' : '1px solid #334155',
        borderRadius: 8,
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
      }}
    >
      <div style={{
        width: 36,
        height: 36,
        borderRadius: '50%',
        backgroundColor: '#3b82f6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 16,
        fontWeight: 'bold',
        color: 'white',
        marginBottom: 4,
      }}>
        {agent.name.charAt(0).toUpperCase()}
      </div>
      <div style={{
        width: 8,
        height: 8,
        borderRadius: '50%',
        backgroundColor: getStatusColor(agent.status),
        position: 'absolute',
        bottom: 8,
        right: 8,
      }} />
    </div>
  );
}

export function CoworkingCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedAgent, setSelectedAgent] = useState<string | number | null>(null);
  const [isMounted, setIsMounted] = useState(false);
  
  const agents = useAgentsStore((s) => Object.values(s.agents));
  const isConnected = useAppStore((s) => s.isConnected);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    
    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  }, []);

  const getDeskPositions = useCallback(() => {
    const cols = Math.max(1, Math.ceil(Math.sqrt(agents.length)));
    const cellW = dimensions.width / (cols + 1);
    const cellH = dimensions.height / Math.max(1, Math.ceil(agents.length / cols) + 1);
    
    return agents.map((agent, i) => ({
      agent,
      x: cellW * ((i % cols) + 1),
      y: cellH * (Math.floor(i / cols) + 1),
    }));
  }, [agents, dimensions]);

  if (!isMounted) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100%' 
      }}>
        Loading office...
      </div>
    );
  }

  const deskPositions = getDeskPositions();
  const selectedAgentData = selectedAgent ? agents.find(a => a.id === selectedAgent) : null;

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        backgroundColor: '#0f172a',
        overflow: 'hidden',
      }}
    >
      {/* Connection Status */}
      <div style={{
        position: 'absolute',
        top: 16,
        left: 16,
        zIndex: 10,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 12px',
        backgroundColor: 'rgba(30, 41, 59, 0.8)',
        backdropFilter: 'blur(4px)',
        borderRadius: 16,
        border: '1px solid #334155',
      }}>
        <span style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: isConnected ? '#10b981' : '#ef4444',
          animation: isConnected ? 'pulse 2s infinite' : 'none',
        }} />
        <span style={{ fontSize: 12, color: '#cbd5e1' }}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Agent Count */}
      <div style={{
        position: 'absolute',
        top: 16,
        right: 16,
        zIndex: 10,
        padding: '6px 12px',
        backgroundColor: 'rgba(30, 41, 59, 0.8)',
        backdropFilter: 'blur(4px)',
        borderRadius: 16,
        border: '1px solid #334155',
        fontSize: 12,
        color: '#cbd5e1',
      }}>
        {agents.length} agent{agents.length !== 1 ? 's' : ''} online
      </div>

      {/* Agent Desks */}
      {deskPositions.map(({ agent, x, y }) => (
        <AgentDeskHTML
          key={agent.id}
          agent={agent}
          x={x}
          y={y}
          isSelected={selectedAgent === agent.id}
          onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
        />
      ))}

      {/* Agent Detail Panel */}
      {selectedAgentData && (
        <div style={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          width: 300,
          backgroundColor: '#0f172a',
          border: '1px solid #334155',
          borderRadius: 12,
          padding: 16,
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          zIndex: 20,
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 16,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                backgroundColor: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
                fontWeight: 'bold',
                color: 'white',
              }}>
                {selectedAgentData.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{selectedAgentData.name}</h3>
                <p style={{ margin: 0, fontSize: 12, color: '#64748b' }}>{selectedAgentData.status}</p>
              </div>
            </div>
            <button
              onClick={() => setSelectedAgent(null)}
              style={{
                background: 'none',
                border: 'none',
                color: '#64748b',
                cursor: 'pointer',
                fontSize: 18,
              }}
            >
              ✕
            </button>
          </div>
          
          <div style={{ fontSize: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#64748b' }}>Domain:</span>
              <span>{selectedAgentData.domain || 'N/A'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#64748b' }}>Status:</span>
              <span style={{
                color: selectedAgentData.status === 'WORKING' ? '#4ade80' : 
                       selectedAgentData.status === 'ERROR' ? '#f87171' : '#94a3b8'
              }}>
                {selectedAgentData.status}
              </span>
            </div>
            {selectedAgentData.current_task_id && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Current Task:</span>
                <span style={{ color: '#60a5fa', maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {selectedAgentData.current_task_id}
                </span>
              </div>
            )}
          </div>
          
          <div style={{
            marginTop: 16,
            paddingTop: 16,
            borderTop: '1px solid #1e293b',
            display: 'flex',
            gap: 8,
          }}>
            <button style={{
              flex: 1,
              padding: '8px 0',
              backgroundColor: '#1e293b',
              border: 'none',
              borderRadius: 8,
              color: '#f1f5f9',
              cursor: 'pointer',
              fontSize: 14,
            }}>
              Assign Task
            </button>
            <button style={{
              flex: 1,
              padding: '8px 0',
              backgroundColor: '#3b82f6',
              border: 'none',
              borderRadius: 8,
              color: 'white',
              cursor: 'pointer',
              fontSize: 14,
            }}>
              Chat
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
