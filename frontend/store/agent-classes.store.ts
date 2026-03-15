/*
 * Agent Classes Store - Zustand
 * Manages predefined and custom agent classes
 */
import { create } from 'zustand';
import { AgentClass, DomainEnum } from '@/types';

interface AgentClassesState {
  classes: Record<string, AgentClass>;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setClasses: (classes: AgentClass[]) => void;
  addClass: (agentClass: AgentClass) => void;
  getClassesByDomain: (domain: DomainEnum) => AgentClass[];
  getClassById: (id: string) => AgentClass | undefined;
}

export const useAgentClassesStore = create<AgentClassesState>((set, get) => ({
  classes: {},
  isLoading: false,
  error: null,

  setClasses: (classes: AgentClass[]) => {
    const classesMap = classes.reduce((acc, cls) => {
      acc[cls.id] = cls;
      return acc;
    }, {} as Record<string, AgentClass>);
    set({ classes: classesMap });
  },

  addClass: (agentClass: AgentClass) => {
    set((state) => ({
      classes: { ...state.classes, [agentClass.id]: agentClass },
    }));
  },

  getClassesByDomain: (domain: DomainEnum) => {
    return Object.values(get().classes).filter((cls) => cls.domain === domain);
  },

  getClassById: (id: string) => {
    return get().classes[id];
  },
}));

// Mock data - 17 predefined classes from database-schema.md
export const MOCK_AGENT_CLASSES: AgentClass[] = [
  // TECH Domain
  {
    id: 'class-1',
    name: 'Ethical Hacker',
    description: 'Security specialist focused on finding vulnerabilities and hardening systems',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'hacker', color_primary: '#00FF41', color_secondary: '#1a1a1a', icon: '🔐', badge: 'SEC' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-2',
    name: 'Systems Architect',
    description: 'Designs and oversees complex software architectures and infrastructure',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'architect', color_primary: '#4A90E2', color_secondary: '#1a2744', icon: '🏗️', badge: 'ARCH' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-3',
    name: 'Backend Developer',
    description: 'Builds APIs, services, databases, and server-side logic',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'backend_dev', color_primary: '#7B2FBE', color_secondary: '#2d1a44', icon: '⚙️', badge: 'BE' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-4',
    name: 'Frontend Developer',
    description: 'Creates user interfaces and interactive web applications',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'frontend_dev', color_primary: '#F59E0B', color_secondary: '#44300a', icon: '🎨', badge: 'FE' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-5',
    name: 'DevOps Engineer',
    description: 'Manages CI/CD pipelines, infrastructure, deployments and reliability',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'devops', color_primary: '#10B981', color_secondary: '#0a3327', icon: '🚀', badge: 'OPS' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-6',
    name: 'Data Scientist',
    description: 'Analyzes data, builds models, and extracts insights from large datasets',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'data_scientist', color_primary: '#EF4444', color_secondary: '#440a0a', icon: '📊', badge: 'DS' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-7',
    name: 'ML Engineer',
    description: 'Designs, trains, and deploys machine learning models and pipelines',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'ml_engineer', color_primary: '#8B5CF6', color_secondary: '#2a1a44', icon: '🧠', badge: 'ML' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-8',
    name: 'Data Analyst',
    description: 'Transforms raw data into actionable business insights and reports',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'data_analyst', color_primary: '#06B6D4', color_secondary: '#0a2a30', icon: '📈', badge: 'DA' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-9',
    name: 'QA Engineer',
    description: 'Designs and executes test strategies to ensure software quality',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'qa', color_primary: '#84CC16', color_secondary: '#1a2a06', icon: '✅', badge: 'QA' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-10',
    name: 'AI Researcher',
    description: 'Researches AI capabilities, prompt engineering, and LLM optimization',
    domain: 'TECH',
    is_custom: false,
    default_avatar_config: { sprite_id: 'ai_researcher', color_primary: '#F97316', color_secondary: '#44200a', icon: '🔬', badge: 'AI' },
    created_at: new Date().toISOString(),
  },
  // FINANCE Domain
  {
    id: 'class-11',
    name: 'Finance Manager',
    description: 'Oversees financial operations, budgeting, and strategic financial decisions',
    domain: 'FINANCE',
    is_custom: false,
    default_avatar_config: { sprite_id: 'finance_manager', color_primary: '#D97706', color_secondary: '#44260a', icon: '💰', badge: 'FIN' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-12',
    name: 'Financial Analyst',
    description: 'Analyzes financial data, models, and provides investment recommendations',
    domain: 'FINANCE',
    is_custom: false,
    default_avatar_config: { sprite_id: 'fin_analyst', color_primary: '#B45309', color_secondary: '#3a1a06', icon: '📉', badge: 'FA' },
    created_at: new Date().toISOString(),
  },
  // BUSINESS Domain
  {
    id: 'class-13',
    name: 'Product Manager',
    description: 'Defines product strategy, roadmaps, and coordinates cross-functional teams',
    domain: 'BUSINESS',
    is_custom: false,
    default_avatar_config: { sprite_id: 'pm', color_primary: '#0EA5E9', color_secondary: '#0a2a38', icon: '📋', badge: 'PM' },
    created_at: new Date().toISOString(),
  },
  {
    id: 'class-14',
    name: 'Operations Manager',
    description: 'Optimizes business processes, logistics, and operational efficiency',
    domain: 'BUSINESS',
    is_custom: false,
    default_avatar_config: { sprite_id: 'ops_manager', color_primary: '#64748B', color_secondary: '#1a2030', icon: '⚡', badge: 'OPS' },
    created_at: new Date().toISOString(),
  },
  // HR Domain
  {
    id: 'class-15',
    name: 'HR Manager',
    description: 'Manages recruitment, employee relations, and organizational culture',
    domain: 'HR',
    is_custom: false,
    default_avatar_config: { sprite_id: 'hr_manager', color_primary: '#EC4899', color_secondary: '#44102a', icon: '👥', badge: 'HR' },
    created_at: new Date().toISOString(),
  },
  // MARKETING Domain
  {
    id: 'class-16',
    name: 'Digital Marketing Specialist',
    description: 'Plans and executes digital marketing campaigns, SEO, and growth strategies',
    domain: 'MARKETING',
    is_custom: false,
    default_avatar_config: { sprite_id: 'marketer', color_primary: '#F43F5E', color_secondary: '#44101a', icon: '📣', badge: 'MKT' },
    created_at: new Date().toISOString(),
  },
  // LEGAL Domain
  {
    id: 'class-17',
    name: 'Legal Counsel',
    description: 'Provides legal guidance, contract review, and compliance advice',
    domain: 'LEGAL',
    is_custom: false,
    default_avatar_config: { sprite_id: 'legal', color_primary: '#1E293B', color_secondary: '#0a1020', icon: '⚖️', badge: 'LEG' },
    created_at: new Date().toISOString(),
  },
];
