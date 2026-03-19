'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  type NodeTypes,
  BackgroundVariant,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Plus,
  Save,
  Trash2,
  Play,
  Search,
  Database,
  FileText,
  Check,
  GitBranch,
  Loader2,
  ChevronDown,
} from 'lucide-react';
import { useWorkflows, useCreateWorkflow, useSaveWorkflow, useDeleteWorkflow } from '@/hooks/useWorkflows';
import type { Workflow } from '@/lib/api';

// ─── Node Types ───────────────────────────────────────────────────────────────

function TriggerNode({ data }: { data: { label: string } }) {
  return (
    <div className="min-w-[160px] bg-slate-900 border-2 border-indigo-500/60 rounded-xl p-3 shadow-lg shadow-indigo-500/10">
      <div className="flex items-center gap-2 mb-1">
        <div className="p-1.5 bg-indigo-500/20 rounded-lg">
          <Search className="w-3.5 h-3.5 text-indigo-400" />
        </div>
        <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider">Trigger</span>
      </div>
      <p className="text-sm font-semibold text-white">{data.label}</p>
    </div>
  );
}

function TaskNode({ data }: { data: { label: string } }) {
  return (
    <div className="min-w-[160px] bg-slate-900 border-2 border-blue-500/60 rounded-xl p-3 shadow-lg shadow-blue-500/10">
      <div className="flex items-center gap-2 mb-1">
        <div className="p-1.5 bg-blue-500/20 rounded-lg">
          <Database className="w-3.5 h-3.5 text-blue-400" />
        </div>
        <span className="text-xs font-bold text-blue-300 uppercase tracking-wider">LLM Task</span>
      </div>
      <p className="text-sm font-semibold text-white">{data.label}</p>
    </div>
  );
}

function ConditionNode({ data }: { data: { label: string } }) {
  return (
    <div className="min-w-[160px] bg-slate-900 border-2 border-amber-500/60 rounded-xl p-3 shadow-lg shadow-amber-500/10">
      <div className="flex items-center gap-2 mb-1">
        <div className="p-1.5 bg-amber-500/20 rounded-lg">
          <GitBranch className="w-3.5 h-3.5 text-amber-400" />
        </div>
        <span className="text-xs font-bold text-amber-300 uppercase tracking-wider">Condition</span>
      </div>
      <p className="text-sm font-semibold text-white">{data.label}</p>
    </div>
  );
}

function OutputNode({ data }: { data: { label: string } }) {
  return (
    <div className="min-w-[160px] bg-slate-900 border-2 border-emerald-500/60 rounded-xl p-3 shadow-lg shadow-emerald-500/10">
      <div className="flex items-center gap-2 mb-1">
        <div className="p-1.5 bg-emerald-500/20 rounded-lg">
          <Check className="w-3.5 h-3.5 text-emerald-400" />
        </div>
        <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider">Output</span>
      </div>
      <p className="text-sm font-semibold text-white">{data.label}</p>
    </div>
  );
}

const nodeTypes: NodeTypes = {
  trigger: TriggerNode,
  task: TaskNode,
  condition: ConditionNode,
  output: OutputNode,
};

// ─── Node Templates ───────────────────────────────────────────────────────────

const NODE_TEMPLATES = [
  {
    type: 'trigger',
    label: 'Trigger',
    description: 'Webhook / Message',
    icon: <Search className="w-4 h-4" />,
    color: 'indigo',
  },
  {
    type: 'task',
    label: 'LLM Task',
    description: 'Prompt execution',
    icon: <Database className="w-4 h-4" />,
    color: 'blue',
  },
  {
    type: 'condition',
    label: 'Condition',
    description: 'If / Else routing',
    icon: <GitBranch className="w-4 h-4" />,
    color: 'amber',
  },
  {
    type: 'output',
    label: 'Output',
    description: 'Final result',
    icon: <Check className="w-4 h-4" />,
    color: 'emerald',
  },
];

const COLOR_MAP: Record<string, string> = {
  indigo: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  amber: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  emerald: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
};

