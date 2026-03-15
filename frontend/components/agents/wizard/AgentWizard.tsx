'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Step1Domain } from './Step1Domain';
import { Step2Class } from './Step2Class';
import { Step3Identity } from './Step3Identity';
import { Step4Personality } from './Step4Personality';
import { Step5LlmConfig } from './Step5LlmConfig';
import { Step6Tools } from './Step6Tools';
import { WizardProgress } from './WizardProgress';
import { AvatarPreview } from './AvatarPreview';
import { Agent, AgentClass, DomainEnum, GenderEnum, Personality, LlmConfig, Tool, AvatarConfig } from '@/types';
import { ChevronLeft, ChevronRight, Check, Sparkles } from 'lucide-react';

const STEPS = [
  { id: 1, title: 'Domain', description: 'Choose the domain' },
  { id: 2, title: 'Class', description: 'Select a class' },
  { id: 3, title: 'Identity', description: 'Name & appearance' },
  { id: 4, title: 'Personality', description: 'Traits & style' },
  { id: 5, title: 'AI Config', description: 'LLM settings' },
  { id: 6, title: 'Tools', description: 'Assign capabilities' },
];

interface WizardData {
  domain?: DomainEnum;
  agentClass?: AgentClass;
  customClassName?: string;
  isCustomClass: boolean;
  name?: string;
  gender?: GenderEnum;
  avatarConfig?: AvatarConfig;
  personality?: Personality;
  llmConfigId?: string;
  selectedTools: string[];
}

export function AgentWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [data, setData] = useState<WizardData>({
    isCustomClass: false,
    selectedTools: [],
  });

  const updateData = (updates: Partial<WizardData>) => {
    setData((prev) => ({ ...prev, ...updates }));
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0:
        return !!data.domain;
      case 1:
        return !!data.agentClass || (data.isCustomClass && !!data.customClassName);
      case 2:
        return !!data.name && !!data.gender;
      case 3:
        return !!data.personality;
      case 4:
        return !!data.llmConfigId;
      case 5:
        return true; // Tools are optional
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));
    
    console.log('Creating agent with data:', data);
    
    // TODO: Actual API call
    // const response = await fetch('/api/v1/agents', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(agentData),
    // });
    
    setIsSubmitting(false);
    router.push('/agents');
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <Step1Domain data={data} onChange={updateData} />;
      case 1:
        return <Step2Class data={data} onChange={updateData} />;
      case 2:
        return <Step3Identity data={data} onChange={updateData} />;
      case 3:
        return <Step4Personality data={data} onChange={updateData} />;
      case 4:
        return <Step5LlmConfig data={data} onChange={updateData} />;
      case 5:
        return <Step6Tools data={data} onChange={updateData} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen" style={{ background: '#050b18' }}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #3b6fff, #7c3aed)' }}>
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[#e6edf3]">Create New Agent</h1>
            <p className="text-sm text-[#6e7681]">Configure your AI team member step by step</p>
          </div>
        </div>

        <div className="flex gap-8">
          {/* Left: Form */}
          <div className="flex-1 max-w-2xl">
            {/* Progress */}
            <WizardProgress steps={STEPS} currentStep={currentStep} />

            {/* Step Content */}
            <div className="mt-8 min-h-[400px]">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  {renderStep()}
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-[#21262d]">
              <button
                onClick={handleBack}
                disabled={currentStep === 0}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg
                         text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#21262d]
                         disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </button>

              {currentStep < STEPS.length - 1 ? (
                <button
                  onClick={handleNext}
                  disabled={!canProceed()}
                  className="flex items-center gap-2 px-6 py-2 text-sm font-medium rounded-lg
                           bg-[#238636] text-white hover:bg-[#2ea043]
                           disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!canProceed() || isSubmitting}
                  className="flex items-center gap-2 px-6 py-2 text-sm font-medium rounded-lg
                           bg-[#238636] text-white hover:bg-[#2ea043]
                           disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      Create Agent
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Right: Preview */}
          <div className="w-80 flex-shrink-0">
            <AvatarPreview data={data} />
          </div>
        </div>
      </div>
    </div>
  );
}
