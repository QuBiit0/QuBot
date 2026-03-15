# Qubot — Frontend Architecture

> **Framework**: Next.js 14 (App Router) + React 18 + TypeScript (strict)
> **UI**: TailwindCSS + Shadcn/ui
> **Canvas**: Konva.js (coworking office)
> **State**: Zustand (global) + TanStack Query (server state)

---

## 1. Technology Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Next.js | 14 | App Router, SSR/CSR, routing |
| React | 18 | UI components |
| TypeScript | 5 (strict) | Type safety |
| TailwindCSS | 3 | Utility-first styles |
| Shadcn/ui | latest | Pre-built accessible components |
| Konva.js | 9 | 2D canvas for coworking office |
| react-konva | 18 | React bindings for Konva |
| Zustand | 4 | Global client state |
| TanStack Query | 5 | Server state, caching, mutations |
| dnd-kit | 6 | Drag & drop for Kanban |
| Framer Motion | 11 | Animations |
| socket.io-client | — | NOT used (native WebSocket) |

---

## 2. Directory Structure

```
frontend/
├── app/                           # Next.js App Router
│   ├── layout.tsx                 # Root layout: providers, nav sidebar, WS init
│   ├── page.tsx                   # Redirect → /dashboard
│   │
│   ├── dashboard/
│   │   └── page.tsx               # Coworking office view
│   │
│   ├── mission-control/
│   │   └── page.tsx               # Kanban board
│   │
│   ├── agents/
│   │   ├── page.tsx               # Agent list (table view)
│   │   ├── new/page.tsx           # Agent creation wizard
│   │   └── [id]/
│   │       ├── page.tsx           # Agent detail + edit
│   │       └── memory/page.tsx    # Agent memory management
│   │
│   ├── tasks/
│   │   └── [id]/page.tsx          # Task detail with event timeline
│   │
│   ├── tools/
│   │   ├── page.tsx               # Tool registry
│   │   └── [id]/page.tsx          # Tool config / edit
│   │
│   ├── settings/
│   │   ├── layout.tsx             # Settings sub-layout with tabs
│   │   ├── llm/page.tsx           # LLM provider configs
│   │   └── memory/page.tsx        # Global memory management
│   │
│   └── chat/
│       └── page.tsx               # Orchestrator chat window
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx            # Navigation sidebar
│   │   ├── TopBar.tsx             # Top header with stats
│   │   └── ActivityPanel.tsx      # Right panel: live activity feed
│   │
│   ├── coworking/
│   │   ├── CoworkingCanvas.tsx    # Konva.js Stage wrapper
│   │   ├── OfficeFloor.tsx        # Background tiles, walls, decorations
│   │   ├── DeskGrid.tsx           # Grid of desks with agents
│   │   ├── AgentDesk.tsx          # Single desk: surface + agent + name
│   │   ├── AgentSprite.tsx        # Konva Group: body + domain icon + status
│   │   ├── StatusBubble.tsx       # Thought bubble overlay (WORKING state)
│   │   ├── AgentTooltip.tsx       # HTML overlay tooltip on hover
│   │   └── WorkingParticles.tsx   # Animated dots/sparks (WORKING state)
│   │
│   ├── kanban/
│   │   ├── KanbanBoard.tsx        # Board container with 4 columns
│   │   ├── KanbanColumn.tsx       # Single column (BACKLOG/etc.)
│   │   ├── TaskCard.tsx           # Draggable task card
│   │   ├── TaskCardMini.tsx       # Compact card for sidebar views
│   │   └── TaskDetailModal.tsx    # Full task detail + event timeline
│   │
│   ├── agents/
│   │   ├── AgentList.tsx          # Table view of all agents
│   │   ├── AgentCard.tsx          # Grid card for agent
│   │   ├── AgentBadge.tsx         # Mini: avatar circle + name + dot status
│   │   ├── AgentDetailPanel.tsx   # Full info panel (slide-in from canvas)
│   │   ├── AgentStatusBadge.tsx   # Colored badge: IDLE/WORKING/ERROR/OFFLINE
│   │   └── wizard/
│   │       ├── AgentWizard.tsx    # Multi-step wizard shell
│   │       ├── WizardProgress.tsx # Step indicators
│   │       ├── Step1Domain.tsx    # Domain selection cards
│   │       ├── Step2Class.tsx     # Agent class selection + custom class form
│   │       ├── Step3Identity.tsx  # Gender selector + name input
│   │       ├── Step4Personality.tsx # Sliders for personality traits
│   │       ├── Step5LlmConfig.tsx # LLM provider + model dropdowns
│   │       ├── Step6Tools.tsx     # Tool assignment checkboxes
│   │       └── AvatarPreview.tsx  # Live avatar preview (updates per step)
│   │
│   ├── chat/
│   │   ├── ChatWindow.tsx         # Full chat interface
│   │   ├── ChatMessage.tsx        # Single message bubble (user/assistant)
│   │   ├── ActionChips.tsx        # Visual chips for orchestrator actions
│   │   └── ChatInput.tsx          # Input with send button
│   │
│   ├── activity/
│   │   ├── ActivityFeed.tsx       # Scrollable live log panel
│   │   └── ActivityEntry.tsx      # Single log entry with severity color
│   │
│   ├── tools/
│   │   ├── ToolList.tsx           # Tool registry table
│   │   ├── ToolCard.tsx           # Tool card with type badge
│   │   └── ToolFormModal.tsx      # Create/edit tool modal
│   │
│   ├── llm/
│   │   ├── LlmConfigList.tsx      # List of LLM configs
│   │   ├── LlmConfigForm.tsx      # Create/edit LLM config form
│   │   └── ProviderBadge.tsx      # Color-coded provider badge
│   │
│   └── ui/                        # Shadcn/ui + custom atoms
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Modal.tsx
│       ├── Badge.tsx
│       ├── Slider.tsx
│       └── ...                    # (all Shadcn components)
│
├── lib/
│   ├── api.ts                     # API client (typed fetch wrappers)
│   ├── websocket.ts               # WebSocket singleton + event bus
│   └── utils.ts                   # cn(), formatDate(), etc.
│
├── store/
│   ├── agents.store.ts            # Zustand: agents, statuses, selected
│   ├── tasks.store.ts             # Zustand: tasks, Kanban state
│   ├── activity.store.ts          # Zustand: activity feed entries
│   └── auth.store.ts              # Zustand: JWT token, user session
│
├── hooks/
│   ├── useAgents.ts               # TanStack Query: GET /agents
│   ├── useTasks.ts                # TanStack Query: GET /tasks + mutations
│   ├── useAgentClasses.ts         # TanStack Query: GET /agent-classes
│   ├── useTools.ts                # TanStack Query: GET /tools
│   ├── useLlmConfigs.ts           # TanStack Query: GET /llm-configs
│   ├── useWebSocket.ts            # WS connection + event dispatching
│   └── useActivityFeed.ts         # Activity feed subscription
│
├── types/
│   └── index.ts                   # TypeScript interfaces (mirror backend schemas)
│
├── public/
│   └── sprites/                   # SVG sprites for agent classes
│       ├── hacker.svg
│       ├── finance_manager.svg
│       ├── backend_dev.svg
│       └── ...                    # (one per AgentClass)
│
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

---

## 3. Pages

### `/dashboard` — Coworking Office View

Main landing page. Shows the animated office with all agents at their desks.

```tsx
// app/dashboard/page.tsx
export default function DashboardPage() {
  return (
    <div className="flex h-full">
      {/* Main coworking canvas - takes ~75% width */}
      <div className="flex-1">
        <CoworkingCanvas />
      </div>
      {/* Right panel: activity feed */}
      <div className="w-80 border-l">
        <ActivityFeed />
      </div>
    </div>
  );
}
```

### `/mission-control` — Kanban Board

4-column Kanban with drag & drop.

```tsx
// app/mission-control/page.tsx
export default function MissionControlPage() {
  return (
    <div className="h-full flex flex-col">
      <KanbanToolbar />  {/* Filters, new task button */}
      <KanbanBoard />    {/* 4 columns */}
    </div>
  );
}
```

### `/chat` — Orchestrator Chat

Full-page chat with the orchestrator agent.

### `/agents` — Agent List + Detail

List view with status badges. Click agent → detail/edit panel.

### `/agents/new` — Agent Creation Wizard

6-step multi-page wizard.

---

## 4. Coworking Canvas (Konva.js)

The main visual differentiator — a 2D office rendered on HTML Canvas.

### Canvas Architecture

```tsx
// components/coworking/CoworkingCanvas.tsx
import { Stage, Layer } from "react-konva";

