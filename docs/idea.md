<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# si, preparame la version final listo para copiar y pegarlo. asi empiezo a trabajar en el proyecto

Aquí va la **versión final** del prompt, ya integrada con roles de informática, roles de la vida real y clases personalizables. Está pensada para copiar/pegarla en Claude Code (u otro agente constructor) y que se ponga a desarrollar.

***

Quiero que diseñes y construyas, paso a paso, una aplicación web con backend que actúe como un “Mission Control” de agentes de IA ambientado en una oficina de coworking digital.

La app debe permitir:

- Tener un agente principal orquestador.
- Crear múltiples agentes secundarios (personajes) con roles de informática **y** roles de la vida real (ej. gerente de finanzas, RRHH, etc.).
- Definir clases de agente **predefinidas** y además clases totalmente **personalizables** (nombre libre).
- Visualizar a todos los agentes dentro de un mismo espacio de oficina/cowork (vista isométrica o 2D tipo videojuego) donde se los vea “trabajando”.
- Gestionar tareas en un tablero Kanban (Por hacer / En progreso / En revisión / Listo).
- Asignar tareas a agentes, ver su progreso, logs y herramientas usadas.[^1][^2][^3][^4][^5]

Quiero que construyas esto de forma incremental, generando código real listo para ejecutar (idealmente en un stack moderno tipo: backend en Node/TypeScript o Python; frontend en React/Next.js + Tailwind, pero puedes proponer el stack más razonable).

***

## 1. Objetivos generales del sistema

1.1. Orquestación de agentes

- Un agente principal que recibe las instrucciones del usuario (chat).
- El agente principal decide qué subtareas crear y a qué agentes asignarlas (según sus clases, dominios, skills y carga de trabajo).[^5][^6]
- Los agentes secundarios ejecutan tareas usando herramientas (navegación web, scripts, llamadas API, etc.).

1.2. Entorno “coworking” visual

- Todos los agentes aparecen representados como personajes de videojuego dentro de una oficina compartida (cowork).
- Cada agente tiene:
    - **Clase profesional** (técnica o de negocio).
    - **Dominio** (ej. Tecnología, Finanzas, Marketing, RRHH, Legal, Personalizado).
    - **Género** (masculino, femenino, no binario).
    - **Nombre visible**.
    - **Avatar/skin** acorde a su rol (por ejemplo, hacker con hoodie, gerente de finanzas con traje, etc.).[^4][^7]
- Se debe poder ver quién está trabajando, quién está idle y quién está en error.

1.3. Mission Control

- Tablero Kanban para tareas (similar a OpenClaw Mission Control / Trello).[^2][^8][^1]
- Panel de estado de agentes (online, tarea actual, heartbeat, dominio).
- Activity feed en tiempo real mostrando qué está haciendo cada agente.

1.4. Configuración visual y flexible

- Editor visual para crear/editar agentes (tipo “crear personaje”).
- Configuración de modelos LLM por agente (proveedor, modelo, temperatura, etc.).[^9][^5]
- Configuración de tools/skills y servicios externos por agente.
- Posibilidad de crear **nuevas clases de agente personalizadas** por UI (ej. “Gerente de Finanzas LATAM”, “Coach de Productividad”).[^7][^10]

***

## 2. Stack recomendado

Si no tienes una fuerte preferencia, usa:

- **Backend**
    - Lenguaje: TypeScript.
    - Framework: Node + NestJS o Express organizado en módulos.
    - Base de datos: PostgreSQL usando Prisma (o similar ORM).
    - Comunicación en tiempo real: WebSockets (Socket.IO o equivalente).
    - Opcional: Redis para colas/eventos si es necesario.
- **Frontend**
    - React + Next.js.
    - TailwindCSS para estilos.
    - Para la vista del coworking, puedes usar:
        - Componentes React + CSS/SVG, o
        - Una librería ligera tipo Konva.js o PixiJS si lo ves conveniente.
