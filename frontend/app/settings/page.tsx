'use client';

import { useState, useEffect } from 'react';
import { Bell, Shield, User, Cpu, Key } from 'lucide-react';
import { authApi, api, ApiError } from '@/lib/api';
import type { UserResponse } from '@/lib/api';

type Section = 'profile' | 'security' | 'llm' | 'notifications' | 'apikey';

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

const sections: { id: Section; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'profile',       label: 'Profile',         icon: User  },
  { id: 'security',      label: 'Security',        icon: Shield },
  { id: 'llm',           label: 'LLM Configs',     icon: Cpu   },
  { id: 'notifications', label: 'Notifications',   icon: Bell  },
  { id: 'apikey',        label: 'API Key',         icon: Key   },
];

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

// ── Profile section ──────────────────────────────────────────────────────────
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

// ── Security section ─────────────────────────────────────────────────────────
function SecuritySection() {
  const [current,  setCurrent]  = useState('');
  const [newPw,    setNewPw]    = useState('');
  const [confirm,  setConfirm]  = useState('');
  const [loading,  setLoading]  = useState(false);
  const [msg,      setMsg]      = useState('');
  const [isError,  setIsError]  = useState(false);

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

// ── LLM Configs section ───────────────────────────────────────────────────────
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
    try {
      await api.delete(`/llm-configs/${id}`);
      load();
    } catch {/* ignore */}
  };

  const PROVIDERS = ['OPENAI', 'ANTHROPIC', 'GOOGLE', 'GROQ', 'OLLAMA', 'LOCAL'];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.92)' }}>LLM Configurations</h2>
        <button
          onClick={() => setShowForm(s => !s)}
          className="px-3 py-1.5 text-[12px] font-semibold rounded-lg"
          style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.25)', color: '#6366f1' }}
        >
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
          <div className="flex gap-2">
            <SaveBtn loading={saving} label="Create Config" />
          </div>
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
            <button
              onClick={() => del(c.id)}
              className="text-[11px] px-2 py-1 rounded"
              style={{ color: '#f43f5e', background: 'rgba(244,63,94,0.08)' }}
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── API Key section ───────────────────────────────────────────────────────────
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
        Generate an API key for programmatic access to Qubot. Use it in the <code style={{ color: '#6366f1' }}>X-API-Key</code> header.
      </p>

      {apiKey && (
        <div className="rounded-xl p-4" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
          <Label>Your API Key (copy now)</Label>
          <div className="flex items-center gap-2 mt-1">
            <code className="flex-1 text-[12px] break-all px-3 py-2 rounded-lg"
              style={{ background: 'rgba(0,0,0,0.4)', color: '#10b981', fontFamily: 'monospace' }}>
              {apiKey}
            </code>
            <button
              onClick={() => { navigator.clipboard.writeText(apiKey); }}
              className="px-3 py-2 text-[11px] font-semibold rounded-lg shrink-0"
              style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981' }}
            >
              Copy
            </button>
          </div>
        </div>
      )}

      <Feedback msg={msg} isError={isError} />

      <div className="flex gap-2">
        <button
          onClick={generate}
          disabled={loading}
          className="px-4 py-2 text-[13px] font-semibold rounded-lg"
          style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', opacity: loading ? 0.7 : 1 }}
        >
          {loading ? 'Generating…' : 'Generate New Key'}
        </button>
        <button
          onClick={revoke}
          disabled={revoking}
          className="px-4 py-2 text-[13px] font-semibold rounded-lg"
          style={{ background: 'rgba(244,63,94,0.08)', color: '#f43f5e', border: '1px solid rgba(244,63,94,0.2)' }}
        >
          {revoking ? 'Revoking…' : 'Revoke Key'}
        </button>
      </div>
    </div>
  );
}

// ── Notifications section ─────────────────────────────────────────────────────
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

// ── Main ─────────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const [active, setActive] = useState<Section>('profile');

  const content: Record<Section, React.ReactNode> = {
    profile:       <ProfileSection />,
    security:      <SecuritySection />,
    llm:           <LlmSection />,
    notifications: <NotificationsSection />,
    apikey:        <ApiKeySection />,
  };

  return (
    <div className="h-full flex flex-col" style={{ background: '#060912' }}>
      <div className="max-w-5xl mx-auto w-full px-4 py-6 flex flex-col gap-4 flex-1">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'rgba(255,255,255,0.92)' }}>Settings</h1>
          <p className="text-[13px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Manage your Qubot preferences and integrations</p>
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

          {/* Content */}
          <div className="flex-1 rounded-xl p-6 overflow-y-auto"
            style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(14px)', border: '1px solid rgba(99,102,241,0.15)' }}>
            {content[active]}
          </div>
        </div>
      </div>
    </div>
  );
}