export function CoworkingCanvas() {
  const agents = useAgentsStore(s => s.agents);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Responsive resize
  useEffect(() => {
    const observer = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="w-full h-full bg-slate-900">
      <Stage width={dimensions.width} height={dimensions.height}>
        {/* Layer 1: Office floor background */}
        <Layer>
          <OfficeFloor width={dimensions.width} height={dimensions.height} />
        </Layer>

        {/* Layer 2: Desks and agents */}
        <Layer>
          <DeskGrid
            agents={agents}
            onAgentClick={(id) => setSelectedAgentId(id)}
          />
        </Layer>

        {/* Layer 3: Effects (particles, bubbles) */}
        <Layer>
          {agents.filter(a => a.status === "WORKING").map(agent => (
            <WorkingParticles key={agent.id} agentId={agent.id} />
          ))}
        </Layer>
      </Stage>

      {/* HTML overlay for tooltip (Konva doesn't do HTML well) */}
      {selectedAgentId && (
        <AgentDetailPanel
          agentId={selectedAgentId}
          onClose={() => setSelectedAgentId(null)}
        />
      )}
    </div>
  );
}
```

### Agent Sprite (Konva Group)

```tsx
// components/coworking/AgentSprite.tsx
import { Group, Rect, Circle, Text, Image } from "react-konva";
import { useImage } from "react-konva-utils";

interface AgentSpriteProps {
  agent: Agent;
  x: number;
  y: number;
  onClick: () => void;
}

export function AgentSprite({ agent, x, y, onClick }: AgentSpriteProps) {
  const [spriteImage] = useImage(`/sprites/${agent.avatar_config.sprite_id}.svg`);
  const isWorking = agent.status === "WORKING";
  const isError = agent.status === "ERROR";
  const isOffline = agent.status === "OFFLINE";

  const opacity = isOffline ? 0.4 : 1.0;

  return (
    <Group x={x} y={y} opacity={opacity} onClick={onClick} onTap={onClick}>
      {/* Agent body (sprite image) */}
      <Image
        image={spriteImage}
        width={48}
        height={64}
        offsetX={24}
        offsetY={32}
        filters={isOffline ? [Konva.Filters.Grayscale] : []}
      />

      {/* Status indicator dot */}
      <Circle
        x={20}
        y={-28}
        radius={5}
        fill={
          isWorking ? "#22c55e" :
          isError ? "#ef4444" :
          isOffline ? "#6b7280" :
          "#94a3b8"  // IDLE
        }
        shadowColor={isWorking ? "#22c55e" : undefined}
        shadowBlur={isWorking ? 8 : 0}
      />

      {/* Error icon */}
      {isError && (
        <Text
          text="⚠️"
          x={-12}
          y={-50}
          fontSize={20}
        />
      )}

      {/* Name label */}
      <Text
        text={agent.name}
        fontSize={10}
        fill="white"
        x={-30}
        y={36}
        width={60}
        align="center"
      />

      {/* Domain badge */}
      <Text
        text={agent.avatar_config.icon}
        fontSize={14}
        x={16}
        y={-50}
      />
    </Group>
  );
}
```

### Office Floor (Background)

```tsx
// components/coworking/OfficeFloor.tsx
import { Rect, Line, Group } from "react-konva";

export function OfficeFloor({ width, height }: { width: number; height: number }) {
  const TILE_SIZE = 48;
  const tiles = [];

  // Draw checkerboard floor tiles
  for (let row = 0; row * TILE_SIZE < height; row++) {
    for (let col = 0; col * TILE_SIZE < width; col++) {
      tiles.push(
        <Rect
          key={`${row}-${col}`}
          x={col * TILE_SIZE}
          y={row * TILE_SIZE}
          width={TILE_SIZE}
          height={TILE_SIZE}
          fill={(row + col) % 2 === 0 ? "#1e293b" : "#1a2332"}
        />
      );
    }
  }

  return <Group>{tiles}</Group>;
}
```

### Agent Desk

```tsx
// components/coworking/AgentDesk.tsx
import { Group, Rect, Image } from "react-konva";
import { useImage } from "react-konva-utils";

export function AgentDesk({ agent, gridX, gridY, onClick }) {
  const [deskImage] = useImage("/sprites/desk.svg");
  const DESK_W = 80, DESK_H = 60;
  const x = gridX * (DESK_W + 20) + 40;
  const y = gridY * (DESK_H + 80) + 40;

  return (
    <Group x={x} y={y}>
      {/* Desk surface */}
      <Image image={deskImage} width={DESK_W} height={DESK_H} />

      {/* Monitor glow (WORKING state) */}
      {agent?.status === "WORKING" && (
        <Rect
          x={20}
          y={-10}
          width={40}
          height={30}
          fill="#3b82f6"
          opacity={0.2}
          cornerRadius={2}
        />
      )}

      {/* Agent sprite above desk */}
      {agent && (
        <AgentSprite
          agent={agent}
          x={DESK_W / 2}
          y={-10}
          onClick={onClick}
        />
      )}
    </Group>
  );
}
```

---

## 5. Living Office — Agent Animation System

This is the core visual differentiator of Qubot. The coworking canvas is not static — agents **physically move, interact, and display real-time dialogue** that mirrors what is actually happening in the backend. Every WebSocket event triggers a visual sequence.

### 5.1 Agent UI State Machine

Each agent sprite has its own animation state machine, independent of the backend `AgentStatusEnum`:

```typescript
// types/animation.ts
export type AgentAnimationState =
  | "IDLE_AT_DESK"       // Sitting, slow breathing pulse
  | "STANDING_UP"        // Rising from chair (0.4s tween)
  | "WALKING"            // Moving toward a target position
  | "TALKING"            // Standing next to another agent, dialog active
  | "LISTENING"          // Receiving dialog from another agent
  | "WALKING_BACK"       // Returning to own desk
  | "SITTING_DOWN"       // Returning to chair (0.4s tween)
  | "WORKING"            // At desk, typing animation + monitor glow
  | "THINKING"           // Thought bubble with spinner/ellipsis
  | "ERROR"              // Red shake + alert icon
  | "OFFLINE";           // Desaturated, slumped
```

### 5.2 Animation Event Queue

All animations are queued — never overlapping. A `AnimationQueue` singleton processes one sequence at a time per agent.

```typescript
// lib/animationQueue.ts

export interface AnimationSequence {
  agentId: string;
  steps: AnimationStep[];
}

export interface AnimationStep {
  type:
    | "WALK_TO_AGENT"     // Walk to another agent's desk position
    | "WALK_TO_DESK"      // Walk back to own desk
    | "SHOW_DIALOG"       // Speech bubble with text + optional target
    | "SHOW_THOUGHT"      // Thought bubble (internal monologue)
    | "SET_STATE"         // Snap to animation state
    | "WAIT"              // Pause N ms
    | "SHAKE";            // Error shake
  targetAgentId?: string; // For WALK_TO_AGENT
  text?: string;          // For SHOW_DIALOG / SHOW_THOUGHT
  duration?: number;      // ms
  state?: AgentAnimationState;
}

class AnimationQueueManager {
  private queues: Map<string, AnimationSequence[]> = new Map();
  private running: Set<string> = new Set();

  enqueue(sequence: AnimationSequence) {
    const q = this.queues.get(sequence.agentId) ?? [];
    q.push(sequence);
    this.queues.set(sequence.agentId, q);
    if (!this.running.has(sequence.agentId)) {
      this.processNext(sequence.agentId);
    }
  }

  private async processNext(agentId: string) {
    const q = this.queues.get(agentId);
    if (!q || q.length === 0) { this.running.delete(agentId); return; }
    this.running.add(agentId);
    const seq = q.shift()!;
    for (const step of seq.steps) {
      await this.executeStep(agentId, step);
    }
    this.processNext(agentId); // Process next in queue
  }

  private async executeStep(agentId: string, step: AnimationStep): Promise<void> {
    // Dispatches to Konva animation engine
    return new Promise(resolve => {
      animationEngine.execute(agentId, step, resolve);
    });
  }
}

export const animationQueue = new AnimationQueueManager();
```

### 5.3 WebSocket → Animation Mapping

```typescript
// hooks/useOfficeAnimations.ts
// Translates backend WebSocket events into animation sequences

import { useEffect } from "react";
import { useWebSocket } from "./useWebSocket";
import { animationQueue } from "@/lib/animationQueue";
import { useAgentsStore } from "@/store/agents.store";

export function useOfficeAnimations() {
  const { on } = useWebSocket();
  const agents = useAgentsStore(s => s.agents);

  useEffect(() => {
    // ── Task assigned: orchestrator walks to assignee and delegates ──
    on("task_status_changed", (event) => {
      if (event.payload.old_status === "BACKLOG" && event.payload.new_status === "IN_PROGRESS") {
        const orchestrator = Object.values(agents).find(a => a.is_orchestrator);
        const assignee = agents[event.payload.assigned_agent_id];
        if (!orchestrator || !assignee) return;

        const taskTitle = event.payload.task_title ?? "a task";

        animationQueue.enqueue({
          agentId: orchestrator.id,
          steps: [
            { type: "SET_STATE", state: "STANDING_UP", duration: 400 },
            { type: "WALK_TO_AGENT", targetAgentId: assignee.id, duration: 800 },
            { type: "SET_STATE", state: "TALKING" },
            { type: "SHOW_DIALOG", text: `Hey, I need you to: "${taskTitle}"`, duration: 3000 },
            { type: "WALK_TO_DESK", duration: 800 },
            { type: "SET_STATE", state: "SITTING_DOWN", duration: 400 },
            { type: "SET_STATE", state: "IDLE_AT_DESK" },
          ],
        });

        animationQueue.enqueue({
          agentId: assignee.id,
          steps: [
            { type: "WAIT", duration: 1200 }, // Wait for orchestrator to arrive
            { type: "SET_STATE", state: "LISTENING" },
            { type: "SHOW_THOUGHT", text: "Got it, on it!", duration: 1500 },
            { type: "WAIT", duration: 1500 },
            { type: "SET_STATE", state: "WORKING" },
          ],
        });
      }
    });

    // ── Tool call: agent shows what tool they're using ──
    on("task_event_created", (event) => {
      if (event.payload.event_type === "TOOL_CALL") {
        const agentId = event.payload.agent_id;
        const toolName = event.payload.payload?.tool ?? "tool";
        animationQueue.enqueue({
          agentId,
          steps: [
            { type: "SHOW_THOUGHT", text: `Using ${toolName}...`, duration: 2000 },
          ],
        });
      }
      if (event.payload.event_type === "PROGRESS_UPDATE") {
        const agentId = event.payload.agent_id;
        const msg = event.payload.payload?.message ?? "";
        if (msg) {
          animationQueue.enqueue({
            agentId,
            steps: [
              { type: "SHOW_THOUGHT", text: msg.slice(0, 60), duration: 2500 },
            ],
          });
        }
      }
    });

    // ── Task completed: agent stands up, stretches, sits back ──
    on("task_status_changed", (event) => {
      if (event.payload.new_status === "DONE") {
        const agentId = event.payload.assigned_agent_id;
        if (!agentId) return;
        animationQueue.enqueue({
          agentId,
          steps: [
            { type: "SHOW_DIALOG", text: "✅ Done!", duration: 1500 },
            { type: "WAIT", duration: 500 },
            { type: "SET_STATE", state: "IDLE_AT_DESK" },
          ],
        });
      }
    });

    // ── Task failed: error shake + message ──
    on("task_status_changed", (event) => {
      if (event.payload.new_status === "FAILED") {
        const agentId = event.payload.assigned_agent_id;
        if (!agentId) return;
        animationQueue.enqueue({
          agentId,
          steps: [
            { type: "SHAKE", duration: 600 },
            { type: "SET_STATE", state: "ERROR" },
            { type: "SHOW_DIALOG", text: "❌ I couldn't complete this task", duration: 2500 },
          ],
        });
      }
    });

    // ── Agent comes online ──
    on("agent_status_changed", (event) => {
      if (event.payload.status === "IDLE") {
        animationQueue.enqueue({
          agentId: event.payload.agent_id,
          steps: [{ type: "SET_STATE", state: "IDLE_AT_DESK" }],
        });
      }
      if (event.payload.status === "OFFLINE") {
        animationQueue.enqueue({
          agentId: event.payload.agent_id,
          steps: [{ type: "SET_STATE", state: "OFFLINE" }],
        });
      }
    });
  }, [on, agents]);
}
```

### 5.4 Konva Animation Engine

```typescript
// lib/konvaAnimationEngine.ts
// Executes individual AnimationStep on the Konva layer

import Konva from "konva";

type StepCallback = () => void;

class KonvaAnimationEngine {
  private nodes: Map<string, Konva.Group> = new Map();
  private deskPositions: Map<string, { x: number; y: number }> = new Map();

  registerAgent(agentId: string, node: Konva.Group, deskPos: { x: number; y: number }) {
    this.nodes.set(agentId, node);
    this.deskPositions.set(agentId, deskPos);
  }

  execute(agentId: string, step: AnimationStep, done: StepCallback) {
    const node = this.nodes.get(agentId);
    if (!node) { done(); return; }

    switch (step.type) {
      case "WALK_TO_AGENT": {
        const targetPos = this.deskPositions.get(step.targetAgentId!);
        if (!targetPos) { done(); return; }
        // Stop 60px away from target desk
        const destX = targetPos.x - 60;
        const destY = targetPos.y;
        node.to({ x: destX, y: destY, duration: (step.duration ?? 800) / 1000, onFinish: done });
        break;
      }
      case "WALK_TO_DESK": {
        const ownPos = this.deskPositions.get(agentId)!;
        node.to({ x: ownPos.x, y: ownPos.y, duration: (step.duration ?? 800) / 1000, onFinish: done });
        break;
      }
      case "SHOW_DIALOG": {
        showBubble(node, step.text!, "dialog", step.duration ?? 2500, done);
        break;
      }
      case "SHOW_THOUGHT": {
        showBubble(node, step.text!, "thought", step.duration ?? 2000, done);
        break;
      }
      case "SHAKE": {
        const origX = node.x();
        let ticks = 0;
        const anim = new Konva.Animation(() => {
          node.x(origX + (ticks % 2 === 0 ? 6 : -6));
          ticks++;
          if (ticks > 10) { node.x(origX); anim.stop(); done(); }
        }, node.getLayer());
        anim.start();
        break;
      }
      case "SET_STATE": {
        // Dispatch state change to the AgentSprite component via event
        dispatchAgentStateChange(agentId, step.state!);
        setTimeout(done, step.duration ?? 0);
        break;
      }
      case "WAIT": {
        setTimeout(done, step.duration ?? 500);
        break;
      }
      default:
        done();
    }
  }
}

function showBubble(
  node: Konva.Group,
  text: string,
  type: "dialog" | "thought",
  duration: number,
  done: StepCallback
) {
  // Create a Konva Group: rounded rect + tail + Text
  const padding = 10;
  const maxWidth = 180;
  const label = new Konva.Text({ text, fontSize: 12, fontFamily: "sans-serif", width: maxWidth, wrap: "word" });
  const w = Math.min(label.width() + padding * 2, maxWidth + padding * 2);
  const h = label.height() + padding * 2;

  const bubble = new Konva.Group({ x: node.x() - w / 2, y: node.y() - h - 50 });
  const bg = new Konva.Rect({
    width: w, height: h,
    fill: type === "dialog" ? "#ffffff" : "#fffde7",
    stroke: type === "dialog" ? "#333" : "#f9a825",
    strokeWidth: 1.5,
    cornerRadius: 8,
  });
  label.x(padding); label.y(padding);
  bubble.add(bg, label);
  node.getLayer()?.add(bubble);

  // Fade in
  bubble.opacity(0);
  bubble.to({ opacity: 1, duration: 0.2 });

  // Auto-dismiss
  setTimeout(() => {
    bubble.to({ opacity: 0, duration: 0.3, onFinish: () => { bubble.destroy(); done(); } });
  }, duration - 300);
}

export const animationEngine = new KonvaAnimationEngine();
```

### 5.5 Idle Animations

When an agent is in `IDLE_AT_DESK` state, a continuous ambient animation plays:

```typescript
// components/coworking/IdleAnimation.tsx — runs on every IDLE agent

function startIdleAnimation(node: Konva.Group) {
  // Slow breathing: gentle scale pulse every 3 seconds
  const breathe = new Konva.Animation((frame) => {
    const scale = 1 + 0.012 * Math.sin((frame!.time * Math.PI) / 3000);
    node.scaleY(scale);
  }, node.getLayer());
  breathe.start();
  return breathe; // Store to stop when agent becomes WORKING
}

// Random idle events (every 15-30 seconds one of these fires):
const IDLE_THOUGHTS = [
  "☕ Need coffee...",
  "📰 Checking the news",
  "😴 Nothing to do...",
  "🎵 La la la...",
  "👀 Watching the clock",
];

function scheduleRandomIdleThought(agentId: string) {
  const delay = 15000 + Math.random() * 15000;
  setTimeout(() => {
    const text = IDLE_THOUGHTS[Math.floor(Math.random() * IDLE_THOUGHTS.length)];
    animationQueue.enqueue({
      agentId,
      steps: [{ type: "SHOW_THOUGHT", text, duration: 2000 }],
    });
    scheduleRandomIdleThought(agentId); // Reschedule
  }, delay);
}
```

### 5.6 Agent Pathfinding

Agents walk in straight lines between desks. The desk grid is a fixed layout computed from the canvas size and number of agents.

```typescript
// lib/deskGrid.ts

export interface DeskPosition {
  agentId: string;
  x: number;    // Center X of desk
  y: number;    // Center Y of desk
  row: number;
  col: number;
}

export function computeDeskLayout(
  agentCount: number,
  canvasWidth: number,
  canvasHeight: number
): DeskPosition[] {
  const cols = Math.ceil(Math.sqrt(agentCount));
  const rows = Math.ceil(agentCount / cols);
  const cellW = canvasWidth / (cols + 1);
  const cellH = canvasHeight / (rows + 1);

  return Array.from({ length: agentCount }, (_, i) => ({
    agentId: "",  // Filled in by CoworkingCanvas
    x: cellW * ((i % cols) + 1),
    y: cellH * (Math.floor(i / cols) + 1),
    row: Math.floor(i / cols),
    col: i % cols,
  }));
}
```

### 5.7 New Backend WebSocket Event: `agent_interaction`

To support agent-to-agent interactions in the UI (e.g., two sub-agents collaborating), add a new broadcast event:

```python
# backend/app/realtime/events.py — new event type

async def broadcast_agent_interaction(
    source_agent_id: str,
    target_agent_id: str,
    message: str,
    task_id: str
):
    await broadcast_to_channel("ws:global", {
        "type": "agent_interaction",
        "payload": {
            "source_agent_id": source_agent_id,
            "target_agent_id": target_agent_id,
            "message": message,      # What the source agent "says" to the target
            "task_id": task_id,
        }
    })
```

Called from `ExecutionService` when the orchestrator assigns work or when an agent requests help from another.

Frontend hook receives `agent_interaction` events and triggers walk + dialog sequences between the two agents.

### 5.8 Visual Summary

```
User sends chat message
    │
    ▼
Orchestrator agent: IDLE_AT_DESK → STANDING_UP → WALKING (to assignee)
                   → TALKING ("Hey, I need you to: [task title]")
                   → WALKING_BACK → SITTING_DOWN → IDLE_AT_DESK
                                             │
                                             ▼
                               Assignee: LISTENING → THINKING
                                        → WORKING (typing at desk)
                                        → SHOW_THOUGHT ("Using web browser...")
                                        → SHOW_THOUGHT ("Summarizing results...")
                                        → SHOW_DIALOG ("✅ Done!")
                                        → IDLE_AT_DESK
```

---

## 6. Kanban Board

```tsx
// components/kanban/KanbanBoard.tsx
import { DndContext, DragEndEvent, closestCenter } from "@dnd-kit/core";
import { useTasks } from "@/hooks/useTasks";
import { KanbanColumn } from "./KanbanColumn";
import { api } from "@/lib/api";

const COLUMNS = [
  { id: "BACKLOG", label: "Backlog", color: "slate" },
  { id: "IN_PROGRESS", label: "In Progress", color: "blue" },
  { id: "IN_REVIEW", label: "In Review", color: "yellow" },
  { id: "DONE", label: "Done", color: "green" },
];

export function KanbanBoard() {
  const { data: tasks, refetch } = useTasks();

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const taskId = active.id as string;
    const newStatus = over.id as string; // Column id = status

    // Optimistic update
    await api.patch(`/tasks/${taskId}/status`, { status: newStatus });
    refetch();
  };

  const tasksByStatus = COLUMNS.reduce((acc, col) => {
    acc[col.id] = tasks?.filter(t => t.status === col.id) || [];
    return acc;
  }, {} as Record<string, Task[]>);

  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <div className="flex gap-4 h-full p-4 overflow-x-auto">
        {COLUMNS.map(column => (
          <KanbanColumn
            key={column.id}
            id={column.id}
            label={column.label}
            color={column.color}
            tasks={tasksByStatus[column.id]}
          />
        ))}
      </div>
    </DndContext>
  );
}
```

---

## 6. Agent Creation Wizard

```tsx
// components/agents/wizard/AgentWizard.tsx
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const STEPS = [
  "Domain",
  "Class",
  "Identity",
  "Personality",
  "LLM Config",
  "Tools",
];