- **LLM**
    - Capa de abstracción de modelos con proveedores: OpenAI, Anthropic, Google, Groq, modelos locales, etc.
    - Configuración persistida en BD por agente y/o por provider.[^5][^9]

Eres libre de ajustar el stack si ves un motivo sólido, pero explica el cambio.

***

## 3. Modelo de dominio (backend) – Detallado

### 3.1. Agentes

Crea un modelo `Agent` con al menos:

- `id` (UUID).
- `name` (string).
- `gender` (enum: MALE, FEMALE, NON_BINARY).
- `classId` (FK a una tabla de clases de agente).
- `domain` (enum: TECH, BUSINESS, FINANCE, HR, MARKETING, LEGAL, PERSONAL, OTHER).
- `roleDescription` (texto breve del rol).
- `personality` (json/text: gustos, fortalezas, debilidades, estilo de trabajo).
- `llmConfigId` (FK a tabla LLMConfig).
- `toolConfigId` (FK a tabla que asocia herramientas).
- `avatarConfig` (json para colores, sprite, iconos, etc.).
- `status` (enum: IDLE, WORKING, ERROR, OFFLINE).
- `currentTaskId` (FK opcional).
- timestamps (`createdAt`, `updatedAt`).


### 3.2. Clases de agente (predefinidas + personalizadas)

Tabla `AgentClass`:

- `id`.
- `name` (string, ej. “Hacker ético”, “Gerente de Finanzas”).
- `description` (string, descripción funcional).
- `domain` (enum como arriba).
- `isCustom` (boolean, true si la definió el usuario).
- `defaultAvatarConfig` (json para apariencia base).

Incluye **clases predefinidas** como base, al menos:

- Dominio TECH:
    - Hacker ético.
    - Arquitecto de sistemas.
    - Desarrollador backend.
    - Desarrollador frontend.
    - Ingeniero DevOps / SRE.
    - Científico de datos.
    - Ingeniero de ML.
    - Analista de datos.
    - Ingeniero de pruebas / QA.
    - Researcher de IA / Prompt Engineer.
- Dominio BUSINESS / FINANCE / OTROS:
    - Gerente de Finanzas.
    - Analista financiero.
    - Product Manager técnico.
    - Gerente de Operaciones.
    - HR Manager.
    - Especialista en Marketing Digital.
    - Legal Counsel.

Además, el sistema debe permitir **crear nuevas clases** por UI:

- Nombre libre.
- Descripción.
- Dominio.
- Config visual por defecto.

Estas se almacenan con `isCustom = true`.[^10][^7]

### 3.3. Configuración de modelos LLM

Tabla `LlmConfig`:

- `id`.
- `provider` (enum: OPENAI, ANTHROPIC, GOOGLE, GROQ, LOCAL, OTHER).
- `modelName` (string, ej. `gpt-4.1`, `claude-3.7-sonnet`).
- `temperature` (float).
- `topP`, `maxTokens`, etc.
- `apiKeyRef` (referencia a un secreto o env var).
- `extraConfig` (json).

Opcionalmente, tabla `ModelProvider` para centralizar endpoint/baseUrl, límites, etc.[^9]

### 3.4. Herramientas / Skills / Servicios

Tabla `Tool`:

- `id`.
- `name`.
- `type` (enum: SYSTEM_SHELL, WEB_BROWSER, FILESYSTEM, HTTP_API, SCHEDULER, CUSTOM).
- `description`.
- `inputSchema` (json).
- `outputSchema` (json).
- `config` (json: base URL, headers, auth, etc.).

Tabla `AgentTool` (many‑to‑many):

- `agentId`.
- `toolId`.
- `permissions` (enum: READ_ONLY, READ_WRITE, DANGEROUS).

La lógica debe permitir:

- Registrar nuevas tools desde UI.
- Asignarlas a agentes específicos.


### 3.5. Tareas (Jobs / Missions)

Tabla `Task`:

