'use client';

import { useEffect, useState } from 'react';
import { Search, Filter, Zap, Shield, Code, Database, Globe, Terminal, Folder, Clock, Bot, Key, Link, BookOpen, Mail, Bell, Server, Lock, Users, Boxes } from 'lucide-react';
import { api } from '@/lib/api';

interface AvailableTool {
  type: string;
  function: {
    name: string;
    description: string;
    parameters: {
      type: string;
      properties: Record<string, { type: string; description: string; default?: unknown }>;
      required: string[];
    };
  };
}

interface ExecuteResult {
  success: boolean;
  data?: unknown;
  error?: string;
  stdout?: string;
  execution_time_ms?: number;
}

const TOOL_ICONS: Record<string, React.ReactNode> = {
  web_browser:        <Globe className="w-5 h-5" />,
  web_search:         <Search className="w-5 h-5" />,
  browser_automation: <Bot className="w-5 h-5" />,
  http_api:           <Link className="w-5 h-5" />,
  system_shell:       <Terminal className="w-5 h-5" />,
  filesystem:         <Folder className="w-5 h-5" />,
  scheduler:          <Clock className="w-5 h-5" />,
  code_executor:      <Code className="w-5 h-5" />,
  document_reader:    <BookOpen className="w-5 h-5" />,
  database_query:    <Database className="w-5 h-5" />,
  agent_memory:       <Boxes className="w-5 h-5" />,
  github:            <Link className="w-5 h-5" />,
  email:             <Mail className="w-5 h-5" />,
  notification:      <Bell className="w-5 h-5" />,
  docs_search:       <BookOpen className="w-5 h-5" />,
  mcp_installer:     <Server className="w-5 h-5" />,
  delegate_task:     <Users className="w-5 h-5" />,
  create_agent:      <Bot className="w-5 h-5" />,
  create_skill:      <Zap className="w-5 h-5" />,
  channel_manager:   <Link className="w-5 h-5" />,
  sessions:          <Clock className="w-5 h-5" />,
  spawn_subagent:    <Users className="w-5 h-5" />,
  gateway:           <Server className="w-5 h-5" />,
  nodes:             <Server className="w-5 h-5" />,
  canvas:            <Boxes className="w-5 h-5" />,
  image_generation:  <Boxes className="w-5 h-5" />,
  browser_profiles:  <Globe className="w-5 h-5" />,
  apply_patch:       <Code className="w-5 h-5" />,
};

const TOOL_COLORS: Record<string, string> = {
  web:              '#3b82f6',
  search:           '#6366f1',
  automation:       '#8b5cf6',
  communication:    '#06b6d4',
  system:           '#f59e0b',
  file:             '#22c55e',
  scheduler:        '#ec4899',
  code:             '#10b981',
  data:             '#f97316',
  agent:            '#a855f7',
  security:         '#ef4444',
};

const TOOL_CATEGORIES: Record<string, string[]> = {
  web: ['web_browser', 'web_search', 'browser_automation', 'http_api', 'browser_profiles', 'docs_search'],
  communication: ['email', 'notification', 'channel_manager'],
  file: ['filesystem', 'document_reader'],
  code: ['code_executor', 'github', 'apply_patch', 'system_shell'],
  data: ['database_query', 'agent_memory', 'canvas', 'image_generation'],
  scheduler: ['scheduler'],
  agent: ['delegate_task', 'create_agent', 'create_skill', 'sessions', 'spawn_subagent', 'nodes'],
  system: ['gateway', 'mcp_installer'],
};

const CATEGORY_LABELS: Record<string, string> = {
  web: 'Web & Browsing',
  communication: 'Communication',
  file: 'File Management',
  code: 'Code & Development',
  data: 'Data & AI',
  scheduler: 'Scheduler',
  agent: 'Agent Control',
  system: 'System & Integration',
};

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  web: <Globe className="w-4 h-4" />,
  communication: <Mail className="w-4 h-4" />,
  file: <Folder className="w-4 h-4" />,
  code: <Code className="w-4 h-4" />,
  data: <Database className="w-4 h-4" />,
  scheduler: <Clock className="w-4 h-4" />,
  agent: <Users className="w-4 h-4" />,
  system: <Server className="w-4 h-4" />,
};

