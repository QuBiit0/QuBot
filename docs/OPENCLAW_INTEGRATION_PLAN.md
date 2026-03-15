# 📋 Plan de Integración: Funcionalidades OpenClaw → Qubot

> **Análisis realizado:** 15 Marzo 2026  
> **Objetivo:** Integrar las mejores funcionalidades de OpenClaw manteniendo la diferenciación visual de Qubot

---

## 🎯 Resumen Ejecutivo

### Diferenciador Principal de Qubot
**"La Oficina Digital de Agentes AI"** - Qubot visualiza tu equipo de agentes como una oficina de coworking real, donde puedes VER quién está trabajando, asignar tareas arrastrando tarjetas, y configurar cada agente con una interfaz 100% visual.

### Qué SÍ tiene OpenClaw (y Qubot debe integrar)
1. **Skills System** - Agentes pueden crear sus propios skills/tools
2. **Proactividad** - Heartbeat system, tareas en background (cron-like)
3. **6 Plataformas de Messaging** - WhatsApp, Telegram, Discord, Slack, Signal, iMessage
4. **Auto-configuración** - One-liner de instalación
5. **Hot-reload de skills** - Sin reiniciar el sistema

### Qué NO tiene OpenClaw (diferenciadores Qubot)
1. ❌ **Visual UI** - Solo CLI + chat
2. ❌ **Multi-agent real** - Single agent por instancia
3. ❌ **Mission Control visual** - Kanban básico
4. ❌ **11+ LLM providers** - No soporta chinos (Kimi, MiniMax, Zhipu)
5. ❌ **Sistema de clases de agente** - Todos iguales
6. ❌ **Control de permisos granular** - Acceso total a skills

---

## 📊 Matriz de Funcionalidades a Integrar

### CRÍTICO (Must Have) - Implementar esta semana

| # | Funcionalidad | Origen | Complejidad | Impacto |
|---|---------------|--------|-------------|---------|
| 1 | **Skills System** | OpenClaw | Alta | ⭐⭐⭐⭐⭐ |
| 2 | **Agent Creation Wizard** | Qubot Plan | Media | ⭐⭐⭐⭐⭐ |
| 3 | **Coworking Canvas** | Qubot Plan | Alta | ⭐⭐⭐⭐⭐ |
| 4 | **Kanban Board funcional** | Qubot Plan | Media | ⭐⭐⭐⭐ |

### ALTO (Should Have) - Implementar este mes

| # | Funcionalidad | Origen | Complejidad | Impacto |
|---|---------------|--------|-------------|---------|
| 5 | **6 Messaging Platforms** | OpenClaw | Alta | ⭐⭐⭐⭐ |
| 6 | **Proactivity System** | OpenClaw | Media | ⭐⭐⭐⭐ |
| 7 | **Memory System 3-capas** | Qubot Plan | Media | ⭐⭐⭐ |
| 8 | **Tool System avanzado** | Qubot Plan | Media | ⭐⭐⭐⭐ |

### MEDIO (Nice to Have) - Implementar Q2

| # | Funcionalidad | Origen | Complejidad | Impacto |
|---|---------------|--------|-------------|---------|
| 9 | **Workflow Builder Visual** | Qubot Plan | Alta | ⭐⭐⭐ |
| 10 | **Gamification** | Qubot Plan | Baja | ⭐⭐ |
| 11 | **Analytics Dashboard** | Qubot Plan | Media | ⭐⭐⭐ |
| 12 | **Integration Hub** | Qubot Plan | Alta | ⭐⭐⭐ |

---

## 🔧 1. Skills System (CRÍTICO)

### Descripción
Sistema que permite a los agentes CREAR sus propios skills/tools dinámicamente, con hot-reload sin reiniciar el sistema.