export function AgentWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<Partial<AgentCreatePayload>>({});

  const updateForm = (data: Partial<AgentCreatePayload>) => {
    setFormData(prev => ({ ...prev, ...data }));
  };

  const handleSubmit = async () => {
    const agent = await api.post("/agents", formData);
    router.push(`/agents/${agent.data.id}`);
  };

  return (
    <div className="flex h-full">
      {/* Left: form steps */}
      <div className="flex-1 max-w-xl">
        <WizardProgress steps={STEPS} currentStep={step} />

        <div className="mt-6">
          {step === 0 && <Step1Domain data={formData} onChange={updateForm} />}
          {step === 1 && <Step2Class data={formData} onChange={updateForm} />}
          {step === 2 && <Step3Identity data={formData} onChange={updateForm} />}
          {step === 3 && <Step4Personality data={formData} onChange={updateForm} />}
          {step === 4 && <Step5LlmConfig data={formData} onChange={updateForm} />}
          {step === 5 && <Step6Tools data={formData} onChange={updateForm} />}
        </div>

        <div className="flex justify-between mt-8">
          {step > 0 && (
            <Button variant="outline" onClick={() => setStep(s => s - 1)}>
              Back
            </Button>
          )}
          {step < STEPS.length - 1 ? (
            <Button onClick={() => setStep(s => s + 1)}>Next</Button>
          ) : (
            <Button onClick={handleSubmit}>Create Agent</Button>
          )}
        </div>
      </div>

      {/* Right: live avatar preview */}
      <div className="w-72 flex items-center justify-center border-l bg-slate-900">
        <AvatarPreview agent={formData} />
      </div>
    </div>
  );
}
```

### Step 1: Domain Selection

```tsx
// components/agents/wizard/Step1Domain.tsx
const DOMAINS = [
  { id: "TECH", label: "Technology", icon: "💻", description: "Software, infrastructure, data" },
  { id: "FINANCE", label: "Finance", icon: "💰", description: "Financial analysis, accounting" },
  { id: "BUSINESS", label: "Business", icon: "📊", description: "Strategy, operations, PM" },
  { id: "HR", label: "Human Resources", icon: "👥", description: "Recruitment, people ops" },
  { id: "MARKETING", label: "Marketing", icon: "📣", description: "Growth, brand, campaigns" },
  { id: "LEGAL", label: "Legal", icon: "⚖️", description: "Compliance, contracts, advice" },
  { id: "PERSONAL", label: "Personal", icon: "🎯", description: "Productivity, personal assistant" },
  { id: "OTHER", label: "Other", icon: "⚡", description: "Custom domain" },
];

