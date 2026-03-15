# Frameworks de Priorización — Product Manager

> Guía rápida de frameworks para priorizar features y tomar decisiones de producto.

## MoSCoW Method

| Categoría | Significado | Ejemplo |
|-----------|------------|---------|
| **Must Have** | Sin esto, el release no tiene sentido | Login, CRUD básico |
| **Should Have** | Importante pero no crítico | Filtros avanzados |
| **Could Have** | Nice to have si hay tiempo | Dark mode |
| **Won't Have** | Deliberadamente fuera de scope | Chatbot IA |

### Uso Práctico

```markdown
## Sprint 5 - MoSCoW

### Must Have (80% del esfuerzo)
- [ ] Endpoint de checkout completo
- [ ] Email de confirmación de compra
- [ ] Validación de stock en tiempo real

### Should Have (15% del esfuerzo)
- [ ] Historial de órdenes
- [ ] Notificación push al cambiar estado

### Could Have (5% del esfuerzo si sobra tiempo)
- [ ] Descuento por cupón
- [ ] Share order vía WhatsApp

### Won't Have (next sprint)
- [ ] Sistema de puntos/rewards
- [ ] Integración con marketplace
```

## RICE Score

```
RICE = (Reach × Impact × Confidence) / Effort
```

| Factor | Escala | Ejemplo |
|--------|--------|---------|
| **Reach** | Usuarios/quarter | 5000 users/quarter |
| **Impact** | 0.25 - 3 | 2 = High impact |
| **Confidence** | 0-100% | 80% |
| **Effort** | Person-weeks | 3 person-weeks |

```
Feature A: (5000 × 2 × 0.8) / 3 = 2666
Feature B: (1000 × 3 × 0.9) / 1 = 2700  ← Winner
Feature C: (500 × 1 × 0.5) / 5 = 50
```

## ICE Score

```
ICE = Impact × Confidence × Ease (cada uno 1-10)
```

| Feature | Impact | Confidence | Ease | Score |
|---------|--------|------------|------|-------|
| Dark mode | 4 | 9 | 7 | 252 |
| Social login | 7 | 8 | 5 | 280 ← |
| Advanced search | 6 | 6 | 3 | 108 |

## Kano Model

```
                    Satisfacción
                         ↑
                    ╱ Delighters
                  ╱    (Wow!)
                ╱
  ─────────────┼────────────── → Funcionalidad
                ╲
                  ╲  Performance
                    ╲ (More = Better)
                     
─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ Basics
                    │           (Expected)
                    ↓
               Insatisfacción
```

| Tipo | Ejemplo | Sin ella | Con ella |
|------|---------|----------|----------|
| **Basic** | Login funcione | Muy enojado | Normal |
| **Performance** | Velocidad | Algo molesto | Más contento |
| **Delighter** | Animaciones | No nota | Wow! |

## User Story Template

```markdown
### US-{ID}: {Título conciso}

**Como** {rol/persona},
**quiero** {acción/feature},
**para** {beneficio/valor de negocio}.

#### Acceptance Criteria
- [ ] Dado {contexto}, cuando {acción}, entonces {resultado esperado}
- [ ] Dado {contexto 2}, cuando {acción 2}, entonces {resultado 2}

#### Technical Notes
- Endpoints: POST /api/v1/...
- Dependencias: Auth service
- Effort estimate: M (1-2 días)

#### Definition of Done
- [ ] Código implementado y test passing
- [ ] PR reviewed y mergeado
- [ ] Documentación actualizada
- [ ] Desplegado en staging
```

## Métricas de Producto (North Star)

| Tipo de Producto | North Star Metric | Supporting Metrics |
|-----------------|-------------------|-------------------|
| **SaaS B2B** | MRR / ARR | Churn, NPS, CAC |
| **Marketplace** | GMV | Take rate, Liquidity |
| **Social** | DAU/MAU | Retention D1/D7/D30 |
| **E-commerce** | Revenue per User | AOV, Conversion Rate |
| **Productivity** | Weekly Active Users | Tasks completed/week |
