'use client';

import { Agent } from '@/types';

interface AgentDeskProps {
  agent: Agent;
  x: number;
  y: number;
  isSelected?: boolean;
  isLead?: boolean;
  onClick?: () => void;
}

const STATUS_CONFIG: Record<string, { color: string; glow: string; label: string }> = {
  IDLE:    { color: '#64748b', glow: 'rgba(100,116,139,0.3)', label: 'Idle' },
  idle:    { color: '#64748b', glow: 'rgba(100,116,139,0.3)', label: 'Idle' },
  WORKING: { color: '#10b981', glow: 'rgba(16,185,129,0.45)', label: 'Working' },
  busy:    { color: '#10b981', glow: 'rgba(16,185,129,0.45)', label: 'Working' },
  ERROR:   { color: '#f43f5e', glow: 'rgba(244,63,94,0.45)', label: 'Error' },
  OFFLINE: { color: '#374151', glow: 'rgba(55,65,81,0.2)', label: 'Offline' },
};

export function AgentDesk({ agent, x, y, isSelected, isLead, onClick }: AgentDeskProps) {
  const rawStatus = agent.status ?? 'IDLE';
  const status = STATUS_CONFIG[rawStatus] ?? STATUS_CONFIG['IDLE']!;
  const avatarColor =
    (agent.avatar_config as Record<string, string> | undefined)?.color_primary ?? '#6366f1';
  const initial = agent.name.charAt(0).toUpperCase();
  const isWorking = ['WORKING', 'busy'].includes(rawStatus);
  const isOffline = rawStatus === 'OFFLINE';

  const totalW = isLead ? 112 : 100;
  const avatarOuter = isLead ? 56 : 50;
  const avatarInner = isLead ? 48 : 42;
  const deskW = isLead ? 104 : 92;
  const deskH = isLead ? 40 : 34;

  return (
    <div
      onClick={onClick}
      className="hover:-translate-y-1 transition-transform duration-150"
      style={{
        position: 'absolute',
        left: x - totalW / 2,
        top: y - 78,
        width: totalW,
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 4,
        opacity: isOffline ? 0.45 : 1,
        transition: 'opacity 0.3s ease, transform 0.15s ease',
        userSelect: 'none',
      }}
    >
      {/* Working badge */}
      {isWorking && (
        <div
          className="animate-pulse"
          style={{
            fontSize: 8,
            padding: '2px 8px',
            borderRadius: 12,
            background: 'rgba(16,185,129,0.1)',
            border: '1px solid rgba(16,185,129,0.45)',
            color: '#10b981',
            letterSpacing: '0.1em',
            fontWeight: 700,
            fontFamily: 'system-ui, sans-serif',
            whiteSpace: 'nowrap',
          }}
        >
          ● ACTIVE
        </div>
      )}

      {/* Lead crown */}
      {isLead && !isWorking && (
        <div
          style={{
            fontSize: 14,
            lineHeight: 1,
            filter: 'drop-shadow(0 0 8px rgba(245,158,11,0.9))',
          }}
        >
          👑
        </div>
      )}

      {/* Avatar */}
      <div style={{ position: 'relative', flexShrink: 0 }}>
        {/* Animated ping ring for working agents */}
        {isWorking && (
          <div
            className="animate-ping"
            style={{
              position: 'absolute',
              inset: -5,
              borderRadius: '50%',
              border: `1.5px solid ${status.color}`,
              opacity: 0.4,
            }}
          />
        )}

        {/* Gradient ring */}
        <div
          style={{
            width: avatarOuter,
            height: avatarOuter,
            borderRadius: '50%',
            padding: 2,
            background: isSelected
              ? 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%)'
              : isLead
              ? `linear-gradient(135deg, ${avatarColor}, ${avatarColor}aa)`
              : `linear-gradient(135deg, ${avatarColor}88, ${avatarColor}33)`,
            boxShadow: isSelected
              ? `0 0 20px rgba(99,102,241,0.55), 0 0 40px rgba(99,102,241,0.2)`
              : isLead
              ? `0 0 18px ${avatarColor}55`
              : `0 0 10px ${avatarColor}28`,
          }}
        >
          {/* Inner circle */}
          <div
            style={{
              width: avatarInner,
              height: avatarInner,
              borderRadius: '50%',
              background: `radial-gradient(circle at 35% 35%, ${avatarColor}ee, ${avatarColor}99)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: isLead ? 20 : 17,
              fontWeight: 800,
              color: '#fff',
              textShadow: '0 1px 4px rgba(0,0,0,0.5)',
              letterSpacing: '-0.02em',
              fontFamily: 'system-ui, -apple-system, sans-serif',
            }}
          >
            {initial}
          </div>
        </div>

        {/* Status dot */}
        <div
          style={{
            position: 'absolute',
            bottom: 2,
            right: 2,
            width: 13,
            height: 13,
            borderRadius: '50%',
            background: status.color,
            border: '2px solid #060912',
            boxShadow: `0 0 8px ${status.glow}`,
          }}
        />
      </div>

      {/* Desk */}
      <div style={{ position: 'relative', width: deskW }}>
        {/* Top highlight edge */}
        <div
          style={{
            height: 1,
            background: `linear-gradient(90deg, transparent, ${
              isSelected ? '#6366f155' : '#1e2d4060'
            }, transparent)`,
          }}
        />

        {/* Desk surface */}
        <div
          style={{
            width: deskW,
            height: deskH,
            background: isSelected
              ? 'linear-gradient(180deg, #1a1b3d 0%, #10132a 100%)'
              : 'linear-gradient(180deg, #131926 0%, #0d1117 100%)',
            border: `1px solid ${isSelected ? '#6366f14a' : '#1a2535'}`,
            borderTop: `1px solid ${isSelected ? '#6366f130' : '#1e2d4080'}`,
            borderRadius: '6px 6px 0 0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 5,
            position: 'relative',
            overflow: 'hidden',
            boxShadow: isSelected
              ? `0 0 0 1px #6366f122, 0 6px 20px rgba(0,0,0,0.6), 0 0 24px rgba(99,102,241,0.12)`
              : '0 4px 14px rgba(0,0,0,0.55)',
          }}
        >
          {/* Working ambient glow strip at top of desk */}
          {isWorking && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 1,
                background: `linear-gradient(90deg, transparent, ${avatarColor}70, transparent)`,
              }}
            />
          )}

          {/* Monitor */}
          <div
            style={{
              width: isLead ? 42 : 36,
              height: isLead ? 28 : 23,
              background: isWorking ? 'linear-gradient(135deg, #081830, #04111f)' : '#050810',
              borderRadius: 3,
              position: 'relative',
              overflow: 'hidden',
              boxShadow: isWorking
                ? `0 0 14px ${avatarColor}38, 0 0 28px ${avatarColor}12, inset 0 0 6px rgba(99,102,241,0.06)`
                : '0 0 4px rgba(0,0,0,0.6)',
              border: `1px solid ${isWorking ? avatarColor + '35' : '#0f1a2a'}`,
            }}
          >
            {isWorking && (
              <>
                {/* Simulated code lines */}
                <div
                  style={{
                    position: 'absolute',
                    top: 4,
                    left: 4,
                    right: 4,
                    height: 1.5,
                    background: `${avatarColor}cc`,
                    borderRadius: 1,
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: 8,
                    left: 4,
                    right: 8,
                    height: 1,
                    background: '#1e4068',
                    borderRadius: 1,
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: 11,
                    left: 4,
                    right: 10,
                    height: 1,
                    background: '#1e3558',
                    borderRadius: 1,
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: 14,
                    left: 4,
                    right: 12,
                    height: 1,
                    background: '#162a40',
                    borderRadius: 1,
                  }}
                />
              </>
            )}
            {/* Screen glare */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '40%',
                height: '35%',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '0 0 100% 0',
              }}
            />
          </div>

          {/* Keyboard */}
          <div
            style={{
              width: isLead ? 28 : 23,
              height: isLead ? 10 : 9,
              background: '#070c14',
              borderRadius: 2,
              border: '1px solid #0f1a2a',
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gridTemplateRows: 'repeat(2, 1fr)',
              gap: 1.5,
              padding: 2,
              boxSizing: 'border-box',
            }}
          >
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                style={{
                  background: isWorking ? '#0d2040' : '#0a1225',
                  borderRadius: 0.5,
                }}
              />
            ))}
          </div>
        </div>

        {/* Desk front depth panel */}
        <div
          style={{
            width: deskW - 6,
            marginLeft: 3,
            height: 7,
            background: 'linear-gradient(180deg, #080b14, #040710)',
            borderRadius: '0 0 5px 5px',
            borderLeft: '1px solid #0d1628',
            borderRight: '1px solid #0d1628',
            borderBottom: '1px solid #0d1628',
          }}
        />
      </div>

      {/* Nameplate */}
      <div
        style={{
          background: 'rgba(6,9,18,0.88)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          border: `1px solid ${isSelected ? '#6366f130' : '#1a253566'}`,
          borderRadius: 7,
          padding: '3px 10px 4px',
          textAlign: 'center',
          maxWidth: deskW,
          boxShadow: isSelected ? '0 0 14px rgba(99,102,241,0.12)' : '0 2px 8px rgba(0,0,0,0.4)',
        }}
      >
        <div
          style={{
            fontSize: isLead ? 11 : 10,
            fontWeight: 700,
            color: isSelected ? '#a5b4fc' : '#c9d1dc',
            letterSpacing: '0.04em',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            maxWidth: deskW - 20,
          }}
        >
          {agent.name}
        </div>
        <div
          style={{
            fontSize: 8,
            color: status.color,
            letterSpacing: '0.1em',
            fontWeight: 600,
            marginTop: 1,
            fontFamily: 'system-ui, -apple-system, sans-serif',
          }}
        >
          {status.label.toUpperCase()}
        </div>
      </div>
    </div>
  );
}
