'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Tool, ToolTypeEnum } from '@/types';
import { Wrench, Globe, Terminal, FileText, Calendar, Code, Shield, Check } from 'lucide-react';

interface Step6ToolsProps {
  data: { selectedTools: string[] };
  onChange: (updates: { selectedTools: string[] }) => void;
}

// Mock Tools
const MOCK_TOOLS: Tool[] = [
  {
    id: 'tool-1',
    name: 'Web Browser',
    type: 'WEB_BROWSER',
    description: 'Browse websites and extract information from web pages',
    input_schema: {},
    output_schema: {},
    config: {},
    is_dangerous: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'tool-2',
    name: 'HTTP API Client',
    type: 'HTTP_API',
    description: 'Make HTTP requests to external APIs and services',
    input_schema: {},
    output_schema: {},
    config: {},
    is_dangerous: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'tool-3',
    name: 'File System',
    type: 'FILE_SYSTEM',
    description: 'Read and write files in a sandboxed environment',
    input_schema: {},
    output_schema: {},
    config: {},
    is_dangerous: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'tool-4',
    name: 'Shell Executor',
    type: 'SYSTEM_SHELL',
    description: 'Execute whitelisted shell commands',
    input_schema: {},
    output_schema: {},
    config: {},
    is_dangerous: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'tool-5',
    name: 'Database Query',
    type: 'DATABASE',
    description: 'Execute database queries and operations',
    input_schema: {},
    output_schema: {},
    config: {},
    is_dangerous: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'tool-6',
    name: 'Memory Write',
    type: 'CUSTOM',
    description: 'Store information in the agent\'s persistent memory',
    input_schema: {},
    output_schema: {},
    config: {},
    is_dangerous: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const TOOL_ICONS: Record<string, React.ReactNode> = {
  WEB_BROWSER: <Globe className="w-5 h-5" />,
  HTTP_API: <Code className="w-5 h-5" />,
  FILE_SYSTEM: <FileText className="w-5 h-5" />,
  SYSTEM_SHELL: <Terminal className="w-5 h-5" />,
  DATABASE: <Calendar className="w-5 h-5" />,
  CUSTOM: <Wrench className="w-5 h-5" />,
};

const TOOL_COLORS: Record<string, string> = {
  WEB_BROWSER: '#3b82f6',
  HTTP_API: '#10b981',
  FILE_SYSTEM: '#f59e0b',
  SYSTEM_SHELL: '#ef4444',
  DATABASE: '#8b5cf6',
  CUSTOM: '#6b7280',
};

export function Step6Tools({ data, onChange }: Step6ToolsProps) {
  const [tools] = useState<Tool[]>(MOCK_TOOLS);

  const toggleTool = (toolId: string) => {
    const isSelected = data.selectedTools.includes(toolId);
    if (isSelected) {
      onChange({ selectedTools: data.selectedTools.filter((id) => id !== toolId) });
    } else {
      onChange({ selectedTools: [...data.selectedTools, toolId] });
    }
  };

  const selectedCount = data.selectedTools.length;

  return (
    <div>
      <h2 className="text-xl font-bold text-[#e6edf3] mb-2">Assign Tools</h2>
      <p className="text-sm text-[#6e7681] mb-6">
        Select the tools this agent can use to complete tasks. 
        You can always modify these later.
      </p>

      {/* Selection Summary */}
      <div className="flex items-center justify-between mb-4 p-3 bg-[#1a2540] rounded-lg">
        <span className="text-sm text-[#8b949e]">
          Selected: <span className="text-[#e6edf3] font-semibold">{selectedCount}</span> tools
        </span>
        {selectedCount > 0 && (
          <button
            onClick={() => onChange({ selectedTools: [] })}
            className="text-xs text-[#6e7681] hover:text-[#ef4444] transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-2 gap-3">
        {tools.map((tool, index) => {
          const isSelected = data.selectedTools.includes(tool.id);
          const color = TOOL_COLORS[tool.type];

          return (
            <motion.button
              key={tool.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => toggleTool(tool.id)}
              className={`relative p-4 rounded-xl border text-left transition-all duration-200
                ${isSelected
                  ? 'border-[#3b6fff] bg-[#1a2540]'
                  : 'border-[#30363d] bg-[#0d1117] hover:border-[#484f58]'
                }`}
            >
              {/* Checkbox */}
              <div
                className={`absolute top-3 right-3 w-5 h-5 rounded border-2 flex items-center justify-center
                  transition-all ${isSelected
                    ? 'bg-[#3b6fff] border-[#3b6fff]'
                    : 'border-[#484f58]'
                  }`}
              >
                {isSelected && <Check className="w-3 h-3 text-white" />}
              </div>

              {/* Danger Badge */}
              {tool.is_dangerous && (
                <div className="absolute top-3 right-10 flex items-center gap-1 px-1.5 py-0.5 
                              rounded bg-[#ef4444]/20 text-[#ef4444] text-[9px] font-semibold">
                  <Shield className="w-3 h-3" />
                  DANGER
                </div>
              )}

              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{
                    backgroundColor: color + '20',
                    color: color,
                  }}
                >
                  {TOOL_ICONS[tool.type]}
                </div>

                <div className="min-w-0 pr-6">
                  <h3 className="font-medium text-[#e6edf3] text-sm truncate">{tool.name}</h3>
                  <p className="text-[10px] text-[#6e7681] mt-0.5 line-clamp-2">
                    {tool.description}
                  </p>
                  <span
                    className="inline-block mt-1.5 text-[9px] px-1.5 py-0.5 rounded font-medium"
                    style={{
                      backgroundColor: color + '20',
                      color: color,
                    }}
                  >
                    {tool.type.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Info */}
      <div className="mt-6 p-4 bg-[#1a2540]/50 rounded-lg border border-[#1e3060]">
        <div className="flex items-start gap-3">
          <Shield className="w-4 h-4 text-[#f59e0b] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-[#e6edf3] font-medium mb-1">Permission Levels</p>
            <p className="text-[11px] text-[#6e7681]">
              Tools marked with <span className="text-[#ef4444]">DANGER</span> can execute 
              destructive operations. By default, agents get READ_ONLY permission. You can 
              upgrade to READ_WRITE or DANGEROUS in the agent settings after creation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
