'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import {
  Search, Filter, Star, Download, Globe, Bot, Wrench,
  CheckCircle2, Loader2, AlertCircle, Package, Plus,
  Cpu, Database, Code2, Terminal, ShieldAlert, MessageSquare,
  Zap, BarChart3, Calendar, FileText,
} from 'lucide-react';
import { agentClassesApi, availableToolsApi, agentsApi, AgentClass, AvailableTool } from '@/lib/api';

// ─── Icon map for domains ─────────────────────────────────────────────────────

const DOMAIN_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  TECH: Code2, FINANCE: BarChart3, MARKETING: MessageSquare,
  HR: Bot, LEGAL: ShieldAlert, BUSINESS: Cpu, PERSONAL: Calendar,
  OTHER: Package, DATA: Database, SYSTEM: Terminal, WEB: Globe,
};

const DOMAIN_COLOR: Record<string, string> = {
  TECH: 'blue', FINANCE: 'emerald', MARKETING: 'amber', HR: 'purple',
  LEGAL: 'red', BUSINESS: 'cyan', PERSONAL: 'pink', OTHER: 'slate',
  DATA: 'indigo', SYSTEM: 'orange', WEB: 'teal',
};

const COLOR_CLASSES: Record<string, { bg: string; text: string; border: string }> = {
  blue:    { bg: 'bg-blue-500/15',    text: 'text-blue-400',    border: 'border-blue-500/20' },
  emerald: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  amber:   { bg: 'bg-amber-500/15',   text: 'text-amber-400',   border: 'border-amber-500/20' },
  purple:  { bg: 'bg-purple-500/15',  text: 'text-purple-400',  border: 'border-purple-500/20' },
  red:     { bg: 'bg-red-500/15',     text: 'text-red-400',     border: 'border-red-500/20' },
  cyan:    { bg: 'bg-cyan-500/15',    text: 'text-cyan-400',    border: 'border-cyan-500/20' },
  pink:    { bg: 'bg-pink-500/15',    text: 'text-pink-400',    border: 'border-pink-500/20' },
  slate:   { bg: 'bg-slate-500/15',   text: 'text-slate-400',   border: 'border-slate-500/20' },
  indigo:  { bg: 'bg-indigo-500/15',  text: 'text-indigo-400',  border: 'border-indigo-500/20' },
  orange:  { bg: 'bg-orange-500/15',  text: 'text-orange-400',  border: 'border-orange-500/20' },
  teal:    { bg: 'bg-teal-500/15',    text: 'text-teal-400',    border: 'border-teal-500/20' },
};

// ─── Deploy Agent Modal ───────────────────────────────────────────────────────

