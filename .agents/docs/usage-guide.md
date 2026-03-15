# 📖 LMAgent General Usage Guide

## 1. Filosofía
LMAgent convierte tu IDE en una agencia de desarrollo de software completa. No hablas con un "chatbot", hablas con **Ingenieros Especialistas**.

## 2. Flujo de Trabajo (The Loop)
Todo trabajo sigue este ciclo:

1.  **Activación**: Usas un Trigger (`/dev`, `/pm`) o el Agente detecta la tarea.
2.  **Contexto**: El Agente lee `AGENTS.md` y `active_context.md`.
3.  **Planificación**: El Agente propone un plan (si es complejo).
4.  **Ejecución**: El Agente usa herramientas (`read_file`, `run_command`).
5.  **Memoria**: Al terminar, el Agente actualiza `.agents/memory/`.

## 3. Mejores Prácticas
- **Sé explícito**: "Actúa como `/front` y crea el componente X".
- **Usa la Memoria**: Si algo cambia en el negocio, actualiza `05-product-state.md`.
- **Validación**: Siempre pide al agente que verifique su trabajo (`/test`).

## 4. Solución de Problemas
- **El agente alucina**: Dile "Lee AGENTS.md de nuevo".
- **El agente ignora reglas**: Verifica que `.agents/rules` estén instaladas en tu carpeta de IDE (`.cursor/rules`, etc.).
