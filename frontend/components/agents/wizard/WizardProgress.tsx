'use client';

import React from 'react';
import { Check } from 'lucide-react';

interface Step {
  id: number;
  title: string;
  description: string;
}

interface WizardProgressProps {
  steps: Step[];
  currentStep: number;
}

export function WizardProgress({ steps, currentStep }: WizardProgressProps) {
  return (
    <div className="relative">
      {/* Progress Line */}
      <div className="absolute top-5 left-0 right-0 h-0.5 bg-[#21262d]">
        <div
          className="h-full bg-[#3b6fff] transition-all duration-300"
          style={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
        />
      </div>

      {/* Steps */}
      <div className="relative flex justify-between">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isPending = index > currentStep;

          return (
            <div key={step.id} className="flex flex-col items-center">
              {/* Circle */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold
                  transition-all duration-200 border-2 z-10
                  ${isCompleted
                    ? 'bg-[#238636] border-[#238636] text-white'
                    : isCurrent
                    ? 'bg-[#0d1117] border-[#3b6fff] text-[#3b6fff] shadow-lg shadow-[#3b6fff]/20'
                    : 'bg-[#0d1117] border-[#30363d] text-[#484f58]'
                  }`}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5" />
                ) : (
                  step.id
                )}
              </div>

              {/* Label */}
              <div className="mt-2 text-center">
                <p
                  className={`text-xs font-medium ${
                    isCurrent ? 'text-[#e6edf3]' : isCompleted ? 'text-[#8b949e]' : 'text-[#484f58]'
                  }`}
                >
                  {step.title}
                </p>
                <p className="text-[10px] text-[#6e7681] hidden sm:block">{step.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
