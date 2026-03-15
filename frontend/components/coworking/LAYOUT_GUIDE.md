# 🏢 Qubot Office Layout System

Sistema de posicionamiento automático y escalable para agentes AI en el coworking canvas.

---

## 📊 Capacidades y Límites

| Rango | Agente Count | Layout | Escala | Calidad Visual |
|-------|-------------|--------|--------|----------------|
| 🟢 **Óptimo** | 1-8 | U-Shape | 100% | Excelente |
| 🟡 **Bueno** | 9-16 | U-Shape Compact | 90% | Muy Buena |
| 🟠 **Aceptable** | 17-24 | Auditorium | 80% | Buena |
| 🔴 **Compacto** | 25-32 | Hex Grid | 70% | Regular |
| ⛔ **Límite** | 33+ | - | - | No recomendado |

**Límite absoluto:** 32 agentes

---

## 🎯 Algoritmos de Layout

### 1. U-Shape (1-16 agentes)
```
        ┌─────────┐
        │  LEAD   │
        └────┬────┘
   ┌───────┐   ┌───────┐
   │ TECH  │   │  OPS  │
   ├───────┤   ├───────┤
   │ TECH  │   │  OPS  │
   └───────┘   └───────┘
      └───────────┘
         DATA
```

- Lead arriba en el centro
- Tech team a la izquierda
- Ops team a la derecha
- Data/Creative abajo

### 2. Auditorium (17-24 agentes)
```
        ┌─────────┐
        │  LEAD   │
        └─────────┘
   ┌─────────────────────┐
   │  row 1: 8 agents    │
   ├─────────────────────┤
   │  row 2: 8 agents    │
   ├─────────────────────┤
   │  row 3: 7 agents    │
   └─────────────────────┘
```

- Filas dinámicas según ancho del canvas
- Agentes más pequeños (80% escala)
- Distribución uniforme

### 3. Hex Grid (25-32 agentes)
```
           ┌─────────┐
           │  LEAD   │
           └────┬────┘
        ┌───┐ ┌───┐ ┌───┐
        │ 6 │ │ 5 │ │ 4 │  ← ring 1
        └───┘ └───┘ └───┘
     ┌───┐ ┌───┐ ┌───┐ ┌───┐
     │12 │ │11 │ │10 │ │ 9 │  ← ring 2
     └───┘ └───┘ └───┘ └───┘
   ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐
   │18 │ │17 │ │16 │ │15 │ │14 │  ← ring 3
   └───┘ └───┘ └───┘ └───┘ └───┘
```

- Distribución hexagonal eficiente
- Máxima densidad de agentes
- Escala reducida (70%)

---

## 🧠 Clasificación Automática por Dominio

El sistema clasifica agentes automáticamente:

| Tipo | Keywords Detectados |
|------|---------------------|
| **Lead** | `isLead`, `isOrchestrator`, nombre contiene "lead" |
| **Tech** | `frontend`, `backend`, `dev`, `database`, `mobile`, `fullstack` |
| **Ops** | `devops`, `security`, `sre`, `infra`, `ops` |
| **Data** | `data`, `ml`, `ai`, `analytics`, `scientist` |
| **Creative** | `design`, `ux`, `content`, `writer`, `creative` |

---

## 📐 Configuración Ajustable

```typescript
const LAYOUT_CONFIG = {
  SPACING_X: 130,      // Espaciado horizontal
  SPACING_Y: 100,      // Espaciado vertical
  LEAD_Y_OFFSET: 30,   // Lead más arriba
  
  MARGIN_LEFT: 80,     // Margen izquierdo
  MARGIN_RIGHT: 80,    // Margen derecho
  MARGIN_TOP: 60,      // Margen superior
  MARGIN_BOTTOM: 60,   // Margen inferior
  
  MAX_AGENTS_CLEAN: 16,      // Se ven perfectos
  MAX_AGENTS_COMFORTABLE: 24, // Se ven bien
  MAX_AGENTS_HARD: 32,        // Límite absoluto
  
  SCALE_FULL: 1.0,     // Escala normal
  SCALE_MEDIUM: 0.9,   // 9-16 agentes
  SCALE_SMALL: 0.8,    // 17-24 agentes
  SCALE_TINY: 0.7,     // 25-32 agentes
};
```

---

## 🚀 Uso del Layout Engine

```typescript
import { calculateAgentPositions, getLayoutStats } from './AgentLayoutEngine';

// Calcular posiciones
const canvasDims = {
  width: 800,
  height: 450,
  wallHeight: 90
};

const { positions, layoutType, warnings } = calculateAgentPositions(
  agents, 
  canvasDims
);

// Verificar estadísticas
const stats = getLayoutStats(agents, canvasDims);
console.log(stats);
// {
//   totalAgents: 12,
//   layoutType: 'ushape',
//   positionsCalculated: 12,
//   overlaps: 0,
//   scale: 0.9,
//   recommendedMax: 16,
//   hardLimit: 32
// }
```

---

## ⚠️ Mejores Prácticas

1. **Para ≤8 agentes:** Layout óptimo, todos los detalles visibles
2. **Para 9-16:** Aún se ven bien, ligeramente más compacto
3. **Para 17-24:** Considerar agrupar por proyecto/equipo
4. **Para 25-32:** Último recurso, información reducida
5. **>32 agentes:** Usar vista alternativa (lista, mapa, filtros)

---

## 🔮 Futuras Mejoras

- [ ] Scroll/Pan cuando hay muchos agentes
- [ ] Zoom in/out
- [ ] Mini-map para navegación
- [ ] Colapso de clusters
- [ ] Filtrado por dominio/equipo
- [ ] Vistas alternativas (lista, grid, grafo)

---

## 📈 Visualización de Escalabilidad

```
Agentes:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32
          █  █  █  █  █  █  █  █  ▓  ▓  ▓  ▓  ▓  ▓  ▓  ▓  ░  ░  ░  ░  ░  ░  ░  ░  ▒  ▒  ▒  ▒  ▒  ▒  ▒  ▒
          └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
               Óptimo (8)            Bueno (16)         Aceptable (24)       Límite (32)
```

**Leyenda:**
- `█` Verde - Óptimo
- `▓` Amarillo - Bueno
- `░` Naranja - Aceptable
- `▒` Rojo - Compacto
