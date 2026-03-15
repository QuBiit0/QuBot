'use client';

import { Agent } from '@/types';

export interface AgentPosition {
  id: string | number;
  x: number;
  y: number;
  scale: number;
  zone: 'lead' | 'tech' | 'ops' | 'data' | 'creative' | 'overflow';
  row: number;
  col: number;
  agent: Agent;
}

export interface CanvasDimensions {
  width: number;
  height: number;
}

/**
 * Classify agents by their role/domain
 */
function classifyAgent(agent: Agent): AgentPosition['zone'] {
  const domain = agent.domain?.toLowerCase() || '';
  const role = agent.role?.toLowerCase() || '';
  
  // Lead/Architect roles
  if (role.includes('lead') || role.includes('architect') || role.includes('manager')) {
    return 'lead';
  }
  
  // Tech domain
  if (domain.includes('development') || domain.includes('devops') || domain.includes('engineering')) {
    return 'tech';
  }
  
  // Data domain
  if (domain.includes('data') || domain.includes('analytics') || domain.includes('ml')) {
    return 'data';
  }
  
  // Creative domain
  if (domain.includes('design') || domain.includes('creative') || domain.includes('ux')) {
    return 'creative';
  }
  
  // Ops domain
  if (domain.includes('ops') || domain.includes('support') || domain.includes('infra')) {
    return 'ops';
  }
  
  return 'overflow';
}

/**
 * Check if two positions overlap
 */
function checkOverlap(
  pos1: { x: number; y: number },
  pos2: { x: number; y: number },
  minDistance: number = 90
): boolean {
  const dx = pos1.x - pos2.x;
  const dy = pos1.y - pos2.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  return distance < minDistance;
}

/**
 * Find a non-overlapping position
 */
function findValidPosition(
  baseX: number,
  baseY: number,
  existingPositions: { x: number; y: number }[],
  canvasWidth: number,
  canvasHeight: number,
  attempts: number = 50
): { x: number; y: number } {
  let x = baseX;
  let y = baseY;
  
  for (let i = 0; i < attempts; i++) {
    const hasOverlap = existingPositions.some((pos) => checkOverlap({ x, y }, pos));
    
    if (!hasOverlap) {
      return { x, y };
    }
    
    // Jitter position
    const angle = (Math.random() * Math.PI * 2);
    const radius = 60 + (i * 10);
    x = baseX + Math.cos(angle) * radius;
    y = baseY + Math.sin(angle) * radius;
    
    // Keep within canvas bounds (with padding)
    x = Math.max(80, Math.min(canvasWidth - 80, x));
    y = Math.max(80, Math.min(canvasHeight - 80, y));
  }
  
  return { x, y };
}

/**
 * Generate cathedral-style layout for small teams (up to 12 agents)
 */
function generateCathedralLayout(
  agents: Agent[],
  canvas: CanvasDimensions
): AgentPosition[] {
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const existingPositions: { x: number; y: number }[] = [];
  
  return agents.map((agent, index) => {
    const zone = classifyAgent(agent);
    
    // Position based on zone
    let baseX = centerX;
    let baseY = centerY;
    
    switch (zone) {
      case 'lead':
        // Center-back (the "altar")
        baseX = centerX;
        baseY = canvas.height * 0.25;
        break;
      case 'tech':
        // Left transept
        baseX = canvas.width * 0.25;
        baseY = centerY + (index % 3) * 80;
        break;
      case 'data':
        // Right transept
        baseX = canvas.width * 0.75;
        baseY = centerY + (index % 3) * 80;
        break;
      case 'creative':
        // Near the "windows" (top)
        baseX = centerX + (Math.random() - 0.5) * 200;
        baseY = canvas.height * 0.15;
        break;
      case 'ops':
        // Near the entrance (bottom)
        baseX = centerX + (index % 2) * 120 - 60;
        baseY = canvas.height * 0.75;
        break;
      default:
        // Scattered in the nave
        baseX = centerX + (Math.random() - 0.5) * 300;
        baseY = centerY + (Math.random() - 0.5) * 100;
    }
    
    const { x, y } = findValidPosition(baseX, baseY, existingPositions, canvas.width, canvas.height);
    existingPositions.push({ x, y });
    
    return {
      id: agent.id,
      x,
      y,
      scale: 1.0,
      zone,
      row: Math.floor(index / 3),
      col: index % 3,
      agent,
    };
  });
}

/**
 * Generate grid layout for medium teams (13-20 agents)
 */
function generateGridLayout(
  agents: Agent[],
  canvas: CanvasDimensions
): AgentPosition[] {
  const cols = Math.ceil(Math.sqrt(agents.length * 1.5));
  const cellWidth = canvas.width / cols;
  const cellHeight = canvas.height / Math.ceil(agents.length / cols);
  
  return agents.map((agent, index) => {
    const zone = classifyAgent(agent);
    const col = index % cols;
    const row = Math.floor(index / cols);
    
    // Add some randomness for organic feel
    const jitterX = (Math.random() - 0.5) * 40;
    const jitterY = (Math.random() - 0.5) * 40;
    
    return {
      id: agent.id,
      x: col * cellWidth + cellWidth / 2 + jitterX,
      y: row * cellHeight + cellHeight / 2 + jitterY,
      scale: 0.85,
      zone,
      row,
      col,
      agent,
    };
  });
}

/**
 * Generate compact layout for large teams (21+ agents)
 */
function generateCompactLayout(
  agents: Agent[],
  canvas: CanvasDimensions
): AgentPosition[] {
  const cols = Math.ceil(Math.sqrt(agents.length * 2));
  const cellWidth = canvas.width / cols;
  const cellHeight = canvas.height / Math.ceil(agents.length / cols);
  
  return agents.map((agent, index) => {
    const zone = classifyAgent(agent);
    const col = index % cols;
    const row = Math.floor(index / cols);
    
    // Less jitter for compact layout
    const jitterX = (Math.random() - 0.5) * 20;
    const jitterY = (Math.random() - 0.5) * 20;
    
    return {
      id: agent.id,
      x: col * cellWidth + cellWidth / 2 + jitterX,
      y: row * cellHeight + cellHeight / 2 + jitterY,
      scale: 0.7,
      zone,
      row,
      col,
      agent,
    };
  });
}

/**
 * Main layout function that selects the appropriate strategy
 */
export function calculateAgentPositions(
  agents: Agent[],
  canvas: CanvasDimensions
): AgentPosition[] {
  if (agents.length === 0) return [];
  
  if (agents.length <= 12) {
    return generateCathedralLayout(agents, canvas);
  }
  
  if (agents.length <= 20) {
    return generateGridLayout(agents, canvas);
  }
  
  return generateCompactLayout(agents, canvas);
}

/**
 * Animate agent movement with easing
 */
export function easePosition(
  current: number,
  target: number,
  factor: number = 0.1
): number {
  return current + (target - current) * factor;
}