### Modelo de Datos
```typescript
interface Skill {
  id: string;
  name: string;
  description: string;
  code: string; // Python/JS code
  language: 'python' | 'javascript';
  parameters: SkillParameter[];
  created_by: string; // agent_id
  is_public: boolean;
  version: string;
  created_at: Date;
  updated_at: Date;
}

interface SkillParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  required: boolean;
  default?: any;
}

interface AgentSkill {
  id: string;
  agent_id: string;
  skill_id: string;
  config: Record<string, any>;
  is_enabled: boolean;
}
```

### API Endpoints
```yaml
POST   /api/v1/skills              # Crear skill
GET    /api/v1/skills              # Listar skills públicos
GET    /api/v1/skills/:id          # Obtener skill
PUT    /api/v1/skills/:id          # Actualizar skill
DELETE /api/v1/skills/:id          # Eliminar skill
POST   /api/v1/skills/:id/execute  # Ejecutar skill

POST   /api/v1/agents/:id/skills         # Asignar skill a agente
DELETE /api/v1/agents/:id/skills/:sid    # Remover skill de agente
```

### Implementación Backend
1. **Skill Registry Service** - Registro y versionado de skills
2. **Skill Execution Engine** - Sandbox seguro para ejecutar código
3. **Hot Reload System** - Recarga sin reiniciar workers
4. **Skill Marketplace** - Repositorio de skills públicos

### UI Components
- `SkillEditor` - Editor de código con Monaco/CodeMirror
- `SkillMarketplace` - Grid de skills disponibles
- `SkillTester` - Testing interactivo de skills
- `AgentSkillsPanel` - Gestión de skills por agente

---

## 🎮 2. Agent Creation Wizard (CRÍTICO)

### Descripción
Wizard visual de 6 pasos para crear agentes con personalización completa.

### Flujo del Wizard
```yaml
Step 1: Dominio
  - Seleccionar dominio: TECH, FINANCE, MARKETING, HR, LEGAL, BUSINESS
  - Icono y color automático por dominio

Step 2: Clase de Agente
  - Templates predefinidos por dominio
  - Ejemplos:
    - TECH: Frontend Dev, Backend Dev, DevOps, Security Engineer
    - FINANCE: Analyst, Accountant, Auditor, Advisor
    - MARKETING: Content Writer, SEO Specialist, Social Media Manager

Step 3: Personalización Básica
  - Nombre
  - Género (para avatar)
  - Personalidad (sliders: Formal↔Casual, Analítico↔Creativo)

Step 4: Configuración LLM
  - Provider dropdown (11 opciones)
  - Modelo dropdown (filtrado por provider)
  - Temperature slider
  - Max tokens

Step 5: Tools/Skills
  - Lista de checkboxes con permisos
  - Categories: File System, APIs, Browsers, Databases, Custom Skills

Step 6: Preview y Confirmación
  - Avatar preview animado
  - Resumen de configuración
  - Botón "Crear Agente"
```

### Componentes React
```typescript
// components/wizard/AgentWizard.tsx
interface AgentWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (agent: CreateAgentDTO) => void;
}

// hooks/useAgentWizard.ts
const useAgentWizard = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<Partial<Agent>>({});
  const [preview, setPreview] = useState<AgentPreview | null>(null);
  
  const canProceed = () => {
    switch(step) {
      case 1: return !!formData.domain;
      case 2: return !!formData.agent_class_id;
      case 3: return !!formData.name;
      case 4: return !!formData.llm_config;
      case 5: return true; // Tools opcionales
      case 6: return true;
    }
  };
  
  return { step, setStep, formData, setFormData, preview, canProceed };
};
```

---

## 🏢 3. Coworking Canvas (CRÍTICO)

### Descripción
Visualización de la oficina digital con agentes como sprites animados.

### Features
```yaml
Canvas 2D (Konva.js):
  - Grid de escritorios (layout automático)
  - Agentes como sprites animados
  - Estados visuales: IDLE, WORKING, ERROR, OFFLINE
  - Burbujas de diálogo en tiempo real
  - Efectos de partículas (opcional)
  
Interacciones:
  - Click en agente → Panel de detalle
  - Drag & drop para reordenar escritorios
  - Zoom/Pan del espacio
  - Múltiples "salas" (equipos separados)
  
Animaciones:
  - IDLE: Respiración sutil
  - WORKING: Indicador de actividad pulsante
  - TYPING: Animación de escritura
  - ERROR: Indicador rojo parpadeante
```

