'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { DomainEnum, DOMAIN_CONFIG, GenderEnum, AgentStatusEnum } from '@/types';
import { Bot, User, Sparkles } from 'lucide-react';

interface AvatarPreviewProps {
  data: {
    domain?: DomainEnum;
    name?: string;
    gender?: GenderEnum;
    avatarConfig?: {
      color_primary?: string;
      color_secondary?: string;
      icon?: string;
    };
    agentClass?: {
      name?: string;
      default_avatar_config?: {
        icon?: string;
        badge?: string;
      };
    };
    isCustomClass?: boolean;
    customClassName?: string;
  };
}

const GENDER_SYMBOLS: Record<GenderEnum, string> = {
  MALE: '♂',
  FEMALE: '♀',
  NON_BINARY: '⚧',
  NEUTRAL: '○',
};

export function AvatarPreview({ data }: AvatarPreviewProps) {
  const domainConfig = data.domain ? DOMAIN_CONFIG[data.domain] : null;
  const primaryColor = data.avatarConfig?.color_primary || domainConfig?.color || '#3b6fff';
  const secondaryColor = data.avatarConfig?.color_secondary || '#1a2744';
  const icon = data.agentClass?.default_avatar_config?.icon || domainConfig?.icon || '🤖';
  const badge = data.agentClass?.default_avatar_config?.badge || 'AGENT';

  return (
    <div className="sticky top-8">
      <div className="bg-[#0d1117] border border-[#30363d] rounded-xl p-6">
        <h3 className="text-sm font-semibold text-[#e6edf3] mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#3b6fff]" />
          Agent Preview
        </h3>

        {/* Avatar Card */}
        <div className="relative">
          {/* Card Background */}
          <div
            className="rounded-xl p-6 border-2 transition-all duration-300"
            style={{
              background: `linear-gradient(135deg, ${secondaryColor}40 0%, #0d1117 100%)`,
              borderColor: primaryColor,
            }}
          >
            {/* Status Badge */}
            <div className="absolute top-3 right-3 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#238636] animate-pulse" />
              <span className="text-[10px] text-[#3fb950] font-medium">IDLE</span>
            </div>

            {/* Avatar Icon */}
            <div className="flex justify-center mb-4">
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className="relative"
              >
                {/* Glow effect */}
                <div
                  className="absolute inset-0 rounded-full blur-xl opacity-30"
                  style={{ backgroundColor: primaryColor }}
                />
                
                {/* Avatar circle */}
                <div
                  className="relative w-24 h-24 rounded-full flex items-center justify-center text-5xl"
                  style={{
                    background: `linear-gradient(135deg, ${primaryColor}30 0%, ${primaryColor}10 100%)`,
                    border: `3px solid ${primaryColor}`,
                    boxShadow: `0 0 30px ${primaryColor}30`,
                  }}
                >
                  {icon}
                </div>

                {/* Gender badge */}
                {data.gender && (
                  <div
                    className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full flex items-center justify-center text-lg
                             border-2 border-[#0d1117]"
                    style={{ backgroundColor: primaryColor }}
                  >
                    {GENDER_SYMBOLS[data.gender]}
                  </div>
                )}
              </motion.div>
            </div>

            {/* Name */}
            <div className="text-center mb-4">
              <h4 className="text-lg font-bold text-[#e6edf3]">
                {data.name || 'Unnamed Agent'}
              </h4>
              <p className="text-xs text-[#8b949e]">
                {data.isCustomClass 
                  ? data.customClassName || 'Custom Class'
                  : data.agentClass?.name || 'Select a class'}
              </p>
            </div>

            {/* Domain Badge */}
            {domainConfig && (
              <div className="flex justify-center mb-4">
                <span
                  className="text-xs px-3 py-1 rounded-full font-medium"
                  style={{
                    backgroundColor: `${domainConfig.color}20`,
                    color: domainConfig.color,
                    border: `1px solid ${domainConfig.color}40`,
                  }}
                >
                  {domainConfig.icon} {domainConfig.label}
                </span>
              </div>
            )}

            {/* Stats Preview */}
            <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-[#30363d]">
              <div className="text-center">
                <p className="text-[10px] text-[#6e7681] uppercase tracking-wide">Class</p>
                <p className="text-xs font-semibold text-[#8b949e] truncate">
                  {badge}
                </p>
              </div>
              <div className="text-center border-x border-[#30363d]">
                <p className="text-[10px] text-[#6e7681] uppercase tracking-wide">Tasks</p>
                <p className="text-xs font-semibold text-[#3fb950]">0</p>
              </div>
              <div className="text-center">
                <p className="text-[10px] text-[#6e7681] uppercase tracking-wide">Status</p>
                <p className="text-xs font-semibold text-[#58a6ff]">Ready</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-4 p-3 bg-[#1a2540]/50 rounded-lg border border-[#1e3060]">
          <p className="text-[11px] text-[#6e7681]">
            <span className="text-[#58a6ff]">💡 Tip:</span> The agent will appear in your coworking 
            office once created. You can assign tasks and configure tools anytime.
          </p>
        </div>
      </div>
    </div>
  );
}
