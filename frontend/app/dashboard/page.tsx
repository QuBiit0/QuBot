'use client';

import dynamic from 'next/dynamic';
import { Plus, Users, Activity } from 'lucide-react';
import Link from 'next/link';
import MetricCards from '@/components/dashboard/MetricCards';
import ActiveMissions from '@/components/dashboard/ActiveMissions';
import { useAgents } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';
import { useAppStore } from '@/store/app.store';
import { useAgentsStore } from '@/store/agents.store';

const OfficeSystem = dynamic(() => import('@/components/coworking/OfficeSystem'), { ssr: false });

export default function DashboardPage() {
  // Hydrate stores from real API
  useAgents();
  useTasks();

  const isConnected = useAppStore((s) => s.isConnected);
  const agents = useAgentsStore((s) => s.agents);

  const agentList = Object.values(agents);
  const onlineCount = agentList.filter((a) => a.status !== 'OFFLINE').length;
  const totalCount = agentList.length;

  return (
    <div className="h-full flex flex-col" style={{ background: 'transparent' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-6 py-4 border-b"
        style={{
          background: 'rgba(10, 15, 30, 0.6)',
          backdropFilter: 'blur(12px)',
          borderColor: 'rgba(255, 255, 255, 0.05)',
        }}
      >
        <div className="flex items-center gap-4">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(59, 111, 255, 0.2) 0%, rgba(163, 113, 247, 0.2) 100%)',
              border: '1px solid rgba(59, 111, 255, 0.3)',
            }}
          >
            <Users className="w-5 h-5" style={{ color: '#3b6fff' }} />
          </div>
          <div>
            <h1 className="text-xl font-bold" style={{ color: '#e6edf3' }}>
              Main Office
            </h1>
            <p className="text-xs flex items-center gap-1" style={{ color: '#6e7681' }}>
              <Activity
                className="w-3 h-3"
                style={{ color: isConnected ? '#3fb950' : '#6e7681' }}
              />
              {totalCount > 0 ? `${onlineCount}/${totalCount} agents online` : 'Loading agents...'}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Link
            href="/agents/new"
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, #3b6fff 0%, #58a6ff 100%)',
              boxShadow: '0 4px 15px rgba(59, 111, 255, 0.3)',
              color: '#fff',
            }}
          >
            <Plus className="w-4 h-4" />
            New Agent
          </Link>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Office Canvas */}
        <div className="flex-1 relative overflow-hidden">
          {/* Background Effects */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: `
                radial-gradient(ellipse at 20% 80%, rgba(59, 111, 255, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(163, 113, 247, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(63, 185, 80, 0.03) 0%, transparent 70%)
              `,
            }}
          />
          <div
            className="absolute inset-0 pointer-events-none opacity-30"
            style={{
              backgroundImage: `repeating-linear-gradient(
                0deg,
                transparent,
                transparent 60px,
                rgba(255, 255, 255, 0.01) 60px,
                rgba(255, 255, 255, 0.01) 61px
              )`,
            }}
          />
          <OfficeSystem />
        </div>

        {/* Right: Mission Control Panel */}
        <div
          className="w-80 border-l flex flex-col overflow-y-auto"
          style={{
            background: 'rgba(10, 15, 30, 0.6)',
            backdropFilter: 'blur(12px)',
            borderColor: 'rgba(255, 255, 255, 0.05)',
          }}
        >
          {/* Mission Control Header */}
          <div
            className="px-4 py-3 border-b"
            style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}
          >
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{
                  background: isConnected ? '#3fb950' : '#6e7681',
                  animation: isConnected ? 'pulse 2s infinite' : 'none',
                }}
              />
              <span
                className="text-xs font-semibold uppercase tracking-wider"
                style={{ color: '#6e7681' }}
              >
                Mission Control
              </span>
            </div>
          </div>

          <MetricCards />

          <div style={{ height: 1, background: 'rgba(255, 255, 255, 0.05)' }} />

          <ActiveMissions />
        </div>
      </div>
    </div>
  );
}
