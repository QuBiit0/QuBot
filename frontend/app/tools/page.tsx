'use client';

import { useEffect, useState } from 'react';
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

const TOOL_ICONS: Record<string, string> = {
  web_browser:       '🌐',
  web_search:        '🔍',
  browser_automation:'🤖',
  http_api:          '📡',
  system_shell:      '💻',
  filesystem:        '📁',
  scheduler:         '⏰',
};

const TOOL_COLORS: Record<string, string> = {
  web_browser:       '#3b82f6',
  web_search:        '#6366f1',
  browser_automation:'#8b5cf6',
  http_api:          '#06b6d4',
  system_shell:      '#f59e0b',
  filesystem:        '#22c55e',
  scheduler:         '#ec4899',
};

function RiskBadge({ name }: { name: string }) {
  const dangerous = ['system_shell', 'filesystem'];
  const isDangerous = dangerous.includes(name);
  return (
    <span
      className="text-[9px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide"
      style={{
        background: isDangerous ? 'rgba(244,63,94,0.1)' : 'rgba(16,185,129,0.1)',
        color: isDangerous ? '#f43f5e' : '#10b981',
        border: `1px solid ${isDangerous ? 'rgba(244,63,94,0.2)' : 'rgba(16,185,129,0.2)'}`,
      }}
    >
      {isDangerous ? 'Dangerous' : 'Safe'}
    </span>
  );
}

function ParamRow({ name, schema, required }: {
  name: string;
  schema: { type: string; description: string; default?: unknown };
  required: boolean;
}) {
  return (
    <div className="flex items-start gap-2 py-1 border-b" style={{ borderColor: 'rgba(99,102,241,0.08)' }}>
      <span className="font-mono text-[11px] shrink-0 mt-0.5" style={{ color: '#6366f1', width: 120 }}>{name}</span>
      <span className="text-[10px] px-1.5 py-0.5 rounded shrink-0" style={{ background: 'rgba(99,102,241,0.08)', color: 'rgba(255,255,255,0.4)' }}>
        {schema.type}
      </span>
      {!required && (
        <span className="text-[9px] px-1.5 py-0.5 rounded shrink-0" style={{ background: 'rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.3)' }}>
          optional
        </span>
      )}
      <span className="text-[11px] flex-1" style={{ color: 'rgba(255,255,255,0.55)' }}>{schema.description}</span>
    </div>
  );
}

