'use client';

import { useState, useEffect } from 'react';
import { Server, Plus, Search, Cpu, HardDrive, Network, Wifi, WifiOff, Trash2, RefreshCw, Terminal, Globe, Circle, X, Check } from 'lucide-react';
import { api } from '@/lib/api';

interface Node {
  id: string;
  name: string;
  host: string;
  port: number;
  status: 'online' | 'offline' | 'busy' | 'error';
  capabilities: string[];
  mac_address?: string;
  ssh_key_path?: string;
  last_seen?: string;
  active_tasks: number;
  cpu_usage?: number;
  memory_usage?: number;
  disk_usage?: number;
}

const CAPABILITY_ICONS: Record<string, React.ReactNode> = {
  general: <Cpu className="w-3 h-3" />,
  coding: <Terminal className="w-3 h-3" />,
  browser: <Globe className="w-3 h-3" />,
  storage: <HardDrive className="w-3 h-3" />,
  network: <Network className="w-3 h-3" />,
};

const STATUS_COLORS: Record<string, string> = {
  online: '#22c55e',
  offline: '#6b7280',
  busy: '#f59e0b',
  error: '#ef4444',
};

function NodeCard({ node, onDelete }: { node: Node; onDelete: () => void }) {
  const statusColor = STATUS_COLORS[node.status];
  const isOnline = node.status === 'online' || node.status === 'busy';

  return (
    <div className="rounded-xl overflow-hidden transition-all duration-200 hover:scale-[1.01]"
      style={{ background: 'rgba(6,9,18,0.88)', backdropFilter: 'blur(14px)', border: `1px solid ${statusColor}20` }}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `${statusColor}15`, border: `1px solid ${statusColor}25` }}>
            <Server className="w-6 h-6" style={{ color: statusColor }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-[14px]" style={{ color: 'rgba(255,255,255,0.92)' }}>
                {node.name}
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded uppercase font-medium"
                style={{ background: `${statusColor}15`, color: statusColor }}>
                {node.status}
              </span>
            </div>
            <p className="text-[12px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
              {node.host}:{node.port}
            </p>
          </div>
          <div className="flex items-center gap-1">
            {isOnline ? (
              <Wifi className="w-4 h-4" style={{ color: statusColor }} />
            ) : (
              <WifiOff className="w-4 h-4 text-gray-500" />
            )}
          </div>
        </div>

        {node.capabilities.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {node.capabilities.map(cap => (
              <span key={cap} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px]"
                style={{ background: 'rgba(99,102,241,0.1)', color: 'rgba(255,255,255,0.5)' }}>
                {CAPABILITY_ICONS[cap] || <Circle className="w-3 h-3" />}
                {cap}
              </span>
            ))}
          </div>
        )}

        {isOnline && (
          <div className="grid grid-cols-3 gap-2 mt-3">
            <div className="p-2 rounded-lg" style={{ background: 'rgba(0,0,0,0.3)' }}>
              <div className="text-[14px] font-bold" style={{ color: '#3b82f6' }}>{node.cpu_usage ?? 0}%</div>
              <div className="text-[9px]" style={{ color: 'rgba(255,255,255,0.3)' }}>CPU</div>
            </div>
            <div className="p-2 rounded-lg" style={{ background: 'rgba(0,0,0,0.3)' }}>
              <div className="text-[14px] font-bold" style={{ color: '#22c55e' }}>{node.memory_usage ?? 0}%</div>
              <div className="text-[9px]" style={{ color: 'rgba(255,255,255,0.3)' }}>RAM</div>
            </div>
            <div className="p-2 rounded-lg" style={{ background: 'rgba(0,0,0,0.3)' }}>
              <div className="text-[14px] font-bold" style={{ color: '#f59e0b' }}>{node.active_tasks}</div>
              <div className="text-[9px]" style={{ color: 'rgba(255,255,255,0.3)' }}>Tasks</div>
            </div>
          </div>
        )}

        {node.last_seen && (
          <div className="mt-3 pt-3 border-t" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
            <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
              Last seen: {node.last_seen}
            </span>
          </div>
        )}
      </div>

      <div className="flex border-t" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
        <button className="flex-1 flex items-center justify-center gap-1 py-2 text-[12px] transition-colors hover:bg-white/5"
          style={{ color: 'rgba(255,255,255,0.5)' }}>
          <RefreshCw className="w-3 h-3" />
          Refresh
        </button>
        <button onClick={onDelete}
          className="flex-1 flex items-center justify-center gap-1 py-2 text-[12px] transition-colors hover:bg-red-500/10"
          style={{ color: 'rgba(239,68,68,0.6)' }}>
          <Trash2 className="w-3 h-3" />
          Remove
        </button>
      </div>
    </div>
  );
}

