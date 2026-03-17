'use client';

import { useState, useEffect } from 'react';
import {
  Bell, Shield, User, Cpu, Key,
  Wrench, Server, ChevronDown, ChevronRight,
  Plus, Trash2, RefreshCw,
} from 'lucide-react';
import { authApi, api, ApiError } from '@/lib/api';
import type { UserResponse } from '@/lib/api';

type Section = 'profile' | 'security' | 'llm' | 'notifications' | 'apikey' | 'integrations' | 'mcp';

// ── Types ─────────────────────────────────────────────────────────────────────

interface LlmConfig {
  id: string;
  name?: string;
  provider: string;
  model_name?: string;
  model?: string;
  temperature: number;
  max_tokens: number;
  is_default?: boolean;
  created_at?: string;
}

interface ToolField {
  name: string;
  label: string;
  type: 'text' | 'password' | 'number' | 'boolean' | 'select';
  default?: unknown;
  env_var?: string;
  description?: string;
  required?: boolean;
  options?: string[];
}

interface ToolConfig {
  tool_name: string;
  label: string;
  description: string;
  icon: string;
  category: string;
  enabled: boolean;
  configured: boolean;
  status: 'configured' | 'unconfigured' | 'optional';
  config: Record<string, unknown>;
  fields: ToolField[];
}

interface MCPServer {
  id: string;
  name: string;
  description: string;
  server_type: 'sse' | 'stdio';
  url: string;
  headers: Record<string, string>;
  command: string;
  args: string[];
  env_vars: Record<string, string>;
  enabled: boolean;
  status: string;
  tools_cache: Array<{ name: string; description: string }>;
  last_connected: string | null;
  error_msg: string;
  created_at: string;
}

// ── Nav ───────────────────────────────────────────────────────────────────────

const sections: { id: Section; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'profile',       label: 'Profile',         icon: User   },
  { id: 'security',      label: 'Security',        icon: Shield },
  { id: 'llm',           label: 'LLM Configs',     icon: Cpu    },
  { id: 'notifications', label: 'Notifications',   icon: Bell   },
  { id: 'apikey',        label: 'API Key',         icon: Key    },
  { id: 'integrations',  label: 'Integrations',    icon: Wrench },
  { id: 'mcp',           label: 'MCP Servers',     icon: Server },
];

// ── Shared helpers ────────────────────────────────────────────────────────────

const inputCls: React.CSSProperties = {
  background: 'rgba(0,0,0,0.35)',
  border: '1px solid rgba(99,102,241,0.18)',
  color: 'rgba(255,255,255,0.85)',
  borderRadius: 8,
  padding: '8px 12px',
  fontSize: 13,
  width: '100%',
  outline: 'none',
};

function Label({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-[11px] font-semibold uppercase tracking-wider mb-1.5"
      style={{ color: 'rgba(255,255,255,0.35)' }}>
      {children}
    </label>
  );
}

function SaveBtn({ loading, label = 'Save Changes' }: { loading: boolean; label?: string }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="px-4 py-2 text-[13px] font-semibold rounded-lg transition-opacity"
      style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', opacity: loading ? 0.7 : 1 }}
    >
      {loading ? 'Saving…' : label}
    </button>
  );
}

function Feedback({ msg, isError }: { msg: string; isError: boolean }) {
  if (!msg) return null;
  return (
    <div className="rounded-lg px-3 py-2 text-[12px]"
      style={{
        background: isError ? 'rgba(244,63,94,0.08)' : 'rgba(16,185,129,0.08)',
        border: `1px solid ${isError ? 'rgba(244,63,94,0.2)' : 'rgba(16,185,129,0.2)'}`,
        color: isError ? '#f43f5e' : '#10b981',
      }}>
      {msg}
    </div>
  );
}

// ── Profile ───────────────────────────────────────────────────────────────────

