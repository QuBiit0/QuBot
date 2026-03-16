'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LlmConfig, LlmProviderEnum } from '@/types';
import { Cpu, Thermometer, Hash, Sparkles, Check, Plus } from 'lucide-react';

interface Step5LlmConfigProps {
  data: { llmConfigId?: string };
  onChange: (updates: { llmConfigId?: string }) => void;
}

// Mock LLM Configs
const MOCK_LLM_CONFIGS: LlmConfig[] = [
  {
    id: 'llm-1',
    name: 'GPT-4o',
    provider: 'OPENAI',
    model_name: 'gpt-4o',
    temperature: 0.7,
    top_p: 1.0,
    max_tokens: 4096,
    api_key_ref: 'OPENAI_API_KEY',
    extra_config: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'llm-2',
    name: 'Claude 3.5 Sonnet',
    provider: 'ANTHROPIC',
    model_name: 'claude-3-5-sonnet-20241022',
    temperature: 0.7,
    top_p: 1.0,
    max_tokens: 8192,
    api_key_ref: 'ANTHROPIC_API_KEY',
    extra_config: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'llm-3',
    name: 'Gemini 1.5 Pro',
    provider: 'GOOGLE',
    model_name: 'gemini-1.5-pro',
    temperature: 0.7,
    top_p: 1.0,
    max_tokens: 8192,
    api_key_ref: 'GOOGLE_API_KEY',
    extra_config: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'llm-4',
    name: 'Llama 3.3 70B (Groq)',
    provider: 'GROQ',
    model_name: 'llama-3.3-70b-versatile',
    temperature: 0.7,
    top_p: 1.0,
    max_tokens: 4096,
    api_key_ref: 'GROQ_API_KEY',
    extra_config: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'llm-5',
    name: 'Local (Ollama)',
    provider: 'LOCAL',
    model_name: 'llama3.2',
    temperature: 0.7,
    top_p: 1.0,
    max_tokens: 4096,
    api_key_ref: 'OLLAMA_HOST',
    extra_config: { base_url: 'http://localhost:11434/v1' },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const PROVIDER_COLORS: Record<LlmProviderEnum, string> = {
  OPENAI: '#10a37f',
  ANTHROPIC: '#d4a574',
  GOOGLE: '#4285f4',
  GROQ: '#f55036',
  OLLAMA: '#ff6b6b',
  LOCAL: '#8b5cf6',
  OTHER: '#6b7280',
};

const PROVIDER_LABELS: Record<LlmProviderEnum, string> = {
  OPENAI: 'OpenAI',
  ANTHROPIC: 'Anthropic',
  GOOGLE: 'Google',
  GROQ: 'Groq',
  OLLAMA: 'Ollama',
  LOCAL: 'Local',
  OTHER: 'Other',
};

export function Step5LlmConfig({ data, onChange }: Step5LlmConfigProps) {
  const [configs] = useState<LlmConfig[]>(MOCK_LLM_CONFIGS);
  const [showCreateForm, setShowCreateForm] = useState(false);

  return (
    <div>
      <h2 className="text-xl font-bold text-[#e6edf3] mb-2">AI Configuration</h2>
      <p className="text-sm text-[#6e7681] mb-6">
        Select the LLM that will power this agent. You can configure temperature and other parameters.
      </p>

      {/* LLM Configs List */}
      <div className="space-y-3 mb-4">
        {configs.map((config, index) => {
          const isSelected = data.llmConfigId === config.id;
          const providerColor = PROVIDER_COLORS[config.provider as LlmProviderEnum];

          return (
            <motion.button
              key={config.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => onChange({ llmConfigId: config.id })}
              className={`w-full p-4 rounded-xl border text-left transition-all duration-200
                ${isSelected
                  ? 'border-[#3b6fff] bg-[#1a2540]'
                  : 'border-[#30363d] bg-[#0d1117] hover:border-[#484f58]'
                }`}
            >
              <div className="flex items-start gap-4">
                {/* Provider Icon */}
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{
                    backgroundColor: providerColor + '20',
                    border: `1px solid ${providerColor}40`,
                  }}
                >
                  <Cpu className="w-6 h-6" style={{ color: providerColor }} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-[#e6edf3]">{config.name}</h3>
                    {isSelected && (
                      <Check className="w-4 h-4 text-[#3b6fff]" />
                    )}
                  </div>
                  
                  <p className="text-xs text-[#6e7681] mb-2">
                    {PROVIDER_LABELS[config.provider as LlmProviderEnum]} • {config.model_name}
                  </p>

                  {/* Parameters */}
                  <div className="flex items-center gap-4 text-[10px] text-[#8b949e]">
                    <span className="flex items-center gap-1">
                      <Thermometer className="w-3 h-3" />
                      Temp: {config.temperature}
                    </span>
                    <span className="flex items-center gap-1">
                      <Hash className="w-3 h-3" />
                      Max tokens: {config.max_tokens.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Create New Config */}
      {!showCreateForm ? (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowCreateForm(true)}
          className="w-full p-4 rounded-xl border-2 border-dashed border-[#30363d] 
                   hover:border-[#3b6fff] hover:bg-[#1a2540] transition-all duration-200
                   flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5 text-[#3b6fff]" />
          <span className="text-sm font-medium text-[#3b6fff]">Create New LLM Configuration</span>
        </motion.button>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-5 rounded-xl border border-[#3b6fff] bg-[#1a2540]"
        >
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-[#3b6fff]" />
            <span className="text-sm font-medium text-[#e6edf3]">New LLM Configuration</span>
          </div>
          
          <p className="text-xs text-[#6e7681] mb-4">
            This feature will be available once the backend LLM service is fully implemented.
            For now, select one of the predefined configurations above.
          </p>

          <button
            onClick={() => setShowCreateForm(false)}
            className="px-4 py-2 text-xs font-medium text-[#8b949e] 
                     hover:text-[#e6edf3] transition-colors"
          >
            Cancel
          </button>
        </motion.div>
      )}

      {/* Info Box */}
      <div className="mt-6 p-4 bg-[#1a2540]/50 rounded-lg border border-[#1e3060]">
        <p className="text-[11px] text-[#6e7681]">
          <span className="text-[#58a6ff]">ℹ️ Note:</span> API keys are configured server-side 
          via environment variables. The agent will use the key referenced by <code className="text-[#e6edf3] bg-[#0d1117] px-1 rounded">api_key_ref</code>.
        </p>
      </div>
    </div>
  );
}
