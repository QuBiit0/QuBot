'use client';

import { useEffect, useState } from 'react';
import { Search, Plus, Star, Download, Zap, Code, Palette, Database, Globe, Shield, BookOpen, Settings, Trash2, Eye, Edit, GitBranch, FileText, Folder, ChevronRight, X, Check } from 'lucide-react';
import { api } from '@/lib/api';

interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  triggers: string[];
  icon: string;
  created_by: string | null;
  is_public: boolean;
  is_official: boolean;
  version: string;
  usage_count: number;
  rating_average: number;
  rating_count: number;
  base_path: string;
  has_scripts: boolean;
  has_templates: boolean;
  has_assets: boolean;
  has_references: boolean;
  created_at: string;
  updated_at: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  agent:       '#a855f7',
  coding:      '#10b981',
  design:      '#ec4899',
  data:        '#f97316',
  web:         '#3b82f6',
  security:    '#ef4444',
  documentation: '#6366f1',
  integration: '#06b6d4',
  custom:      '#8b5cf6',
};

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  agent:       <Zap className="w-4 h-4" />,
  coding:      <Code className="w-4 h-4" />,
  design:      <Palette className="w-4 h-4" />,
  data:        <Database className="w-4 h-4" />,
  web:         <Globe className="w-4 h-4" />,
  security:    <Shield className="w-4 h-4" />,
  documentation: <BookOpen className="w-4 h-4" />,
  integration: <GitBranch className="w-4 h-4" />,
  custom:      <FileText className="w-4 h-4" />,
};

function CategoryBadge({ category }: { category: string }) {
  const color = CATEGORY_COLORS[category] || '#6366f1';
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium"
      style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}>
      {CATEGORY_ICONS[category] || <FileText className="w-3 h-3" />}
      {category}
    </span>
  );
}

