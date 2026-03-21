'use client';
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { agentsApi, ApiError } from '@/lib/api';
import { Agent, DOMAIN_CONFIG } from '@/types';

type AgentStatus = 'IDLE' | 'WORKING' | 'ERROR' | 'OFFLINE';

const STATUS_CFG: Record<AgentStatus, { label: string; color: string; bg: string }> = {
  IDLE:    { label: 'Idle',    color: '#10b981', bg: 'rgba(16,185,129,0.12)'  },
  WORKING: { label: 'Working', color: '#f0a500', bg: 'rgba(240,165,0,0.12)'   },
  OFFLINE: { label: 'Offline', color: '#64748b', bg: 'rgba(100,116,139,0.12)' },
  ERROR:   { label: 'Error',   color: '#f43f5e', bg: 'rgba(244,63,94,0.12)'   },
};

const DOMAINS = Object.keys(DOMAIN_CONFIG) as (keyof typeof DOMAIN_CONFIG)[];
const STATUSES: AgentStatus[] = ['IDLE', 'WORKING', 'OFFLINE', 'ERROR'];

// ── Avatar ────────────────────────────────────────────────────────────────────
function Avatar({ agent, size = 56 }: { agent: Agent; size?: number }) {
  const domainKey = (agent.domain?.toUpperCase() ?? 'OTHER') as keyof typeof DOMAIN_CONFIG;
  const c = DOMAIN_CONFIG[domainKey]?.color ?? '#6b7280';
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
  const base: React.CSSProperties = {
    background: '#060912',
    border: '1px solid rgba(99,102,241,0.18)',
    color: 'rgba(255,255,255,0.9)',
    borderRadius: 8,
    outline: 'none',
    fontSize: 13,
    padding: '7px 10px',
    width: '100%',
  };

  if (!edit) {
    return (
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>
          {label}
        </div>
        <div className="text-[13px]" style={{ color: 'rgba(255,255,255,0.85)' }}>{value || '—'}</div>
      </div>
    );
  }

  if (type === 'select-domain') {
    return (
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>{label}</div>
        <select value={value} onChange={e => onChange(e.target.value)} style={base}>
          {DOMAINS.map(d => (
            <option key={d} value={d}>{DOMAIN_CONFIG[d]?.label ?? d}</option>
          ))}
        </select>
      </div>
    );
  }

  if (type === 'select-status') {
    return (
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>{label}</div>
        <select value={value} onChange={e => onChange(e.target.value)} style={base}>
          {STATUSES.map(s => <option key={s} value={s}>{STATUS_CFG[s].label}</option>)}
        </select>
      </div>
    );
  }

  if (type === 'textarea') {
    return (
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>{label}</div>
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          rows={5}
          style={{ ...base, resize: 'vertical', fontFamily: 'ui-monospace, SFMono-Regular, monospace', fontSize: 12 }}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>{label}</div>
      <input value={value} onChange={e => onChange(e.target.value)} style={base} />
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function AgentDetailPage() {
  const params  = useParams();
  const router  = useRouter();
  const agentId = params?.id as string;

  const [agent,    setAgent]    = useState<Agent | null>(null);
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
      const res = await agentsApi.getById(agentId);
      const data = res.data ?? (res as unknown as Agent);
      setAgent(data);
      setForm(data);
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Failed to load agent';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async () => {
    if (!agent) return;
    setSaving(true);
    setError('');
    try {
      const res = await agentsApi.update(String(agentId), {
        role:        form.role,
        domain:      form.domain,
        description: form.description,
        config:      form.config,
      });
      const updated = res.data ?? (res as unknown as Agent);
      setAgent(updated);
      setForm(updated);
      setEdit(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!agent) return;
    if (!confirm(`Delete agent "${agent.name}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await agentsApi.delete(String(agentId));
      router.push('/agents');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Delete failed');
      setDeleting(false);
    }
  };

  const f = (key: keyof Agent) => (v: string) =>
    setForm(prev => ({ ...prev, [key]: v }));

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center h-[calc(100vh-76px)]"
      style={{ background: '#060912' }}>
      <div className="flex flex-col items-center gap-3">
        <div className="flex gap-1">
          {[0, 1, 2].map(i => (
            <span key={i} className="w-2 h-2 rounded-full animate-bounce"
              style={{ background: '#6366f1', animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
        <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12 }}>Loading agent…</span>
      </div>
    </div>
  );

  // ── Error ────────────────────────────────────────────────────────────────────
  if (error && !agent) return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-76px)] gap-4"
      style={{ background: '#060912' }}>
      <div className="text-4xl">⚠️</div>
      <div style={{ color: '#f43f5e', fontSize: 14 }}>{error}</div>
      <Link href="/agents"
        className="px-4 py-2 text-[12px] font-semibold rounded-lg"
        style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff' }}>
        ← Back to Agents
      </Link>
    </div>
  );

  if (!agent) return null;

  const statusKey = (agent.status?.toUpperCase() ?? 'OFFLINE') as AgentStatus;
  const st = STATUS_CFG[statusKey] ?? STATUS_CFG.OFFLINE;
  const domainKey = (agent.domain?.toUpperCase() ?? 'OTHER') as keyof typeof DOMAIN_CONFIG;
  const domainCfg = DOMAIN_CONFIG[domainKey];

  return (
    <div className="h-[calc(100vh-76px)] overflow-y-auto" style={{ background: '#060912' }}>
      <div className="max-w-4xl mx-auto px-4 py-6 flex flex-col gap-5">

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
          <Link href="/dashboard" style={{ color: '#6366f1' }} className="hover:underline flex items-center gap-1">
            <span>🏠</span> Office
          </Link>
          <span>/</span>
          <Link href="/agents" style={{ color: 'rgba(255,255,255,0.5)' }} className="hover:underline">Agents</Link>
          <span>/</span>
          <span style={{ color: 'rgba(255,255,255,0.85)' }}>{agent.name}</span>
        </div>

        {/* Header card */}
        <div className="rounded-xl p-5"
          style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(14px)', border: '1px solid rgba(99,102,241,0.22)' }}>
          <div className="flex items-start gap-4">
            <Avatar agent={agent} size={64} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-[20px] font-bold" style={{ color: 'rgba(255,255,255,0.92)' }}>{agent.name}</h1>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                  style={{ color: st.color, background: st.bg }}>
                  ● {st.label}
                </span>
                {statusKey === 'WORKING' && (
                  <span className="w-2 h-2 rounded-full animate-ping" style={{ background: '#10b981' }} />
                )}
              </div>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <span className="text-[12px]" style={{ color: 'rgba(255,255,255,0.55)' }}>{agent.role}</span>
                {domainCfg && (
                  <>
                    <span style={{ color: 'rgba(99,102,241,0.4)' }}>·</span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md"
                      style={{ color: domainCfg.color, background: `${domainCfg.color}18` }}>
                      {domainCfg.icon} {domainCfg.label}
                    </span>
                  </>
                )}
              </div>
              {agent.description && (
                <p className="text-[12px] mt-1.5 line-clamp-2" style={{ color: 'rgba(255,255,255,0.45)' }}>
                  {agent.description}
                </p>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {!edit ? (
                <>
                  <button
                    onClick={() => setEdit(true)}
                    className="px-3 py-1.5 text-[12px] font-semibold rounded-lg transition-colors"
                    style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.6)', border: '1px solid rgba(99,102,241,0.18)' }}
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="px-3 py-1.5 text-[12px] font-semibold rounded-lg"
                    style={{ background: 'rgba(244,63,94,0.08)', color: '#f43f5e', border: '1px solid rgba(244,63,94,0.2)' }}
                  >
                    {deleting ? 'Deleting…' : 'Delete'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => { setEdit(false); setForm(agent); setError(''); }}
                    className="px-3 py-1.5 text-[12px] font-semibold rounded-lg"
                    style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.6)', border: '1px solid rgba(99,102,241,0.18)' }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-3 py-1.5 text-[12px] font-semibold rounded-lg"
                    style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', opacity: saving ? 0.7 : 1 }}
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
            style={{ background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.2)', color: '#f43f5e' }}>
            {error}
          </div>
        )}

        {/* Config grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Identity */}
          <div className="rounded-xl p-5 flex flex-col gap-4"
            style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(10px)', border: '1px solid rgba(99,102,241,0.15)' }}>
            <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'rgba(255,255,255,0.3)' }}>
              Identity
            </div>
            <Field label="Role"        value={form.role   ?? ''} edit={edit} onChange={f('role')} />
            <Field label="Domain"      value={form.domain ?? ''} edit={edit} onChange={f('domain')} type="select-domain" />
            <Field label="Status"      value={form.status ?? ''} edit={edit} onChange={f('status')} type="select-status" />
            <Field label="Description" value={form.description ?? ''} edit={edit} onChange={f('description')} />
          </div>

          {/* Stats */}
          <div className="rounded-xl p-5 flex flex-col gap-4"
            style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(10px)', border: '1px solid rgba(99,102,241,0.15)' }}>
            <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'rgba(255,255,255,0.3)' }}>
              Info
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>ID</div>
              <div className="text-[12px] font-mono" style={{ color: 'rgba(255,255,255,0.5)' }}>{agent.id}</div>
            </div>
            {agent.created_at && (
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>Created</div>
                <div className="text-[12px]" style={{ color: 'rgba(255,255,255,0.55)' }}>
                  {new Date(agent.created_at).toLocaleString()}
                </div>
              </div>
            )}
            {agent.updated_at && (
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>Updated</div>
                <div className="text-[12px]" style={{ color: 'rgba(255,255,255,0.55)' }}>
                  {new Date(agent.updated_at).toLocaleString()}
                </div>
              </div>
            )}
            {agent.current_task && (
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>Current Task</div>
                <div className="text-[12px]" style={{ color: '#6366f1' }}>{agent.current_task.title}</div>
              </div>
            )}
          </div>
        </div>

        {/* System Prompt / Config */}
        <div className="rounded-xl p-5 flex flex-col gap-4"
          style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(10px)', border: '1px solid rgba(99,102,241,0.15)' }}>
          <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'rgba(255,255,255,0.3)' }}>
            System Prompt
          </div>
          <Field
            label="Instructions"
            value={(form.config?.system_prompt as string) ?? ''}
            edit={edit}
            onChange={v => setForm(prev => ({ ...prev, config: { ...(prev.config ?? {}), system_prompt: v } }))}
            type="textarea"
          />
        </div>

      </div>
    </div>
  );
}