- `id`.
- `title`.
- `description`.
- `status` (enum: BACKLOG, IN_PROGRESS, IN_REVIEW, DONE, FAILED).
- `priority` (enum: LOW, MEDIUM, HIGH, CRITICAL).
- `domainHint` (opcional: TECH, FINANCE, HR, etc., para ayudar al orquestador a elegir agente).[^11][^7]
- `createdBy` (usuario humano / sistema).
- `assignedAgentId` (FK opcional).
- `createdAt`, `updatedAt`, `completedAt` (nullable).

Tabla `TaskEvent`:

- `id`.
- `taskId`.
- `type` (CREATED, ASSIGNED, STARTED, TOOL_CALL, PROGRESS_UPDATE, COMPLETED, FAILED, COMMENT).
- `payload` (json con detalles).
- timestamps.


### 3.6. Memoria

Diseña tablas:

- `GlobalMemory` (documentos, notas globales).
- `AgentMemory` (memoria específica por agente).
- `TaskMemory` (resúmenes/logs por tarea).

Deja preparada la estructura para a futuro integrar un vector DB (no es obligatorio implementarlo ahora).

***

## 4. Lógica de orquestación

### 4.1. Agente principal (orquestador)

- Endpoint `/chat` que recibe mensajes del usuario.
- El backend llama al LLM del agente principal con:
    - Mensaje del usuario.
    - Contexto resumido de tareas recientes.
    - Lista de agentes disponibles (clase, dominio, estado, cola de trabajo).[^6][^5]

El LLM debe producir:

- Una **respuesta textual** inmediata para el usuario (cuando corresponda).
- Una lista de **acciones estructuradas**, por ejemplo:

```json
{
  "actions": [
    {
      "type": "CREATE_TASK",
      "payload": {
        "title": "...",
        "description": "...",
        "domainHint": "FINANCE",
        "preferredClass": "Gerente de Finanzas",
        "priority": "HIGH"
      }
    },
    {
      "type": "ASSIGN_TASK",
      "payload": {
        "taskId": "existing-task-id",
        "agentId": "some-agent-id"
      }
    }
  ]
}
```

Define claramente este contrato JSON y valida del lado servidor.

### 4.2. Asignación y ejecución de tareas

- Un “task scheduler” en el backend revisa tareas en `BACKLOG` o con `ASSIGN_TASK` pendiente.
- Para asignar tarea a un agente:
    - Filtra por dominio y clase preferida.
    - Considera carga de trabajo actual (cuántas tareas en progreso tiene).
    - Elige agente y actualiza `assignedAgentId` + `status = IN_PROGRESS`.[^7][^5]
- Loop de ejecución de tareas:
    - Construye un prompt para el LLM del agente con:
        - Descripción de la tarea.
        - Memoria relevante.
        - Lista de tools disponibles y la forma de llamarlas (function‑calling / tool‑calling).
    - El LLM “pide” llamadas a tools (en formato JSON).
    - El backend ejecuta las tools, registra `TaskEvent` y devuelve resultados en el siguiente mensaje del loop.
    - El loop puede repetirse hasta que el LLM marque la tarea como completada o fallida.

No hace falta un planner súper avanzado desde el inicio, pero deja el loop modular.

***

## 5. Interfaz visual – Coworking + Mission Control

Construye una SPA (Next.js) con las siguientes vistas:

### 5.1. Vista “Coworking”

- Pantalla que representa una oficina/cowork:
    - Escritorios o pods donde se ubican los agentes.
    - Cada `Agent` se muestra como personaje:
        - Sprite/logo diferente según `AgentClass`.
        - Diferencias visuales según género (cuando tenga sentido) o representación neutra.
        - Elementos visuales según dominio:
            - Tech: iconos de código/terminal.
            - Finanzas: gráficos, dólar/euro.
            - Marketing: megáfono, gráfico de barras, etc.[^4][^7]
