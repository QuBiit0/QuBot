'use client';

import { useState } from 'react';
import { Bell, Shield, User, Palette, Server } from 'lucide-react';

const settingsSections = [
  {
    id: 'profile',
    label: 'Profile',
    icon: User,
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: Bell,
  },
  {
    id: 'appearance',
    label: 'Appearance',
    icon: Palette,
  },
  {
    id: 'security',
    label: 'Security',
    icon: Shield,
  },
  {
    id: 'server',
    label: 'Server',
    icon: Server,
  },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('profile');

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-slate-400">Manage your Qubot preferences</p>
      </div>

      <div className="flex gap-6 flex-1">
        {/* Sidebar */}
        <div className="w-64 space-y-1">
          {settingsSections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                  activeSection === section.id
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                <Icon className="w-5 h-5" />
                {section.label}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-6">
          {activeSection === 'profile' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Profile Settings</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Display Name</label>
                  <input
                    type="text"
                    defaultValue="Admin User"
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Email</label>
                  <input
                    type="email"
                    defaultValue="admin@qubot.local"
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors">
                  Save Changes
                </button>
              </div>
            </div>
          )}

          {activeSection === 'notifications' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Notification Preferences</h2>
              <div className="space-y-3">
                {['Task completions', 'Agent status changes', 'System alerts', 'Weekly reports'].map((item) => (
                  <label key={item} className="flex items-center gap-3">
                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-slate-600" />
                    <span>{item}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {activeSection === 'appearance' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Appearance</h2>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Theme</label>
                <select className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg">
                  <option>Dark</option>
                  <option>Light</option>
                  <option>System</option>
                </select>
              </div>
            </div>
          )}

          {activeSection === 'security' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Security</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Current Password</label>
                  <input
                    type="password"
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-2">New Password</label>
                  <input
                    type="password"
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
                  />
                </div>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors">
                  Update Password
                </button>
              </div>
            </div>
          )}

          {activeSection === 'server' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Server Configuration</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">API URL</label>
                  <input
                    type="text"
                    defaultValue="http://localhost:8000/api"
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-2">WebSocket URL</label>
                  <input
                    type="text"
                    defaultValue="ws://localhost:8000/ws"
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
                  />
                </div>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors">
                  Save Configuration
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
