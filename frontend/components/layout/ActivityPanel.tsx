'use client';

import { useActivityStore } from '@/store/activity.store';
import { cn } from '@/lib/utils';
import { Pause, Play, Trash2, Radio } from 'lucide-react';

const severityColors = {
  info: { border: 'rgba(107, 124, 153, 0.3)', bg: 'rgba(107, 124, 153, 0.1)', color: '#8b949e' },
  success: { border: 'rgba(63, 185, 80, 0.3)', bg: 'rgba(63, 185, 80, 0.1)', color: '#3fb950' },
  warning: { border: 'rgba(240, 165, 0, 0.3)', bg: 'rgba(240, 165, 0, 0.1)', color: '#f0a500' },
  error: { border: 'rgba(248, 81, 73, 0.3)', bg: 'rgba(248, 81, 73, 0.1)', color: '#f85149' },
};

const severityIcons = {
  info: 'ℹ️',
  success: '✅',
  warning: '⚠️',
  error: '❌',
};

export function ActivityPanel() {
  const entries = useActivityStore((s) => s.entries);
  const isPaused = useActivityStore((s) => s.isPaused);
  const togglePause = useActivityStore((s) => s.togglePause);
  const clear = useActivityStore((s) => s.clear);

  return (
    <aside 
      className="w-80 flex flex-col border-l"
      style={{ 
        background: 'rgba(10, 15, 30, 0.8)',
        backdropFilter: 'blur(12px)',
        borderColor: 'rgba(255, 255, 255, 0.05)',
      }}
    >
      {/* Header */}
      <div 
        className="p-4 border-b flex items-center justify-between"
        style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}
      >
        <div className="flex items-center gap-2">
          <Radio 
            className="w-4 h-4" 
            style={{ color: isPaused ? '#6e7681' : '#3fb950' }}
          />
          <div>
            <h2 className="font-semibold text-sm" style={{ color: '#e6edf3' }}>Activity Log</h2>
            <p className="text-[10px]" style={{ color: isPaused ? '#f85149' : '#3fb950' }}>
              {isPaused ? '● PAUSED' : '● LIVE'}
            </p>
          </div>
        </div>
        <div className="flex gap-1">
          <button
            onClick={togglePause}
            className="p-2 rounded-lg transition-all hover:scale-105"
            style={{ 
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#8b949e',
            }}
            title={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          </button>
          <button
            onClick={clear}
            className="p-2 rounded-lg transition-all hover:scale-105"
            style={{ 
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#8b949e',
            }}
            title="Clear feed"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Activity List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {entries.length === 0 && (
          <div 
            className="text-center py-8 rounded-lg"
            style={{ 
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px dashed rgba(255, 255, 255, 0.1)',
            }}
          >
            <p className="text-sm" style={{ color: '#6e7681' }}>No activity yet...</p>
            <p className="text-xs mt-1" style={{ color: '#484f58' }}>Events will appear here</p>
          </div>
        )}
        
        {entries.map((entry) => {
          const colors = severityColors[entry.severity];
          return (
            <div
              key={entry.id}
              className="text-sm p-3 rounded-lg border transition-all hover:scale-[1.02]"
              style={{
                background: colors.bg,
                borderColor: colors.border,
              }}
            >
              <div className="flex items-start gap-2">
                <span className="text-lg">{severityIcons[entry.severity]}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-xs leading-relaxed" style={{ color: colors.color }}>
                    {entry.message}
                  </p>
                  {entry.agent_name && (
                    <p className="text-[10px] mt-1" style={{ color: '#6e7681' }}>
                      via <span style={{ color: '#8b949e' }}>{entry.agent_name}</span>
                    </p>
                  )}
                  <p className="text-[9px] mt-1 font-mono" style={{ color: '#484f58' }}>
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