### Layout Engine
```typescript
// components/coworking/LayoutEngine.ts
interface DeskPosition {
  id: string;
  x: number;
  y: number;
  agentId?: string;
}

const calculateDeskPositions = (
  agentCount: number, 
  canvasWidth: number, 
  canvasHeight: number
): DeskPosition[] => {
  const cols = Math.ceil(Math.sqrt(agentCount));
  const rows = Math.ceil(agentCount / cols);
  const cellW = canvasWidth / (cols + 1);
  const cellH = canvasHeight / (rows + 1);
  
  return Array.from({ length: agentCount }, (_, i) => ({
    id: `desk-${i}`,
    x: cellW * ((i % cols) + 1),
    y: cellH * (Math.floor(i / cols) + 1),
  }));
};
```

### Agent Sprite System
```typescript
interface AgentSprite {
  id: string;
  colorPrimary: string;
  colorSecondary: string;
  avatarType: 'robot' | 'human' | 'abstract';
  animations: {
    idle: AnimationFrame[];
    working: AnimationFrame[];
    typing: AnimationFrame[];
    error: AnimationFrame[];
  };
}

// Renderizado con react-konva
<Group x={desk.x} y={desk.y}>
  {/* Desk */}
  <Rect width={80} height={60} fill="#334155" cornerRadius={8} />
  
  {/* Agent Avatar */}
  <AgentAvatar 
    agent={agent} 
    state={agent.status}
    onClick={() => onSelect(agent.id)}
  />
  
  {/* Status Indicator */}
  <StatusIndicator status={agent.status} />
  
  {/* Name Label */}
  <Text text={agent.name} y={70} align="center" width={80} />
</Group>
```

---

## 📋 4. Kanban Board Funcional (CRÍTICO)

### Descripción
Board drag-and-drop para gestión de tareas con integración real-time.

### Features
```yaml
Columns:
  - BACKLOG (gris)
  - IN_PROGRESS (azul)
  - IN_REVIEW (amarillo)
  - DONE (verde)
  - FAILED (rojo)

Task Cards:
  - Título
  - Descripción (expandible)
  - Prioridad (LOW, MEDIUM, HIGH, CRITICAL)
  - Dominio (icono)
  - Agente asignado (avatar)
  - Fecha de creación/due date
  
Interactions:
  - Drag & drop entre columnas
  - Click para editar detalle
  - Botón "+" para crear tarea rápida
  - Filtros por dominio/prioridad/agente
```

### Implementación con @dnd-kit
```typescript
// components/kanban/KanbanBoard.tsx
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';

const KanbanBoard = () => {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;
    
    const taskId = active.id as string;
    const newStatus = over.id as TaskStatus;
    
    updateTaskStatus(taskId, newStatus);
  };

  return (
    <DndContext 
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4">
        {COLUMNS.map((col) => (
          <KanbanColumn key={col.id} id={col.id}>
            <SortableContext 
              items={tasksByColumn[col.id]}
              strategy={verticalListSortingStrategy}
            >
              {tasksByColumn[col.id].map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </SortableContext>
          </KanbanColumn>
        ))}
      </div>
    </DndContext>
  );
};
```

---

## 💬 5. Messaging Integrations (ALTO)

### Plataformas a Soportar
| Plataforma | Prioridad | Complejidad | Librería Sugerida |
|------------|-----------|-------------|-------------------|
| **Telegram** | Alta | Baja | `python-telegram-bot` |
| **Discord** | Alta | Media | `discord.py` |
| **Slack** | Alta | Media | `slack-sdk` |
| **WhatsApp** | Media | Alta | `whatsapp-web.js` o API oficial |
| **Signal** | Baja | Alta | `signal-cli` |
| **iMessage** | Baja | Muy Alta | Solo macOS |