- Estados:
    - `WORKING`: animación de teclear, luces en el monitor, etc.
    - `IDLE`: postura más neutra.
    - `ERROR`: icono de alerta sobre el personaje.
    - `OFFLINE`: personaje “apagado” o sin luz en el escritorio.
- Tooltip o panel al hacer hover/click:
    - Nombre, clase, dominio.
    - Estado actual.
    - Tarea actual (si hay).


### 5.2. Mission Control / Kanban

- Tablero con columnas:
    - Por hacer (BACKLOG).
    - En progreso.
    - En revisión.
    - Listo.
- Cada tarjeta de tarea muestra:
    - Título.
    - Agente asignado (mini avatar).
    - Prioridad.
    - Dominio.
- Drag \& drop manual para cambiar:
    - Columna (estado).
    - Agente asignado (al arrastrar sobre la “fila” o la columna de un agente).
- Cada cambio hace llamadas al backend para actualizar `Task`.[^3][^1][^2]


### 5.3. Panel de agentes

- Barra lateral o pestaña “Agentes” con list view:
    - Avatar pequeño.
    - Nombre.
    - Clase.
    - Dominio.
    - Estado.
    - Tarea actual.
- Al hacer click:
    - Mostrar ficha completa:
        - Datos básicos.
        - Personality.
        - Modelo LLM.
        - Lista de tools asignadas.
        - Historial de tareas recientes.
    - Botón “Editar agente”.


### 5.4. Activity feed

- Panel tipo log en vivo:
    - “Hacker Ético 01 empezó tarea X”.
    - “Gerente de Finanzas ejecutó tool: HTTP_API (GET /balances)”.
    - “HR Manager falló al llamar API de empleados (401)”.
- Implementar con WebSocket o long‑polling para actualizaciones en tiempo real.[^1][^2][^3]

***

## 6. Editor visual de agentes (crear personaje)

Implementa un wizard de varios pasos:

1. **Dominio**
    - Selección de dominio: Tecnología, Finanzas, Negocios, RRHH, Marketing, Legal, Personal, Otro.
2. **Clase de agente**
    - Muestra lista de `AgentClass` predefinidas filtradas por dominio.
    - Opción clara: “Crear nueva clase personalizada”.
    - Si el usuario elige crear clase:
        - Formulario:
            - Nombre de la clase (texto libre, ej. “Gerente de Finanzas LATAM”).
            - Descripción.
            - Dominio.
            - Config visual base (iconos, color, etc.).
        - Guarda la nueva clase (`isCustom = true`) y la usa para el agente.
3. **Género y nombre**
    - Género: Masculino, Femenino, No binario.
    - Nombre del agente (texto libre).
4. **Personalidad y estilo de trabajo**
    - Campos o sliders para:
        - Orientado a detalle / visión global.
        - Conservador / arriesgado con tools.
        - Formal / informal en lenguaje.
    - Estos valores se guardan en `personality` y luego se usan en el prompt.
5. **Configuración de LLM**
    - Dropdown de proveedor y modelo (usando `LlmConfig` existentes).
    - Sliders para temperatura, maxTokens, etc.[^5][^9]
6. **Herramientas**
    - Checklist de tools disponibles.
    - Opciones de permisos (read, read‑write, dangerous).

Al finalizar, se crea el `Agent` en la BD y aparece en la oficina.

***

## 7. Editor de tools y servicios

- Pantalla “Tools”:
    - Listado de tools con:
        - Nombre.
        - Tipo.
        - Dominio recomendado (si aplica).
        - Botones de editar/eliminar.
- Formulario para crear/editar tool:
    - Nombre.
    - Tipo (SYSTEM_SHELL, HTTP_API, etc.).
    - Descripción.
    - Configuración:
        - Para HTTP_API: base URL, método, headers, auth, etc.
        - Para SYSTEM_SHELL: comandos permitidos, directorio base, sandbox.
    - Esquema de entrada/salida (JSON Schema simple).

