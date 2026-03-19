'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Kanban, 
  Users, 
  MessageSquare, 
  Settings,
  Wrench,
  Sparkles,
  Zap,
  Store,
  ClipboardList,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/dashboard', label: 'Office', icon: LayoutDashboard },
  { href: '/mission-control', label: 'Mission Control', icon: Kanban },
  { href: '/tasks', label: 'Tasks', icon: ClipboardList },
  { href: '/agents', label: 'Agents', icon: Users },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/tools', label: 'Tools', icon: Wrench },
  { href: '/marketplace', label: 'Marketplace', icon: Store },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside 
      className="w-64 flex flex-col border-r"
      style={{ 
        background: 'rgba(10, 15, 30, 0.8)',
        backdropFilter: 'blur(12px)',
        borderColor: 'rgba(255, 255, 255, 0.05)',
      }}
    >
      {/* Logo */}
      <div 
        className="p-4 border-b flex flex-col"
        style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}
      >
        <Link href="/" className="flex items-center gap-3">
          <div 
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ 
              background: 'linear-gradient(135deg, #3b6fff 0%, #a371f7 100%)',
              boxShadow: '0 4px 15px rgba(59, 111, 255, 0.3)',
            }}
          >
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold" style={{ color: '#e6edf3' }}>Qubot</span>
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3 text-green-400" />
              <span className="text-[10px] font-medium text-green-400">LIVE</span>
            </div>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                isActive
                  ? 'text-white font-medium'
                  : 'hover:text-white'
              )}
              style={{
                background: isActive 
                  ? 'linear-gradient(90deg, rgba(59, 111, 255, 0.2) 0%, rgba(59, 111, 255, 0.05) 100%)' 
                  : 'transparent',
                borderLeft: isActive ? '3px solid #3b6fff' : '3px solid transparent',
                color: isActive ? '#e6edf3' : '#8b949e',
              }}
            >
              <Icon 
                className="w-5 h-5 transition-colors" 
                style={{ color: isActive ? '#3b6fff' : '#6e7681' }}
              />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div 
        className="p-4 border-t text-xs"
        style={{ 
          borderColor: 'rgba(255, 255, 255, 0.05)',
          color: '#6e7681',
        }}
      >
        <p className="font-medium" style={{ color: '#8b949e' }}>Qubot v1.0.0</p>
        <p className="mt-0.5">AI Agent Mission Control</p>
      </div>
    </aside>
  );
}