function SkillCard({ skill, onView, onEdit }: { skill: Skill; onView: () => void; onEdit: () => void }) {
  const color = CATEGORY_COLORS[skill.category] || '#6366f1';

  return (
    <div className="rounded-xl overflow-hidden transition-all duration-200 hover:scale-[1.01]"
      style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(14px)', border: `1px solid ${color}20` }}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="text-2xl w-10 h-10 flex items-center justify-center rounded-lg shrink-0"
            style={{ background: `${color}15`, border: `1px solid ${color}25` }}>
            {skill.icon || '📦'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-[14px]" style={{ color: 'rgba(255,255,255,0.92)' }}>
                {skill.name}
              </h3>
              {skill.is_official && (
                <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded uppercase"
                  style={{ background: 'rgba(234,179,8,0.1)', color: '#eab308', border: '1px solid rgba(234,179,8,0.2)' }}>
                  Official
                </span>
              )}
            </div>
            <p className="text-[12px] mt-1 line-clamp-2" style={{ color: 'rgba(255,255,255,0.45)' }}>
              {skill.description}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <CategoryBadge category={skill.category} />
          {skill.triggers.slice(0, 3).map(trigger => (
            <span key={trigger} className="text-[10px] px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.35)' }}>
              {trigger}
            </span>
          ))}
          {skill.triggers.length > 3 && (
            <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
              +{skill.triggers.length - 3}
            </span>
          )}
        </div>

        <div className="flex items-center gap-4 mt-3 pt-3 border-t" style={{ borderColor: `${color}10` }}>
          <div className="flex items-center gap-1">
            <Star className="w-3 h-3" style={{ color }} />
            <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.5)' }}>
              {skill.rating_average > 0 ? skill.rating_average.toFixed(1) : '-'}
            </span>
          </div>
          <div className="text-[11px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
            v{skill.version}
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <button onClick={onView}
              className="p-1.5 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: 'rgba(255,255,255,0.4)' }}>
              <Eye className="w-4 h-4" />
            </button>
            <button onClick={onEdit}
              className="p-1.5 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: 'rgba(255,255,255,0.4)' }}>
              <Edit className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function CreateModal({ onClose, onCreated }: {
  onClose: () => void;
  onCreated: (skill: Skill) => void;
}) {
  const [form, setForm] = useState({
    id: '',
    name: '',
    description: '',
    category: 'custom',
    icon: '📦',
    triggers: '',
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const categories = ['agent', 'coding', 'design', 'data', 'web', 'security', 'documentation', 'integration', 'custom'];
  const icons = ['📦', '🔧', '🤖', '⚡', '🎨', '📊', '🌐', '🛡️', '📝', '🔗', '✨', '🚀', '💡', '🎯', '🔍'];

  const create = async () => {
    if (!form.id || !form.name) {
      setError('ID and name are required');
      return;
    }

    setCreating(true);
    setError('');

    try {
      const res = await api.post<{ data: Skill }>('/skills', {
        id: form.id.toLowerCase().replace(/\s+/g, '-'),
        name: form.name,
        description: form.description,
        category: form.category,
        icon: form.icon,
        triggers: form.triggers.split(',').map(t => t.trim()).filter(Boolean),
        is_public: true,
      });

      onCreated(res.data);
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create skill');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(3,6,8,0.85)', backdropFilter: 'blur(8px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="w-full max-w-md rounded-xl overflow-hidden"
        style={{ background: '#060912', border: '1px solid rgba(99,102,241,0.25)' }}>
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: 'rgba(99,102,241,0.15)' }}>
          <h2 className="font-semibold text-[15px]" style={{ color: 'rgba(255,255,255,0.92)' }}>Create New Skill</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg" style={{ color: 'rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.05)' }}>
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 flex flex-col gap-4">
          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Skill ID (slug)
            </label>
            <input
              className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
              style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
              placeholder="my-awesome-skill"
              value={form.id}
              onChange={e => setForm(f => ({ ...f, id: e.target.value }))}
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Name *
            </label>
            <input
              className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
              style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
              placeholder="My Awesome Skill"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Description
            </label>
            <textarea
              className="w-full text-[13px] rounded-lg px-3 py-2 outline-none resize-none"
              style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)', height: 80 }}
              placeholder="What does this skill do..."
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
                Category
              </label>
              <select
                className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
                style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
                value={form.category}
                onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
                {categories.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
                Icon
              </label>
              <div className="flex flex-wrap gap-1">
                {icons.map(icon => (
                  <button key={icon}
                    onClick={() => setForm(f => ({ ...f, icon }))}
                    className="w-8 h-8 rounded-lg text-base flex items-center justify-center transition-colors"
                    style={{
                      background: form.icon === icon ? 'rgba(99,102,241,0.3)' : 'rgba(0,0,0,0.4)',
                      border: form.icon === icon ? '1px solid rgba(99,102,241,0.5)' : '1px solid rgba(99,102,241,0.1)',
                    }}>
                    {icon}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Triggers (comma-separated)
            </label>
            <input
              className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
              style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
              placeholder="/skill, skill-name"
              value={form.triggers}
              onChange={e => setForm(f => ({ ...f, triggers: e.target.value }))}
            />
          </div>

          {error && (
            <div className="px-3 py-2 rounded-lg text-[12px]" style={{ background: 'rgba(244,63,94,0.1)', color: '#f43f5e' }}>
              {error}
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <button onClick={onClose}
              className="flex-1 py-2 rounded-lg text-[13px] font-medium"
              style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.6)' }}>
              Cancel
            </button>
            <button onClick={create} disabled={creating}
              className="flex-1 py-2 rounded-lg text-[13px] font-semibold"
              style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', opacity: creating ? 0.7 : 1 }}>
              {creating ? 'Creating...' : 'Create Skill'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SkillDetailModal({ skill, onClose }: { skill: Skill; onClose: () => void }) {
  const color = CATEGORY_COLORS[skill.category] || '#6366f1';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(3,6,8,0.85)', backdropFilter: 'blur(8px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="w-full max-w-2xl rounded-xl overflow-hidden max-h-[90vh] flex flex-col"
        style={{ background: '#060912', border: `1px solid ${color}30` }}>
        <div className="flex items-center justify-between px-5 py-4 border-b shrink-0" style={{ borderColor: `${color}20` }}>
          <div className="flex items-center gap-3">
            <span className="text-3xl">{skill.icon}</span>
            <div>
              <h2 className="font-semibold text-[16px]" style={{ color: 'rgba(255,255,255,0.92)' }}>{skill.name}</h2>
              <div className="flex items-center gap-2 mt-1">
                <CategoryBadge category={skill.category} />
                <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.35)' }}>v{skill.version}</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg" style={{ color: 'rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.05)' }}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="overflow-y-auto p-5 flex-1">
          <p className="text-[13px]" style={{ color: 'rgba(255,255,255,0.65)' }}>
            {skill.description}
          </p>

          <div className="grid grid-cols-3 gap-3 mt-5">
            <div className="rounded-lg p-3" style={{ background: 'rgba(0,0,0,0.3)' }}>
              <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>Used</div>
              <div className="text-[18px] font-bold" style={{ color }}>{skill.usage_count}</div>
            </div>
            <div className="rounded-lg p-3" style={{ background: 'rgba(0,0,0,0.3)' }}>
              <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>Rating</div>
              <div className="flex items-center gap-1">
                <Star className="w-4 h-4" style={{ color }} />
                <span className="text-[18px] font-bold" style={{ color }}>{skill.rating_average > 0 ? skill.rating_average.toFixed(1) : '-'}</span>
              </div>
            </div>
            <div className="rounded-lg p-3" style={{ background: 'rgba(0,0,0,0.3)' }}>
              <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>Reviews</div>
              <div className="text-[18px] font-bold" style={{ color }}>{skill.rating_count}</div>
            </div>
          </div>

          <div className="mt-5">
            <h3 className="text-[12px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'rgba(255,255,255,0.3)' }}>
              Triggers
            </h3>
            <div className="flex flex-wrap gap-2">
              {skill.triggers.map(t => (
                <span key={t} className="px-2 py-1 rounded text-[12px] font-mono"
                  style={{ background: `${color}15`, color: 'rgba(255,255,255,0.7)' }}>
                  {t}
                </span>
              ))}
              {skill.triggers.length === 0 && (
                <span className="text-[12px]" style={{ color: 'rgba(255,255,255,0.3)' }}>No triggers defined</span>
              )}
            </div>
          </div>

          <div className="mt-5">
            <h3 className="text-[12px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'rgba(255,255,255,0.3)' }}>
              Components
            </h3>
            <div className="flex flex-wrap gap-2">
              {[
                { key: 'has_scripts', icon: <Code className="w-3 h-3" />, label: 'Scripts' },
                { key: 'has_templates', icon: <FileText className="w-3 h-3" />, label: 'Templates' },
                { key: 'has_assets', icon: <Folder className="w-3 h-3" />, label: 'Assets' },
                { key: 'has_references', icon: <BookOpen className="w-3 h-3" />, label: 'References' },
              ].map(item => (
                <span key={item.key}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px]"
                  style={{
                    background: skill[item.key as keyof Skill] ? `${color}15` : 'rgba(0,0,0,0.2)',
                    color: skill[item.key as keyof Skill] ? color : 'rgba(255,255,255,0.25)',
                  }}>
                  {item.icon}
                  {item.label}
                  {skill[item.key as keyof Skill] ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-5">
            <h3 className="text-[12px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'rgba(255,255,255,0.3)' }}>
              Path
            </h3>
            <code className="text-[11px] px-2 py-1 rounded block" style={{ background: 'rgba(0,0,0,0.3)', color: 'rgba(255,255,255,0.5)' }}>
              {skill.base_path}
            </code>
          </div>
        </div>

        <div className="px-5 py-4 border-t shrink-0" style={{ borderColor: `${color}20` }}>
          <button onClick={onClose}
            className="w-full py-2 rounded-lg text-[13px] font-medium"
            style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.6)' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [showOfficial, setShowOfficial] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);

  const loadSkills = () => {
    setLoading(true);
    api.get<{ data: Skill[] }>('/skills')
      .then(res => {
        setSkills(res.data ?? []);
        setLoading(false);
      })
      .catch(e => {
        setError(e instanceof Error ? e.message : 'Failed to load skills');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadSkills();
  }, []);

  const categories = [...new Set(skills.map(s => s.category))];

  const filteredSkills = skills.filter(skill => {
    if (search) {
      const s = search.toLowerCase();
      if (!skill.name.toLowerCase().includes(s) && !skill.description.toLowerCase().includes(s)) {
        return false;
      }
    }
    if (activeCategory && skill.category !== activeCategory) return false;
    if (showOfficial && !skill.is_official) return false;
    return true;
  });

  const stats = {
    total: skills.length,
    official: skills.filter(s => s.is_official).length,
    categories: new Set(skills.map(s => s.category)).size,
  };

  return (
    <div className="h-full overflow-y-auto" style={{ background: 'linear-gradient(180deg, #060912 0%, #0a0f1a 100%)' }}>
      <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col gap-5">

        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'rgba(255,255,255,0.92)' }}>Skills</h1>
            <p className="text-[13px] mt-1" style={{ color: 'rgba(255,255,255,0.45)' }}>
              Reusable agent capabilities and workflows
            </p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold transition-opacity hover:opacity-90"
            style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff' }}>
            <Plus className="w-4 h-4" />
            New Skill
          </button>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'rgba(255,255,255,0.3)' }} />
              <input
                type="text"
                className="w-full pl-10 pr-4 py-2 text-[13px] rounded-lg outline-none"
                style={{ background: 'rgba(6,9,18,0.88)', border: '1px solid rgba(99,102,241,0.15)', color: 'rgba(255,255,255,0.85)' }}
                placeholder="Search skills..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer" style={{ background: 'rgba(6,9,18,0.88)', border: '1px solid rgba(99,102,241,0.15)' }}>
              <input type="checkbox" checked={showOfficial} onChange={e => setShowOfficial(e.target.checked)} className="w-4 h-4 accent-indigo-500" />
              <span className="text-[12px]" style={{ color: 'rgba(255,255,255,0.6)' }}>Official Only</span>
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
              }}>
              All ({stats.total})
            </button>
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat === activeCategory ? null : cat)}
                className="px-3 py-1.5 text-[12px] font-medium rounded-lg transition-all flex items-center gap-1.5"
                style={{
                  background: activeCategory === cat ? `${CATEGORY_COLORS[cat] || '#6366f1'}20` : 'rgba(255,255,255,0.05)',
                  color: activeCategory === cat ? CATEGORY_COLORS[cat] || '#6366f1' : 'rgba(255,255,255,0.5)',
                  border: activeCategory === cat ? `1px solid ${CATEGORY_COLORS[cat] || '#6366f1'}40` : '1px solid transparent',
                }}>
                {CATEGORY_ICONS[cat] || <FileText className="w-3 h-3" />}
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl p-4" style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#6366f1' }}>{stats.total}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Total Skills</div>
          </div>
          <div className="rounded-xl p-4" style={{ background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#eab308' }}>{stats.official}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Official</div>
          </div>
          <div className="rounded-xl p-4" style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#10b981' }}>{stats.categories}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Categories</div>
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

        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredSkills.map(skill => (
              <SkillCard
                key={skill.id}
                skill={skill}
                onView={() => setSelectedSkill(skill)}
                onEdit={() => setSelectedSkill(skill)}
              />
            ))}
          </div>
        )}

        {!loading && filteredSkills.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.1)' }}>
              <FileText className="w-8 h-8" style={{ color: 'rgba(255,255,255,0.2)' }} />
            </div>
            <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>
              {search ? 'No skills match your search' : 'No skills yet'}
            </span>
            {!search && (
              <button onClick={() => setShowCreate(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium mt-2"
                style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1' }}>
                <Plus className="w-4 h-4" />
                Create your first skill
              </button>
            )}
          </div>
        )}
      </div>

      {showCreate && (
        <CreateModal
          onClose={() => setShowCreate(false)}
          onCreated={(skill) => {
            setSkills(prev => [skill, ...prev]);
            setShowCreate(false);
          }}
        />
      )}

      {selectedSkill && (
        <SkillDetailModal
          skill={selectedSkill}
          onClose={() => setSelectedSkill(null)}
        />
      )}
    </div>
  );
}
