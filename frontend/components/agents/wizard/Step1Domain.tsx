'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { DomainEnum, DOMAIN_CONFIG } from '@/types';
import { Check } from 'lucide-react';

interface Step1DomainProps {
  data: { domain?: DomainEnum };
  onChange: (updates: { domain?: DomainEnum }) => void;
}

const DOMAINS: DomainEnum[] = ['TECH', 'BUSINESS', 'FINANCE', 'HR', 'MARKETING', 'LEGAL', 'OTHER'];

export function Step1Domain({ data, onChange }: Step1DomainProps) {
  return (
    <div>
      <h2 className="text-xl font-bold text-[#e6edf3] mb-2">Select a Domain</h2>
      <p className="text-sm text-[#6e7681] mb-6">
        Choose the primary domain for your agent. This determines the types of tasks 
        they are best suited for.
      </p>

      <div className="grid grid-cols-2 gap-4">
        {DOMAINS.map((domain, index) => {
          const config = DOMAIN_CONFIG[domain];
          const isSelected = data.domain === domain;

          return (
            <motion.button
              key={domain}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => onChange({ domain })}
              className={`relative p-4 rounded-xl border-2 text-left transition-all duration-200
                ${isSelected
                  ? 'border-[#3b6fff] bg-[#1a2540]'
                  : 'border-[#30363d] bg-[#0d1117] hover:border-[#484f58] hover:bg-[#161b22]'
                }`}
            >
              {/* Selection indicator */}
              {isSelected && (
                <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-[#3b6fff] 
                              flex items-center justify-center">
                  <Check className="w-3 h-3 text-white" />
                </div>
              )}

              {/* Icon */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-3"
                style={{
                  backgroundColor: `${config.color}20`,
                  border: `1px solid ${config.color}40`,
                }}
              >
                {config.icon}
              </div>

              {/* Label */}
              <h3 className="font-semibold text-[#e6edf3] mb-1">{config.label}</h3>
              <p className="text-xs text-[#6e7681]">
                {getDomainDescription(domain)}
              </p>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

function getDomainDescription(domain: DomainEnum): string {
  const descriptions: Record<DomainEnum, string> = {
    TECH: 'Software development, DevOps, data science, and AI/ML',
    BUSINESS: 'Product management, operations, and strategy',
    FINANCE: 'Financial analysis, budgeting, and investment',
    HR: 'Recruitment, employee relations, and culture',
    MARKETING: 'Campaigns, SEO, content, and growth',
    LEGAL: 'Contracts, compliance, and legal advice',
    PERSONAL: 'Personal tasks and lifestyle management',
    OTHER: 'Specialized or miscellaneous tasks',
  };
  return descriptions[domain];
}
