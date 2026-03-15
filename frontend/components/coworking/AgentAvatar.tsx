'use client';

import { useState, useEffect, useRef } from 'react';
import { Group, Circle, Text, Rect } from 'react-konva';
import { Agent } from '@/types';
import { generateAgentSprite } from './AgentSprite';

interface AgentAvatarProps {
  agent: Agent;
  x: number;
  y: number;
  scale: number;
  isSelected?: boolean;
  onClick?: () => void;
}

export function AgentAvatar({
  agent,
  x,
  y,
  scale,
  isSelected,
  onClick,
}: AgentAvatarProps) {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [bounceY, setBounceY] = useState(0);
  const [glowOpacity, setGlowOpacity] = useState(0.3);
  const animationRef = useRef<number>();

  // Generate avatar on mount
  useEffect(() => {
    const img = new Image();
    img.src = generateAgentSprite(agent);
    img.onload = () => setImage(img);
  }, [agent]);

  // Idle/working animation
  useEffect(() => {
    let startTime = Date.now();
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      
      if (agent.state === 'working') {
        // Working: faster bounce
        const bounce = Math.sin(elapsed / 200) * 3;
        setBounceY(bounce);
        
        // Pulsing glow
        const glow = 0.3 + Math.sin(elapsed / 500) * 0.2;
        setGlowOpacity(glow);
      } else if (agent.state === 'thinking') {
        // Thinking: slower, more subtle bounce
        const bounce = Math.sin(elapsed / 400) * 1.5;
        setBounceY(bounce);
        setGlowOpacity(0.2);
      } else if (agent.state === 'talking') {
        // Talking: irregular bounce
        const bounce = Math.sin(elapsed / 150) * 2;
        setBounceY(bounce);
        setGlowOpacity(0.4);
      } else {
        // Idle: very subtle breathing effect
        const bounce = Math.sin(elapsed / 1000) * 0.5;
        setBounceY(bounce);
        setGlowOpacity(0.15);
      }
      
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [agent.state]);

  const getStatusColor = () => {
    switch (agent.state) {
      case 'working': return '#10b981'; // green
      case 'thinking': return '#f59e0b'; // amber
      case 'talking': return '#3b82f6'; // blue
      case 'idle': return '#64748b'; // slate
      default: return '#64748b';
    }
  };

  const getStatusGlow = () => {
    switch (agent.state) {
      case 'working': return `rgba(16, 185, 129, ${glowOpacity})`;
      case 'thinking': return `rgba(245, 158, 11, ${glowOpacity})`;
      case 'talking': return `rgba(59, 130, 246, ${glowOpacity})`;
      case 'idle': return `rgba(100, 116, 139, ${glowOpacity})`;
      default: return `rgba(100, 116, 139, ${glowOpacity})`;
    }
  };

  const avatarSize = 50 * scale;

  return (
    <Group
      x={x}
      y={y + bounceY}
      onClick={onClick}
      onTap={onClick}
      cursor="pointer"
    >
      {/* Selection Ring */}
      {isSelected && (
        <Circle
          x={0}
          y={0}
          radius={avatarSize / 2 + 6}
          fill="rgba(59, 130, 246, 0.2)"
          stroke="#3b82f6"
          strokeWidth={3}
          shadowColor="#3b82f6"
          shadowBlur={15}
          shadowOpacity={0.5}
        />
      )}

      {/* Status Glow */}
      <Circle
        x={0}
        y={0}
        radius={avatarSize / 2 + 4}
        fill={getStatusGlow()}
      />

      {/* Avatar Image */}
      {image && (
        <Rect
          x={-avatarSize / 2}
          y={-avatarSize / 2}
          width={avatarSize}
          height={avatarSize}
          fillPatternImage={image}
          fillPatternScale={{
            x: avatarSize / 100,
            y: avatarSize / 100,
          }}
          cornerRadius={avatarSize / 2}
          shadowColor="black"
          shadowBlur={10}
          shadowOpacity={0.4}
          shadowOffsetY={3}
        />
      )}

      {/* Status Indicator */}
      <Circle
        x={avatarSize / 2 - 8}
        y={avatarSize / 2 - 8}
        radius={7}
        fill={getStatusColor()}
        stroke="#1e293b"
        strokeWidth={2}
        shadowColor={getStatusColor()}
        shadowBlur={8}
        shadowOpacity={0.6}
      />

      {/* Agent Name Label */}
      <Group y={avatarSize / 2 + 12}>
        <Rect
          x={-60}
          y={-10}
          width={120}
          height={22}
          fill="rgba(15, 23, 42, 0.9)"
          cornerRadius={6}
          shadowColor="black"
          shadowBlur={5}
          shadowOpacity={0.3}
        />
        <Text
          text={agent.name}
          fontSize={12}
          fontFamily="system-ui, -apple-system, sans-serif"
          fontStyle="bold"
          fill="#e2e8f0"
          align="center"
          width={120}
          y={-4}
        />
      </Group>

      {/* Current Task Label (if working) */}
      {agent.state === 'working' && agent.current_task && (
        <Group y={avatarSize / 2 + 36}>
          <Rect
            x={-70}
            y={-10}
            width={140}
            height={22}
            fill="rgba(16, 185, 129, 0.15)"
            stroke="rgba(16, 185, 129, 0.3)"
            strokeWidth={1}
            cornerRadius={6}
          />
          <Text
            text={agent.current_task.title}
            fontSize={10}
            fontFamily="system-ui, -apple-system, sans-serif"
            fill="#10b981"
            align="center"
            width={140}
            y={-4}
            ellipsis
          />
        </Group>
      )}

      {/* State indicator text */}
      <Group y={avatarSize / 2 + (agent.state === 'working' && agent.current_task ? 56 : 36)}>
        <Text
          text={agent.state.toUpperCase()}
          fontSize={9}
          fontFamily="system-ui, -apple-system, sans-serif"
          fill={getStatusColor()}
          align="center"
          width={120}
          x={-60}
          opacity={0.8}
        />
      </Group>
    </Group>
  );
}
