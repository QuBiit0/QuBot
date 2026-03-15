'use client';
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type AgentStatus = 'idle' | 'busy' | 'offline' | 'error';

interface Agent {
  id: number;
  name: string;
  role: string;
  skill: string;
  domain: string;
  status: AgentStatus;
  avatar_url?: string;
  system_prompt?: string;
}

interface AgentTask {
  id: number;
  title: string;
  status: string;
  priority: number;
}

const STATUS_CFG: Record<AgentStatus, { label: string; color: string; bg: string }> = {
  idle:    { label: 'Idle',    color: '#3fb950', bg: 'rgba(63,185,80,0.12)'   },
  busy:    { label: 'Working', color: '#f0a500', bg: 'rgba(240,165,0,0.12)'   },
  offline: { label: 'Offline', color: '#484f58', bg: 'rgba(72,79,88,0.12)'    },
  error:   { label: 'Error',   color: '#f85149', bg: 'rgba(248,81,73,0.12)'   },
};

const TASK_STATUS_CFG: Record<string, { label: string; color: string }> = {
  pending:     { label: 'Pending',     color: '#8b949e' },
  planning:    { label: 'Planning',    color: '#58a6ff' },
  in_progress: { label: 'In Progress', color: '#f0a500' },
  completed:   { label: 'Completed',   color: '#3fb950' },
  failed:      { label: 'Failed',      color: '#f85149' },
};

const DOMAIN_COLOR: Record<string, string> = {
  development: '#58a6ff',
  management:  '#a371f7',
  research:    '#3fb950',
  design:      '#f778ba',
  marketing:   '#f0a500',
  general:     '#8b949e',
};

const DOMAINS = ['development', 'management', 'research', 'design', 'marketing', 'general'];
const STATUSES: AgentStatus[] = ['idle', 'busy', 'offline', 'error'];

// ── Avatar ────────────────────────────────────────────────────────────────────
function Avatar({ agent, size = 56 }: { agent: Agent; size?: number }) {
  const c = DOMAIN_COLOR[agent.domain] ?? '#8b949e';
  return (
    <div
      className="flex items-center justify-center font-bold flex-shrink-0"
      style={{
        width: size, height: size, borderRadius: size * 0.28,
        background: `${c}18`, border: `1.5px solid ${c}40`, color: c,
        fontSize: size * 0.4,
      }}
    >
      {agent.name.charAt(0).toUpperCase()}
    </div>
  );
}

