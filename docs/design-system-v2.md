# Qubot — Design System v2 (Premium Glassmorphism)
> **Estado**: Implementado y desplegado | **Versión**: 2.0 | **Fecha**: 2026-03-16

---

## 1. Concepto Visual

**"Deep Space HQ"** — Oficina corporativa futurista de noche con estética glassmorphism.
La paleta base evoca un cielo profundo de madrugada: fondos casi negros con tinta azul índigo,
acentos en violeta/índigo, y elementos translúcidos que dejan ver capas de profundidad.

---

## 2. Tokens de Diseño

### 2.1 Colores — Tema Night (principal)

```css
/* ── Fondos ── */
--bg-deep:        #060912;   /* base, cielo de noche */
--bg-deeper:      #030608;   /* fondo de fondo, más oscuro */

/* ── Acentos ── */
--accent:         #6366f1;   /* índigo — botones, bordes activos */
--accent-glow:    rgba(99,102,241,0.35);
--secondary:      #8b5cf6;   /* violeta — gradientes, badges secundarios */

/* ── Superficie Glass ── */
--glass-bg:       rgba(6,9,18,0.88);
--glass-border:   rgba(99,102,241,0.22);

/* ── Texto ── */
--text-primary:   rgba(255,255,255,0.92);
--text-secondary: rgba(255,255,255,0.55);
--text-muted:     rgba(255,255,255,0.30);

/* ── Estado ── */
--status-active:  #10b981;   /* verde esmeralda */
--status-idle:    #64748b;   /* pizarra */
--status-error:   #f43f5e;   /* rosa rojo */
--status-offline: #374151;

/* ── Superficies ── */
--surface-1:      rgba(255,255,255,0.04);
--surface-2:      rgba(255,255,255,0.07);
--surface-3:      rgba(255,255,255,0.10);
```

### 2.2 Colores — Tema Day

```css
--bg-deep:        #e8f0ff;
--bg-deeper:      #d0def8;
--accent:         #4f46e5;
--glass-bg:       rgba(232,240,255,0.88);
--glass-border:   rgba(79,70,229,0.25);
```

### 2.3 Colores — Tema Sunset

```css
--bg-deep:        #1a0e1f;
--bg-deeper:      #120a16;
--accent:         #e879f9;
--secondary:      #f97316;
--glass-bg:       rgba(26,14,31,0.88);
--glass-border:   rgba(232,121,249,0.22);
```

### 2.4 Tipografía

| Uso | Familia | Peso | Tamaño |
|-----|---------|------|--------|
| Body / UI | `system-ui, -apple-system` | 400/500/600 | 11–14px |
| Monospace / Badges | `ui-monospace, SFMono-Regular` | 500 | 10–12px |
| Números (stats) | `tabular-nums` feature | 700 | 14–18px |

### 2.5 Espaciado

| Token | Valor |
|-------|-------|
| `--radius-sm` | 6px |
| `--radius-md` | 10px |
| `--radius-lg` | 16px |
| `--radius-xl` | 20px |

### 2.6 Efectos Glass

```css
/* Panel principal */
backdrop-filter: blur(14px);
background: rgba(6,9,18,0.88);
border: 1px solid rgba(99,102,241,0.22);

/* Card de escritorio */
backdrop-filter: blur(10px);
background: rgba(15,20,40,0.85);
border: 1px solid rgba(99,102,241,0.15);

/* Anillo de avatar activo */
box-shadow: 0 0 20px rgba(16,185,129,0.45);

/* Monitor encendido */
box-shadow: 0 0 12px rgba(99,102,241,0.5);
```

---

## 3. Componentes Implementados

### 3.1 `OfficeSystem.tsx` — Canvas Principal

**Descripción**: Sala SVG de oficina futurista con todos sus elementos como componentes React internos.

#### Capas del Canvas (de atrás a adelante)

