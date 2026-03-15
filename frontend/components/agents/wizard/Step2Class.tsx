'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AgentClass, DomainEnum } from '@/types';
import { Check, Plus, Sparkles } from 'lucide-react';
import { useAgentClassesStore, MOCK_AGENT_CLASSES } from '@/store/agent-classes.store';

interface Step2ClassProps {
  data: {
    domain?: DomainEnum;
    agentClass?: AgentClass;
    isCustomClass: boolean;
    customClassName?: string;
  };
  onChange: (updates: {
    agentClass?: AgentClass;
    isCustomClass: boolean;
    customClassName?: string;
  }) => void;
}

export function Step2Class({ data, onChange }: Step2ClassProps) {
  const { classes, setClasses } = useAgentClassesStore();
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customName, setCustomName] = useState(data.customClassName || '');

  // Initialize mock data
  useEffect(() => {
    setClasses(MOCK_AGENT_CLASSES);
  }, [setClasses]);

  const filteredClasses = Object.values(classes).filter(
    (cls) => cls.domain === data.domain
  );

  const handleSelectClass = (agentClass: AgentClass) => {
    onChange({
      agentClass,
      isCustomClass: false,
      customClassName: undefined,
    });
    setShowCustomForm(false);
  };

  const handleCreateCustom = () => {
    if (!customName.trim()) return;
    
    const customClass: AgentClass = {
      id: `custom-${Date.now()}`,
      name: customName,
      description: 'Custom agent class created by user',
      domain: data.domain!,
      is_custom: true,
      default_avatar_config: {
        sprite_id: 'custom',
        color_primary: '#8b5cf6',
        color_secondary: '#2a1a44',
        icon: '✨',
        badge: 'CUST',
      },
      created_at: new Date().toISOString(),
    };

    onChange({
      agentClass: customClass,
      isCustomClass: true,
      customClassName: customName,
    });
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-[#e6edf3] mb-2">Select Agent Class</h2>
      <p className="text-sm text-[#6e7681] mb-6">
        Choose a predefined class or create a custom one for your agent.
      </p>

      {/* Predefined Classes */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {filteredClasses.map((cls, index) => {
          const isSelected = data.agentClass?.id === cls.id && !data.isCustomClass;

          return (
            <motion.button
              key={cls.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => handleSelectClass(cls)}
              className={`relative p-4 rounded-xl border text-left transition-all duration-200
                ${isSelected
                  ? 'border-[#3b6fff] bg-[#1a2540]'
                  : 'border-[#30363d] bg-[#0d1117] hover:border-[#484f58]'
                }`}
            >
              {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#3b6fff] 
                              flex items-center justify-center">
                  <Check className="w-3 h-3 text-white" />
                </div>
              )}

              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0"
                  style={{
                    backgroundColor: cls.default_avatar_config.color_primary + '20',
                    border: `1px solid ${cls.default_avatar_config.color_primary}40`,
                  }}
                >
                  {cls.default_avatar_config.icon}
                </div>
                <div className="min-w-0">
                  <h3 className="font-medium text-[#e6edf3] text-sm truncate">{cls.name}</h3>
                  <p className="text-[10px] text-[#6e7681] mt-0.5 line-clamp-2">
                    {cls.description}
                  </p>
                  <span
                    className="inline-block mt-1 text-[9px] px-1.5 py-0.5 rounded font-medium"
                    style={{
                      backgroundColor: cls.default_avatar_config.color_primary + '20',
                      color: cls.default_avatar_config.color_primary,
                    }}
                  >
                    {cls.default_avatar_config.badge}
                  </span>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Custom Class Option */}
      {!showCustomForm ? (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowCustomForm(true)}
          className="w-full p-4 rounded-xl border-2 border-dashed border-[#30363d] 
                   hover:border-[#8b5cf6] hover:bg-[#1a2540] transition-all duration-200
                   flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5 text-[#8b5cf6]" />
          <span className="text-sm font-medium text-[#8b5cf6]">Create Custom Class</span>
        </motion.button>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl border border-[#8b5cf6] bg-[#1a2540]"
        >
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-[#8b5cf6]" />
            <span className="text-sm font-medium text-[#e6edf3]">Custom Class</span>
          </div>
          
          <input
            type="text"
            placeholder="Enter class name (e.g., 'Blockchain Specialist')"
            value={customName}
            onChange={(e) => setCustomName(e.target.value)}
            className="w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg
                     text-sm text-[#e6edf3] placeholder-[#484f58]
                     focus:border-[#8b5cf6] focus:outline-none transition-colors mb-3"
            autoFocus
          />

          <div className="flex gap-2">
            <button
              onClick={() => setShowCustomForm(false)}
              className="flex-1 px-3 py-1.5 text-xs font-medium text-[#8b949e] 
                       hover:text-[#e6edf3] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateCustom}
              disabled={!customName.trim()}
              className="flex-1 px-3 py-1.5 text-xs font-medium bg-[#8b5cf6] 
                       text-white rounded-lg hover:bg-[#9f75ff]
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Create
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