function AddNodeModal({ onClose, onAdd }: {
  onClose: () => void;
  onAdd: (node: Partial<Node>) => void;
}) {
  const [form, setForm] = useState({
    name: '',
    host: '',
    port: '22',
    mac_address: '',
    capabilities: [] as string[],
  });
  const [adding, setAdding] = useState(false);

  const capabilities = ['general', 'coding', 'browser', 'storage', 'network'];
  const toggleCap = (cap: string) => {
    setForm(f => ({
      ...f,
      capabilities: f.capabilities.includes(cap)
        ? f.capabilities.filter(c => c !== cap)
        : [...f.capabilities, cap]
    }));
  };

  const add = async () => {
    if (!form.name || !form.host) return;
    setAdding(true);
    
    const node: Partial<Node> = {
      id: `node_${Date.now()}`,
      name: form.name,
      host: form.host,
      port: parseInt(form.port),
      capabilities: form.capabilities.length > 0 ? form.capabilities : ['general'],
      status: 'offline',
      active_tasks: 0,
    };
    
    onAdd(node);
    onClose();
    setAdding(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(3,6,8,0.85)', backdropFilter: 'blur(8px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="w-full max-w-md rounded-xl overflow-hidden"
        style={{ background: '#060912', border: '1px solid rgba(99,102,241,0.25)' }}>
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: 'rgba(99,102,241,0.15)' }}>
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" />
            <h2 className="font-semibold text-[15px]" style={{ color: 'rgba(255,255,255,0.92)' }}>Add Node</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg" style={{ color: 'rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.05)' }}>
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 flex flex-col gap-4">
          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Node Name *
            </label>
            <input
              className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
              style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
              placeholder="My Mac Mini"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
                Host/IP *
              </label>
              <input
                className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
                style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
                placeholder="192.168.1.100"
                value={form.host}
                onChange={e => setForm(f => ({ ...f, host: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
                Port
              </label>
              <input
                className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
                style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
                placeholder="22"
                value={form.port}
                onChange={e => setForm(f => ({ ...f, port: e.target.value }))}
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
              MAC Address
            </label>
            <input
              className="w-full text-[13px] rounded-lg px-3 py-2 outline-none"
              style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(99,102,241,0.18)', color: 'rgba(255,255,255,0.85)' }}
              placeholder="AA:BB:CC:DD:EE:FF"
              value={form.mac_address}
              onChange={e => setForm(f => ({ ...f, mac_address: e.target.value }))}
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider block mb-2" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Capabilities
            </label>
            <div className="flex flex-wrap gap-2">
              {capabilities.map(cap => (
                <button key={cap}
                  onClick={() => toggleCap(cap)}
                  className="px-3 py-1.5 rounded-lg text-[12px] flex items-center gap-1.5 transition-colors"
                  style={{
                    background: form.capabilities.includes(cap) ? 'rgba(99,102,241,0.2)' : 'rgba(0,0,0,0.3)',
                    color: form.capabilities.includes(cap) ? '#6366f1' : 'rgba(255,255,255,0.5)',
                    border: form.capabilities.includes(cap) ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent',
                  }}>
                  {CAPABILITY_ICONS[cap]}
                  {cap}
                  {form.capabilities.includes(cap) && <Check className="w-3 h-3" />}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button onClick={onClose}
              className="flex-1 py-2 rounded-lg text-[13px] font-medium"
              style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.6)' }}>
              Cancel
            </button>
            <button onClick={add} disabled={adding || !form.name || !form.host}
              className="flex-1 py-2 rounded-lg text-[13px] font-semibold"
              style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', opacity: (adding || !form.name || !form.host) ? 0.5 : 1 }}>
              {adding ? 'Adding...' : 'Add Node'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function NodesPage() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);

  useEffect(() => {
    setNodes([
      {
        id: '1',
        name: 'Mac Mini Office',
        host: '192.168.1.100',
        port: 22,
        status: 'online',
        capabilities: ['coding', 'browser', 'general'],
        cpu_usage: 45,
        memory_usage: 62,
        active_tasks: 3,
        last_seen: 'Just now',
      },
      {
        id: '2',
        name: 'Linux Server',
        host: '10.0.0.50',
        port: 22,
        status: 'busy',
        capabilities: ['coding', 'storage', 'general'],
        cpu_usage: 89,
        memory_usage: 78,
        active_tasks: 7,
        last_seen: 'Just now',
      },
      {
        id: '3',
        name: 'Windows PC',
        host: '192.168.1.200',
        port: 3389,
        status: 'offline',
        capabilities: ['general'],
        active_tasks: 0,
        last_seen: '2 hours ago',
      },
    ]);
    setLoading(false);
  }, []);

  const filteredNodes = nodes.filter(node => {
    if (search && !node.name.toLowerCase().includes(search.toLowerCase()) && !node.host.includes(search)) {
      return false;
    }
    if (filterStatus && node.status !== filterStatus) return false;
    return true;
  });

  const stats = {
    total: nodes.length,
    online: nodes.filter(n => n.status === 'online').length,
    busy: nodes.filter(n => n.status === 'busy').length,
    offline: nodes.filter(n => n.status === 'offline' || n.status === 'error').length,
  };

  const deleteNode = (id: string) => {
    setNodes(prev => prev.filter(n => n.id !== id));
  };

  return (
    <div className="h-full overflow-y-auto" style={{ background: 'linear-gradient(180deg, #060912 0%, #0a0f1a 100%)' }}>
      <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col gap-5">

        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'rgba(255,255,255,0.92)' }}>Remote Nodes</h1>
            <p className="text-[13px] mt-1" style={{ color: 'rgba(255,255,255,0.45)' }}>
              Distributed task execution across remote machines
            </p>
          </div>
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold transition-opacity hover:opacity-90"
            style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff' }}>
            <Plus className="w-4 h-4" />
            Add Node
          </button>
        </div>

        <div className="grid grid-cols-4 gap-4">
          <div className="rounded-xl p-4" style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#6366f1' }}>{stats.total}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Total Nodes</div>
          </div>
          <div className="rounded-xl p-4" style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#22c55e' }}>{stats.online}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Online</div>
          </div>
          <div className="rounded-xl p-4" style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#f59e0b' }}>{stats.busy}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Busy</div>
          </div>
          <div className="rounded-xl p-4" style={{ background: 'rgba(107,114,128,0.08)', border: '1px solid rgba(107,114,128,0.15)' }}>
            <div className="text-[24px] font-bold" style={{ color: '#6b7280' }}>{stats.offline}</div>
            <div className="text-[11px] mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Offline</div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'rgba(255,255,255,0.3)' }} />
            <input
              type="text"
              className="w-full pl-10 pr-4 py-2 text-[13px] rounded-lg outline-none"
              style={{ background: 'rgba(6,9,18,0.88)', border: '1px solid rgba(99,102,241,0.15)', color: 'rgba(255,255,255,0.85)' }}
              placeholder="Search nodes..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-1">
            {[
              { key: null, label: 'All' },
              { key: 'online', label: 'Online' },
              { key: 'busy', label: 'Busy' },
              { key: 'offline', label: 'Offline' },
            ].map(f => (
              <button key={f.key ?? 'all'}
                onClick={() => setFilterStatus(f.key)}
                className="px-3 py-1.5 text-[12px] rounded-lg transition-all"
                style={{
                  background: filterStatus === f.key ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
                  color: filterStatus === f.key ? '#6366f1' : 'rgba(255,255,255,0.5)',
                }}>
                {f.label}
              </button>
            ))}
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

        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredNodes.map(node => (
              <NodeCard key={node.id} node={node} onDelete={() => deleteNode(node.id)} />
            ))}
          </div>
        )}

        {!loading && filteredNodes.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.1)' }}>
              <Server className="w-8 h-8" style={{ color: 'rgba(255,255,255,0.2)' }} />
            </div>
            <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>
              {search ? 'No nodes match your search' : 'No nodes registered'}
            </span>
            {!search && (
              <button onClick={() => setShowAdd(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium mt-2"
                style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1' }}>
                <Plus className="w-4 h-4" />
                Add your first node
              </button>
            )}
          </div>
        )}
      </div>

      {showAdd && (
        <AddNodeModal
          onClose={() => setShowAdd(false)}
          onAdd={(node) => setNodes(prev => [...prev, node as Node])}
        />
      )}
    </div>
  );
}