Esto no necesita ser 100% perfecto en la primera versión, pero sí debe permitir:

- Añadir nuevas tools desde UI.
- Asignarlas a agentes desde el editor de agentes.

***

## 8. APIs y estructura de código

Pido que:

- Definas rutas REST claras para:
    - CRUD de `Agent`.
    - CRUD de `AgentClass`.
    - CRUD de `Task`.
    - CRUD de `Tool`.
    - CRUD de `LlmConfig`.
    - Endpoints de chat y orquestación (`/chat`, `/tasks/{id}/events`, etc.).
- Organices el backend en módulos:
    - `agents`
    - `agent-classes`
    - `tasks`
    - `tools`
    - `llm`
    - `memory`
    - `orchestrator`
    - `realtime`
- Genere tests básicos al menos para:
    - Creación y edición de agente.
    - Creación y cambio de estado de tarea.
    - Creación de una clase personalizada.

***

## 9. Fases de implementación

Implementa el sistema en fases, y al final de cada fase:

- Muestra el árbol de archivos.
- Explica cómo correr el proyecto (comandos).
- Indica qué está listo y qué falta.

Fase 1 – Backend mínimo

- Modelos de BD + migraciones.
- CRUD de agentes, clases, tareas, tools, llm configs.
- Endpoint `/chat` que por ahora solo crea tareas dummy.

Fase 2 – Frontend Mission Control básico

- Tablero Kanban conectado al backend.
- Lista de agentes (sin coworking gráfico aún).

Fase 3 – Vista coworking

- Render simple de oficina.
- Personajes básicos por agente (sprites simples).

Fase 4 – Editor de agentes y tools

- Wizard de creación de agente (con dominios, clases, custom class, género, etc.).
- Editor de tools.

Fase 5 – Orquestación real con LLM y tools

- Loop principal agente orquestador + agentes de trabajo.
- Soporte inicial para algunas tools reales (ej. HTTP_API genérica, un shell muy limitado).

Fase 6 – Pulido y mejoras

- Animaciones, efectos visuales.
- Filtros por dominio, agrupación de agentes, mejoras en logs.

***

## 10. Estilo y requisitos extra

- Usa nombres de entidades y enums en inglés, pero la UI principal puede estar en español.
- Mantén el código modular y legible, con comentarios donde sea clave.
- Prepara el proyecto para que pueda crecer hacia integraciones con frameworks tipo OpenClaw/PicoClaw y otros mission controls multi‑agente (roles, permisos, equipos).[^8][^2][^1][^5]

Empieza ahora generando:

1. La estructura de carpetas del repo (backend + frontend).
2. El esquema inicial de base de datos (Prisma o equivalente).
3. Archivos de configuración y boilerplate para levantar el entorno de desarrollo (incluyendo `docker-compose` si lo consideras útil).

***

¿Listo?

<div align="center">⁂</div>

[^1]: https://www.dan-malone.com/blog/mission-control-ai-agent-squads

[^2]: https://clawcontrol.dev

[^3]: https://www.reddit.com/r/buildinpublic/comments/1r8f02i/day_1_of_launching_my_ai_agent_dashboard_16/

[^4]: https://www.flexandthecity.news/articles/ai-agents-in-coworking-what-they-are-how-they-work-and-why-they-matter-1/

[^5]: https://goldie.agency/openclaw-mission-control-agent-teams/

[^6]: https://www.pedowitzgroup.com/assign-roles-permissions-ai-agents

[^7]: https://www.teamdecoder.com/de-de/blog/practical-examples-of-ai-agent-roles-in-teams

[^8]: https://github.com/abhi1693/openclaw-mission-control

[^9]: https://docs.picoclaw.io/docs/configuration/model-list/

[^10]: https://contextual.ai/blog/introducing-custom-roles-for-users-and-groups

[^11]: https://gozen.io/blog/examples-of-ai-agents-in-workplace/

