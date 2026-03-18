'use client'

import { useState } from 'react';
import {
  Search,
  CheckCircle2,
  Filter,
  Star,
  Download,
  Database,
  Globe,
  ShieldAlert,
  Terminal,
  MessageSquare,
  Code2
} from 'lucide-react';

// Mock Data for the Marketplace
const SKILLS_DB = [
  {
    id: 'sk-1',
    name: 'Advanced PostgreSQL',
    author: 'Qubot Core',
    description: 'Enables deep logical reasoning over complex distributed SQL schemas and query optimization.',
    icon: Database,
    category: 'Data',
    downloads: '12k',
    rating: 4.9,
    installed: true,
    tags: ['sql', 'postgres', 'db'],
  },
  {
    id: 'sk-2',
    name: 'Web Scraper Pro',
    author: 'DataBots Inc',
    description: 'A robust web scaping skill supporting headless browsers, stealth plugins, and captcha bypass.',
    icon: Globe,
    category: 'Web',
    downloads: '84k',
    rating: 4.7,
    installed: false,
    tags: ['puppeteer', 'scraping', 'automation'],
  },
  {
    id: 'sk-3',
    name: 'Ethical Hacker Pentest',
    author: 'SecOpsLabs',
    description: 'Full automated penetration testing with OWASP Top 10 coverage and reporting.',
    icon: ShieldAlert,
    category: 'Security',
    downloads: '4k',
    rating: 4.5,
    installed: false,
    tags: ['security', 'owasp', 'audit'],
  },
  {
    id: 'sk-4',
    name: 'System Shell Root',
    author: 'Qubot Core',
    description: 'Execute arbitrary bash scripts directly on the host machine. (High Risk)',
    icon: Terminal,
    category: 'System',
    downloads: '45k',
    rating: 4.8,
    installed: true,
    tags: ['bash', 'cli', 'system'],
  },
  {
    id: 'sk-5',
    name: 'Social Media Manager',
    author: 'MarketingAI',
    description: 'Auto-generates content, scheduling, and community engagement for Twitter & LinkedIn.',
    icon: MessageSquare,
    category: 'Marketing',
    downloads: '150k',
    rating: 4.9,
    installed: false,
    tags: ['social', 'linkedin', 'x'],
  },
  {
    id: 'sk-6',
    name: 'React Expert',
    author: 'FrontendMasters',
    description: 'Specializes in creating accessible, beautiful NextJS and React components.',
    icon: Code2,
    category: 'Software',
    downloads: '92k',
    rating: 4.9,
    installed: false,
    tags: ['react', 'nextjs', 'component'],
  },
]

export default function MarketplacePage() {
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('All')

  // Derive categories
  const categories = ['All', ...Array.from(new Set(SKILLS_DB.map((s) => s.category)))]

  // Filter skills
  const filteredSkills = SKILLS_DB.filter((skill) => {
    const matchesSearch = skill.name.toLowerCase().includes(search.toLowerCase()) || skill.tags.some(t => t.includes(search.toLowerCase()))
    const matchesCat = categoryFilter === 'All' || skill.category === categoryFilter
    return matchesSearch && matchesCat
  })

  return (
    <div className="flex flex-col h-full bg-slate-950 p-6 text-slate-200 relative overflow-hidden">
      {/* Premium Background Elements */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[800px] h-[800px] bg-indigo-600/10 rounded-full blur-[150px] pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between mb-8 relative z-10">
        <div className="flex items-center gap-4">
          <Globe className="w-10 h-10 text-blue-400" />
          <div>
            <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 tracking-tight">
              Skills Marketplace
            </h1>
            <p className="text-slate-400 mt-2 font-medium">Discover, install, and upgrade capabilities over your autonomous workforce.</p>
          </div>
        </div>
      </div>

      <div className="space-y-8 flex-1 overflow-y-auto custom-scrollbar relative z-10">
        {/* Search & Filter Bar */}
        <div className="flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
            <input
              type="text"
              placeholder="Search skills by name, tag, or capability..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-900/50 border border-white/5 focus:border-blue-500/50 rounded-xl py-3 pl-12 pr-4 text-slate-200 placeholder:text-slate-500 outline-none transition-all focus:ring-4 focus:ring-blue-500/10 backdrop-blur-sm"
            />
          </div>

          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 custom-scrollbar mask-edges">
            <Filter className="w-5 h-5 text-slate-400 mr-2 shrink-0" />
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  categoryFilter === cat
                    ? 'bg-blue-600 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]'
                    : 'bg-slate-900/50 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-white/5'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSkills.map((skill) => (
            <div
              key={skill.id}
              className="group relative bg-slate-900/40 border border-white/5 rounded-2xl p-6 transition-all hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.5)] hover:border-blue-500/30 overflow-hidden flex flex-col h-full"
            >
              {/* Background Glow */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl group-hover:bg-blue-500/10 transition-colors pointer-events-none" />

              <div className="flex items-start justify-between mb-4 relative z-10">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center border border-white/5 shadow-inner">
                  <skill.icon className="w-6 h-6 text-blue-400" />
                </div>
                {skill.installed ? (
                  <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-full border border-emerald-400/20">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Installed
                  </span>
                ) : (
                  <span className="text-xs font-medium text-slate-500 bg-slate-800 px-2.5 py-1 rounded-full border border-white/5">
                    {skill.category}
                  </span>
                )}
              </div>

              <div className="space-y-2 mb-6 relative z-10 flex-1">
                <h3 className="text-lg font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                  {skill.name}
                </h3>
                <p className="text-sm text-slate-500">by {skill.author}</p>
                <p className="text-sm text-slate-400 leading-relaxed mt-2 line-clamp-3">
                  {skill.description}
                </p>
              </div>

              <div className="flex items-center gap-2 mb-6 relative z-10">
                {skill.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 bg-slate-950/50 px-2.5 py-1 rounded-md border border-white/5"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* Action Bar */}
              <div className="pt-4 border-t border-white/5 flex items-center justify-between mt-auto relative z-10">
                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <span className="flex items-center gap-1.5" title="Downloads">
                    <Download className="w-4 h-4" />
                    {skill.downloads}
                  </span>
                  <span className="flex items-center gap-1.5 text-amber-500/80" title="Rating">
                    <Star className="w-4 h-4 fill-amber-500/80" />
                    {skill.rating}
                  </span>
                </div>

                <button
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                    skill.installed
                      ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_4px_14px_rgba(37,99,235,0.3)] hover:shadow-[0_4px_20px_rgba(37,99,235,0.5)]'
                  }`}
                >
                  {skill.installed ? (
                    'Manage'
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      Install
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}

          {filteredSkills.length === 0 && (
            <div className="col-span-full py-20 flex flex-col items-center justify-center text-slate-500">
              <Search className="w-12 h-12 mb-4 text-slate-600 opacity-50" />
              <p className="text-lg font-medium">No skills found</p>
              <p className="text-sm">Try adjusting your search or filters.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
