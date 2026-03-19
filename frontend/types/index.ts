// Agent types
export type AgentStatus = 'IDLE' | 'WORKING' | 'ERROR' | 'OFFLINE';

export enum AgentStatusEnum {
  IDLE = 'IDLE',
  WORKING = 'WORKING',
  ERROR = 'ERROR',
  OFFLINE = 'OFFLINE',
}

export interface AvatarConfig {
  color_primary?: string;
  color_secondary?: string;
  avatar_style?: string;
}

export interface Agent {
  id: string;
  name: string;
  role?: string;
  role_description?: string;
  domain?: string;
  description?: string;
  state?: 'idle' | 'working' | 'thinking' | 'talking';
  status: AgentStatus;
  current_task?: {
    id: string;
    title: string;
    status: TaskStatus;
  } | null;
  current_task_id?: string | null;
  x?: number;
  y?: number;
  scale?: number;
  config?: Record<string, unknown>;
  avatar_config?: AvatarConfig;
  created_at?: string;
  updated_at?: string;
}

// Task types
export type TaskStatus = 'BACKLOG' | 'IN_PROGRESS' | 'DONE' | 'FAILED';

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  assigned_agent_id?: string | null;
  assigned_to?: {
    id: string | number;
    name: string;
  } | null;
  assigned_agent_name?: string;
  domain_hint?: string;
  tags?: string[];
  due_date?: string;
  created_at?: string;
  updated_at?: string;
}

// Activity/Event types
export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: string;
  message: string;
  severity: 'info' | 'success' | 'warning' | 'error';
  agent_id?: string;
  agent_name?: string;
  metadata?: Record<string, unknown>;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  meta?: {
    page?: number;
    per_page?: number;
    total?: number;
    total_pages?: number;
  };
}

export interface ApiError {
  status: number;
  message: string;
  errors?: Record<string, string[]>;
}

// WebSocket types
export interface WebSocketMessage {
  type: 'AGENT_UPDATE' | 'TASK_UPDATE' | 'ACTIVITY_EVENT' | 'METRICS_UPDATE' | 'PING' | 'PONG';
  id?: string;
  payload?: unknown;
  timestamp?: string;
}

// Layout types
export interface Position {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

// Navigation types
export interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

// Domain configuration
export const PRIORITY_CONFIG: Record<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL', { label: string; color: string }> = {
  LOW: { label: 'Low', color: '#8b949e' },
  MEDIUM: { label: 'Medium', color: '#58a6ff' },
  HIGH: { label: 'High', color: '#f0a500' },
  CRITICAL: { label: 'Critical', color: '#f85149' },
};

export const STATUS_CONFIG: Record<TaskStatus, { label: string; color: string }> = {
  BACKLOG: { label: 'Backlog', color: '#6b7c99' },
  FAILED: { label: 'Failed', color: '#f85149' },
  IN_PROGRESS: { label: 'In Progress', color: '#f0a500' },
  DONE: { label: 'Done', color: '#3fb950' },
};

export const DOMAIN_CONFIG = {
  TECH: { label: 'Tecnología', icon: '💻', color: '#3b82f6' },
  FINANCE: { label: 'Finanzas', icon: '💰', color: '#22c55e' },
  MARKETING: { label: 'Marketing', icon: '📢', color: '#f59e0b' },
  HR: { label: 'Recursos Humanos', icon: '👥', color: '#8b5cf6' },
  LEGAL: { label: 'Legal', icon: '⚖️', color: '#ef4444' },
  BUSINESS: { label: 'Negocios', icon: '💼', color: '#06b6d4' },
  PERSONAL: { label: 'Personal', icon: '🏠', color: '#ec4899' },
  OTHER: { label: 'Otros', icon: '🔧', color: '#6b7280' },
};

// Agent Wizard types
export interface AgentClass {
  id: string;
  name: string;
  description: string;
  domain: string;
  icon?: string;
  is_custom?: boolean;
  default_avatar_config?: {
    sprite_id?: string;
    icon?: string;
    badge?: string;
    color_primary?: string;
    color_secondary?: string;
  };
  created_at?: string;
}

export type DomainEnum = 'TECH' | 'FINANCE' | 'MARKETING' | 'HR' | 'LEGAL' | 'BUSINESS' | 'PERSONAL' | 'OTHER';

export type GenderEnum = 'MALE' | 'FEMALE' | 'NEUTRAL' | 'NON_BINARY';

export interface Personality {
  formality?: number;
  creativity?: number;
  detail_oriented?: number;
  risk_tolerance?: number;
  strengths?: string[];
  weaknesses?: string[];
  communication_style?: string;
}

export type LlmProviderEnum = 'OPENAI' | 'ANTHROPIC' | 'GOOGLE' | 'GROQ' | 'OLLAMA' | 'LOCAL' | 'OTHER';

export interface LlmConfig {
  id?: string;
  name?: string;
  provider: string | LlmProviderEnum;
  model?: string;
  model_name?: string;
  temperature: number;
  max_tokens: number;
  top_p?: number;
  api_key_ref?: string;
  extra_config?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export type ToolTypeEnum = 'BUILTIN' | 'CUSTOM' | 'PLUGIN' | 'WEB_BROWSER' | 'FILE_SYSTEM' | 'FILESYSTEM' | 'CODE_EXECUTION' | 'SCHEDULER' | 'API_CALL' | 'DATABASE' | 'MESSAGING' | 'HTTP_API' | 'SYSTEM_SHELL';

export type PermissionEnum = 'READ_ONLY' | 'READ_WRITE' | 'DANGEROUS';

export interface Tool {
  id: string;
  name: string;
  description: string;
  icon?: string;
  type?: ToolTypeEnum;
  category?: string;
  permission?: PermissionEnum;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  config?: Record<string, unknown>;
  is_dangerous?: boolean;
  is_enabled?: boolean;
  created_at?: string;
  updated_at?: string;
}
