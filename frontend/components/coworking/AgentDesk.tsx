'use client';

import { Group, Rect, Circle, Text } from 'react-konva';
import { Agent } from '@/types';

interface AgentDeskProps {
  agent: Agent;
  x: number;
  y: number;
  isSelected?: boolean;
  isLead?: boolean;
  onClick?: () => void;
}

const STATUS_COLORS = {
  IDLE: '#64748b',
  WORKING: '#10b981',
  ERROR: '#ef4444',
  OFFLINE: '#374151',
};

export function AgentDesk({ agent, x, y, isSelected, isLead, onClick }: AgentDeskProps) {
  const statusColor = STATUS_COLORS[agent.status as keyof typeof STATUS_COLORS] || '#64748b';
  const initial = agent.name.charAt(0).toUpperCase();
  
  // Get color from avatar_config or default
  const avatarColor = agent.avatar_config?.color_primary || '#3b82f6';
  
  return (
    <Group x={x} y={y} onClick={onClick} onTap={onClick} cursor="pointer">
      {/* Desk */}
      <Rect
        x={-40}
        y={-30}
        width={80}
        height={60}
        fill="#1e293b"
        stroke={isSelected ? '#3b82f6' : '#334155'}
        strokeWidth={isSelected ? 3 : 1}
        cornerRadius={8}
        shadowColor="black"
        shadowBlur={5}
        shadowOpacity={0.3}
      />
      
      {/* Computer */}
      <Rect
        x={-15}
        y={-25}
        width={30}
        height={20}
        fill="#0f172a"
        cornerRadius={2}
      />
      
      {/* Screen glow when working */}
      {agent.status === 'WORKING' && (
        <Rect
          x={-13}
          y={-23}
          width={26}
          height={16}
          fill="#3b82f6"
          opacity={0.3 + Math.sin(Date.now() / 500) * 0.2}
          cornerRadius={2}
        />
      )}
      
      {/* Agent Avatar */}
      <Circle
        x={0}
        y={5}
        radius={18}
        fill={avatarColor}
        stroke="#1e293b"
        strokeWidth={3}
      />
      
      {/* Initial */}
      <Text
        text={initial}
        fontSize={16}
        fontStyle="bold"
        fill="white"
        align="center"
        verticalAlign="middle"
        x={-10}
        y={-3}
        width={20}
        height={20}
      />
      
      {/* Status Indicator */}
      <Circle
        x={12}
        y={18}
        radius={6}
        fill={statusColor}
        stroke="#1e293b"
        strokeWidth={2}
      />
      
      {/* Name Label */}
      <Text
        text={agent.name}
        fontSize={11}
        fontStyle="bold"
        fill="#e2e8f0"
        align="center"
        x={-40}
        y={38}
        width={80}
      />
      
      {/* Status Label */}
      <Text
        text={agent.status}
        fontSize={9}
        fill={statusColor}
        align="center"
        x={-40}
        y={50}
        width={80}
      />
      
      {/* Current Task */}
      {agent.current_task_id && (
        <Rect
          x={-35}
          y={-55}
          width={70}
          height={18}
          fill="rgba(16, 185, 129, 0.2)"
          stroke="rgba(16, 185, 129, 0.5)"
          strokeWidth={1}
          cornerRadius={4}
        />
      )}
    </Group>
  );
}
