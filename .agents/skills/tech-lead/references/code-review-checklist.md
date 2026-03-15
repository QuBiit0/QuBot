# Code Review Checklist — Tech Lead

> Checklist sistemático para revisión de código con criterios claros.

## Pre-Review (Antes de Mirar Código)

- [ ] ¿El PR tiene descripción clara del cambio?
- [ ] ¿Hay link al ticket/issue?
- [ ] ¿El tamaño es razonable? (<400 líneas ideal, <800 máximo)
- [ ] ¿Los tests están incluidos?

## Correctness (¿Funciona?)

### Lógica
- [ ] ¿La lógica resuelve el problema descrito?
- [ ] ¿Se manejan los edge cases?
  - Inputs vacíos / null / undefined
  - Listas vacías
  - Valores negativos o cero
  - Strings con espacios o caracteres especiales
- [ ] ¿Hay race conditions posibles?
- [ ] ¿Se validan los inputs del usuario?

### Error Handling
- [ ] ¿Los errores se capturan y manejan apropiadamente?
- [ ] ¿Los mensajes de error son informativos (sin filtrar datos sensibles)?
- [ ] ¿Hay fallback para dependencias externas?
- [ ] ¿Los errores se propagan correctamente (no se "tragan")?

## Security (¿Es Seguro?)

- [ ] ¿Hay secretos hardcodeados? (API keys, passwords)
- [ ] ¿Se usa parametrización en queries SQL?
- [ ] ¿Los inputs se sanitizan antes de renderizar?
- [ ] ¿Los endpoints tienen autenticación/autorización?
- [ ] ¿Se valida ownership de recursos?

## Performance (¿Es Eficiente?)

- [ ] ¿Hay N+1 queries?
- [ ] ¿Se usa paginación para listas grandes?
- [ ] ¿Hay loops innecesarios o ineficientes?
- [ ] ¿Se cachea lo que debe cachearse?
- [ ] ¿Las queries tienen los índices necesarios?

## Readability (¿Se Entiende?)

- [ ] ¿Los nombres de variables/funciones son descriptivos?
- [ ] ¿Hay comentarios donde la lógica no es obvia?
- [ ] ¿Las funciones son cortas y hacen una sola cosa?
- [ ] ¿El código sigue las convenciones del proyecto?
- [ ] ¿Hay código duplicado que debería extraerse?

## Architecture (¿Encaja?)

- [ ] ¿Sigue los patrones existentes del proyecto?
- [ ] ¿Las dependencias son apropiadas? (no circular dependencies)
- [ ] ¿La separación de responsabilidades es correcta?
- [ ] ¿Se evita el acoplamiento excesivo?

## Testing

- [ ] ¿Los tests cubren el happy path?
- [ ] ¿Los tests cubren los edge cases importantes?
- [ ] ¿Los tests son independientes (no dependen de orden)?
- [ ] ¿Los nombres de tests describen el escenario?
- [ ] ¿Coverage ≥ 80% en código nuevo?

## Feedback Guidelines

### Tono
- ✅ "¿Qué te parece si...?" (sugerencia)
- ✅ "Considerar..." (optional)
- ✅ "Esto podría causar X porque..." (explicativo)
- ❌ "Esto está mal" (sin contexto)
- ❌ "Yo lo haría diferente" (sin explicar por qué)

### Categorías de Comentarios

| Prefijo | Significado | Bloquea PR? |
|---------|------------|-------------|
| `[blocker]` | Debe corregirse antes de merge | ✅ Sí |
| `[suggestion]` | Mejora recomendada | ❌ No |
| `[nit]` | Nitpick, cosmético | ❌ No |
| `[question]` | Pregunta, necesito entender | Depende |
| `[praise]` | Comentario positivo | ❌ No |

### Example Comments

```
[blocker] Esta query es vulnerable a SQL injection.
Usar parametrización: `select(User).where(User.id == user_id)`

[suggestion] Considerar extraer esta lógica a un service separado.
Facilitaría testing y reutilización.

[nit] Preferiría `is_active` en lugar de `active`.
Consistente con los otros modelos.

[praise] 🎉 Excelente manejo de los edge cases.
El test de empty list es particularmente bueno.
```

## Technical Debt Assessment

| Nivel | Acción | Cuándo |
|-------|--------|--------|
| **Crítico** | Fix antes de merge | Siempre |
| **Alto** | Ticket creado, fix en próximo sprint | Esta iteración |
| **Medio** | Ticket creado, backlog | Cuando corresponda |
| **Bajo** | Documentar para futuro | Eventualmente |
