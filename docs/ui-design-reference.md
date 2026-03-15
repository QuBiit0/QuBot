# Qubot — UI Design Reference
> **Concepto visual**: Qubot Office — AI Coworking Dashboard

---

## 1. Visión General

La interfaz de **Qubot Office** es un dashboard de oficina de IA con dos paneles principales:
- **Left / Main Panel**: Vista de oficina coworking (isométrica / pixel-art 2D)
- **Right Panel**: Pipeline de requests + Activity Log en tiempo real

---

## 2. Layout General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TOPBAR: Logo | Office | Tasks          [Stats: Tasks · Tokens · Cost · Today] │
├────────────────────────────────────────────────────────────────────────────────┤
│  TABS: Main Office | Interaction Stats | Agent Thoughts | Cost Savings |       │
│         Agent Usage | Token Monitor | Security | Database                      │
├──────────────────────────────────────────────┬─────────────────────────────────┤
│                                              │  Request Pipeline (0 active)    │
│          COWORKING CANVAS                    │  ─────────────────────────────  │
│          (2D pixel-art office)               │  [Waiting for requests...]      │
│                                              │  Status badges: Received /      │
│  Each agent is a pixel character at a desk:  │  Analysing / Task Created /     │
│  - Frontend (UI/UX Developer)               │  Assigned / Working / Done      │
│  - Lead (Tech Lead / Mission Controller)    ├─────────────────────────────────┤
│  - Backend (Backend & Infrastructure)       │  Activity Log • LIVE            │
│  - Scheduler (Post Queue Checker)           │  [N events]                     │
│  - QA (QA & Security)                       │  ─────────────────────────────  │
│  - Content / Olivia (LinkedIn Creator)      │  10:49:42 ✅ Done [Fui yo...] │
│                                              │  10:48:13 ⚙️ Working  Lead...  │
│  [● 3/6 online]  [LIVE badge + timestamp]   │  10:44:11 👤 User [new req]    │
│                                              │  ...                            │
└──────────────────────────────────────────────┴─────────────────────────────────┘
```

---

## 3. Topbar / Header

| Elemento | Descripción |
|----------|-------------|
| **Logo** | Icono cuadrado + nombre del proyecto ("Qubot") + subtítulo "AI Office Dashboard" |
| **LIVE badge** | Badge verde pulsante que indica conexión activa a WebSocket |
| **Navegación** | `Office` · `Tasks` (tabs centrales) |
| **Stats Bar** | `Tasks: N` · `Tokens: X.XXM` · `Cost: $X.XX` · `Today: $X.XX` |

### Stats en tiempo real
- **Tasks**: Número de tareas activas
- **Tokens**: Total de tokens consumidos en la sesión
- **Cost**: Costo total acumulado en USD
- **Today**: Costo del día actual

---

## 4. Tab Navigation (Segunda fila)

| Tab | Contenido |
|-----|-----------|
| **Main Office** | Vista principal de coworking (default) |
| **Interaction Stats** | Métricas de interacciones por agente |
| **Agent Thoughts** | Stream del "inner monologue" de cada agente |
| **Cost Savings** | Análisis de costos y optimizaciones |
| **Agent Usage** | Métricas de uso por agente (tokens, tasks, etc.) |
| **Token Monitor** | Uso de tokens en tiempo real por modelo/proveedor |
| **Security** | Logs de seguridad, permisos, accesos |
| **Database** | Vista read-only de tablas/entidades principales |

---

## 5. Panel Izquierdo: Coworking Canvas

### 5.1 Estilo Visual
- **Estética**: Pixel art / 8-16 bit, vista isométrica o top-down levemente inclinada
- **Ambiente**: Oficina de coworking con:
  - Madera en el suelo
  - Escritorios individuales con monitores
  - Plantas decorativas
  - Lámparas colgantes con luz cálida
  - Ventanas al fondo con vista urbana
  - Librería/rack de servidores al fondo
  - Pizarrón/pantalla central con nombre del proyecto

### 5.2 Representación de Agentes

Cada agente es un **personaje pixel-art** sentado en su escritorio:

```
┌─────────────────────────────┐
│  [Avatar pixel-art]         │
│  ┌─────────────────────┐    │
│  │  NOMBRE DEL ROL     │    │
│  │  Clase / Descripción│    │
│  └─────────────────────┘    │
└─────────────────────────────┘
```

| Agente Predefinido | Rol visible | Posición |
|--------------------|-------------|----------|
| Lead | Tech Lead / Mission Controller | Centro-arriba |
| Frontend | UI/UX Developer | Izquierda |
| Backend | Backend & Infrastructure | Derecha |
| QA | QA & Security | Abajo-centro |
| Scheduler | Post Queue Checker | Abajo-izquierda |
| Content | LinkedIn Content Creator | Abajo-derecha |

### 5.3 Estados Visuales de Agentes

| Estado | Visual |
|--------|--------|
| `WORKING` | Animación de tipeo en teclado, monitor encendido con actividad |
| `IDLE` | Personaje en postura neutra, monitor encendido |
| `ERROR` | Icono ⚠️ sobre el personaje, monitor en rojo |
| `OFFLINE` | Personaje desvanecido/apagado, monitor apagado |

### 5.4 Overlay del Agente (Tooltip/Badge)
Al hacer hover o click sobre un agente:
```
┌─────────────────────────────┐
│ 👤 Nombre del Agente        │
│ 🏷️ Clase: Backend Engineer  │
│ 🌐 Dominio: TECH            │
│ ⚡ Estado: WORKING           │
│ 📋 Tarea: "Refactor API..." │
└─────────────────────────────┘
```

### 5.5 Indicadores Globales
- **● N/M online**: Badge en esquina inferior izquierda (ej: "● 3/6 online")
- **LIVE + timestamp**: Indicador en esquina superior derecha del canvas

---

## 6. Panel Derecho

### 6.1 Request Pipeline

```
┌──────────────────────────────────────────┐
│  🔄 Request Pipeline          [N active] │
├──────────────────────────────────────────┤
│                                          │
│     [Ícono]                              │
│  Waiting for requests...                 │
│                                          │
│  Status Flow:                            │
│  ● Received → Analysing → Task Created   │
│  → Assigned → Working → Done            │
└──────────────────────────────────────────┘
```

**Badges de estado** con colores:
- `Received` — gris
- `Analysing` — amarillo
- `Task Created` — azul
- `Assigned` — púrpura
- `Working` — naranja/ámbar
- `Done` — verde

### 6.2 Activity Log

```
┌──────────────────────────────────────────────────────────┐
│  📋 Activity Log • LIVE                    [1793 events] │
├──────────────────────────────────────────────────────────┤
│  10:49:42  ✅ Done  [Lead] Done: "Fui yo (main/0pvs)..." │
│  10:49:13  ⚙️ Working  [Lead] Responding: "message"      │
│  10:44:11  👤 User  [Lead] "(new request)"               │
│  10:44:23  ✅ Done  [Lead] Done: "HEARTBEAT_OK"          │
│  10:44:19  ⚙️ Working  [Lead] Responding: "message"      │
│  10:43:31  ✅ Done  [Lead] Done: "Liste ✅ El problema.. │
│  10:43:19  ⚙️ Working  [Lead] "(new request)"            │
│  ...                                                     │
└──────────────────────────────────────────────────────────┘
```

**Formato de cada entrada:**
```
[HH:MM:SS]  [StatusIcon]  [StatusBadge]  [AgentBadge]  [Mensaje truncado]
```

**Íconos de status:**
- `✅` — Done
- `⚙️` — Working
- `👤` — User input
- `📋` — Task Created
- `🔄` — Assigned
- `❌` — Failed/Error

---

## 7. Color Palette (Dark Theme)

```css
/* Background */
--bg-primary:    #0d1117;   /* Fondo principal */
--bg-secondary:  #161b22;   /* Paneles/cards */
--bg-tertiary:   #21262d;   /* Items en listas */