function ProfileSection() {
  const [user,      setUser]      = useState<UserResponse | null>(null);
  const [fullName,  setFullName]  = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [loading,   setLoading]   = useState(false);
  const [msg,       setMsg]       = useState('');
  const [isError,   setIsError]   = useState(false);

  useEffect(() => {
    authApi.me().then(u => {
      setUser(u);
      setFullName(u.full_name ?? '');
      setAvatarUrl(u.avatar_url ?? '');
    }).catch(() => {});
  }, []);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setMsg(''); setIsError(false);
    try {
      await api.patch('/auth/me', { full_name: fullName, avatar_url: avatarUrl });
      setMsg('Profile updated successfully');
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : 'Update failed');
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={save} className="space-y-5">
      <h2 className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.92)' }}>Profile</h2>

      <div className="flex items-center gap-4">
        <div className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-bold"
          style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.25)', color: '#6366f1' }}>
          {user?.full_name?.charAt(0)?.toUpperCase() ?? user?.username?.charAt(0)?.toUpperCase() ?? '?'}
        </div>
        <div>
          <div className="font-semibold text-[15px]" style={{ color: 'rgba(255,255,255,0.85)' }}>{user?.username}</div>
          <div className="text-[12px]" style={{ color: 'rgba(255,255,255,0.4)' }}>{user?.email}</div>
          <div className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded mt-1 inline-block"
            style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1' }}>
            {user?.role ?? 'user'}
          </div>
        </div>
      </div>

      <div>
        <Label>Full Name</Label>
        <input style={inputCls} value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Your display name" />
      </div>

      <div>
        <Label>Email (read-only)</Label>
        <input style={{ ...inputCls, opacity: 0.5 }} value={user?.email ?? ''} readOnly />
      </div>

      <div>
        <Label>Avatar URL</Label>
        <input style={inputCls} value={avatarUrl} onChange={e => setAvatarUrl(e.target.value)} placeholder="https://..." />
      </div>

      <Feedback msg={msg} isError={isError} />
      <SaveBtn loading={loading} />
    </form>
  );
}

// ── Security ──────────────────────────────────────────────────────────────────

function SecuritySection() {
  const [current, setCurrent] = useState('');
  const [newPw,   setNewPw]   = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg,     setMsg]     = useState('');
  const [isError, setIsError] = useState(false);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPw !== confirm) { setMsg('Passwords do not match'); setIsError(true); return; }
    setLoading(true); setMsg(''); setIsError(false);
    try {
      await api.post('/auth/change-password', { current_password: current, new_password: newPw });
      setMsg('Password changed. You will need to log in again.');
      setCurrent(''); setNewPw(''); setConfirm('');
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : 'Change failed');
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={save} className="space-y-5">
      <h2 className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.92)' }}>Security</h2>

      <div>
        <Label>Current Password</Label>
        <input type="password" style={inputCls} value={current} onChange={e => setCurrent(e.target.value)} required />
      </div>
      <div>
        <Label>New Password</Label>
        <input type="password" style={inputCls} value={newPw} onChange={e => setNewPw(e.target.value)} required />
      </div>
      <div>
        <Label>Confirm New Password</Label>
        <input type="password" style={inputCls} value={confirm} onChange={e => setConfirm(e.target.value)} required />
      </div>

      <Feedback msg={msg} isError={isError} />
      <SaveBtn loading={loading} label="Change Password" />
    </form>
  );
}

// ── LLM Configs ───────────────────────────────────────────────────────────────