// ─── Starter Workflow ─────────────────────────────────────────────────────────

const STARTER_NODES: Node[] = [
  { id: '1', type: 'trigger', position: { x: 50, y: 150 }, data: { label: 'User Input' } },
  { id: '2', type: 'task', position: { x: 300, y: 150 }, data: { label: 'Planner Agent' } },
  { id: '3', type: 'task', position: { x: 550, y: 50 }, data: { label: 'Coder Agent' } },
  { id: '4', type: 'condition', position: { x: 550, y: 250 }, data: { label: 'Review Check' } },
  { id: '5', type: 'output', position: { x: 800, y: 150 }, data: { label: 'Final Output' } },
];

const STARTER_EDGES: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e2-3', source: '2', target: '3', animated: true },
  { id: 'e2-4', source: '2', target: '4' },
  { id: 'e3-5', source: '3', target: '5' },
  { id: 'e4-5', source: '4', target: '5' },
];

// ─── Main Component ───────────────────────────────────────────────────────────

export function WorkflowBuilderVisual() {
  const [nodes, setNodes, onNodesChange] = useNodesState(STARTER_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(STARTER_EDGES);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [showWorkflowPicker, setShowWorkflowPicker] = useState(false);
  const [nodeCounter, setNodeCounter] = useState(10);

  const { data: workflows = [], isLoading: loadingWorkflows } = useWorkflows();
  const createWorkflow = useCreateWorkflow();
  const saveWorkflow = useSaveWorkflow();
  const deleteWorkflow = useDeleteWorkflow();

  // Load workflow into canvas
  const loadWorkflow = useCallback((wf: Workflow) => {
    setActiveWorkflowId(wf.id);
    setWorkflowName(wf.name);
    setNodes((wf.nodes as Node[]) || STARTER_NODES);
    setEdges((wf.edges as Edge[]) || STARTER_EDGES);
    setShowWorkflowPicker(false);
  }, [setNodes, setEdges]);

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge({ ...connection, animated: true }, eds)),
    [setEdges]
  );

  const addNode = useCallback(
    (type: string, label: string) => {
      const id = String(nodeCounter + 1);
      setNodeCounter((c) => c + 1);
      const newNode: Node = {
        id,
        type,
        position: { x: 150 + Math.random() * 300, y: 100 + Math.random() * 200 },
        data: { label },
      };
      setNodes((nds) => [...nds, newNode]);
    },
    [nodeCounter, setNodes]
  );

  const handleSave = useCallback(async () => {
    if (!activeWorkflowId) {
      // Create new workflow, then save nodes/edges
      const result = await createWorkflow.mutateAsync({ name: workflowName });
      const wf = result.data as Workflow;
      await saveWorkflow.mutateAsync({ id: wf.id, nodes: nodes as never[], edges: edges as never[] });
      setActiveWorkflowId(wf.id);
    } else {
      await saveWorkflow.mutateAsync({
        id: activeWorkflowId,
        nodes: nodes as never[],
        edges: edges as never[],
        name: workflowName,
      });
    }
  }, [activeWorkflowId, workflowName, nodes, edges, createWorkflow, saveWorkflow]);

  const handleDelete = useCallback(async () => {
    if (!activeWorkflowId) return;
    await deleteWorkflow.mutateAsync(activeWorkflowId);
    setActiveWorkflowId(null);
    setWorkflowName('New Workflow');
    setNodes(STARTER_NODES);
    setEdges(STARTER_EDGES);
  }, [activeWorkflowId, deleteWorkflow, setNodes, setEdges]);

  const isSaving = createWorkflow.isPending || saveWorkflow.isPending;

  return (
    <div className="w-full h-full flex bg-slate-950">
      {/* Sidebar */}
      <div className="w-64 flex-none bg-slate-900/60 border-r border-white/10 flex flex-col z-20">
        {/* Workflow Selector */}
        <div className="p-3 border-b border-white/5">
          <button
            onClick={() => setShowWorkflowPicker((v) => !v)}
            className="w-full flex items-center justify-between px-3 py-2 bg-slate-800/60 border border-white/10 rounded-lg text-sm text-white hover:border-white/20 transition-colors"
          >
            <span className="truncate max-w-[140px]">{workflowName}</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          </button>

          {showWorkflowPicker && (
            <div className="mt-1 bg-slate-800 border border-white/10 rounded-lg overflow-hidden shadow-xl">
              <button
                onClick={() => {
                  setActiveWorkflowId(null);
                  setWorkflowName('New Workflow');
                  setNodes(STARTER_NODES);
                  setEdges(STARTER_EDGES);
                  setShowWorkflowPicker(false);
                }}
                className="w-full px-3 py-2 text-left text-sm text-blue-400 hover:bg-white/5 border-b border-white/5 flex items-center gap-2"
              >
                <Plus className="w-3.5 h-3.5" /> New Workflow
              </button>
              {loadingWorkflows ? (
                <div className="px-3 py-2 text-xs text-slate-500">Loading...</div>
              ) : workflows.length === 0 ? (
                <div className="px-3 py-2 text-xs text-slate-500">No saved workflows</div>
              ) : (
                workflows.map((wf) => (
                  <button
                    key={wf.id}
                    onClick={() => loadWorkflow(wf)}
                    className="w-full px-3 py-2 text-left text-sm text-white hover:bg-white/5 flex items-center gap-2"
                  >
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    <span className="truncate">{wf.name}</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Node Templates */}
        <div className="p-3 border-b border-white/5">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Add Node</p>
          <div className="space-y-1.5">
            {NODE_TEMPLATES.map((tpl) => (
              <button
                key={tpl.type}
                onClick={() => addNode(tpl.type, tpl.label)}
                className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg border text-left hover:opacity-90 transition-opacity ${COLOR_MAP[tpl.color]}`}
              >
                <span>{tpl.icon}</span>
                <div>
                  <p className="text-xs font-semibold">{tpl.label}</p>
                  <p className="text-[10px] opacity-70">{tpl.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-auto p-3 space-y-2 border-t border-white/5">
          <div className="flex gap-2">
            <input
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="flex-1 min-w-0 px-2 py-1.5 bg-slate-800 border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500/50"
              placeholder="Workflow name"
            />
          </div>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className="w-full flex items-center justify-center gap-2 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors shadow-[0_0_15px_rgba(37,99,235,0.3)]"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {isSaving ? 'Saving…' : 'Save'}
          </button>

          <div className="flex gap-2">
            <button className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-400 text-xs font-medium rounded-lg transition-colors">
              <Play className="w-3.5 h-3.5 fill-current" /> Run
            </button>
            {activeWorkflowId && (
              <button
                onClick={handleDelete}
                disabled={deleteWorkflow.isPending}
                className="flex items-center justify-center gap-1.5 px-3 py-2 bg-red-600/10 hover:bg-red-600/20 border border-red-500/20 text-red-400 text-xs rounded-lg transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          colorMode="dark"
          defaultEdgeOptions={{ animated: false, style: { stroke: 'rgba(148,163,184,0.4)', strokeWidth: 2 } }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={24}
            size={1}
            color="rgba(148,163,184,0.15)"
          />
          <Controls
            className="!bg-slate-900 !border-white/10 !rounded-xl overflow-hidden"
            showInteractive={false}
          />
          <MiniMap
            className="!bg-slate-900 !border-white/10 !rounded-xl overflow-hidden"
            nodeColor={(n) => {
              if (n.type === 'trigger') return '#6366f1';
              if (n.type === 'task') return '#3b82f6';
              if (n.type === 'condition') return '#f59e0b';
              return '#10b981';
            }}
            maskColor="rgba(2,6,23,0.7)"
          />
          <Panel position="top-right">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/80 border border-white/10 rounded-lg text-xs text-slate-400 backdrop-blur-md">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {nodes.length} nodes · {edges.length} edges
            </div>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  );
}