/* Borders */
--border:        #30363d;

/* Text */
--text-primary:  #e6edf3;
--text-secondary:#8b949e;
--text-muted:    #484f58;

/* Accent / Status */
--green:         #3fb950;   /* Online, Done, LIVE */
--yellow:        #d29922;   /* Working, Analysing */
--blue:          #58a6ff;   /* Task Created, links */
--purple:        #bc8cff;   /* Assigned */
--orange:        #f0883e;   /* Warnings */
--red:           #f85149;   /* Error, Failed */

/* Canvas */
--canvas-bg:     #1a1f2e;   /* Fondo del coworking */
```

---

## 8. Tipografía

| Uso | Fuente | Peso | Tamaño |
|-----|--------|------|--------|
| Logo | Monospace / JetBrains Mono | Bold | 16px |
| Headings | Inter / System UI | SemiBold | 14px |
| Body | Inter / System UI | Regular | 13px |
| Code / Logs | JetBrains Mono | Regular | 12px |
| Timestamps | Monospace | Regular | 11px |
| Stats numbers | Tabular Nums (Inter) | Bold | 14px |

---

## 9. Componentes UI Clave

### 9.1 AgentCard (en el canvas)
```tsx
// Superposición sobre el sprite del agente
<AgentCard
  name="Frontend"
  role="UI/UX Developer"
  status="WORKING"
  task="Implement dashboard layout"