| Capa | Componente interno | Descripción |
|------|--------------------|-------------|
| 1 | `PremiumFloor` | Suelo de mármol negro con gradiente radial |
| 2 | `PremiumBackWall` | Pared trasera con patrón de líneas sutiles y separador luminoso |
| 3 | `PremiumWindows` | Ventanas con silueta de ciudad nocturna, estrellas y luna |
| 4 | `HolographicDisplay` | Pantalla holográfica animada (reemplaza la pizarra) |
| 5 | `PremiumBookshelf` | Librería minimalista con libros y pantalla |
| 6 | `PremiumServerRack` | Rack de servidores con LEDs de actividad |
| 7 | `PremiumPlant` | Planta decorativa con ramas SVG |
| 8 | `PremiumClock` | Reloj analógico con agujas en tiempo real |
| 9 | `AgentDesk` × N | Escritorios individuales de agentes (draggable) |

#### `HolographicDisplay`
- Borde gradiente animado (índigo → violeta → cian)
- Brackets de esquina estilo HUD
- Línea de scanline animada
- Texto del proyecto en tipografía monospace
- Brillo de fondo radial

#### `PremiumWindows`
- Silueta de ciudad SVG determinista (sin `Math.random()` para evitar hydration mismatch)
- Cielo nocturno con gradiente azul medianoche
- Luna con halo radial
- Grid de ventanas edificios con iluminación variada
- Estrellas SVG deterministas

#### `PremiumClock`
- Reloj analógico SVG con hora real del sistema
- Tick marks con marcas de hora en color accent
- Agujas: hora, minutos, segundos con `requestAnimationFrame`

### 3.2 `AgentDesk.tsx` — Escritorio de Agente

**Descripción**: Escritorio 3D premium con avatar, monitor, teclado y placa identificadora.

#### Anatomía visual (de abajo a arriba)

```
┌─────────────────────────────────────────┐
│  PLACA / NAMEPLATE (glassmorphism)      │
│  [● status dot] Nombre  [BADGE]        │
├─────────────────────────────────────────┤
│  TECLADO  [grid 6×3 de teclas]         │
├─────────────────────────────────────────┤
│  MONITOR  [pantalla con código animado] │
│  [base del monitor]                     │
├─────────────────────────────────────────┤
│  ESCRITORIO  [superficie 3D con borde]  │
│  Panel frontal con profundidad          │
└─────────────────────────────────────────┘
         [AVATAR con anillo de estado]
```

#### Avatar

| Elemento | Detalle |
|----------|---------|
| Forma | Círculo de 40px |
| Anillo | Gradiente de 2px, color según status |
| Agente WORKING | `animate-ping` en segundo anillo (pulso verde) |
| Agente Lead | Corona SVG amarilla encima del avatar |
| Letra | Inicial del nombre, coloreada según status |

#### Monitor

- Pantalla oscura con efecto glow del color accent
- Líneas de código simuladas (4 barras de ancho y opacidad variados)
- Borde inferior con brillo (`box-shadow: inset 0 -1px 0 accent`)

#### Nameplate (Glassmorphism)

```css
background: rgba(6,9,18,0.75);
border: 1px solid rgba(99,102,241,0.2);
backdrop-filter: blur(10px);
border-radius: 8px;
```

Contiene:
- Punto de status con color dinámico
- Nombre del agente
- Badge de rol (monospace, truncado)

#### STATUS_CONFIG

| Valor | Color | Glow | Label |
|-------|-------|------|-------|
| `IDLE` / `idle` | `#64748b` | `rgba(100,116,139,0.3)` | Idle |
| `WORKING` / `busy` | `#10b981` | `rgba(16,185,129,0.45)` | Working |
| `ERROR` | `#f43f5e` | `rgba(244,63,94,0.45)` | Error |
| `OFFLINE` | `#374151` | `rgba(55,65,81,0.2)` | Offline |

---

## 4. Layout del Sistema de Oficina