### Arquitectura
```yaml
Adapter Pattern:
  BaseAdapter:
    - connect()
    - disconnect()
    - send_message()
    - on_message(callback)
  
  TelegramAdapter(BaseAdapter):
    - Usa webhooks o polling
    - Soporta markdown
    - Bot commands
  
  DiscordAdapter(BaseAdapter):
    - Slash commands
    - Embeds ricos
    - Threads
  
  SlackAdapter(BaseAdapter):
    - Block Kit UI
    - Home tab
    - Shortcuts
```

### Configuración por Agente
```typescript
interface MessagingConfig {
  agent_id: string;
  platforms: {
    telegram?: {
      bot_token: string;
      allowed_chats: string[];
    };
    discord?: {
      bot_token: string;
      guild_id: string;
      allowed_channels: string[];
    };
    slack?: {
      bot_token: string;
      signing_secret: string;
    };
  };
  default_response_time: number; // segundos
  auto_respond: boolean;
}
```

---

## ⏰ 6. Proactivity System (ALTO)

### Descripción
Sistema de heartbeats y tareas programadas (cron-like) para agentes proactivos.

### Features
```yaml
Heartbeat System:
  - Cada agente reporta status cada 30s
  - Health check automático
  - Auto-restart de agents caídos
  
Scheduled Tasks:
  - Cron expressions ("0 9 * * MON")
  - Intervals ("every 30 minutes")
  - One-time schedules ("at 2026-03-20 14:00")
  
Proactive Behaviors:
  - Monitoreo de fuentes externas
  - Alertas basadas en condiciones
  - Reportes automáticos periódicos
```

### Modelo de Datos
```typescript
interface ScheduledTask {
  id: string;
  agent_id: string;
  name: string;
  description: string;
  schedule_type: 'cron' | 'interval' | 'once';
  schedule_value: string; // cron expr o interval
  task_template: {
    title: string;
    description: string;
    domain: DomainEnum;
  };
  is_enabled: boolean;
  last_run?: Date;
  next_run?: Date;
  created_at: Date;
}

interface Heartbeat {
  agent_id: string;
  timestamp: Date;
  status: 'healthy' | 'warning' | 'critical';
  cpu_percent: number;
  memory_mb: number;
  active_tasks: number;
}
```

---

## 🧠 7. Memory System 3-Capas (ALTO)

### Arquitectura
```yaml
Layer 1: GlobalMemory
  - Conocimiento compartido entre todos los agentes
  - Tagged y searchable
  - Vector-ready para RAG futuro
  
Layer 2: AgentMemory
  - Memoria específica por agente
  - Importancia: 1-5
  - Auto-aprendizaje de preferencias
  
Layer 3: TaskMemory
  - Resumen automático post-tarea
  - Key facts extraídos
  - Referencia para tareas futuras similares
```

### Implementación
```typescript
interface MemoryEntry {
  id: string;
  layer: 'global' | 'agent' | 'task';
  agent_id?: string;
  task_id?: string;
  content: string;
  importance: 1 | 2 | 3 | 4 | 5;
  tags: string[];
  embedding?: number[]; // Para futura búsqueda semántica
  created_at: Date;
  access_count: number;
  last_accessed?: Date;
}

// Memory retrieval con context injection
const getRelevantMemories = async (
  agentId: string,
  query: string,
  context: 'task' | 'conversation'
): Promise<MemoryEntry[]> => {
  // 1. Buscar en AgentMemory
  // 2. Buscar en GlobalMemory relevante
  // 3. Buscar en TaskMemory de tareas similares
  // 4. Ordenar por importancia y relevancia
};
```

---

## 🛠️ 8. Tool System Avanzado (ALTO)

