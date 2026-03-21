'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronRight, ChevronLeft, Check, User, Briefcase, 
  Settings, Sparkles, Bot, Code, Palette, Shield,
  Cpu, MessageSquare, Database, Globe, Wrench
} from 'lucide-react';
import { useCreateAgent } from '@/hooks/useAgents';
import { useSkills } from '@/hooks/useSkills';
import { SkillMarketplace } from '@/components/skills/SkillMarketplace';
import { cn } from '@/lib/utils';
import { toast } from '@/components/ui';

interface AgentWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  onCreate?: (agentData: any) => void;
}

type Step = 'domain' | 'class' | 'profile' | 'llm' | 'skills' | 'review';

const DOMAINS = [
  { id: 'TECH', name: 'Technology', icon: Code, color: 'bg-blue-500', description: 'Development, DevOps, Security' },
  { id: 'FINANCE', name: 'Finance', icon: Database, color: 'bg-green-500', description: 'Analysis, Accounting, Trading' },
  { id: 'MARKETING', name: 'Marketing', icon: Globe, color: 'bg-purple-500', description: 'Content, SEO, Social Media' },
  { id: 'HR', name: 'Human Resources', icon: User, color: 'bg-pink-500', description: 'Recruiting, Culture, Training' },
  { id: 'LEGAL', name: 'Legal', icon: Shield, color: 'bg-red-500', description: 'Contracts, Compliance, IP' },
  { id: 'BUSINESS', name: 'Business', icon: Briefcase, color: 'bg-orange-500', description: 'Strategy, Operations, Sales' },
];

const AGENT_CLASSES: Record<string, { id: string; name: string; description: string; icon: any }[]> = {
  TECH: [
    { id: 'fullstack_dev', name: 'Full Stack Developer', description: 'Builds complete web applications', icon: Code },
    { id: 'frontend_dev', name: 'Frontend Developer', description: 'Creates user interfaces', icon: Palette },
    { id: 'backend_dev', name: 'Backend Developer', description: 'Server-side logic and APIs', icon: Database },
    { id: 'devops_eng', name: 'DevOps Engineer', description: 'CI/CD and infrastructure', icon: Cpu },
    { id: 'security_eng', name: 'Security Engineer', description: 'Security audits and hardening', icon: Shield },
    { id: 'data_eng', name: 'Data Engineer', description: 'Data pipelines and analytics', icon: Database },
  ],
  FINANCE: [
    { id: 'financial_analyst', name: 'Financial Analyst', description: 'Market analysis and forecasting', icon: Database },
    { id: 'accountant', name: 'Accountant', description: 'Bookkeeping and financial reports', icon: Briefcase },
    { id: 'auditor', name: 'Auditor', description: 'Compliance and risk assessment', icon: Shield },
    { id: 'trader', name: 'Trader', description: 'Trading strategies and execution', icon: Globe },
  ],
  MARKETING: [
    { id: 'content_writer', name: 'Content Writer', description: 'Blog posts and copywriting', icon: MessageSquare },
    { id: 'seo_specialist', name: 'SEO Specialist', description: 'Search engine optimization', icon: Globe },
    { id: 'social_manager', name: 'Social Media Manager', description: 'Social media strategy', icon: User },
    { id: 'brand_strategist', name: 'Brand Strategist', description: 'Brand development', icon: Palette },
  ],
  HR: [
    { id: 'recruiter', name: 'Recruiter', description: 'Talent acquisition', icon: User },
    { id: 'hr_generalist', name: 'HR Generalist', description: 'Employee relations', icon: Briefcase },
    { id: 'trainer', name: 'Trainer', description: 'Employee development', icon: MessageSquare },
  ],
  LEGAL: [
    { id: 'contract_lawyer', name: 'Contract Specialist', description: 'Contract review and drafting', icon: Shield },
    { id: 'compliance_officer', name: 'Compliance Officer', description: 'Regulatory compliance', icon: Shield },
    { id: 'ip_attorney', name: 'IP Specialist', description: 'Intellectual property', icon: Shield },
  ],
  BUSINESS: [
    { id: 'business_analyst', name: 'Business Analyst', description: 'Process optimization', icon: Database },
    { id: 'product_manager', name: 'Product Manager', description: 'Product strategy', icon: Briefcase },
    { id: 'sales_rep', name: 'Sales Representative', description: 'Sales and CRM', icon: User },
    { id: 'strategist', name: 'Strategist', description: 'Business strategy', icon: Globe },
  ],
};

