'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { GenderEnum, DomainEnum, DOMAIN_CONFIG } from '@/types';
import { User, Palette } from 'lucide-react';

interface Step3IdentityProps {
  data: {
    name?: string;
    gender?: GenderEnum;
    domain?: DomainEnum;
    avatarConfig?: {
      color_primary?: string;
      color_secondary?: string;
    };
  };
  onChange: (updates: {
    name?: string;
    gender?: GenderEnum;
    avatarConfig?: {
      color_primary?: string;
      color_secondary?: string;
    };
  }) => void;
}

const GENDERS: { value: GenderEnum; label: string; symbol: string; color: string }[] = [
  { value: 'MALE', label: 'Male', symbol: '♂', color: '#3b82f6' },
  { value: 'FEMALE', label: 'Female', symbol: '♀', color: '#ec4899' },
  { value: 'NON_BINARY', label: 'Non-binary', symbol: '⚧', color: '#8b5cf6' },
];

const COLOR_PRESETS = [
  { primary: '#3b82f6', secondary: '#1a2744', name: 'Blue' },
  { primary: '#10b981', secondary: '#0a3327', name: 'Green' },
  { primary: '#f59e0b', secondary: '#44300a', name: 'Amber' },
  { primary: '#ef4444', secondary: '#440a0a', name: 'Red' },
  { primary: '#8b5cf6', secondary: '#2a1a44', name: 'Purple' },
  { primary: '#ec4899', secondary: '#44102a', name: 'Pink' },
  { primary: '#06b6d4', secondary: '#0a2a30', name: 'Cyan' },
  { primary: '#f97316', secondary: '#44200a', name: 'Orange' },
];

export function Step3Identity({ data, onChange }: Step3IdentityProps) {
  const domainColor = data.domain ? DOMAIN_CONFIG[data.domain].color : '#3b82f6';

  return (
    <div>
      <h2 className="text-xl font-bold text-[#e6edf3] mb-2">Agent Identity</h2>
      <p className="text-sm text-[#6e7681] mb-6">
        Give your agent a name and customize their appearance.
      </p>

      {/* Name Input */}
      <div className="mb-6">
        <label className="flex items-center gap-2 text-sm font-medium text-[#e6edf3] mb-2">
          <User className="w-4 h-4 text-[#8b949e]" />
          Agent Name
        </label>
        <input
          type="text"
          placeholder="e.g., 'Sophia', 'Max', 'Aria'"
          value={data.name || ''}
          onChange={(e) => onChange({ name: e.target.value })}
          className="w-full px-4 py-3 bg-[#0d1117] border border-[#30363d] rounded-xl
                   text-[#e6edf3] placeholder-[#484f58]
                   focus:border-[#3b6fff] focus:outline-none focus:ring-1 focus:ring-[#3b6fff]
                   transition-all"
          maxLength={50}
        />
        <p className="text-xs text-[#6e7681] mt-1.5">
          Choose a memorable name. This will be displayed in the office and task assignments.
        </p>
      </div>

      {/* Gender Selection */}
      <div className="mb-6">
        <label className="text-sm font-medium text-[#e6edf3] mb-3 block">
          Gender
        </label>
        <div className="grid grid-cols-3 gap-3">
          {GENDERS.map((gender) => {
            const isSelected = data.gender === gender.value;
            return (
              <motion.button
                key={gender.value}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onChange({ gender: gender.value })}
                className={`p-4 rounded-xl border-2 transition-all duration-200
                  ${isSelected
                    ? 'border-[#3b6fff] bg-[#1a2540]'
                    : 'border-[#30363d] bg-[#0d1117] hover:border-[#484f58]'
                  }`}
              >
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-xl mx-auto mb-2"
                  style={{
                    backgroundColor: isSelected ? gender.color + '30' : '#21262d',
                    border: `2px solid ${isSelected ? gender.color : '#30363d'}`,
                    color: gender.color,
                  }}
                >
                  {gender.symbol}
                </div>
                <p className="text-sm font-medium text-[#e6edf3]">{gender.label}</p>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Color Selection */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-[#e6edf3] mb-3">
          <Palette className="w-4 h-4 text-[#8b949e]" />
          Color Theme
        </label>
        <div className="grid grid-cols-4 gap-3">
          {COLOR_PRESETS.map((color) => {
            const isSelected = data.avatarConfig?.color_primary === color.primary;
            return (
              <motion.button
                key={color.primary}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() =>
                  onChange({
                    avatarConfig: {
                      ...data.avatarConfig,
                      color_primary: color.primary,
                      color_secondary: color.secondary,
                    },
                  })
                }
                className={`relative p-3 rounded-xl border-2 transition-all duration-200
                  ${isSelected
                    ? 'border-[#3b6fff]'
                    : 'border-[#30363d] hover:border-[#484f58]'
                  }`}
                style={{ backgroundColor: color.secondary + '40' }}
              >
                <div
                  className="w-full h-8 rounded-lg mb-2"
                  style={{ backgroundColor: color.primary }}
                />
                <p className="text-xs text-[#8b949e]">{color.name}</p>
                {isSelected && (
                  <div className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full 
                                bg-[#3b6fff] flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" 
                         stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                )}
              </motion.button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