function LlmSection() {
  const [configs,  setConfigs]  = useState<LlmConfig[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form,     setForm]     = useState({ provider: 'OPENAI', model_name: '', temperature: '0.7', max_tokens: '4096', name: '' });
  const [saving,   setSaving]   = useState(false);
  const [msg,      setMsg]      = useState('');
  const [isError,  setIsError]  = useState(false);

  const load = () => {
    setLoading(true);
    api.get<{ data: LlmConfig[] }>('/llm-configs')
      .then(r => { setConfigs(r.data ?? (r as unknown as LlmConfig[])); setLoading(false); })
      .catch(e => { setError(e instanceof Error ? e.message : 'Failed to load'); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setMsg(''); setIsError(false);
    try {
      await api.post('/llm-configs', {
        provider: form.provider,
        model_name: form.model_name,
        temperature: parseFloat(form.temperature),
        max_tokens: parseInt(form.max_tokens, 10),
        name: form.name || undefined,
      });
      setMsg('LLM config created');
      setShowForm(false);
      load();
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : 'Create failed');
      setIsError(true);
    } finally {
      setSaving(false);
    }
  };

  const del = async (id: string) => {
    if (!confirm('Delete this LLM config?')) return;
    try { await api.delete(`/llm-configs/${id}`); load(); } catch {/* ignore */}
  };

  const PROVIDERS = ['OPENAI', 'ANTHROPIC', 'GOOGLE', 'GROQ', 'OLLAMA', 'LOCAL'];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.92)' }}>LLM Configurations</h2>
        <button onClick={() => setShowForm(s => !s)}
          className="px-3 py-1.5 text-[12px] font-semibold rounded-lg"
          style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.25)', color: '#6366f1' }}>
          {showForm ? 'Cancel' : '+ New Config'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={create} className="rounded-xl p-4 flex flex-col gap-3"
          style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)' }}>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Name (optional)</Label>
              <input style={inputCls} value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="GPT-4 Production" />
            </div>
            <div>
              <Label>Provider</Label>
              <select style={inputCls} value={form.provider} onChange={e => setForm(p => ({ ...p, provider: e.target.value }))}>
                {PROVIDERS.map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <Label>Model Name</Label>
              <input style={inputCls} value={form.model_name} onChange={e => setForm(p => ({ ...p, model_name: e.target.value }))} placeholder="gpt-4o" required />
            </div>
            <div>
              <Label>Temperature</Label>
              <input type="number" min="0" max="2" step="0.1" style={inputCls} value={form.temperature} onChange={e => setForm(p => ({ ...p, temperature: e.target.value }))} />
            </div>
            <div>
              <Label>Max Tokens</Label>
              <input type="number" min="1" style={inputCls} value={form.max_tokens} onChange={e => setForm(p => ({ ...p, max_tokens: e.target.value }))} />
            </div>
          </div>
          <Feedback msg={msg} isError={isError} />
          <SaveBtn loading={saving} label="Create Config" />
        </form>
      )}

      {loading && <div className="text-[13px]" style={{ color: 'rgba(255,255,255,0.35)' }}>Loading…</div>}
      {error   && <Feedback msg={error} isError />}

      {configs.length === 0 && !loading && (
        <div className="text-center py-8" style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>
          No LLM configs yet. Add one above.
        </div>
      )}

      <div className="flex flex-col gap-2">
        {configs.map(c => (
          <div key={c.id} className="flex items-center gap-3 px-4 py-3 rounded-xl"
            style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.12)' }}>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-[13px]" style={{ color: 'rgba(255,255,255,0.85)' }}>
                {c.name ?? `${c.provider}/${c.model_name ?? c.model}`}
              </div>
              <div className="text-[11px]" style={{ color: 'rgba(255,255,255,0.4)' }}>
                {c.provider} · temp {c.temperature} · {c.max_tokens} tokens
                {c.is_default && <span className="ml-2 text-[#6366f1]">★ default</span>}
              </div>
            </div>
            <button onClick={() => del(c.id)}
              className="text-[11px] px-2 py-1 rounded"
              style={{ color: '#f43f5e', background: 'rgba(244,63,94,0.08)' }}>
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── API Key ───────────────────────────────────────────────────────────────────

function ApiKeySection() {
  const [apiKey,   setApiKey]   = useState<string | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [msg,      setMsg]      = useState('');
  const [isError,  setIsError]  = useState(false);

  const generate = async () => {
    setLoading(true); setMsg(''); setIsError(false);
    try {
      const res = await api.post<{ api_key: string }>('/auth/api-key', {});
      setApiKey(res.api_key);
      setMsg('API key generated. Copy it now — it will not be shown again.');
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : 'Failed to generate key');
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  const revoke = async () => {
    if (!confirm('Revoke API key? This will invalidate all existing integrations.')) return;
    setRevoking(true);
    try {
      await api.delete('/auth/api-key');
      setApiKey(null);
      setMsg('API key revoked.');
    } catch {/* ignore */} finally {
      setRevoking(false);
    }
  };

  return (
    <div className="space-y-5">
      <h2 className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.92)' }}>API Key</h2>
      <p className="text-[13px]" style={{ color: 'rgba(255,255,255,0.45)' }}>
        Generate an API key for programmatic access to Qubot. Use it in the{' '}
        <code style={{ color: '#6366f1' }}>X-API-Key</code> header.
      </p>

      {apiKey && (
        <div className="rounded-xl p-4" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
          <Label>Your API Key (copy now)</Label>
          <div className="flex items-center gap-2 mt-1">
            <code className="flex-1 text-[12px] break-all px-3 py-2 rounded-lg"
              style={{ background: 'rgba(0,0,0,0.4)', color: '#10b981', fontFamily: 'monospace' }}>
              {apiKey}
            </code>
            <button onClick={() => { navigator.clipboard.writeText(apiKey); }}
              className="px-3 py-2 text-[11px] font-semibold rounded-lg shrink-0"
              style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981' }}>
              Copy
            </button>
          </div>
        </div>
      )}

      <Feedback msg={msg} isError={isError} />

      <div className="flex gap-2">
        <button onClick={generate} disabled={loading}
          className="px-4 py-2 text-[13px] font-semibold rounded-lg"
          style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', opacity: loading ? 0.7 : 1 }}>
          {loading ? 'Generating…' : 'Generate New Key'}
        </button>
        <button onClick={revoke} disabled={revoking}
          className="px-4 py-2 text-[13px] font-semibold rounded-lg"
          style={{ background: 'rgba(244,63,94,0.08)', color: '#f43f5e', border: '1px solid rgba(244,63,94,0.2)' }}>
          {revoking ? 'Revoking…' : 'Revoke Key'}
        </button>
      </div>
    </div>
  );
}

// ── Notifications ─────────────────────────────────────────────────────────────

function NotificationsSection() {
  return (
    <div className="space-y-5">
      <h2 className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.92)' }}>Notifications</h2>
      <div className="space-y-3">
        {['Task completions', 'Agent status changes', 'System alerts', 'Weekly reports'].map(item => (
          <label key={item} className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" defaultChecked className="w-4 h-4 accent-indigo-500" />
            <span className="text-[13px]" style={{ color: 'rgba(255,255,255,0.7)' }}>{item}</span>
          </label>
        ))}
      </div>
      <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
        Email notifications require SMTP configuration in server settings.
      </p>
    </div>
  );
}

// ── Integrations (Tool Configs) ───────────────────────────────────────────────

function ToolCard({ tool, onUpdate }: { tool: ToolConfig; onUpdate: (updated: ToolConfig) => void }) {
  const [expanded,  setExpanded]  = useState(false);
  const [fieldVals, setFieldVals] = useState<Record<string, unknown>>(() => ({ ...tool.config }));
  const [enabled,   setEnabled]   = useState(tool.enabled);
  const [saving,    setSaving]    = useState(false);
  const [testing,   setTesting]   = useState(false);
  const [msg,       setMsg]       = useState('');
  const [isError,   setIsError]   = useState(false);

  const statusColor = tool.status === 'configured' ? '#10b981'
    : tool.status === 'optional' ? '#f59e0b' : 'rgba(255,255,255,0.25)';
  const statusLabel = tool.status === 'configured' ? 'Configured'
    : tool.status === 'optional' ? 'Optional' : 'Not configured';

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setMsg(''); setIsError(false);
    try {
      const res = await api.put<{ data: ToolConfig }>(
        `/integrations/tool-configs/${tool.tool_name}`,
        { enabled, config: fieldVals }
      );
      setMsg('Saved');
      onUpdate(res.data);
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : 'Save failed');
      setIsError(true);
    } finally {
      setSaving(false);
    }
  };

  const test = async () => {
    setTesting(true); setMsg(''); setIsError(false);
    try {
      const res = await api.post<{ data: { success: boolean; message?: string; output?: string; error?: string } }>(
        `/integrations/tool-configs/${tool.tool_name}/test`, {}
      );
      const d = res.data;
      setMsg(d.success ? (d.message ?? d.output ?? 'Test passed ✓') : (d.error ?? 'Test failed'));
      setIsError(!d.success);
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : 'Test failed');
      setIsError(true);
    } finally {
      setTesting(false);
    }
  };

  const renderField = (f: ToolField) => {
    const val = fieldVals[f.name] ?? f.default ?? '';
    const set = (v: unknown) => setFieldVals(p => ({ ...p, [f.name]: v }));

    if (f.type === 'boolean') {
      return (
        <label key={f.name} className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" className="w-4 h-4 accent-indigo-500"
            checked={Boolean(val)} onChange={e => set(e.target.checked)} />
          <span className="text-[13px]" style={{ color: 'rgba(255,255,255,0.7)' }}>{f.label}</span>
          {f.description && (
            <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>— {f.description}</span>
          )}
        </label>
      );
    }

    if (f.type === 'select' && f.options) {
      return (
        <div key={f.name}>
          <Label>{f.label}{f.required && <span style={{ color: '#f43f5e' }}> *</span>}</Label>
          {f.description && <p className="text-[11px] mb-1.5" style={{ color: 'rgba(255,255,255,0.3)' }}>{f.description}</p>}
          <select style={inputCls} value={String(val)} onChange={e => set(e.target.value)}>
            {f.options.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
        </div>
      );
    }

    return (
      <div key={f.name}>
        <Label>{f.label}{f.required && <span style={{ color: '#f43f5e' }}> *</span>}</Label>
        {f.description && <p className="text-[11px] mb-1.5" style={{ color: 'rgba(255,255,255,0.3)' }}>{f.description}</p>}
        <input
          type={f.type === 'password' ? 'password' : f.type === 'number' ? 'number' : 'text'}
          style={inputCls}
          value={String(val)}
          placeholder={f.env_var ? `env: ${f.env_var}` : ''}
          onChange={e => set(f.type === 'number' ? Number(e.target.value) : e.target.value)}
        />
      </div>
    );
  };

  return (
    <div className="rounded-xl overflow-hidden"
      style={{ border: '1px solid rgba(99,102,241,0.15)', background: 'rgba(99,102,241,0.03)' }}>

      {/* Header row */}
      <div className="flex items-center gap-3 px-4 py-3">
        <span className="text-2xl leading-none">{tool.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-[13px]" style={{ color: 'rgba(255,255,255,0.88)' }}>{tool.label}</span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(99,102,241,0.1)', color: 'rgba(255,255,255,0.35)' }}>
              {tool.category}
            </span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
              style={{ background: `${statusColor}18`, color: statusColor }}>
              {statusLabel}
            </span>
          </div>
          <div className="text-[11px] mt-0.5 truncate" style={{ color: 'rgba(255,255,255,0.35)' }}>
            {tool.description}
          </div>
        </div>

        {/* Enable toggle */}
        <button
          type="button"
          onClick={() => { const next = !enabled; setEnabled(next); }}
          className="shrink-0 w-9 h-5 rounded-full relative transition-colors"
          style={{ background: enabled ? '#6366f1' : 'rgba(255,255,255,0.12)' }}
        >
          <span className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all"
            style={{ left: enabled ? '18px' : '2px' }} />
        </button>

        {/* Expand */}
        {tool.fields.length > 0 && (
          <button type="button" onClick={() => setExpanded(s => !s)}
            className="shrink-0 w-7 h-7 flex items-center justify-center rounded-lg"
            style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.4)' }}>
            {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      {/* Expanded config form */}
      {expanded && tool.fields.length > 0 && (
        <form onSubmit={save}
          className="border-t px-4 py-4 flex flex-col gap-4"
          style={{ borderColor: 'rgba(99,102,241,0.12)', background: 'rgba(0,0,0,0.15)' }}>
          <div className="grid grid-cols-2 gap-4">
            {tool.fields.map(f => renderField(f))}
          </div>
          <Feedback msg={msg} isError={isError} />
          <div className="flex items-center gap-2">
            <SaveBtn loading={saving} />
            <button type="button" onClick={test} disabled={testing}
              className="px-4 py-2 text-[13px] font-semibold rounded-lg"
              style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)',
                       opacity: testing ? 0.7 : 1 }}>
              {testing ? 'Testing…' : 'Test Connection'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

function IntegrationsSection() {
  const [tools,   setTools]   = useState<ToolConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [filter,  setFilter]  = useState('');

  useEffect(() => {
    api.get<{ data: ToolConfig[] }>('/integrations/tool-configs')
      .then(r => { setTools(r.data); setLoading(false); })
      .catch(e => { setError(e instanceof Error ? e.message : 'Failed to load'); setLoading(false); });
  }, []);

  const update = (updated: ToolConfig) =>
    setTools(prev => prev.map(t => t.tool_name === updated.tool_name ? updated : t));

  const filtered = filter
    ? tools.filter(t =>
        t.label.toLowerCase().includes(filter.toLowerCase()) ||
        t.category.toLowerCase().includes(filter.toLowerCase()))
    : tools;

  // Group by category
  const categories = [...new Set(filtered.map(t => t.category))];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-[18px] font-semibold shrink-0" style={{ color: 'rgba(255,255,255,0.92)' }}>
          Tools & Integrations
        </h2>
        <input
          style={{ ...inputCls, width: 200 }}
          placeholder="Filter tools…"
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
      </div>

      <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
        Configure credentials and settings for each tool. Values from environment variables are used as defaults.
        Expand a tool to override them.
      </p>

      {loading && <div className="text-[13px]" style={{ color: 'rgba(255,255,255,0.35)' }}>Loading tools…</div>}
      {error   && <Feedback msg={error} isError />}

      {categories.map(cat => (
        <div key={cat} className="space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-widest"
            style={{ color: 'rgba(255,255,255,0.25)' }}>
            {cat}
          </div>
          {filtered.filter(t => t.category === cat).map(t => (
            <ToolCard key={t.tool_name} tool={t} onUpdate={update} />
          ))}
        </div>
      ))}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-8 text-[13px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
          No tools found.
        </div>
      )}
    </div>
  );
}

// ── MCP Servers ───────────────────────────────────────────────────────────────

const EMPTY_MCP = {
  name: '', description: '', server_type: 'sse' as 'sse' | 'stdio',
  url: '', command: '', args: '', env_vars: '', headers: '', enabled: true,
};

function McpSection() {
  const [servers,  setServers]  = useState<MCPServer[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form,     setForm]     = useState({ ...EMPTY_MCP });
  const [saving,   setSaving]   = useState(false);
  const [formMsg,  setFormMsg]  = useState('');
  const [formErr,  setFormErr]  = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testMsgs, setTestMsgs] = useState<Record<string, { msg: string; err: boolean }>>({});

  const load = () => {
    setLoading(true);
    api.get<{ data: MCPServer[] }>('/integrations/mcp-servers')
      .then(r => { setServers(r.data); setLoading(false); })
      .catch(e => { setError(e instanceof Error ? e.message : 'Failed to load'); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const parseKV = (raw: string): Record<string, string> => {
    const obj: Record<string, string> = {};
    raw.split('\n').forEach(line => {
      const i = line.indexOf('=');
      if (i > 0) obj[line.slice(0, i).trim()] = line.slice(i + 1).trim();
    });
    return obj;
  };

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setFormMsg(''); setFormErr(false);
    try {
      await api.post('/integrations/mcp-servers', {
        name: form.name,
        description: form.description,
        server_type: form.server_type,
        url: form.url,
        command: form.command,
        args: form.args ? form.args.split(/\s+/).filter(Boolean) : [],
        headers: parseKV(form.headers),
        env_vars: parseKV(form.env_vars),
        enabled: form.enabled,
      });
      setForm({ ...EMPTY_MCP });
      setShowForm(false);
      load();
    } catch (err) {
      setFormMsg(err instanceof ApiError ? err.message : 'Create failed');
      setFormErr(true);
    } finally {
      setSaving(false);
    }
  };

  const del = async (id: string) => {
    if (!confirm('Remove this MCP server?')) return;
    try { await api.delete(`/integrations/mcp-servers/${id}`); load(); } catch {/* ignore */}
  };

  const testServer = async (id: string) => {
    setTestingId(id); setTestMsgs(p => ({ ...p, [id]: { msg: '', err: false } }));
    try {
      const res = await api.post<{ data: { status: string; tools: unknown[]; tool_count: number; error?: string } }>(
        `/integrations/mcp-servers/${id}/test`, {}
      );
      const d = res.data;
      const ok = d.status === 'connected';
      const count = d.tool_count ?? d.tools?.length ?? 0;
      setTestMsgs(p => ({
        ...p,
        [id]: {
          msg: ok ? `Connected · ${count} tool${count !== 1 ? 's' : ''} available` : (d.error ?? 'Test failed'),
          err: !ok,
        }
      }));
      if (ok) load(); // refresh to update tools_cache
    } catch (err) {
      setTestMsgs(p => ({
        ...p,
        [id]: { msg: err instanceof ApiError ? err.message : 'Test failed', err: true }
      }));
    } finally {
      setTestingId(null);
    }
  };

  const statusColor = (s: string) =>
    s === 'connected' ? '#10b981' : s === 'error' ? '#f43f5e' : 'rgba(255,255,255,0.3)';

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.92)' }}>MCP Servers</h2>
        <button onClick={() => setShowForm(s => !s)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold rounded-lg"
          style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.25)', color: '#6366f1' }}>
          <Plus className="w-3.5 h-3.5" />
          {showForm ? 'Cancel' : 'Add Server'}
        </button>
      </div>

      <p className="text-[12px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
        Connect to Model Context Protocol (MCP) servers to give agents access to additional tools.
        Supports SSE (HTTP) and stdio (local process) transports.
      </p>

      {/* Add server form */}
      {showForm && (
        <form onSubmit={create} className="rounded-xl p-4 flex flex-col gap-4"
          style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)' }}>
          <div className="text-[13px] font-semibold" style={{ color: 'rgba(255,255,255,0.7)' }}>New MCP Server</div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Name *</Label>
              <input style={inputCls} required value={form.name}
                onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="My MCP Server" />
            </div>
            <div>
              <Label>Type</Label>
              <select style={inputCls} value={form.server_type}
                onChange={e => setForm(p => ({ ...p, server_type: e.target.value as 'sse' | 'stdio' }))}>
                <option value="sse">SSE (HTTP)</option>
                <option value="stdio">stdio (local process)</option>
              </select>
            </div>
            <div className="col-span-2">
              <Label>Description</Label>
              <input style={inputCls} value={form.description}
                onChange={e => setForm(p => ({ ...p, description: e.target.value }))} placeholder="Optional description" />
            </div>

            {form.server_type === 'sse' ? (
              <>
                <div className="col-span-2">
                  <Label>URL *</Label>
                  <input style={inputCls} required value={form.url}
                    onChange={e => setForm(p => ({ ...p, url: e.target.value }))} placeholder="https://mcp.example.com" />
                </div>
                <div className="col-span-2">
                  <Label>Headers (KEY=VALUE, one per line)</Label>
                  <textarea style={{ ...inputCls, height: 72, resize: 'none' } as React.CSSProperties}
                    value={form.headers} onChange={e => setForm(p => ({ ...p, headers: e.target.value }))}
                    placeholder={'Authorization=Bearer token123\nX-Custom-Header=value'} />
                </div>
              </>
            ) : (
              <>
                <div>
                  <Label>Command *</Label>
                  <input style={inputCls} required value={form.command}
                    onChange={e => setForm(p => ({ ...p, command: e.target.value }))} placeholder="npx or python" />
                </div>
                <div>
                  <Label>Arguments (space-separated)</Label>
                  <input style={inputCls} value={form.args}
                    onChange={e => setForm(p => ({ ...p, args: e.target.value }))} placeholder="-y @modelcontextprotocol/server-filesystem /tmp" />
                </div>
                <div className="col-span-2">
                  <Label>Environment Variables (KEY=VALUE, one per line)</Label>
                  <textarea style={{ ...inputCls, height: 72, resize: 'none' } as React.CSSProperties}
                    value={form.env_vars} onChange={e => setForm(p => ({ ...p, env_vars: e.target.value }))}
                    placeholder={'API_KEY=sk-...\nDEBUG=true'} />
                </div>
              </>
            )}
          </div>

          <Feedback msg={formMsg} isError={formErr} />
          <div className="flex gap-2">
            <SaveBtn loading={saving} label="Add Server" />
          </div>
        </form>
      )}

      {loading && <div className="text-[13px]" style={{ color: 'rgba(255,255,255,0.35)' }}>Loading…</div>}
      {error   && <Feedback msg={error} isError />}

      {servers.length === 0 && !loading && (
        <div className="text-center py-10 rounded-xl"
          style={{ background: 'rgba(99,102,241,0.03)', border: '1px dashed rgba(99,102,241,0.15)', color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>
          <Server className="w-8 h-8 mx-auto mb-2 opacity-20" />
          No MCP servers connected yet. Add one above.
        </div>
      )}

      <div className="flex flex-col gap-3">
        {servers.map(s => {
          const tMsg = testMsgs[s.id];
          const isTesting = testingId === s.id;
          return (
            <div key={s.id} className="rounded-xl overflow-hidden"
              style={{ border: '1px solid rgba(99,102,241,0.15)', background: 'rgba(99,102,241,0.03)' }}>

              <div className="flex items-center gap-3 px-4 py-3">
                {/* Status dot */}
                <div className="w-2 h-2 rounded-full shrink-0"
                  style={{ background: statusColor(s.status), boxShadow: `0 0 6px ${statusColor(s.status)}` }} />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-[13px]" style={{ color: 'rgba(255,255,255,0.88)' }}>{s.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold"
                      style={{ background: 'rgba(99,102,241,0.12)', color: '#6366f1' }}>
                      {s.server_type.toUpperCase()}
                    </span>
                    {s.tools_cache.length > 0 && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold"
                        style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981' }}>
                        {s.tools_cache.length} tools
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] mt-0.5" style={{ color: 'rgba(255,255,255,0.3)' }}>
                    {s.server_type === 'sse' ? s.url : `${s.command} ${s.args.join(' ')}`}
                    {s.last_connected && (
                      <span className="ml-2">· last sync {new Date(s.last_connected).toLocaleString()}</span>
                    )}
                  </div>
                  {s.status === 'error' && s.error_msg && (
                    <div className="text-[11px] mt-0.5" style={{ color: '#f43f5e' }}>{s.error_msg}</div>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button type="button" onClick={() => testServer(s.id)} disabled={isTesting}
                    className="flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-semibold rounded-lg"
                    style={{ background: 'rgba(99,102,241,0.12)', color: '#6366f1',
                             border: '1px solid rgba(99,102,241,0.2)', opacity: isTesting ? 0.6 : 1 }}>
                    <RefreshCw className={`w-3 h-3 ${isTesting ? 'animate-spin' : ''}`} />
                    {isTesting ? 'Syncing…' : 'Sync'}
                  </button>
                  <button type="button" onClick={() => del(s.id)}
                    className="w-7 h-7 flex items-center justify-center rounded-lg"
                    style={{ background: 'rgba(244,63,94,0.08)', color: '#f43f5e' }}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Test result message */}
              {tMsg?.msg && (
                <div className="px-4 pb-3">
                  <Feedback msg={tMsg.msg} isError={tMsg.err} />
                </div>
              )}

              {/* Tool list (expanded when synced) */}
              {s.tools_cache.length > 0 && (
                <div className="border-t px-4 py-3"
                  style={{ borderColor: 'rgba(99,102,241,0.1)', background: 'rgba(0,0,0,0.1)' }}>
                  <div className="text-[10px] font-bold uppercase tracking-widest mb-2"
                    style={{ color: 'rgba(255,255,255,0.2)' }}>Available Tools</div>
                  <div className="flex flex-wrap gap-1.5">
                    {s.tools_cache.map(t => (
                      <span key={t.name}
                        className="text-[11px] px-2 py-0.5 rounded"
                        style={{ background: 'rgba(99,102,241,0.1)', color: 'rgba(255,255,255,0.55)' }}
                        title={t.description}>
                        {t.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [active, setActive] = useState<Section>('profile');

  const content: Record<Section, React.ReactNode> = {
    profile:       <ProfileSection />,
    security:      <SecuritySection />,
    llm:           <LlmSection />,
    notifications: <NotificationsSection />,
    apikey:        <ApiKeySection />,
    integrations:  <IntegrationsSection />,
    mcp:           <McpSection />,
  };

  return (
    <div className="h-full flex flex-col" style={{ background: '#060912' }}>
      <div className="max-w-5xl mx-auto w-full px-4 py-6 flex flex-col gap-4 flex-1">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'rgba(255,255,255,0.92)' }}>Settings</h1>
          <p className="text-[13px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Manage your Qubot preferences and integrations
          </p>
        </div>

        <div className="flex gap-5 flex-1 min-h-0">
          {/* Sidebar */}
          <nav className="w-52 shrink-0 flex flex-col gap-1">
            {sections.map(s => {
              const Icon = s.icon;
              const isActive = active === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => setActive(s.id)}
                  className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left text-[13px] font-medium transition-colors"
                  style={{
                    background: isActive ? 'rgba(99,102,241,0.15)' : 'transparent',
                    color: isActive ? '#6366f1' : 'rgba(255,255,255,0.5)',
                    border: isActive ? '1px solid rgba(99,102,241,0.25)' : '1px solid transparent',
                  }}
                >
                  <Icon className="w-4 h-4" />
                  {s.label}
                </button>
              );
            })}
          </nav>

          {/* Content panel */}
          <div className="flex-1 rounded-xl p-6 overflow-y-auto"
            style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(14px)', border: '1px solid rgba(99,102,241,0.15)' }}>
            {content[active]}
          </div>
        </div>
      </div>
    </div>
  );
}