export function Step1Domain({ data, onChange }) {
  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Choose a Domain</h2>
      <p className="text-slate-400 mb-6">
        What area of expertise will this agent focus on?
      </p>
      <div className="grid grid-cols-2 gap-3">
        {DOMAINS.map(domain => (
          <button
            key={domain.id}
            onClick={() => onChange({ domain: domain.id })}
            className={`p-4 rounded-lg border text-left transition-all ${
              data.domain === domain.id
                ? "border-blue-500 bg-blue-500/10"
                : "border-slate-700 hover:border-slate-500"
            }`}
          >
            <span className="text-2xl">{domain.icon}</span>
            <div className="font-medium mt-1">{domain.label}</div>
            <div className="text-xs text-slate-400">{domain.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
```

### Step 4: Personality Sliders

```tsx
// components/agents/wizard/Step4Personality.tsx
export function Step4Personality({ data, onChange }) {
  const personality = data.personality || {};

  const updateTrait = (trait: string, value: number) => {
    onChange({ personality: { ...personality, [trait]: value } });
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Personality & Style</h2>

      {/* Detail vs. Speed slider */}
      <TraitSlider
        label="Working Style"
        lowLabel="Big picture thinker"
        highLabel="Detail-oriented"
        value={personality.detail_oriented ?? 50}
        onChange={v => updateTrait("detail_oriented", v)}
      />

      {/* Risk Tolerance */}
      <TraitSlider
        label="Risk Tolerance"
        lowLabel="Conservative"
        highLabel="Bold & experimental"
        value={personality.risk_tolerance ?? 50}
        onChange={v => updateTrait("risk_tolerance", v)}
      />

      {/* Formality */}
      <TraitSlider
        label="Communication Style"
        lowLabel="Casual & friendly"
        highLabel="Formal & precise"
        value={personality.formality ?? 50}
        onChange={v => updateTrait("formality", v)}
      />

      {/* Strengths */}
      <div className="mt-4">
        <label className="text-sm font-medium">Strengths</label>
        <TagInput
          tags={personality.strengths || []}
          onChange={tags => updateTrait("strengths", tags)}
          placeholder="Add a strength..."
        />
      </div>
    </div>
  );
}
```

---

## 7. State Management

### Zustand Stores

```typescript
// store/agents.store.ts
import { create } from "zustand";

interface AgentState {
  agents: Agent[];
  setAgents: (agents: Agent[]) => void;
  updateStatus: (agentId: string, status: string, extra?: Partial<Agent>) => void;
}

export const useAgentsStore = create<AgentState>((set) => ({
  agents: [],
  setAgents: (agents) => set({ agents }),
  updateStatus: (agentId, status, extra = {}) =>
    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === agentId ? { ...a, status, ...extra } : a
      ),
    })),
}));
```

```typescript
// store/tasks.store.ts
import { create } from "zustand";

interface TaskState {
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  updateStatus: (taskId: string, status: string, extra?: Partial<Task>) => void;
  addTask: (task: Task) => void;
}

export const useTasksStore = create<TaskState>((set) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  updateStatus: (taskId, status, extra = {}) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId ? { ...t, status, ...extra } : t
      ),
    })),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
}));
```

### TanStack Query Hooks

```typescript
// hooks/useAgents.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useAgents(filters?: AgentFilters) {
  return useQuery({
    queryKey: ["agents", filters],
    queryFn: () => api.get("/agents", { params: filters }),
    staleTime: 30_000, // 30 seconds
    refetchInterval: 60_000, // Refresh every minute
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AgentCreate) => api.post("/agents", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });
}

