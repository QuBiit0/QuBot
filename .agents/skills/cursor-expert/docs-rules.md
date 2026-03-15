# Creating Cursor Rules (`docs-rules.md`)

Crea reglas de proyecto en `.cursor/rules/` para proveer contexto persistente al agente de IA.

## Recaudación de Requisitos

Antes de crear una regla, determina:
1. **Propósito**: ¿Qué debe forzar o enseñar esta regla?
2. **Alcance**: ¿Debería aplicar siempre, o solo a archivos específicos?
3. **Patrón de archivos (Globs)**: Si es específico, ¿a qué patrones? (ej. `**/*.ts`)

Si el usuario no especifica, pregunta el alcance: *"¿Esta regla aplica siempre o solo a cierto tipo de archivos?"*

## Formato del Archivo Rule

Las reglas son archivos `.mdc` en `.cursor/rules/` con YAML frontmatter:

```markdown
---
description: Breve descripción de la regla
globs: **/*.ts  # Patrón de archivo 
alwaysApply: false  # True si debe aplicar siempre
---

# Título de la Regla

Contenido de la regla aquí...
```

## Mejores Prácticas

- **Mantener las reglas concisas**: Menos de 50 líneas.
- **Una preocupación por regla**: Divide reglas grandes.
- **Ejemplos Concretos**: Provee ejemplos de cómo cumplir o violar la regla.
- **Flexibilidad de Librerías (NUEVO ESTÁNDAR LMAgent)**: Nunca hardcodees versiones o librerías específicas (ej. "Usa React 18") si no es estrictamente necesario o pedido explícitamente. Exprésalo como una recomendación o ejemplo: "Usa librerías actualizadas (ej. React 18+)".

### Ejemplo de Regla

```markdown
---
description: Estándares de manejo de errores
globs: **/*.ts, **/*.js
alwaysApply: false
---

# Manejo de Errores

Siempre utiliza bloques try-catch al realizar peticiones externas:

\`\`\`typescript
// ❌ MAL
try {
  await fetchData();
} catch (e) {}

// ✅ BIEN
try {
  await fetchData();
} catch (e) {
  logger.error('Failed to fetch', { error: e });
  throw new Error('No se pudo recuperar la data', { cause: e });
}
\`\`\`
```
