'use client';

import { Group, Rect, Line, Text } from 'react-konva';

interface OfficeFloorProps {
  width: number;
  height: number;
}

export function OfficeFloor({ width, height }: OfficeFloorProps) {
  const TILE_SIZE = 48;
  
  // Generate grid lines
  const lines = [];
  
  // Vertical lines
  for (let x = 0; x <= width; x += TILE_SIZE) {
    lines.push(
      <Line
        key={`v-${x}`}
        points={[x, 0, x, height]}
        stroke="#1e293b"
        strokeWidth={1}
        opacity={0.5}
      />
    );
  }
  
  // Horizontal lines
  for (let y = 0; y <= height; y += TILE_SIZE) {
    lines.push(
      <Line
        key={`h-${y}`}
        points={[0, y, width, y]}
        stroke="#1e293b"
        strokeWidth={1}
        opacity={0.5}
      />
    );
  }
  
  return (
    <Group>
      {/* Base background */}
      <Rect
        x={0}
        y={0}
        width={width}
        height={height}
        fill="#0f172a"
      />
      
      {/* Grid */}
      {lines}
      
      {/* Zone label */}
      <Rect 
        x={20} 
        y={20} 
        width={100} 
        height={30} 
        fill="#1e293b" 
        cornerRadius={4} 
      />
      <Text
        text="Tech Zone"
        fontSize={12}
        fill="#64748b"
        x={20}
        y={28}
        width={100}
        align="center"
      />
    </Group>
  );
}
