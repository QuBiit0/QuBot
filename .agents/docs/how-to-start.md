# 🤖 Tu Primera Interacción con LMAgent

Una vez instalado LMAgent, sigue este guión para tu primera sesión de trabajo.

## 1. El Check-in Inicial
Abre el chat de tu IDE y preséntate al sistema.

> "Hola. Soy nuevo en este proyecto. Lee `AGENTS.md` y explícame qué roles tengo disponibles."

El agente leerá su propia configuración y te listará los skills activos.

## 2. La Primera Tarea (Ejemplo)
Supongamos que quieres crear un endpoint de Login.

### Paso A: Invoca al Experto
> "Actúa como `/dev`. Vamos a crear un endpoint de login en Node.js."

### Paso B: Dale Contexto
> "El login debe usar JWT y validar contra una base de datos PostgreSQL. Usa las reglas de `04-security.md`."

### Paso C: Refinamiento
El agente te mostrará un plan o código.
> "Eso se ve bien, pero agrega validación de email con Zod."

## 3. Comandos Mágicos
Recuerda estos atajos para el chat:

- **`/orch`**: "Estoy perdido, ayúdame a empezar".
- **`/test`**: "Crea tests para este archivo".
- **`/fix`**: "Arregla este error que veo en la terminal".
