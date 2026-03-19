'use client';

import { Group, Rect, Text } from 'react-konva';
import { Agent } from '@/types';
import { useEffect, useState } from 'react';

interface AgentSpeechBubbleProps {
  agent: Agent;
  x: number;
  y: number;
  isVisible: boolean;
}

export function AgentSpeechBubble({ agent, x, y, isVisible }: AgentSpeechBubbleProps) {
  const [textWidth, setTextWidth] = useState(0);
  const padding = 12;
  const maxWidth = 180;
  const lineHeight = 16;

  // Calculate text dimensions
  const getMessage = () => {
    if (agent.state === 'working' && agent.current_task) {
      return `Working on: ${agent.current_task.title}`;
    }
    if (agent.state === 'thinking') {
      return 'Thinking...';
    }
    if (agent.state === 'talking') {
      return 'In conversation';
    }
    return agent.description || 'Ready for tasks';
  };

  const message = getMessage();
  const lines = Math.ceil(message.length / 25); // Rough estimate
  const bubbleHeight = padding * 2 + lines * lineHeight;
  const bubbleWidth = Math.min(message.length * 6 + padding * 2, maxWidth);

  if (!isVisible) return null;

  return (
    <Group x={x} y={y} opacity={isVisible ? 1 : 0}>
      {/* Bubble Background */}
      <Rect
        x={-bubbleWidth / 2}
        y={-bubbleHeight}
        width={bubbleWidth}
        height={bubbleHeight}
        fill="rgba(15, 23, 42, 0.95)"
        stroke="#3b82f6"
        strokeWidth={1}
        cornerRadius={8}
        shadowColor="black"
        shadowBlur={10}
        shadowOpacity={0.3}
      />

      {/* Speech Bubble Pointer */}
      <Rect
        x={-8}
        y={-2}
        width={16}
        height={16}
        fill="rgba(15, 23, 42, 0.95)"
        rotation={45}
      />

      {/* Text */}
      <Text
        text={message}
        fontSize={12}
        fontFamily="system-ui, sans-serif"
        fill="#e2e8f0"
        align="center"
        width={bubbleWidth - padding * 2}
        x={-bubbleWidth / 2 + padding}
        y={-bubbleHeight + padding}
        wrap="word"
        lineHeight={1.4}
      />

      {/* Role Badge */}
      <Group x={-bubbleWidth / 2} y={-bubbleHeight - 20}>
        <Rect
          width={bubbleWidth}
          height={18}
          fill="#3b82f6"
          cornerRadius={[8, 8, 0, 0]}
        />
        <Text
          text={(agent.role_description ?? agent.role ?? 'Agent').toUpperCase()}
          fontSize={9}
          fontFamily="system-ui, sans-serif"
          fontStyle="bold"
          fill="white"
          align="center"
          width={bubbleWidth}
          y={4}
        />
      </Group>
    </Group>
  );
}