export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();
  const updateStore = useTasksStore(s => s.updateStatus);

  return useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      api.patch(`/tasks/${taskId}/status`, { status }),
    onMutate: async ({ taskId, status }) => {
      // Optimistic update
      updateStore(taskId, status);
    },
    onError: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
```

---

## 8. API Client

```typescript
// lib/api.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request(method: string, path: string, options: any = {}) {
  const token = typeof window !== "undefined"
    ? localStorage.getItem("qubot_token")
    : null;

  const response = await fetch(`${BASE_URL}/api/v1${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
    ...options,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || "Request failed");
  }

  if (response.status === 204) return null;
  const json = await response.json();
  return json.data; // Unwrap the envelope
}

export const api = {
  get: (path: string, options?: any) => request("GET", path, options),
  post: (path: string, body: any) => request("POST", path, { body }),
  put: (path: string, body: any) => request("PUT", path, { body }),
  patch: (path: string, body: any) => request("PATCH", path, { body }),
  delete: (path: string) => request("DELETE", path),
};
```

---

## 9. TypeScript Types

```typescript
// types/index.ts

export type DomainEnum = "TECH" | "BUSINESS" | "FINANCE" | "HR" | "MARKETING" | "LEGAL" | "PERSONAL" | "OTHER";
export type AgentStatus = "IDLE" | "WORKING" | "ERROR" | "OFFLINE";
export type TaskStatus = "BACKLOG" | "IN_PROGRESS" | "IN_REVIEW" | "DONE" | "FAILED";
export type Priority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ToolType = "SYSTEM_SHELL" | "WEB_BROWSER" | "FILESYSTEM" | "HTTP_API" | "SCHEDULER" | "CUSTOM";
export type LlmProvider = "OPENAI" | "ANTHROPIC" | "GOOGLE" | "GROQ" | "LOCAL" | "OTHER";

export interface AvatarConfig {
  sprite_id: string;
  color_primary: string;
  color_secondary: string;
  icon: string;
  desk_position: { x: number; y: number };
}

export interface PersonalityConfig {
  detail_oriented: number;  // 0-100
  risk_tolerance: number;
  formality: number;
  strengths: string[];
  weaknesses: string[];
  communication_style: string;
}

export interface Agent {
  id: string;
  name: string;
  gender: "MALE" | "FEMALE" | "NON_BINARY";
  class_id: string;
  class_name: string;
  domain: DomainEnum;
  role_description: string;
  personality: PersonalityConfig;
  status: AgentStatus;
  is_orchestrator: boolean;
  current_task_id?: string;
  current_task_title?: string;
  avatar_config: AvatarConfig;
  llm_config_id: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: Priority;
  domain_hint?: DomainEnum;
  created_by: string;
  assigned_agent_id?: string;
  assigned_agent_name?: string;
  assigned_agent_avatar?: AvatarConfig;
  parent_task_id?: string;
  subtask_count: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface AgentCreate {
  name: string;
  gender: "MALE" | "FEMALE" | "NON_BINARY";
  class_id: string;
  domain: DomainEnum;
  role_description: string;
  personality: PersonalityConfig;
  llm_config_id: string;
  avatar_config: AvatarConfig;
  is_orchestrator: boolean;
  tool_assignments: { tool_id: string; permissions: string }[];
}
```

---

## 10. package.json Dependencies

```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "konva": "^9.3.0",
    "react-konva": "^18.2.10",
    "react-konva-utils": "^1.0.6",
    "@dnd-kit/core": "^6.1.0",
    "@dnd-kit/sortable": "^8.0.0",
    "@tanstack/react-query": "^5.40.0",
    "zustand": "^4.5.0",
    "framer-motion": "^11.3.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.4.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "@types/react": "^18.3.0",
    "tailwindcss": "^3.4.0",
    "eslint": "^8.57.0"
  }
}
```
