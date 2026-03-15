# 🤖 AI Agent Engineering Rules
> **Tipo**: `rule` | **Versión**: 3.0.0 | **Referencia**: `ai-agent-engineer`

## 📌 Core Principles

> ⚠️ **FLEXIBILIDAD DE HERRAMIENTAS**: Frameworks y patrones listados (ej. MCP, RAG, Evals) son **ejemplos de referencia** conceptuales. Tienes la libertad y el deber de sugerir e implementar los protocolos y arquitecturas de agentes más modernos y eficientes del estado del arte.
1. **Tool-First Mindset**: Los agentes no adivinan, usan herramientas.
2. **Determinismo**: `temperature=0` para llamadas a funciones (Function Calling).
3. **Traza de Ejecución**: Todo paso del agente debe ser logueado (Thinking Process).

### 🧠 Arquitecturas Cognitivas Recomendadas
- **ReAct (Reason + Act)**: Bucle de pensar, elegir herramienta, observar resultado original, iterar.
- **Plan-and-Solve**: Para tareas complejas en LMAgent (Level 3+), divide en sub-tareas secuenciales `[ ]` en un archivo Markdown antes de ejecutar.
- **Reflection / Self-Healing**: El agente debe autoevaluar su resultado (ej. con un linter) antes de entregarlo al usuario.

## 🛠️ Tool Definition Standards (MCP)
- **JSON Schema**: Usar esquemas estrictos (`strict: true`).
- **Descripciones**: Deben ser exhaustivas. El LLM "lee" la descripción para saber cuándo usar la tool.
- **Error Handling**: Las tools nunca deben crashear el proceso. Deben retornar errores legibles para que el agente se corrija.

## 🧠 Memory patterns
- **Short-term**: Context window (Chat history). Implementar sliding windows o resúmenes periódicos para no romper el límite de tokens.
- **Long-term**: 
  - *Vector Search (RAG)* para similitud semántica.
  - *Graph RAG* para relaciones complejas entre entidades de un repositorio o base de conocimiento.
  - Generación de *Resúmenes / Artefactos Markdown* locales (usados nativamente por LMAgent en `.agents/memory/`).

## 🧪 Evaluation (Evals)
Todo agente debe tener al menos 1 test de evaluación:
- **Input**: Prompt de prueba.
- **Expected Tool**: La herramienta que DEBE elegir.
- **Expected Args**: Los argumentos aproximados.