/>
```

### 9.2 ActivityLogItem
```tsx
<ActivityLogItem
  timestamp="10:49:42"
  status="DONE"
  agentName="Lead"
  message="Done: 'Fui yo (main/0pvs) quien hizo todo...'"
/>
```

### 9.3 RequestPipelineItem
```tsx
<RequestPipelineItem
  id="req-001"
  statusFlow={["RECEIVED", "ANALYSING", "TASK_CREATED", "ASSIGNED", "WORKING"]}
  currentStatus="WORKING"
  agentName="Backend"
  requestSummary="Refactor authentication module"
/>
```

### 9.4 StatsBar
```tsx
<StatsBar
  tasks={0}
  tokensUsed={10_740_000}   // → "10.74M"
  totalCost={0.00}
  todayCost={0.00}
/>
```

### 9.5 LiveBadge
```tsx
<LiveBadge connected={true} />
// Muestra: ● LIVE (verde pulsante)
```

---

## 10. Responsividad

| Breakpoint | Layout |
|------------|--------|
| < 768px | Stack vertical (canvas arriba, log abajo) |
| 768–1024px | Canvas 60% / Panel 40% |
| > 1024px | Canvas 65% / Panel 35% (layout por defecto) |

---

## 11. Interacciones UX

| Acción | Comportamiento |
|--------|----------------|
| Click en agente | Abre panel lateral con detalles + historial |
| Hover en agente | Tooltip con nombre, clase, estado, tarea actual |
| Click en tarea del log | Abre modal con detalle de la tarea |
| Click "Tasks" (nav) | Navega a vista Kanban |
| Scroll en Activity Log | Historial paginado (infinite scroll up) |
| Click en stat number | Expande a vista detallada de la métrica |

---

## 12. Animaciones

| Elemento | Animación |
|----------|-----------|
| LIVE badge | Pulso verde cada 2s |
| Agente WORKING | Ciclo de tipeo (3 frames) cada 0.8s |
| Nuevo evento en log | Slide-in desde arriba con fade |
| Status badge cambio | Cross-fade 200ms |
| Agente cambia estado | Transición de opacidad 300ms |
| Tokens counter | Count-up animado al incrementar |

---

## 13. Páginas / Rutas

| Ruta | Componente | Descripción |
|------|-----------|-------------|
| `/` | Redirect → `/dashboard` | |
| `/dashboard` | `CoworkingDashboard` | Vista principal (imagen referencia) |
| `/tasks` | `KanbanBoard` | Mission Control / Kanban |
| `/agents` | `AgentList` | Lista de todos los agentes |
| `/agents/new` | `AgentWizard` | Wizard de creación de agente |
| `/agents/[id]` | `AgentDetail` | Detalle + edición |
| `/tools` | `ToolsManager` | Gestión de herramientas |
| `/settings` | `Settings` | Config global: LLM keys, etc. |
| `/settings/llm` | `LLMConfig` | Configuración de modelos |

---

*Este documento define la especificación visual del concepto **Qubot Office** y sirve como guía para implementar el frontend de Qubot.*
