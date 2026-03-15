'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Code, 
  Play, 
  Save, 
  X, 
  Plus, 
  Trash2,
  Settings,
  Terminal
} from 'lucide-react';
import { useCreateSkill, useUpdateSkill, useExecuteSkill, Skill, SkillParameter } from '@/hooks/useSkills';
import { toast } from '@/components/ui';

interface SkillEditorProps {
  skill?: Skill;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const PYTHON_TEMPLATE = `def main(params):
    """
    Main function called when skill is executed.
    
    Args:
        params: Dictionary with input parameters
        
    Returns:
        Result of the skill execution
    """
    # Example: Get parameter
    name = params.get('name', 'World')
    
    # Your skill logic here
    result = f"Hello, {name}!"
    
    return result
`;

const JAVASCRIPT_TEMPLATE = `function main(params) {
    /**
     * Main function called when skill is executed.
     */
    
    // Example: Get parameter
    const name = params.name || 'World';
    
    // Your skill logic here
    const result = "Hello, " + name + "!";
    
    return result;
}
`;

export function SkillEditor({ skill, isOpen, onClose, onSuccess }: SkillEditorProps) {
  const isEditing = !!skill;
  
  const [formData, setFormData] = useState<Partial<Skill>>({
    name: skill?.name || '',
    description: skill?.description || '',
    code: skill?.code || PYTHON_TEMPLATE,
    language: skill?.language || 'python',
    is_public: skill?.is_public || false,
    parameters: skill?.parameters || [],
  });
  
  const [testParams, setTestParams] = useState<Record<string, any>>({});
  const [testResult, setTestResult] = useState<any>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [activeTab, setActiveTab] = useState<'code' | 'params' | 'test'>('code');
  
  const createSkill = useCreateSkill();
  const updateSkill = useUpdateSkill();
  const executeSkill = useExecuteSkill();
  
  if (!isOpen) return null;
  
  const handleSave = async () => {
    try {
      if (isEditing && skill) {
        await updateSkill.mutateAsync({ id: skill.id, data: formData });
        toast.success('Skill updated successfully');
      } else {
        await createSkill.mutateAsync(formData);
        toast.success('Skill created successfully');
      }
      onSuccess?.();
      onClose();
    } catch (error: any) {
      toast.error('Failed to save skill', error.message);
    }
  };
  
  const handleTest = async () => {
    if (!skill) return;
    setIsTesting(true);
    try {
      const result = await executeSkill.mutateAsync({
        skillId: skill.id,
        parameters: testParams,
        timeout: 30,
      });
      setTestResult(result);
      if (result.success) {
        toast.success('Skill executed successfully');
      } else {
        toast.error('Skill execution failed', result.error);
      }
    } catch (error: any) {
      toast.error('Test failed', error.message);
    } finally {
      setIsTesting(false);
    }
  };
  
  const addParameter = () => {
    const newParam: SkillParameter = {
      name: '',
      param_type: 'string',
      description: '',
      required: true,
    };
    setFormData({
      ...formData,
      parameters: [...(formData.parameters || []), newParam],
    });
  };
  
  const updateParameter = (index: number, updates: Partial<SkillParameter>) => {
    const updated = [...(formData.parameters || [])];
    updated[index] = { ...updated[index], ...updates };
    setFormData({ ...formData, parameters: updated });
  };
  
  const removeParameter = (index: number) => {
    const updated = [...(formData.parameters || [])];
    updated.splice(index, 1);
    setFormData({ ...formData, parameters: updated });
  };
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-5xl h-[90vh] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Code className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold">
                {isEditing ? 'Edit Skill' : 'Create Skill'}
              </h2>
              <p className="text-sm text-slate-400">
                {isEditing ? `v${skill?.version}` : 'Define a reusable skill for your agents'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar */}
          <div className="w-80 border-r border-slate-800 p-4 space-y-4 overflow-y-auto">
            <div className="space-y-3">
              <label className="block text-sm font-medium text-slate-300">Skill Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Calculate Fibonacci"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
              />
            </div>
            
            <div className="space-y-3">
              <label className="block text-sm font-medium text-slate-300">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="What does this skill do?"
                rows={3}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white resize-none"
              />
            </div>
            
            {/* Language Selection */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-slate-300">Language</label>
              <div className="flex gap-2">
                {(['python', 'javascript'] as const).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setFormData({ 
                      ...formData, 
                      language: lang,
                      code: lang === 'python' ? PYTHON_TEMPLATE : JAVASCRIPT_TEMPLATE
                    })}
                    className={`flex-1 py-2 px-3 rounded-lg border text-sm font-medium ${
                      formData.language === lang
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'bg-slate-800 border-slate-700 text-slate-400'
                    }`}
                  >
                    {lang === 'python' ? 'Python' : 'JavaScript'}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Visibility */}
            <div className="flex items-center gap-3 p-3 bg-slate-800 rounded-lg">
              <input
                type="checkbox"
                id="is_public"
                checked={formData.is_public}
                onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                className="w-4 h-4 rounded border-slate-600"
              />
              <label htmlFor="is_public" className="text-sm text-slate-300">
                Make this skill public
              </label>
            </div>
            
            {/* Parameters */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-slate-300">Parameters</label>
                <button
                  onClick={addParameter}
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" />
                  Add
                </button>
              </div>
              
              <div className="space-y-2">
                {formData.parameters?.map((param, index) => (
                  <div key={index} className="p-3 bg-slate-800 rounded-lg space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={param.name}
                        onChange={(e) => updateParameter(index, { name: e.target.value })}
                        placeholder="Param name"
                        className="flex-1 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-sm"
                      />
                      <button
                        onClick={() => removeParameter(index)}
                        className="p-1 text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    <select
                      value={param.param_type}
                      onChange={(e) => updateParameter(index, { param_type: e.target.value as any })}
                      className="w-full px-2 py-1 bg-slate-900 border border-slate-700 rounded text-sm"
                    >
                      <option value="string">String</option>
                      <option value="number">Number</option>
                      <option value="boolean">Boolean</option>
                      <option value="array">Array</option>
                      <option value="object">Object</option>
                    </select>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Editor Area */}
          <div className="flex-1 flex flex-col">
            {/* Tabs */}
            <div className="flex border-b border-slate-800">
              {(['code', 'params', 'test'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-3 text-sm font-medium ${
                    activeTab === tab
                      ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-400/10'
                      : 'text-slate-400'
                  }`}
                >
                  {tab === 'code' && 'Code Editor'}
                  {tab === 'params' && 'Parameters'}
                  {tab === 'test' && 'Test Skill'}
                </button>
              ))}
            </div>
            
            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
              {activeTab === 'code' && (
                <textarea
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-full h-full p-4 bg-slate-950 text-slate-200 font-mono text-sm resize-none focus:outline-none"
                  spellCheck={false}
                />
              )}
              
              {activeTab === 'params' && (
                <div className="h-full p-6 overflow-y-auto">
                  <h3 className="text-lg font-semibold mb-4">Parameter Preview</h3>
                  {formData.parameters?.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <Settings className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No parameters defined</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {formData.parameters?.map((param, index) => (
                        <div key={index} className="p-4 bg-slate-800 rounded-lg border border-slate-700">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-blue-400 font-mono">{param.name}</span>
                            <span className="text-xs bg-slate-700 px-2 py-0.5 rounded text-slate-300">
                              {param.param_type}
                            </span>
                          </div>
                          <p className="text-sm text-slate-400">{param.description || 'No description'}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              {activeTab === 'test' && (
                <div className="h-full flex flex-col p-6">
                  {!isEditing ? (
                    <div className="flex-1 flex items-center justify-center text-slate-500">
                      <p>Save the skill first to test it</p>
                    </div>
                  ) : (
                    <>
                      <div className="space-y-4 mb-6">
                        {formData.parameters?.map((param, index) => (
                          <div key={index} className="space-y-2">
                            <label className="text-sm text-slate-300">{param.name}</label>
                            <input
                              type="text"
                              value={testParams[param.name] || ''}
                              onChange={(e) => setTestParams({ ...testParams, [param.name]: e.target.value })}
                              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                            />
                          </div>
                        ))}
                      </div>
                      
                      <button
                        onClick={handleTest}
                        disabled={isTesting}
                        className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg font-medium flex items-center justify-center gap-2"
                      >
                        {isTesting ? 'Running...' : <><Play className="w-4 h-4" /> Run Test</>}
                      </button>
                      
                      {testResult && (
                        <div className={`mt-4 p-4 rounded-lg ${testResult.success ? 'bg-green-900/30 border border-green-700' : 'bg-red-900/30 border border-red-700'}`}>
                          <pre className="text-sm overflow-x-auto">
                            {JSON.stringify(testResult.result || testResult.error, null, 2)}
                          </pre>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Terminal className="w-4 h-4" />
            <span>Skills run in sandboxed environment</span>
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!formData.name || !formData.code}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg font-medium"
            >
              <Save className="w-4 h-4" />
              {isEditing ? 'Update' : 'Create'}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