```
┌──────────────────────────────────────────────────────────────┐
│  HEADER glassmorphism (blur:14px, bg: rgba(6,9,18,0.88))    │
│  [Ícono tema] [Nombre Oficina] ─── [Selector Oficina ▾]     │
│              [● N/M agents online]                           │
│  [○ Night] [○ Day] [○ Sunset]                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  SVG CANVAS (height: calc(100vh - 140px))                   │
│  ┌────────────────────────────────────────┐                  │
│  │  PremiumWindows (fondo)                │                  │
│  │  PremiumBackWall                       │                  │
│  │  HolographicDisplay (centro)           │                  │
│  │  PremiumBookshelf (izq)                │                  │
│  │  PremiumServerRack (der)               │                  │
│  │  PremiumPlant (esquinas)               │                  │
│  │  PremiumClock (pared)                  │                  │
│  │  PremiumFloor                          │                  │
│  │  AgentDesk × N (draggable)             │                  │
│  └────────────────────────────────────────┘                  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  FOOTER glassmorphism                                        │
│  [timestamp LIVE]  [drag hint]  [reset layout btn]          │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. UX y Comportamiento

### 5.1 Drag & Drop

- Cada `AgentDesk` es draggable dentro del canvas SVG
- Las posiciones se persisten en `localStorage` por clave `qubot-office-positions-{officeId}`
- El botón "Reset Layout" restaura posiciones por defecto
- Posiciones por defecto calculadas en grid 3×N según índice del agente

### 5.2 Selector de Oficina

- Dropdown para cambiar de sala si hay múltiples oficinas configuradas
- Persiste la selección en `localStorage`

### 5.3 Selector de Tema

- Tres botones circulares en el header: Night / Day / Sunset
- El tema cambia todos los tokens de color en tiempo real

### 5.4 Animaciones

| Elemento | Tipo | Duración |
|----------|------|----------|
| Agente WORKING | `animate-ping` (Tailwind) | 1s infinito |
| Scanline holográfica | CSS `translateY` | 2s infinito |
| Gradiente HoloDisplay | CSS `rotate` (conic-gradient) | 3s infinito |
| LEDs del server rack | `animate-pulse` (Tailwind) | 1s infinito |
| Agujas del reloj | JS `requestAnimationFrame` | tiempo real |

---

## 6. Estructura de Archivos

```
frontend/
└── components/
    └── coworking/
        ├── OfficeSystem.tsx    ← Canvas SVG + elementos de oficina + lógica
        └── AgentDesk.tsx       ← Escritorio individual de agente
```

### Variables de estado en `OfficeSystem.tsx`

| Estado | Tipo | Descripción |
|--------|------|-------------|
| `currentTheme` | `'night' \| 'day' \| 'sunset'` | Tema activo |
| `positions` | `Record<string, {x, y}>` | Posición de cada escritorio |
| `dragging` | `string \| null` | ID del agente siendo arrastrado |
| `selectedOffice` | `string` | Sala activa |
| `time` | `Date` | Hora actual (reloj) |

---

## 7. Decisiones de Diseño

| Decisión | Razón |
|----------|-------|
| SVG puro (no Three.js / Canvas 2D) | Compatibilidad SSR, no hydration issues, fácil accesibilidad |
| Deterministic heights en bookshelf | Evitar `Math.random()` en render → hydration mismatch en Next.js |
| `backdrop-filter: blur` en lugar de PNG de glass | Permite transparencia real sobre el canvas |
| `animate-ping` de Tailwind para status | CSS puro, sin dependencia de Framer Motion |
| `requestAnimationFrame` para el reloj | Sin `setInterval` que puede acumular drift |
| Posiciones en `localStorage` | Estado de UI efímero, no necesita backend |
| Temas como objeto de tokens | Permite cambio de tema O(1) sin re-renderizar todo el árbol |

---

## 8. Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 2.0 | 2026-03-16 | Rediseño premium completo: glassmorphism, HolographicDisplay, PremiumWindows con ciudad nocturna, AgentDesk 3D, tres temas |
| 1.0 | 2026-01 | Diseño inicial: pixel art, paleta GitHub dark |