### Tipos de Tools
```yaml
HTTP_API:
  - Auth: Bearer, API Key, OAuth2
  - Whitelist de endpoints
  - Rate limiting
  - Timeout configurable

SYSTEM_SHELL:
  - Whitelist de comandos
  - Jail en directorio específico
  - Resource limits (CPU/RAM)
  
WEB_BROWSER:
  - Playwright/Selenium
  - Screenshot capability
  - Form filling
  - JS execution (sandboxed)

FILESYSTEM:
  - Jail en directorio
  - Permisos: READ_ONLY, READ_WRITE
  - Max file size limits

SCHEDULER:
  - Cron expressions
  - Tareas recurrentes
  - Callbacks a agentes

CUSTOM (Skills):
  - Código Python/JS dinámico
  - Sandbox seguro
  - Hot reload
```

### Security Model
```typescript
interface ToolPermission {
  tool_id: string;
  agent_id: string;
  permission_level: 'READ_ONLY' | 'READ_WRITE' | 'DANGEROUS';
  allowed_params?: string[];
  denied_params?: string[];
  rate_limit?: number; // calls per minute
}

// Ejecución con audit logging
const executeTool = async (
  tool: Tool,
  params: any,
  context: ExecutionContext
): Promise<ToolResult> => {
  // 1. Validar permisos
  // 2. Sanitizar parámetros
  // 3. Ejecutar en sandbox
  // 4. Log a auditoría
  // 5. Retornar resultado
};
```

---

## 📅 Roadmap de Implementación

### Semana 1 (15-21 Marzo)
- [ ] Skills System - Backend + Frontend básico
- [ ] Agent Creation Wizard - UI completa
- [ ] Coworking Canvas - MVP con sprites estáticos

### Semana 2 (22-28 Marzo)
- [ ] Kanban Board - Drag & drop funcional
- [ ] Telegram Integration
- [ ] Memory System - Backend

### Semana 3 (29 Marzo - 4 Abril)
- [ ] Discord Integration
- [ ] Proactivity System - Heartbeats
- [ ] Tool System - Refactor + UI

### Semana 4 (5-11 Abril)
- [ ] Slack Integration
- [ ] Workflow Builder MVP
- [ ] Testing + Polish

---

## 🎨 UI/UX Guidelines

### Paleta de Colores
```css
:root {
  /* Base */
  --bg-base: #020617;
  --bg-surface: #0f172a;
  --bg-card: #1e293b;
  --bg-elevated: #334155;
  
  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  
  /* Accents */
  --accent-blue: #3b82f6;
  --accent-green: #10b981;
  --accent-yellow: #f59e0b;
  --accent-red: #ef4444;
  --accent-purple: #8b5cf6;
}
```

### Componentes Prioritarios
1. `AgentCard` - Tarjeta de agente en grid
2. `TaskCard` - Tarjeta de tarea en kanban
3. `ActivityFeed` - Feed de actividad en tiempo real
4. `SkillEditor` - Editor de código para skills
5. `Wizard` - Componente reutilizable para wizards

---

## ✅ Checklist de Integración

### Backend
- [ ] Modelos: Skill, AgentSkill, ScheduledTask, MemoryEntry
- [ ] APIs: Skills CRUD, Execution endpoint
- [ ] Services: SkillExecutionEngine, ProactivityService
- [ ] Integrations: Telegram bot, Discord bot

### Frontend
- [ ] Componentes: SkillMarketplace, SkillEditor, AgentWizard
- [ ] Canvas: CoworkingOffice, AgentSprite, DeskGrid
- [ ] Kanban: DragDropContext, Column, TaskCard
- [ ] Hooks: useSkills, useProactivity, useMessaging

### DevOps
- [ ] Docker: Containers para bots de messaging
- [ ] Config: Variables para tokens de bots
- [ ] Docs: Guías de configuración por plataforma

---

**Nota:** Este plan integra lo mejor de OpenClaw (skills, proactividad, messaging) mientras mantiene y expande la diferenciación visual única de Qubot (Coworking Office, Mission Control, Agent Wizard).
