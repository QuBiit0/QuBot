'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Personality } from '@/types';
import { Brain, Lightbulb, AlertTriangle, MessageSquare } from 'lucide-react';

interface Step4PersonalityProps {
  data: { personality?: Personality };
  onChange: (updates: { personality?: Personality }) => void;
}

interface TraitSliderProps {
  label: string;
  description: string;
  value: number;
  onChange: (value: number) => void;
  leftLabel: string;
  rightLabel: string;
  color: string;
  icon: React.ReactNode;
}

function TraitSlider({
  label,
  description,
  value,
  onChange,
  leftLabel,
  rightLabel,
  color,
  icon,
}: TraitSliderProps) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm font-medium text-[#e6edf3]">{label}</span>
      </div>
      <p className="text-xs text-[#6e7681] mb-3">{description}</p>
      
      <div className="relative">
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-[#6e7681] w-20 text-right">{leftLabel}</span>
          
          <div className="flex-1 relative">
            <input
              type="range"
              min="0"
              max="100"
              value={value}
              onChange={(e) => onChange(parseInt(e.target.value))}
              className="w-full h-2 bg-[#21262d] rounded-lg appearance-none cursor-pointer
                       accent-[#3b6fff] focus:outline-none focus:ring-2 focus:ring-[#3b6fff]/30"
              style={{
                background: `linear-gradient(to right, ${color}40 0%, ${color} ${value}%, #21262d ${value}%, #21262d 100%)`,
              }}
            />
            <div
              className="absolute -top-1 w-4 h-4 rounded-full border-2 border-[#0d1117] 
                       pointer-events-none transition-all"
              style={{
                backgroundColor: color,
                left: `calc(${value}% - 8px)`,
              }}
            />
          </div>
          
          <span className="text-[10px] text-[#6e7681] w-20">{rightLabel}</span>
        </div>
        
        <div className="flex justify-center mt-2">
          <span
            className="text-xs font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: color + '20', color }}
          >
            {value}%
          </span>
        </div>
      </div>
    </div>
  );
}

export function Step4Personality({ data, onChange }: Step4PersonalityProps) {
  const [traits, setTraits] = useState({
    detail_oriented: data.personality?.detail_oriented ?? 50,
    risk_tolerance: data.personality?.risk_tolerance ?? 50,
    formality: data.personality?.formality ?? 50,
    strengths: data.personality?.strengths?.join(', ') || '',
    weaknesses: data.personality?.weaknesses?.join(', ') || '',
    communication_style: data.personality?.communication_style || '',
  });

  useEffect(() => {
    onChange({
      personality: {
        detail_oriented: traits.detail_oriented,
        risk_tolerance: traits.risk_tolerance,
        formality: traits.formality,
        strengths: traits.strengths.split(',').map((s) => s.trim()).filter(Boolean),
        weaknesses: traits.weaknesses.split(',').map((s) => s.trim()).filter(Boolean),
        communication_style: traits.communication_style,
      },
    });
  }, [traits]);

  const updateTrait = (key: keyof typeof traits, value: any) => {
    setTraits((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-[#e6edf3] mb-2">Personality & Style</h2>
      <p className="text-sm text-[#6e7681] mb-6">
        Define how your agent approaches tasks and communicates.
      </p>

      {/* Trait Sliders */}
      <div className="bg-[#0d1117] rounded-xl p-5 border border-[#30363d] mb-6">
        <TraitSlider
          label="Attention to Detail"
          description="How thorough and detail-oriented should the agent be?"
          value={traits.detail_oriented}
          onChange={(v) => updateTrait('detail_oriented', v)}
          leftLabel="Big Picture"
          rightLabel="Detail-Oriented"
          color="#3b82f6"
          icon={<Brain className="w-4 h-4 text-[#3b82f6]" />}
        />

        <TraitSlider
          label="Risk Tolerance"
          description="How comfortable is the agent with taking risks or trying new approaches?"
          value={traits.risk_tolerance}
          onChange={(v) => updateTrait('risk_tolerance', v)}
          leftLabel="Conservative"
          rightLabel="Risk-Taking"
          color="#f59e0b"
          icon={<AlertTriangle className="w-4 h-4 text-[#f59e0b]" />}
        />

        <TraitSlider
          label="Formality"
          description="How formal or casual should the agent's communication be?"
          value={traits.formality}
          onChange={(v) => updateTrait('formality', v)}
          leftLabel="Casual"
          rightLabel="Formal"
          color="#8b5cf6"
          icon={<MessageSquare className="w-4 h-4 text-[#8b5cf6]" />}
        />
      </div>

      {/* Communication Style */}
      <div className="mb-5">
        <label className="flex items-center gap-2 text-sm font-medium text-[#e6edf3] mb-2">
          <Lightbulb className="w-4 h-4 text-[#8b949e]" />
          Communication Style
        </label>
        <textarea
          placeholder="e.g., 'Professional but friendly, prefers structured bullet points'"
          value={traits.communication_style}
          onChange={(e) => updateTrait('communication_style', e.target.value)}
          className="w-full px-4 py-3 bg-[#0d1117] border border-[#30363d] rounded-xl
                   text-[#e6edf3] placeholder-[#484f58] text-sm
                   focus:border-[#3b6fff] focus:outline-none resize-none
                   transition-colors"
          rows={2}
          maxLength={200}
        />
      </div>

      {/* Strengths */}
      <div className="mb-5">
        <label className="text-sm font-medium text-[#e6edf3] mb-2 block">
          Strengths (comma-separated)
        </label>
        <input
          type="text"
          placeholder="e.g., 'data analysis, problem solving, documentation'"
          value={traits.strengths}
          onChange={(e) => updateTrait('strengths', e.target.value)}
          className="w-full px-4 py-3 bg-[#0d1117] border border-[#30363d] rounded-xl
                   text-[#e6edf3] placeholder-[#484f58] text-sm
                   focus:border-[#3b6fff] focus:outline-none transition-colors"
        />
      </div>

      {/* Weaknesses */}
      <div>
        <label className="text-sm font-medium text-[#e6edf3] mb-2 block">
          Weaknesses (comma-separated)
        </label>
        <input
          type="text"
          placeholder="e.g., 'creative writing, ambiguous tasks'"
          value={traits.weaknesses}
          onChange={(e) => updateTrait('weaknesses', e.target.value)}
          className="w-full px-4 py-3 bg-[#0d1117] border border-[#30363d] rounded-xl
                   text-[#e6edf3] placeholder-[#484f58] text-sm
                   focus:border-[#3b6fff] focus:outline-none transition-colors"
        />
      </div>
    </div>
  );
}