function DeployModal({
  agentClass,
  onClose,
}: {
  agentClass: AgentClass;
  onClose: () => void;
}) {
  const [name, setName] = useState(agentClass.name);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();
  const router = useRouter();

  const deploy = useMutation({
    mutationFn: () =>
      agentsApi.create({
        name,
        role: agentClass.name,
        domain: agentClass.domain,
        description: agentClass.description,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      router.push('/agents');
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="w-full max-w-md bg-slate-900 border border-white/10 rounded-2xl p-6 shadow-2xl">
        <h2 className="text-lg font-bold text-white mb-1">Deploy Agent</h2>
        <p className="text-sm text-slate-400 mb-5">
          Create a new agent based on <span className="text-blue-400">{agentClass.name}</span>
        </p>

        <div className="mb-4">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
            Agent Name
          </label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-slate-800/60 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50"
          />
        </div>

        {error && (
          <div className="mb-4 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400 flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => deploy.mutate()}
            disabled={!name.trim() || deploy.isPending}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl flex items-center justify-center gap-2 transition-colors"
          >
            {deploy.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {deploy.isPending ? 'Deploying…' : 'Deploy'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Agent Template Card ──────────────────────────────────────────────────────

function AgentCard({ cls, onDeploy }: { cls: AgentClass; onDeploy: (c: AgentClass) => void }) {
  const color = DOMAIN_COLOR[cls.domain] ?? 'slate';
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const colors = (COLOR_CLASSES[color] ?? COLOR_CLASSES.slate)!;
  const Icon = DOMAIN_ICON[cls.domain] ?? Bot;

  return (
    <div className="group relative bg-slate-900/40 border border-white/5 rounded-2xl p-6 flex flex-col transition-all hover:-translate-y-1 hover:border-blue-500/30 hover:shadow-[0_8px_30px_rgba(0,0,0,0.5)] overflow-hidden">
      <div className={`absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl pointer-events-none ${colors.bg} group-hover:opacity-150 transition-opacity`} />

      <div className="flex items-start justify-between mb-4 relative z-10">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${colors.bg} ${colors.border}`}>
          <Icon className={`w-6 h-6 ${colors.text}`} />
        </div>
        {cls.is_custom ? (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400">
            Custom
          </span>
        ) : (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-800 border border-white/5 text-slate-400">
            Official
          </span>
        )}
      </div>

      <div className="flex-1 relative z-10">
        <h3 className="text-base font-semibold text-white group-hover:text-blue-400 transition-colors mb-1">
          {cls.name}
        </h3>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">{cls.domain}</p>
        <p className="text-sm text-slate-400 leading-relaxed line-clamp-3">{cls.description}</p>
      </div>

      <div className="pt-4 border-t border-white/5 mt-4 relative z-10">
        <button
          onClick={() => onDeploy(cls)}
          className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl flex items-center justify-center gap-2 transition-colors shadow-[0_0_15px_rgba(37,99,235,0.2)]"
        >
          <Plus className="w-4 h-4" />
          Deploy Agent
        </button>
      </div>
    </div>
  );
}

// ─── Tool Card ────────────────────────────────────────────────────────────────

function ToolCard({ tool }: { tool: AvailableTool }) {
  const isDangerous = tool.is_dangerous;
  const colors = (isDangerous ? COLOR_CLASSES.red : COLOR_CLASSES.blue)!;
  const Icon = isDangerous ? ShieldAlert : (DOMAIN_ICON[tool.type?.toUpperCase()] ?? Wrench);

  return (
    <div className="group relative bg-slate-900/40 border border-white/5 rounded-2xl p-6 flex flex-col transition-all hover:-translate-y-1 hover:border-emerald-500/30 hover:shadow-[0_8px_30px_rgba(0,0,0,0.5)] overflow-hidden">
      <div className={`absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl pointer-events-none ${colors.bg} transition-opacity`} />

      <div className="flex items-start justify-between mb-4 relative z-10">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${colors.bg} ${colors.border}`}>
          <Icon className={`w-6 h-6 ${colors.text}`} />
        </div>
        <div className="flex items-center gap-2">
          {isDangerous && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400">
              Dangerous
            </span>
          )}
          <span className={`flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full ${
            tool.is_enabled !== false
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
              : 'bg-slate-800 border border-white/5 text-slate-500'
          }`}>
            {tool.is_enabled !== false ? (
              <><CheckCircle2 className="w-3 h-3" /> Active</>
            ) : 'Inactive'}
          </span>
        </div>
      </div>

      <div className="flex-1 relative z-10">
        <h3 className="text-base font-semibold text-white group-hover:text-emerald-400 transition-colors mb-1">
          {tool.name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
        </h3>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
          {tool.type ?? tool.category ?? 'BUILTIN'}
        </p>
        <p className="text-sm text-slate-400 leading-relaxed line-clamp-3">{tool.description}</p>
      </div>

      <div className="pt-4 border-t border-white/5 mt-4 relative z-10">
        <a
          href="/settings"
          className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-colors"
        >
          <FileText className="w-4 h-4" />
          Configure in Settings
        </a>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type Tab = 'agents' | 'tools';

export default function MarketplacePage() {
  const [search, setSearch] = useState('');
  const [domainFilter, setDomainFilter] = useState('All');
  const [tab, setTab] = useState<Tab>('agents');
  const [deployTarget, setDeployTarget] = useState<AgentClass | null>(null);

  const {
    data: agentClassesRaw,
    isLoading: loadingClasses,
    error: classesError,
  } = useQuery({
    queryKey: ['agent-classes'],
    queryFn: async () => {
      const res = await agentClassesApi.getAll();
      return (res.data ?? []) as AgentClass[];
    },
  });

  const {
    data: toolsRaw,
    isLoading: loadingTools,
    error: toolsError,
  } = useQuery({
    queryKey: ['available-tools'],
    queryFn: async () => {
      const res = await availableToolsApi.getAll();
      return (res.tools ?? []) as AvailableTool[];
    },
  });

  const agentClasses = agentClassesRaw ?? [];
  const tools = toolsRaw ?? [];

  // Derive domains for filter
  const domains = ['All', ...Array.from(new Set(agentClasses.map((c) => c.domain).filter(Boolean)))];

  const filteredClasses = agentClasses.filter((c) => {
    const matchSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.description?.toLowerCase().includes(search.toLowerCase());
    const matchDomain = domainFilter === 'All' || c.domain === domainFilter;
    return matchSearch && matchDomain;
  });

  const filteredTools = tools.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.description?.toLowerCase().includes(search.toLowerCase())
  );

  const isLoading = tab === 'agents' ? loadingClasses : loadingTools;
  const hasError = tab === 'agents' ? classesError : toolsError;

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-200 relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-blue-600/8 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[800px] h-[800px] bg-indigo-600/8 rounded-full blur-[150px] pointer-events-none" />

      {/* Header */}
      <div className="flex-none px-6 pt-6 pb-5 border-b border-white/5 relative z-10 bg-slate-950/50 backdrop-blur-xl">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-500/20 border border-blue-500/20 flex items-center justify-center">
            <Globe className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
              Marketplace
            </h1>
            <p className="text-slate-400 text-sm mt-0.5">
              Deploy agent templates and explore built-in capabilities.
            </p>
          </div>
          <div className="ml-auto flex items-center gap-3 text-sm text-slate-500">
            <span className="flex items-center gap-1.5">
              <Bot className="w-4 h-4 text-blue-400" />
              <span className="text-white font-semibold">{agentClasses.length}</span> templates
            </span>
            <span className="flex items-center gap-1.5">
              <Wrench className="w-4 h-4 text-emerald-400" />
              <span className="text-white font-semibold">{tools.length}</span> tools
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-4">
          <div className="flex gap-1 bg-slate-900/60 p-1 rounded-xl border border-white/5">
            <button
              onClick={() => setTab('agents')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === 'agents'
                  ? 'bg-slate-800 text-blue-400 border border-white/10 shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Bot className="w-4 h-4" /> Agent Templates
              <span className="ml-1 text-xs px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400">
                {agentClasses.length}
              </span>
            </button>
            <button
              onClick={() => setTab('tools')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === 'tools'
                  ? 'bg-slate-800 text-emerald-400 border border-white/10 shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Wrench className="w-4 h-4" /> Built-in Tools
              <span className="ml-1 text-xs px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">
                {tools.length}
              </span>
            </button>
          </div>

          {/* Search */}
          <div className="relative flex-1 max-w-sm group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={tab === 'agents' ? 'Search agent templates…' : 'Search tools…'}
              className="w-full bg-slate-900/60 border border-white/5 focus:border-blue-500/40 rounded-xl py-2 pl-9 pr-4 text-sm text-slate-200 placeholder:text-slate-500 outline-none transition-all"
            />
          </div>

          {/* Domain filter (agents tab only) */}
          {tab === 'agents' && (
            <div className="flex items-center gap-1.5 overflow-x-auto">
              <Filter className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
              {domains.map((d) => (
                <button
                  key={d}
                  onClick={() => setDomainFilter(d)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                    domainFilter === d
                      ? 'bg-blue-600 text-white shadow-[0_0_10px_rgba(37,99,235,0.3)]'
                      : 'bg-slate-900/60 text-slate-400 hover:text-white border border-white/5'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 relative z-10">
        {isLoading ? (
          <div className="flex items-center justify-center h-64 gap-3 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>Loading {tab === 'agents' ? 'agent templates' : 'tools'}…</span>
          </div>
        ) : hasError ? (
          <div className="flex items-center justify-center h-64 gap-3 text-red-400">
            <AlertCircle className="w-6 h-6" />
            <span>Failed to load data. Is the backend running?</span>
          </div>
        ) : tab === 'agents' ? (
          filteredClasses.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500">
              <Bot className="w-12 h-12 mb-4 opacity-30" />
              <p className="font-medium">No agent templates found</p>
              <p className="text-sm mt-1">Try adjusting your search or domain filter.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {filteredClasses.map((cls) => (
                <AgentCard key={cls.id} cls={cls} onDeploy={setDeployTarget} />
              ))}
            </div>
          )
        ) : filteredTools.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-500">
            <Wrench className="w-12 h-12 mb-4 opacity-30" />
            <p className="font-medium">No tools found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {filteredTools.map((tool) => (
              <ToolCard key={tool.name} tool={tool} />
            ))}
          </div>
        )}
      </div>

      {/* Deploy Modal */}
      {deployTarget && (
        <DeployModal agentClass={deployTarget} onClose={() => setDeployTarget(null)} />
      )}
    </div>
  );
}
