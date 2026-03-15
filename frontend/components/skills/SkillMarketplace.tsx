'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Code, Plus, Star, Download, User } from 'lucide-react';
import { useSkills, useAssignSkillToAgent } from '@/hooks/useSkills';
import { SkillEditor } from './SkillEditor';
import { toast } from '@/components/ui';

interface SkillMarketplaceProps {
  agentId?: string; // If provided, shows "Assign" buttons
}

export function SkillMarketplace({ agentId }: SkillMarketplaceProps) {
  const [search, setSearch] = useState('');
  const [language, setLanguage] = useState<string>('');
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingSkill, setEditingSkill] = useState<any>(null);
  
  const { data: skills, isLoading } = useSkills({ 
    public_only: true, 
    search,
    language 
  });
  
  const assignSkill = useAssignSkillToAgent();
  
  const handleAssign = async (skillId: string) => {
    if (!agentId) return;
    try {
      await assignSkill.mutateAsync({ agentId, skillId });
      toast.success('Skill assigned to agent');
    } catch (error: any) {
      toast.error('Failed to assign skill', error.message);
    }
  };
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold">Skill Marketplace</h1>
          <p className="text-slate-400">Discover and create reusable skills for your agents</p>
        </div>
        <button
          onClick={() => { setEditingSkill(null); setIsEditorOpen(true); }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Skill
        </button>
      </div>
      
      {/* Filters */}
      <div className="flex gap-4 p-4 border-b border-slate-800">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search skills..."
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500"
          />
        </div>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
        >
          <option value="">All Languages</option>
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
        </select>
      </div>
      
      {/* Skills Grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-3" />
            Loading skills...
          </div>
        ) : skills?.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <Code className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">No skills found</p>
            <p className="text-sm mt-1">Create your first skill to get started</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {skills?.map((skill) => (
              <motion.div
                key={skill.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      skill.language === 'python' ? 'bg-yellow-600' : 'bg-blue-600'
                    }`}>
                      <Code className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{skill.name}</h3>
                      <p className="text-xs text-slate-500">v{skill.version}</p>
                    </div>
                  </div>
                  {skill.is_official && (
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-400 text-xs rounded-full">
                      Official
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-slate-400 mb-4 line-clamp-2">
                  {skill.description || 'No description'}
                </p>
                
                <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
                  <span className="flex items-center gap-1">
                    <Download className="w-3 h-3" />
                    {skill.usage_count} uses
                  </span>
                  <span className="flex items-center gap-1">
                    <Star className="w-3 h-3" />
                    {skill.rating_average > 0 ? `${skill.rating_average}/5` : 'No ratings'}
                  </span>
                  <span className="flex items-center gap-1">
                    <User className="w-3 h-3" />
                    {skill.created_by ? 'Community' : 'System'}
                  </span>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => { setEditingSkill(skill); setIsEditorOpen(true); }}
                    className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors"
                  >
                    View Code
                  </button>
                  {agentId && (
                    <button
                      onClick={() => handleAssign(skill.id)}
                      disabled={assignSkill.isPending}
                      className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
                    >
                      {assignSkill.isPending ? 'Assigning...' : 'Assign'}
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
      
      <SkillEditor
        skill={editingSkill}
        isOpen={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        onSuccess={() => {}}
      />
    </div>
  );
}
