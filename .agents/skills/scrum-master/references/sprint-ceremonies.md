# Sprint Ceremonies Playbook — Scrum Master

> Guía operativa para facilitar las ceremonias de Scrum.

## Resumen de Ceremonias

| Ceremonia | Duración (2-week sprint) | Frecuencia | Participantes |
|-----------|-------------------------|-----------|---------------|
| Sprint Planning | 2h | Inicio de sprint | Equipo + PO |
| Daily Standup | 15 min | Diaria | Equipo |
| Sprint Review | 1h | Final de sprint | Equipo + Stakeholders |
| Sprint Retro | 1.5h | Final de sprint | Equipo |
| Refinement | 1h | Mid-sprint | Equipo + PO |

## Sprint Planning

### Agenda

```
1. [10 min] Review del Sprint Goal propuesto por PO
2. [20 min] PO presenta top items del backlog
3. [60 min] Equipo estima y selecciona stories
4. [20 min] Descomponer stories en tasks
5. [10 min] Confirmar Sprint Goal y compromiso
```

### Facilitation Script

```
"Bienvenidos al Sprint Planning del Sprint {N}.

{PO}, ¿podrías compartir el Sprint Goal propuesto?
[PO presenta goal]

Veamos las stories más importantes del backlog.
Para cada una:
1. ¿Entendemos completamente lo que hay que hacer?
2. ¿Qué necesitamos para completarla?
3. ¿Cuánto esfuerzo estimamos? (Planning Poker)

¿El equipo se siente comfortable comprometiéndose
con estas {N} stories para este sprint?"
```

### Definition of Ready (DoR)

- [ ] Story tiene acceptance criteria claros
- [ ] Story fue refinada y estimada
- [ ] No hay dependencias externas bloqueantes
- [ ] Diseño/mockup disponible (si aplica)
- [ ] API spec definida (si aplica)

## Daily Standup

### Formato Clásico (3 Preguntas)

```
1. ¿Qué hice ayer?
2. ¿Qué haré hoy?
3. ¿Tengo algún blocker?
```

### Formato Walk the Board (Recomendado)

```
Miramos el board de derecha a izquierda:

1. ¿Qué está "In Review"?     → ¿Quién puede reviewear?
2. ¿Qué está "In Progress"?   → ¿Cómo va? ¿Blockers?
3. ¿Qué está "To Do"?         → ¿Quién toma el siguiente?

Foco: FLUJO del trabajo, no status individual.
```

### Anti-Patterns del Daily

| ❌ Anti-Pattern | ✅ Corrección |
|----------------|---------------|
| Dura 30+ minutos | Strict 15 min. Topics largos → parking lot |
| Status report al SM | Equipo habla entre sí |
| Solo el que habla escucha | Todos engaged |
| No action items | Cada blocker tiene owner |
| Se discuten soluciones | "Hablemos offline después" |

## Sprint Review (Demo)

### Agenda

```
1. [5 min]  Sprint Goal reminder
2. [40 min] Demo de features completadas
3. [10 min] Métricas del sprint (velocity, burndown)
4. [5 min]  Feedback de stakeholders
```

### Facilitación

```
"Hoy mostramos lo que el equipo logró en Sprint {N}.
El Sprint Goal era: {GOAL}.

{Dev1}, ¿podrías demostrar la feature de {X}?

[Stakeholder feedback]

Velocity de este sprint: {V} story points.
Items completados: {N} de {M} planificados.

¿Alguna pregunta o feedback?"
```

## Sprint Retrospective

### Formato: Start-Stop-Continue

```
┌──────────────┬──────────────┬──────────────┐
│   🟢 START   │   🔴 STOP    │  🟡 CONTINUE │
│              │              │              │
│ Pair program │ Meetings sin │ Code reviews │
│ Write ADRs   │ agenda       │ Daily walks  │
│              │ Skip retros  │ Mob debugging│
└──────────────┴──────────────┴──────────────┘
```

### Formato: 4Ls

```
✅ Liked:    ¿Qué nos gustó?
📚 Learned:  ¿Qué aprendimos?
😕 Lacked:   ¿Qué nos faltó?
🔮 Longed:   ¿Qué deseamos para el futuro?
```

### Pasos de la Retro

```
1. [5 min]  Icebreaker / Check-in
2. [10 min] Recolectar datos (silent brainstorm)
3. [10 min] Agrupar temas similares
4. [5 min]  Votar (dot voting: 3 votos cada uno)
5. [20 min] Discutir top 2-3 temas
6. [10 min] Action items (owner + deadline)
```

### Regla de Oro

> "Regardless of what we discover, we understand and truly believe that everyone did the best job they could, given what they knew at the time."
> — Norm Kerth

## Métricas a Trackear

| Métrica | Fórmula | Target |
|---------|---------|--------|
| **Velocity** | SP completados / sprint | Estable ±20% |
| **Commitment Reliability** | SP completados / SP planificados | > 80% |
| **WIP** | Items "In Progress" | ≤ team_size - 1 |
| **Cycle Time** | Start → Done por item | Decreasing |
| **Sprint Goal Hit Rate** | Goals logrados / total | > 80% |