const DANGEROUS_TOOLS = ['system_shell', 'filesystem', 'code_executor', 'apply_patch', 'gateway'];
const AGENT_TOOLS = ['delegate_task', 'create_agent', 'create_skill', 'spawn_subagent'];

function RiskBadge({ name }: { name: string }) {
  const isDangerous = DANGEROUS_TOOLS.includes(name);
  const isAgent = AGENT_TOOLS.includes(name);
  
  if (isAgent) {
    return (
      <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide"
        style={{ background: 'rgba(168,85,247,0.1)', color: '#a855f7', border: '1px solid rgba(168,85,247,0.2)' }}>
        Agent
      </span>
    );
  }
  
  return (
    <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide"
      style={{
        background: isDangerous ? 'rgba(244,63,94,0.1)' : 'rgba(16,185,129,0.1)',
        color: isDangerous ? '#f43f5e' : '#10b981',
        border: `1px solid ${isDangerous ? 'rgba(244,63,94,0.2)' : 'rgba(16,185,129,0.2)'}`,
      }}
    >
      {isDangerous ? 'Caution' : 'Safe'}
    </span>
  );
}

function getToolCategory(name: string): string {
  for (const [cat, tools] of Object.entries(TOOL_CATEGORIES)) {
    if (tools.includes(name)) return cat;
  }
  return 'system';
}

function getToolColor(name: string): string {
  const cat = getToolCategory(name);
  return TOOL_COLORS[cat] || '#6366f1';
}

function ParamRow({ name, schema, required }: {
  name: string;
  schema: { type: string; description: string; default?: unknown };
  required: boolean;
}) {
  return (
    <div className="flex items-start gap-2 py-1.5 border-b" style={{ borderColor: 'rgba(99,102,241,0.06)' }}>
      <code className="text-[11px] shrink-0 mt-0.5 px-1.5 py-0.5 rounded" 
        style={{ background: 'rgba(99,102,241,0.1)', color: '#818cf8', minWidth: 100 }}>
        {name}
      </code>
      <span className="text-[9px] px-1.5 py-0.5 rounded shrink-0" style={{ background: 'rgba(99,102,241,0.08)', color: 'rgba(255,255,255,0.35)' }}>
        {schema.type}
      </span>
      {!required && (
        <span className="text-[9px] px-1 py-0.5 rounded shrink-0" style={{ background: 'rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.25)' }}>
          optional
        </span>
      )}
      <span className="text-[11px] flex-1" style={{ color: 'rgba(255,255,255,0.5)' }}>{schema.description}</span>
    </div>
  );
}

