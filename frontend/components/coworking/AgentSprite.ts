'use client';

import { Agent } from '@/types';

/**
 * Generates an SVG-based avatar for an agent
 * Returns a data URL that can be used as an image source
 */
export function generateAgentSprite(agent: Agent): string {
  const colors = getAgentColors(agent);
  const initial = agent.name.charAt(0).toUpperCase();
  
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:${colors.primary}"/>
          <stop offset="100%" style="stop-color:${colors.secondary}"/>
        </linearGradient>
        <linearGradient id="glow" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:${colors.glow};stop-opacity:0.6"/>
          <stop offset="100%" style="stop-color:${colors.glow};stop-opacity:0"/>
        </linearGradient>
      </defs>
      
      <!-- Background Circle -->
      <circle cx="50" cy="50" r="48" fill="url(#bg)"/>
      
      <!-- Glow Effect -->
      <circle cx="50" cy="50" r="45" fill="url(#glow)"/>
      
      <!-- Avatar Body (Simplified) -->
      <circle cx="50" cy="40" r="20" fill="rgba(255,255,255,0.2)"/>
      <ellipse cx="50" cy="75" rx="25" ry="20" fill="rgba(255,255,255,0.15)"/>
      
      <!-- Initial Letter -->
      <text 
        x="50" 
        y="60" 
        text-anchor="middle" 
        font-family="system-ui, sans-serif" 
        font-size="36" 
        font-weight="bold" 
        fill="white"
      >${initial}</text>
      
      <!-- Decorative Ring -->
      <circle cx="50" cy="50" r="46" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
    </svg>
  `;

  return `data:image/svg+xml;base64,${btoa(svg)}`;
}

function getAgentColors(agent: Agent): { primary: string; secondary: string; glow: string } {
  // Domain-based colors
  const domainColors: Record<string, { primary: string; secondary: string; glow: string }> = {
    'development': { primary: '#059669', secondary: '#047857', glow: '#34d399' },
    'design': { primary: '#db2777', secondary: '#be185d', glow: '#f472b6' },
    'marketing': { primary: '#7c3aed', secondary: '#6d28d9', glow: '#a78bfa' },
    'sales': { primary: '#ea580c', secondary: '#c2410c', glow: '#fb923c' },
    'support': { primary: '#0891b2', secondary: '#0e7490', glow: '#22d3ee' },
    'analytics': { primary: '#4f46e5', secondary: '#4338ca', glow: '#818cf8' },
    'product': { primary: '#0ea5e9', secondary: '#0284c7', glow: '#38bdf8' },
    'devops': { primary: '#65a30d', secondary: '#4d7c0f', glow: '#a3e635' },
  };

  // Default colors
  const defaultColors = { primary: '#3b82f6', secondary: '#2563eb', glow: '#60a5fa' };

  return domainColors[agent.domain?.toLowerCase() ?? ''] || defaultColors;
}

/**
 * Predefined SVG sprites for different agent states
 */
export const agentStateSprites = {
  working: `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
      <line x1="8" y1="21" x2="16" y2="21"/>
      <line x1="12" y1="17" x2="12" y2="21"/>
    </svg>
  `,
  thinking: `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  `,
  talking: `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
    </svg>
  `,
  idle: `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="8" y1="15" x2="16" y2="15"/>
      <line x1="9" y1="9" x2="9.01" y2="9"/>
      <line x1="15" y1="9" x2="15.01" y2="9"/>
    </svg>
  `,
};