function ToolCard({ tool, onTest }: { tool: AvailableTool; onTest: (name: string) => void }) {
  const { name, description, parameters } = tool.function;
  const [open, setOpen] = useState(false);
  const color = TOOL_COLORS[name] ?? '#6366f1';
  const icon = TOOL_ICONS[name] ?? '🔧';
  const requiredSet = new Set(parameters.required ?? []);

  return (
    <div
      className="rounded-xl overflow-hidden transition-all"
      style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(14px)', border: '1px solid rgba(99,102,241,0.15)' }}
    >
      <button
        className="w-full text-left p-4 flex items-start gap-3"
        onClick={() => setOpen(o => !o)}
      >
        <div className="text-2xl w-9 h-9 flex items-center justify-center rounded-lg shrink-0"
          style={{ background: `${color}18`, border: `1px solid ${color}30` }}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-[14px]" style={{ color: 'rgba(255,255,255,0.92)' }}>{name}</span>
            <RiskBadge name={name} />
          </div>
          <p className="text-[12px] mt-0.5 text-left" style={{ color: 'rgba(255,255,255,0.5)' }}>{description}</p>
        </div>
        <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12, marginTop: 4 }}>
          {open ? '▲' : '▼'}
        </span>
      </button>

      {open && (
        <div className="px-4 pb-4 flex flex-col gap-3 border-t" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
          {/* Parameters */}
          <div className="pt-3">
            <div className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'rgba(255,255,255,0.3)' }}>
              Parameters ({Object.keys(parameters.properties ?? {}).length})
            </div>
            <div className="rounded-lg overflow-hidden" style={{ background: 'rgba(0,0,0,0.3)' }}>
              <div className="px-3 py-2">
                {Object.entries(parameters.properties ?? {}).map(([pname, pschema]) => (
                  <ParamRow
                    key={pname}
                    name={pname}
                    schema={pschema}
                    required={requiredSet.has(pname)}
                  />
                ))}
                {Object.keys(parameters.properties ?? {}).length === 0 && (
                  <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>No parameters</span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={() => onTest(name)}
            className="self-start px-3 py-1.5 text-[12px] font-semibold rounded-lg transition-opacity hover:opacity-90"
            style={{ background: `linear-gradient(135deg,${color},${color}cc)`, color: '#fff' }}
          >
            Test Tool
          </button>
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
        style={{ background: '#060912', border: '1px solid rgba(99,102,241,0.25)' }}>
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: 'rgba(99,102,241,0.15)' }}>
          <div>
            <div className="font-semibold" style={{ color: 'rgba(255,255,255,0.92)' }}>Test: {toolName}</div>
            <div className="text-[11px]" style={{ color: 'rgba(255,255,255,0.35)' }}>Execute tool with custom parameters</div>
          </div>
          <button onClick={onClose} style={{ color: 'rgba(255,255,255,0.4)', fontSize: 18 }}>✕</button>
        </div>

        <div className="overflow-y-auto p-5 flex flex-col gap-3">
          {Object.entries(params).map(([k, schema]) => (
            <div key={k}>
              <label className="text-[10px] font-semibold uppercase tracking-wider block mb-1" style={{ color: 'rgba(255,255,255,0.35)' }}>
                {k} <span style={{ color: '#6366f1' }}>({schema.type})</span>
              </label>
              <input
                className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
                style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
                placeholder={schema.default !== undefined ? String(schema.default) : schema.description}
                value={values[k] ?? ''}
                onChange={e => setValues(prev => ({ ...prev, [k]: e.target.value }))}
              />
            </div>
          ))}

          <button
            onClick={run}
            disabled={running}
            className="w-full py-2 font-semibold text-[13px] rounded-lg mt-1"
            style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', opacity: running ? 0.7 : 1 }}
          >
            {running ? 'Running…' : 'Execute'}
          </button>

          {result && (
            <div className="rounded-lg p-3" style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.12)' }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider"
                  style={{ color: result.success ? '#10b981' : '#f43f5e' }}>
                  {result.success ? '✓ Success' : '✗ Failed'}
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

  return (
    <div className="h-full overflow-y-auto" style={{ background: '#060912' }}>
      <div className="max-w-4xl mx-auto px-4 py-6 flex flex-col gap-5">

        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'rgba(255,255,255,0.92)' }}>Tools & Integrations</h1>
          <p className="text-[13px] mt-1" style={{ color: 'rgba(255,255,255,0.45)' }}>
            Built-in tools available to agents for executing actions in the world.
          </p>
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

        {/* Stats */}
        {!loading && tools.length > 0 && (
          <div className="flex items-center gap-4 flex-wrap">
            <div className="rounded-xl px-4 py-3"
              style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
              <div className="text-[22px] font-bold" style={{ color: '#6366f1' }}>{tools.length}</div>
              <div className="text-[10px] uppercase tracking-wider mt-0.5" style={{ color: 'rgba(255,255,255,0.4)' }}>Tools Available</div>
            </div>
          </div>
        )}

        {/* Tool cards */}
        <div className="flex flex-col gap-3">
          {tools.map(tool => (
            <ToolCard key={tool.function.name} tool={tool} onTest={setTestTool} />
          ))}
        </div>

        {!loading && tools.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="text-4xl" style={{ filter: 'grayscale(1)', opacity: 0.4 }}>🔧</div>
            <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>No tools registered yet</span>
          </div>
        )}
      </div>

      {testTool && (
        <TestModal toolName={testTool} tools={tools} onClose={() => setTestTool(null)} />
      )}
    </div>
  );
}