function ToolCard({ tool, onTest }: { tool: AvailableTool; onTest: (name: string) => void }) {
  const { name, description, parameters } = tool.function;
  const [open, setOpen] = useState(false);
  const color = getToolColor(name);
  const icon = TOOL_ICONS[name] || <Server className="w-5 h-5" />;
  const requiredSet = new Set(parameters.required ?? []);
  const paramCount = Object.keys(parameters.properties ?? {}).length;

  return (
    <div className="rounded-xl overflow-hidden transition-all duration-200 hover:scale-[1.01]"
      style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(14px)', border: `1px solid ${color}20` }}>
      <button
        className="w-full text-left p-4 flex items-start gap-3"
        onClick={() => setOpen(o => !o)}
      >
        <div className="w-10 h-10 flex items-center justify-center rounded-lg shrink-0"
          style={{ background: `${color}15`, border: `1px solid ${color}25`, color }}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-[14px]" style={{ color: 'rgba(255,255,255,0.92)' }}>{name}</span>
            <RiskBadge name={name} />
            {paramCount > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.35)' }}>
                {paramCount} params
              </span>
            )}
          </div>
          <p className="text-[12px] mt-1 text-left line-clamp-2" style={{ color: 'rgba(255,255,255,0.45)' }}>{description}</p>
        </div>
        <span style={{ color: 'rgba(255,255,255,0.25)', fontSize: 12, marginTop: 4 }}>
          {open ? '▲' : '▼'}
        </span>
      </button>

      {open && (
        <div className="px-4 pb-4 flex flex-col gap-3 border-t" style={{ borderColor: `${color}15` }}>
          <div className="pt-3">
            <div className="text-[10px] font-semibold uppercase tracking-wider mb-2 flex items-center gap-2" style={{ color: 'rgba(255,255,255,0.3)' }}>
              Parameters ({paramCount})
            </div>
            <div className="rounded-lg overflow-hidden" style={{ background: 'rgba(0,0,0,0.3)' }}>
              <div className="px-3 py-2">
                {Object.entries(parameters.properties ?? {}).map(([pname, pschema]) => (
                  <ParamRow key={pname} name={pname} schema={pschema} required={requiredSet.has(pname)} />
                ))}
                {paramCount === 0 && (
                  <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>No parameters required</span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={(e) => { e.stopPropagation(); onTest(name); }}
              className="px-3 py-1.5 text-[12px] font-semibold rounded-lg transition-opacity hover:opacity-90"
              style={{ background: `linear-gradient(135deg,${color},${color}cc)`, color: '#fff' }}
            >
              Test Tool
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setOpen(false); }}
              className="px-3 py-1.5 text-[12px] rounded-lg transition-opacity hover:opacity-90"
              style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.5)' }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function TestModal({ toolName, tools, onClose }: {
  toolName: string;
  tools: AvailableTool[];
  onClose: () => void;
}) {
  const tool = tools.find(t => t.function.name === toolName);
  const params = tool?.function.parameters.properties ?? {};
  const [values, setValues] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ExecuteResult | null>(null);
  const color = getToolColor(toolName);

  const run = async () => {
    setRunning(true);
    setResult(null);
    try {
      const parsed: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(values)) {
        if (v === '') continue;
        const schema = params[k];
        if (schema?.type === 'integer') parsed[k] = parseInt(v, 10);
        else if (schema?.type === 'number') parsed[k] = parseFloat(v);
        else if (schema?.type === 'boolean') parsed[k] = v === 'true';
        else parsed[k] = v;
      }
      const res = await api.post<{ data: ExecuteResult }>('/tools/execute', {
        tool_name: toolName,
        params: parsed,
      });
      setResult(res.data ?? res as unknown as ExecuteResult);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setResult({ success: false, error: msg });
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(3,6,8,0.85)', backdropFilter: 'blur(8px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="w-full max-w-lg rounded-xl overflow-hidden flex flex-col max-h-[90vh]"
        style={{ background: '#060912', border: `1px solid ${color}30` }}>
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: `${color}20` }}>
          <div>
            <div className="font-semibold flex items-center gap-2" style={{ color: 'rgba(255,255,255,0.92)' }}>
              <span style={{ color }}>Test</span>
              <code className="text-[13px] px-2 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.05)', color }}>
                {toolName}
              </code>
            </div>
            <div className="text-[11px]" style={{ color: 'rgba(255,255,255,0.35)' }}>Execute tool with custom parameters</div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg" style={{ color: 'rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.05)' }}>X</button>
        </div>

        <div className="overflow-y-auto p-5 flex flex-col gap-3">
          {Object.entries(params).map(([k, schema]) => (
            <div key={k}>
              <label className="text-[10px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
                {k} <span style={{ color }}>({schema.type})</span>
              </label>
              <input
                className="w-full text-[13px] rounded-lg px-3 py-2 outline-none transition-colors focus:border-opacity-100"
                style={{ background: 'rgba(0,0,0,0.4)', border: `1px solid ${color}30`, color: 'rgba(255,255,255,0.85)' }}
                placeholder={schema.default !== undefined ? String(schema.default) : schema.description}
                value={values[k] ?? ''}
                onChange={e => setValues(prev => ({ ...prev, [k]: e.target.value }))}
              />
            </div>
          ))}

          {Object.keys(params).length === 0 && (
            <div className="text-center py-6" style={{ color: 'rgba(255,255,255,0.35)' }}>
              No parameters required for this tool
            </div>
          )}

          <button
            onClick={run}
            disabled={running}
            className="w-full py-2.5 font-semibold text-[13px] rounded-lg mt-2 transition-opacity hover:opacity-90"
            style={{ background: `linear-gradient(135deg,${color},${color}cc)`, color: '#fff', opacity: running ? 0.7 : 1 }}
          >
            {running ? 'Running...' : 'Execute'}
          </button>

          {result && (
            <div className="rounded-lg p-3 mt-2" style={{ background: 'rgba(0,0,0,0.3)', border: `1px solid ${result.success ? '#10b981' : '#f43f5e'}30` }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider"
                  style={{ color: result.success ? '#10b981' : '#f43f5e' }}>
                  {result.success ? 'Success' : 'Failed'}
                </span>
                {result.execution_time_ms !== undefined && (
                  <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.3)' }}>{result.execution_time_ms}ms</span>
                )}
              </div>
              <pre className="text-[11px] overflow-auto max-h-48 whitespace-pre-wrap"
                style={{ color: result.success ? 'rgba(255,255,255,0.75)' : '#f43f5e', fontFamily: 'monospace' }}>
                {result.stdout ?? result.error ?? JSON.stringify(result.data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ToolsPage() {
  const [tools, setTools] = useState<AvailableTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [testTool, setTestTool] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [showDangerous, setShowDangerous] = useState(true);

  useEffect(() => {
    api.get<{ data: AvailableTool[] }>('/tools/available')
      .then(res => {
        setTools(res.data ?? (res as unknown as AvailableTool[]));
        setLoading(false);
      })
      .catch(e => {
        setError(e instanceof Error ? e.message : 'Failed to load tools');
        setLoading(false);
      });
  }, []);

  const categories = Object.entries(TOOL_CATEGORIES).map(([key, tools]) => ({
    key,
    label: CATEGORY_LABELS[key] || key,
    icon: CATEGORY_ICONS[key],
    count: tools.filter(t => tools.some(tool => tool === t)).length,
  }));

  const filteredTools = tools.filter(tool => {
    const name = tool.function.name.toLowerCase();
    const desc = tool.function.description.toLowerCase();
    const searchLower = search.toLowerCase();
    
    if (search && !name.includes(searchLower) && !desc.includes(searchLower)) return false;
    if (!showDangerous && DANGEROUS_TOOLS.includes(tool.function.name)) return false;
    if (activeCategory) {
      const catTools = TOOL_CATEGORIES[activeCategory] || [];
      if (!catTools.includes(tool.function.name)) return false;
    }
    return true;
  });

  const groupedTools = filteredTools.reduce((acc, tool) => {
    const cat = getToolCategory(tool.function.name);
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(tool);
    return acc;
  }, {} as Record<string, AvailableTool[]>);

  const stats = {
    total: tools.length,
    dangerous: tools.filter(t => DANGEROUS_TOOLS.includes(t.function.name)).length,
    agent: tools.filter(t => AGENT_TOOLS.includes(t.function.name)).length,
  };

  return (
    <div className="h-full overflow-y-auto" style={{ background: 'linear-gradient(180deg, #060912 0%, #0a0f1a 100%)' }}>
      <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col gap-5">

        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'rgba(255,255,255,0.92)' }}>Tools & Integrations</h1>
            <p className="text-[13px] mt-1" style={{ color: 'rgba(255,255,255,0.45)' }}>
              {stats.total} built-in tools available to agents
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'rgba(255,255,255,0.3)' }} />
              <input
                type="text"
                className="w-full pl-10 pr-4 py-2 text-[13px] rounded-lg outline-none"
                style={{ background: 'rgba(6,9,18,0.88)', border: '1px solid rgba(99,102,241,0.15)', color: 'rgba(255,255,255,0.85)' }}
                placeholder="Search tools..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer" style={{ background: 'rgba(6,9,18,0.88)', border: '1px solid rgba(99,102,241,0.15)' }}>
              <input type="checkbox" checked={showDangerous} onChange={e => setShowDangerous(e.target.checked)} className="w-4 h-4 accent-indigo-500" />
              <span className="text-[12px]" style={{ color: 'rgba(255,255,255,0.6)' }}>Show Caution</span>
            </label>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setActiveCategory(null)}
              className="px-3 py-1.5 text-[12px] font-medium rounded-lg transition-all"
              style={{
                background: !activeCategory ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
                color: !activeCategory ? '#6366f1' : 'rgba(255,255,255,0.5)',
                border: !activeCategory ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent',
              }}
            >
              All ({stats.total})
            </button>
            {categories.map(cat => (
              <button
                key={cat.key}
                onClick={() => setActiveCategory(cat.key === activeCategory ? null : cat.key)}
                className="px-3 py-1.5 text-[12px] font-medium rounded-lg transition-all flex items-center gap-1.5"
                style={{
                  background: activeCategory === cat.key ? `${TOOL_COLORS[cat.key]}20` : 'rgba(255,255,255,0.05)',
                  color: activeCategory === cat.key ? TOOL_COLORS[cat.key] : 'rgba(255,255,255,0.5)',
                  border: activeCategory === cat.key ? `1px solid ${TOOL_COLORS[cat.key]}40` : '1px solid transparent',
                }}
              >
                {cat.icon}
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl p-4" style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#6366f1' }}>{stats.total}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Total Tools</div>
          </div>
          <div className="rounded-xl p-4" style={{ background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#f43f5e' }}>{stats.dangerous}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Caution</div>
          </div>
          <div className="rounded-xl p-4" style={{ background: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#a855f7' }}>{stats.agent}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Agent Control</div>
          </div>
        </div>

        {loading && (
          <div className="flex items-center gap-3 py-10 justify-center">
            {[0, 1, 2].map(i => (
              <span key={i} className="w-2 h-2 rounded-full animate-bounce"
                style={{ background: '#6366f1', animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
        )}

        {error && !loading && (
          <div className="rounded-lg px-4 py-3 text-[13px]"
            style={{ background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.2)', color: '#f43f5e' }}>
            {error}
          </div>
        )}

        {!loading && Object.entries(groupedTools).map(([category, categoryTools]) => (
          <div key={category} className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span style={{ color: TOOL_COLORS[category] || '#6366f1' }}>{CATEGORY_ICONS[category]}</span>
              <span className="text-[13px] font-semibold" style={{ color: 'rgba(255,255,255,0.7)' }}>
                {CATEGORY_LABELS[category] || category}
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.35)' }}>
                {categoryTools.length}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {categoryTools.map(tool => (
                <ToolCard key={tool.function.name} tool={tool} onTest={setTestTool} />
              ))}
            </div>
          </div>
        ))}

        {!loading && filteredTools.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.1)' }}>
              <Server className="w-8 h-8" style={{ color: 'rgba(255,255,255,0.2)' }} />
            </div>
            <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>No tools found</span>
          </div>
        )}
      </div>

      {testTool && (
        <TestModal toolName={testTool} tools={tools} onClose={() => setTestTool(null)} />
      )}
    </div>
  );
}