const LLM_PROVIDERS = [
  { id: 'OPENAI', name: 'OpenAI', models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
  { id: 'ANTHROPIC', name: 'Anthropic', models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'] },
  { id: 'GOOGLE', name: 'Google', models: ['gemini-pro', 'gemini-ultra'] },
  { id: 'GROQ', name: 'Groq', models: ['llama2-70b', 'mixtral-8x7b'] },
  { id: 'DEEPSEEK', name: 'DeepSeek', models: ['deepseek-chat', 'deepseek-coder'] },
  { id: 'KIMI', name: 'Kimi (Moonshot)', models: ['kimi-chat', 'kimi-long'] },
  { id: 'OLLAMA', name: 'Ollama (Local)', models: ['llama2', 'codellama', 'mistral'] },
];

export function AgentWizard({ isOpen, onClose, onSuccess, onCreate }: AgentWizardProps) {
  const [step, setStep] = useState<Step>('domain');
  const [formData, setFormData] = useState({
    domain: '',
    agent_class_id: '',
    name: '',
    gender: 'neutral',
    personality: {
      formality: 50,
      creativity: 50,
      detail_oriented: 50,
    },
    role_description: '',
    llm_config: {
      provider: 'OPENAI',
      model: 'gpt-4',
      temperature: 0.7,
      max_tokens: 2000,
    },
    selected_skills: [] as string[],
  });
  
  const createAgent = useCreateAgent();
  const { data: skills } = useSkills({ public_only: true });
  
  const steps: { id: Step; label: string; icon: any }[] = [
    { id: 'domain', label: 'Domain', icon: Briefcase },
    { id: 'class', label: 'Class', icon: Bot },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'llm', label: 'AI Model', icon: Cpu },
    { id: 'skills', label: 'Skills', icon: Wrench },
    { id: 'review', label: 'Review', icon: Sparkles },
  ];
  
  const canProceed = () => {
    switch (step) {
      case 'domain': return !!formData.domain;
      case 'class': return !!formData.agent_class_id;
      case 'profile': return !!formData.name && formData.name.length >= 2;
      case 'llm': return !!formData.llm_config.provider && !!formData.llm_config.model;
      case 'skills': return true;
      case 'review': return true;
    }
  };
  
  const handleNext = () => {
    const stepOrder: Step[] = ['domain', 'class', 'profile', 'llm', 'skills', 'review'];
    const currentIndex = stepOrder.indexOf(step);
    const nextStep = stepOrder[currentIndex + 1];
    if (currentIndex < stepOrder.length - 1 && nextStep) {
      setStep(nextStep);
    }
  };

  const handleBack = () => {
    const stepOrder: Step[] = ['domain', 'class', 'profile', 'llm', 'skills', 'review'];
    const currentIndex = stepOrder.indexOf(step);
    const prevStep = stepOrder[currentIndex - 1];
    if (currentIndex > 0 && prevStep) {
      setStep(prevStep);
    }
  };
  
  const handleSubmit = async () => {
    try {
      const agentData = {
        name: formData.name,
        gender: formData.gender.toUpperCase(),
        class_id: formData.agent_class_id,
        domain: formData.domain,
        role_description: formData.role_description,
        personality: formData.personality,
        llm_config: formData.llm_config,
        avatar_config: {
          color_primary: DOMAINS.find(d => d.id === formData.domain)?.color.replace('bg-', '') || 'blue-500',
        },
      };
      
      if (onCreate) {
        onCreate(agentData);
      } else {
        await createAgent.mutateAsync(agentData);
      }
      
      toast.success('Agent created successfully!');
      onSuccess?.();
      onClose();
      
      // Reset form
      setStep('domain');
      setFormData({
        domain: '',
        agent_class_id: '',
        name: '',
        gender: 'neutral',
        personality: { formality: 50, creativity: 50, detail_oriented: 50 },
        role_description: '',
        llm_config: { provider: 'OPENAI', model: 'gpt-4', temperature: 0.7, max_tokens: 2000 },
        selected_skills: [],
      });
    } catch (error: any) {
      toast.error('Failed to create agent', error.message);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-4xl h-[85vh] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold">Create New Agent</h2>
              <p className="text-sm text-slate-400">Configure your AI team member</p>
            </div>
            <button onClick={onClose} className="p-2 text-slate-400 hover:text-white">✕</button>
          </div>
          
          {/* Progress */}
          <div className="flex items-center gap-1">
            {steps.map((s, index) => {
              const Icon = s.icon;
              const isActive = s.id === step;
              const isCompleted = steps.findIndex(x => x.id === step) > index;
              
              return (
                <div key={s.id} className="flex items-center">
                  <div className={cn(
                    'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors',
                    isActive && 'bg-blue-600 text-white',
                    isCompleted && 'bg-green-600 text-white',
                    !isActive && !isCompleted && 'bg-slate-800 text-slate-400'
                  )}>
                    {isCompleted ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                    <span className="hidden sm:inline">{s.label}</span>
                  </div>
                  {index < steps.length - 1 && <ChevronRight className="w-4 h-4 text-slate-600 mx-1" />}
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            {/* Step 1: Domain Selection */}
            {step === 'domain' && (
              <motion.div key="domain" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 className="text-lg font-semibold mb-2">Select Domain</h3>
                <p className="text-slate-400 mb-6">Choose the primary domain for your agent</p>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {DOMAINS.map((domain) => {
                    const Icon = domain.icon;
                    return (
                      <button
                        key={domain.id}
                        onClick={() => setFormData({ ...formData, domain: domain.id, agent_class_id: '' })}
                        className={cn(
                          'p-4 rounded-xl border-2 text-left transition-all',
                          formData.domain === domain.id
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-slate-700 hover:border-slate-600'
                        )}
                      >
                        <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center mb-3', domain.color)}>
                          <Icon className="w-6 h-6 text-white" />
                        </div>
                        <h4 className="font-semibold mb-1">{domain.name}</h4>
                        <p className="text-xs text-slate-400">{domain.description}</p>
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}
            
            {/* Step 2: Class Selection */}
            {step === 'class' && (
              <motion.div key="class" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 className="text-lg font-semibold mb-2">Select Agent Class</h3>
                <p className="text-slate-400 mb-6">Choose the specialization for your {DOMAINS.find(d => d.id === formData.domain)?.name} agent</p>
                
                <div className="grid grid-cols-2 gap-4">
                  {AGENT_CLASSES[formData.domain]?.map((cls) => {
                    const Icon = cls.icon;
                    return (
                      <button
                        key={cls.id}
                        onClick={() => setFormData({ ...formData, agent_class_id: cls.id })}
                        className={cn(
                          'p-4 rounded-xl border text-left transition-all',
                          formData.agent_class_id === cls.id
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-slate-700 hover:border-slate-600'
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0">
                            <Icon className="w-5 h-5 text-blue-400" />
                          </div>
                          <div>
                            <h4 className="font-semibold mb-1">{cls.name}</h4>
                            <p className="text-sm text-slate-400">{cls.description}</p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}
            
            {/* Step 3: Profile */}
            {step === 'profile' && (
              <motion.div key="profile" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="max-w-xl mx-auto space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Agent Profile</h3>
                  <p className="text-slate-400">Personalize your agent&apos;s identity</p>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g., Alice, Bob, Charlie"
                      className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Gender</label>
                    <div className="flex gap-3">
                      {['neutral', 'female', 'male'].map((g) => (
                        <button
                          key={g}
                          onClick={() => setFormData({ ...formData, gender: g })}
                          className={cn(
                            'flex-1 py-2 px-4 rounded-lg border capitalize transition-colors',
                            formData.gender === g
                              ? 'border-blue-500 bg-blue-500/10 text-blue-400'
                              : 'border-slate-700 text-slate-400 hover:bg-slate-800'
                          )}
                        >
                          {g}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Role Description</label>
                    <textarea
                      value={formData.role_description}
                      onChange={(e) => setFormData({ ...formData, role_description: e.target.value })}
                      placeholder="Describe this agent's responsibilities..."
                      rows={3}
                      className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white resize-none"
                    />
                  </div>
                  
                  {/* Personality Sliders */}
                  <div className="space-y-4 pt-4 border-t border-slate-800">
                    {[
                      { key: 'formality', label: 'Formality', left: 'Casual', right: 'Formal' },
                      { key: 'creativity', label: 'Creativity', left: 'Analytical', right: 'Creative' },
                      { key: 'detail_oriented', label: 'Detail Orientation', left: 'Big Picture', right: 'Detailed' },
                    ].map((slider) => (
                      <div key={slider.key}>
                        <div className="flex justify-between text-sm mb-2">
                          <span className="text-slate-400">{slider.left}</span>
                          <span className="text-slate-300 font-medium">{slider.label}</span>
                          <span className="text-slate-400">{slider.right}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={formData.personality[slider.key as keyof typeof formData.personality]}
                          onChange={(e) => setFormData({
                            ...formData,
                            personality: { ...formData.personality, [slider.key]: parseInt(e.target.value) }
                          })}
                          className="w-full accent-blue-500"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
            
            {/* Step 4: LLM Configuration */}
            {step === 'llm' && (
              <motion.div key="llm" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="max-w-xl mx-auto space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-2">AI Model Configuration</h3>
                  <p className="text-slate-400">Choose the brain for your agent</p>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Provider</label>
                    <div className="grid grid-cols-2 gap-2">
                      {LLM_PROVIDERS.map((provider) => (
                        <button
                          key={provider.id}
                          onClick={() => setFormData({
                            ...formData,
                            llm_config: { ...formData.llm_config, provider: provider.id, model: provider.models[0] ?? '' }
                          })}
                          className={cn(
                            'p-3 rounded-lg border text-left transition-colors',
                            formData.llm_config.provider === provider.id
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-slate-700 hover:border-slate-600'
                          )}
                        >
                          <span className="font-medium">{provider.name}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Model</label>
                    <select
                      value={formData.llm_config.model}
                      onChange={(e) => setFormData({
                        ...formData,
                        llm_config: { ...formData.llm_config, model: e.target.value }
                      })}
                      className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                    >
                      {LLM_PROVIDERS.find(p => p.id === formData.llm_config.provider)?.models.map((model) => (
                        <option key={model} value={model}>{model}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Temperature: {formData.llm_config.temperature}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={formData.llm_config.temperature}
                      onChange={(e) => setFormData({
                        ...formData,
                        llm_config: { ...formData.llm_config, temperature: parseFloat(e.target.value) }
                      })}
                      className="w-full accent-blue-500"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>Precise</span>
                      <span>Balanced</span>
                      <span>Creative</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
            
            {/* Step 5: Skills */}
            {step === 'skills' && (
              <motion.div key="skills" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 className="text-lg font-semibold mb-2">Assign Skills</h3>
                <p className="text-slate-400 mb-6">Select skills this agent can use (optional)</p>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {skills?.map((skill) => (
                    <label
                      key={skill.id}
                      className={cn(
                        'p-3 rounded-lg border cursor-pointer transition-all',
                        formData.selected_skills.includes(skill.id)
                          ? 'border-blue-500 bg-blue-500/10'
                          : 'border-slate-700 hover:border-slate-600'
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={formData.selected_skills.includes(skill.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({ ...formData, selected_skills: [...formData.selected_skills, skill.id] });
                            } else {
                              setFormData({
                                ...formData,
                                selected_skills: formData.selected_skills.filter(id => id !== skill.id)
                              });
                            }
                          }}
                          className="mt-1 rounded border-slate-600"
                        />
                        <div>
                          <h4 className="font-medium text-sm">{skill.name}</h4>
                          <p className="text-xs text-slate-400">{skill.description?.slice(0, 60)}...</p>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </motion.div>
            )}
            
            {/* Step 6: Review */}
            {step === 'review' && (
              <motion.div key="review" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="max-w-lg mx-auto">
                <h3 className="text-lg font-semibold mb-6">Review Your Agent</h3>
                
                <div className="bg-slate-800 rounded-xl p-6 space-y-4">
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      'w-16 h-16 rounded-xl flex items-center justify-center',
                      DOMAINS.find(d => d.id === formData.domain)?.color
                    )}>
                      <span className="text-2xl font-bold text-white">
                        {formData.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-xl font-bold">{formData.name}</h4>
                      <p className="text-slate-400">
                        {AGENT_CLASSES[formData.domain]?.find(c => c.id === formData.agent_class_id)?.name}
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500">Domain:</span>
                      <span className="ml-2 text-slate-300">{DOMAINS.find(d => d.id === formData.domain)?.name}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Gender:</span>
                      <span className="ml-2 text-slate-300 capitalize">{formData.gender}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Provider:</span>
                      <span className="ml-2 text-slate-300">{LLM_PROVIDERS.find(p => p.id === formData.llm_config.provider)?.name}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Model:</span>
                      <span className="ml-2 text-slate-300">{formData.llm_config.model}</span>
                    </div>
                  </div>
                  
                  {formData.selected_skills.length > 0 && (
                    <div>
                      <span className="text-slate-500 text-sm">Skills:</span>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {formData.selected_skills.map((skillId) => {
                          const skill = skills?.find(s => s.id === skillId);
                          return (
                            <span key={skillId} className="px-2 py-1 bg-slate-700 rounded text-xs">
                              {skill?.name}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 flex justify-between">
          <button
            onClick={handleBack}
            disabled={step === 'domain'}
            className="flex items-center gap-2 px-4 py-2 text-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
          
          {step === 'review' ? (
            <button
              onClick={handleSubmit}
              disabled={createAgent.isPending}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg font-medium transition-colors"
            >
              {createAgent.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Create Agent
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