// ── Field ─────────────────────────────────────────────────────────────────────
function Field({
  label, value, edit, onChange, type = 'text',
}: {
  label: string;
  value: string;
  edit: boolean;
  onChange: (v: string) => void;
  type?: 'text' | 'textarea' | 'select-domain' | 'select-status';
}) {
  const base = {
    background: '#0a0f1e',
    border: '1px solid #1a2540',
    color: '#e6edf3',
    borderRadius: 8,
    outline: 'none',
    fontSize: 13,
    padding: '7px 10px',
    width: '100%',
  };

  if (!edit) {
    return (
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: '#484f58' }}>
          {label}
        </div>
        <div className="text-[13px]" style={{ color: '#e6edf3' }}>{value || '—'}</div>
      </div>
    );
  }

  if (type === 'select-domain') {
    return (
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: '#484f58' }}>{label}</div>
        <select value={value} onChange={e => onChange(e.target.value)} style={base as React.CSSProperties}>
          {DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>
    );
  }

  if (type === 'select-status') {
    return (
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: '#484f58' }}>{label}</div>
        <select value={value} onChange={e => onChange(e.target.value)} style={base as React.CSSProperties}>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
    );
  }

  if (type === 'textarea') {
    return (
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: '#484f58' }}>{label}</div>
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          rows={4}
          style={{ ...base, resize: 'vertical', fontFamily: 'inherit' } as React.CSSProperties}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: '#484f58' }}>{label}</div>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        style={base as React.CSSProperties}
        onFocus={e => (e.target.style.borderColor = '#3b6fff')}
        onBlur={e  => (e.target.style.borderColor = '#1a2540')}
      />
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function AgentDetailPage() {
  const params  = useParams();
  const router  = useRouter();
  const agentId = params?.id as string;

  const [agent,    setAgent]    = useState<Agent | null>(null);
  const [tasks,    setTasks]    = useState<AgentTask[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [edit,     setEdit]     = useState(false);
  const [saving,   setSaving]   = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [form,     setForm]     = useState<Partial<Agent>>({});
  const [error,    setError]    = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [agentRes, tasksRes] = await Promise.all([
        fetch(`${API}/api/v1/agents/${agentId}`),
        fetch(`${API}/api/v1/agents/${agentId}/tasks`),
      ]);
      if (!agentRes.ok) throw new Error('Agent not found');
      const agentData  = await agentRes.json();
      const tasksData  = tasksRes.ok ? await tasksRes.json() : [];
      setAgent(agentData);
      setForm(agentData);
      setTasks(Array.isArray(tasksData) ? tasksData : []);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load agent');
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async () => {
    if (!agent) return;
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/v1/agents/${agentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role:          form.role,
          skill:         form.skill,
          domain:        form.domain,
          status:        form.status,
          system_prompt: form.system_prompt,
        }),
      });
      if (!res.ok) throw new Error('Save failed');
      const updated = await res.json();
      setAgent(updated);
      setForm(updated);
      setEdit(false);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!agent) return;
    if (!confirm(`Delete agent "${agent.name}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API}/api/v1/agents/${agentId}`, { method: 'DELETE' });
      if (!res.ok && res.status !== 204) throw new Error('Delete failed');
      router.push('/agents');
    } catch (e: any) {
      setError(e.message);
      setDeleting(false);
    }
  };

  const f = (key: keyof Agent) => (v: string) =>
    setForm(prev => ({ ...prev, [key]: v }));

  // ── Loading ─────────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center h-[calc(100vh-76px)]" style={{ background: '#090e1a' }}>
      <div className="flex flex-col items-center gap-3">
        <div className="flex gap-1">
          {[0,1,2].map(i => (
            <span key={i} className="w-2 h-2 rounded-full animate-bounce"
              style={{ background: '#3b6fff', animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
        <span style={{ color: '#484f58', fontSize: 12 }}>Loading agent…</span>
      </div>
    </div>
  );

  // ── Error ───────────────────────────────────────────────────────────────────
  if (error && !agent) return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-76px)] gap-4" style={{ background: '#090e1a' }}>
      <div className="text-4xl">⚠️</div>
      <div style={{ color: '#f85149', fontSize: 14 }}>{error}</div>
      <Link href="/agents"
        className="px-4 py-2 text-[12px] font-semibold rounded-lg"
        style={{ background: 'linear-gradient(135deg,#3b6fff,#7c3aed)', color: '#fff' }}>
        ← Back to Agents
      </Link>
    </div>
  );

  if (!agent) return null;

  const st = STATUS_CFG[agent.status] ?? STATUS_CFG.offline;
  const dc = DOMAIN_COLOR[agent.domain] ?? '#8b949e';

  return (
    <div className="h-[calc(100vh-76px)] overflow-y-auto" style={{ background: '#090e1a' }}>
      <div className="max-w-4xl mx-auto px-4 py-6 flex flex-col gap-5">

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-[11px]" style={{ color: '#484f58' }}>
          <Link href="/agents" style={{ color: '#6b7c99' }} className="hover:underline">Agents</Link>
          <span>/</span>
          <span style={{ color: '#e6edf3' }}>{agent.name}</span>
        </div>

        {/* Header card */}
        <div className="rounded-xl p-5"
          style={{ background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.07)' }}>
          <div className="flex items-start gap-4">
            <Avatar agent={agent} size={64} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-[20px] font-bold" style={{ color: '#e6edf3' }}>{agent.name}</h1>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                  style={{ color: st.color, background: st.bg }}>
                  {st.label}
                </span>
                {agent.status === 'busy' && (
                  <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#f0a500' }} />
                )}
              </div>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <span className="text-[12px]" style={{ color: '#8b949e' }}>{agent.role}</span>
                <span style={{ color: '#2a3a5e' }}>·</span>
                <span className="text-[11px] px-2 py-0.5 rounded-md font-mono"
                  style={{ background: '#111927', color: '#8b949e' }}>{agent.skill}</span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md"
                  style={{ color: dc, background: `${dc}18` }}>{agent.domain}</span>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {!edit ? (
                <>
                  <button
                    onClick={() => setEdit(true)}
                    className="px-3 py-1.5 text-[12px] font-semibold rounded-lg transition-colors"
                    style={{ background: '#1a2540', color: '#8b949e', border: '1px solid #1e2d47' }}
                    onMouseEnter={e => { (e.target as HTMLElement).style.color = '#e6edf3'; }}
                    onMouseLeave={e => { (e.target as HTMLElement).style.color = '#8b949e'; }}
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="px-3 py-1.5 text-[12px] font-semibold rounded-lg transition-colors"
                    style={{ background: 'rgba(248,81,73,0.1)', color: '#f85149', border: '1px solid rgba(248,81,73,0.2)' }}
                  >
                    {deleting ? 'Deleting…' : 'Delete'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => { setEdit(false); setForm(agent); setError(''); }}
                    className="px-3 py-1.5 text-[12px] font-semibold rounded-lg"
                    style={{ background: '#1a2540', color: '#8b949e', border: '1px solid #1e2d47' }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-3 py-1.5 text-[12px] font-semibold rounded-lg"
                    style={{ background: 'linear-gradient(135deg,#3b6fff,#7c3aed)', color: '#fff' }}
                  >
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="rounded-lg px-4 py-3 text-[12px]"
            style={{ background: 'rgba(248,81,73,0.1)', border: '1px solid rgba(248,81,73,0.2)', color: '#f85149' }}>
            {error}
          </div>
        )}

        {/* Config grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Identity */}
          <div className="rounded-xl p-5 flex flex-col gap-4"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: '#484f58' }}>
              Identity
            </div>
            <Field label="Role"   value={form.role   ?? ''} edit={edit} onChange={f('role')} />
            <Field label="Skill"  value={form.skill  ?? ''} edit={edit} onChange={f('skill')} />
            <Field label="Domain" value={form.domain ?? ''} edit={edit} onChange={f('domain')} type="select-domain" />
            <Field label="Status" value={form.status ?? ''} edit={edit} onChange={f('status')} type="select-status" />
          </div>

          {/* System Prompt */}
          <div className="rounded-xl p-5 flex flex-col gap-4"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: '#484f58' }}>
              System Prompt
            </div>
            <Field
              label="Instructions"
              value={form.system_prompt ?? ''}
              edit={edit}
              onChange={f('system_prompt')}
              type="textarea"
            />
          </div>
        </div>

        {/* Task history */}
        <div className="rounded-xl overflow-hidden"
          style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="px-5 py-3 border-b flex items-center justify-between"
            style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: '#484f58' }}>
              Recent Tasks
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono"
              style={{ background: '#0f1525', color: '#484f58' }}>
              {tasks.length}
            </span>
          </div>

          {tasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 gap-2">
              <div className="text-2xl" style={{ filter: 'grayscale(1)', opacity: 0.4 }}>📋</div>
              <span style={{ color: '#484f58', fontSize: 12 }}>No tasks yet</span>
            </div>
          ) : (
            tasks.map(task => {
              const tst = TASK_STATUS_CFG[task.status] ?? { label: task.status, color: '#8b949e' };
              return (
                <div key={task.id}
                  className="flex items-center gap-3 px-5 py-2.5 border-b transition-colors"
                  style={{ borderColor: 'rgba(255,255,255,0.04)' }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#0f1525')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <span className="text-[10px] font-mono" style={{ color: '#484f58', width: 28 }}>
                    #{task.id}
                  </span>
                  <span className="flex-1 text-[12px] truncate" style={{ color: '#c9d1d9' }}>
                    {task.title}
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                    style={{ color: tst.color, background: `${tst.color}18` }}>
                    {tst.label}
                  </span>
                  <span className="text-[10px] w-16 text-right" style={{ color: '#484f58' }}>
                    P{task.priority}
                  </span>
                </div>
              );
            })
          )}
        </div>

      </div>
    </div>
  );
}
