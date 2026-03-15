# 🏛️ LMAgent Architecture & Modules Reference

Bienvenido al núcleo de **LMAgent v3.6.0**. Si eres un usuario nuevo que acaba de instalar el framework, este documento es tu **Manual Maestro**. Aquí explicaremos, directorio por directorio y función por función, cómo está estructurado el "Cerebro" de tus agentes y por qué funciona de la manera que lo hace.

> 💡 **Concepto Clave:** LMAgent separa el *Razonamiento* (tus reglas y contexto) de la *Ejecución* (el IDE que uses: Cursor, Windsurf, Trae, etc.). Toda la inteligencia vive centralizada en la carpeta oculta `.agents/` en la raíz de tu proyecto.

---

## 📂 Estructura de Directorios (El Cerebro)

Cuando inicializas LMAgent en tu proyecto (`lmagent init`), se crea la carpeta `.agents/` con los siguientes submódulos críticos:

### `1. /config` (Configuración del Framework)
Aquí reside la parametrización de bajo nivel de cómo el framework opera.
- **`commands.yaml`**: Define los "Triggers" (ej. `/dev`, `/pm`) y mapea qué comando activa qué Skill.
- **`levels.yaml`**: Establece los SLAs (Service Level Agreements) y la complejidad esperada de las tareas (Nivel 0: Trivial a Nivel 4: Crítico).
- **`models.yaml` & `settings.yaml`**: Configuraciones generales de los LLMs subyacentes y el comportamiento global del framework.
- **`tools*.yaml`**: Lista y permisos de "Tools" (funciones) que los agentes tienen permitido usar (ej. `run_command`, `replace_file_content`).

### `2. /rules` (Leyes Inquebrantables)
Reglas mandatorias que CUALQUIER agente debe leer y acatar silenciosamente antes de escribir una línea de código.
- **`00-master.md`**: El punto de entrada a todo el reglamento. Establece la tónica del agente.
- **`02-tech-stack.md`**: Define exactamente qué versiones y tecnologías están permitidas (ej. "Node 22+", "Python 3.12+").
- **`04-security.md`**: Reglas paranoicas sobre cómo evitar y reportar el hardcoding de secretos o vulnerabilidades comunes.
- **`10-git-flow.md`**: Define el estándar de Commits (Ej: Conventional Commits) y uso de ramas.

### `3. /skills` (Agentes Especializados o "Personas")
Este es el catálogo de **38 Roles Expertos** de LMAgent. 
- En lugar de usar un LLM genérico, LMAgent carga bajo demanda un `SKILL.md` hiper-optimizado según lo que necesites.
- Si escribes `/cloud`, se carga el **Cloud Architect**, experto en Terraform y AWS.
- Si escribes `/web3`, se carga el **Blockchain Engineer**, programado con paranoia de seguridad para Solidity/Rust.
- Cada skill tiene un `System Prompt` inyectado que le explica al LLM cómo debe pensar, qué patrones de diseño usar y qué restricciones tiene.

### `4. /workflows` (Procedimientos Estándar Operativos - SOPs)
Rutinas paso-a-paso de cómo resolver tareas largas.
- Archivos como `spec-driven.md` o `resolve-github-issue.md` le enseñan al agente un algoritmo a seguir. 
- Por ejemplo, en un bugfix, el workflow le prohíbe tocar código hasta haber (1) replicado el bug, (2) escrito un test que falle, (3) solucionado el bug, y (4) verificado el test en verde.

### `5. /memory` (El Hipocampo del Agente)
**La joya de la corona del framework.** A diferencia de los modelos normales que olvidan el contexto cuando cierras el chat, LMAgent autogestiona su memoria en estos archivos `.md`.
- **`01-global.md`**: ¿De qué trata esta aplicación? (Identidad del proyecto).
- **`02-active-context.md`**: ¿Qué estamos haciendo *hoy*? (Para retomar trabajo luego de un fin de semana).
- **`03-tech-stack.md`**: Auto-documentación de dependencias instaladas.
- **`04-decision-log.md`**: Un historial (ADRs) de decisiones críticas. Si el agente hoy descubrió un molesto bug y lo solucionó, dejará escrito aquí cómo lo hizo para que el agente del mañana no caiga en la misma trampa.
- **`05-product-state.md`**: Funciones completadas vs el Roadmap futuro.

### `6. /docs` (Documentación del Framework)
Donde te encuentras leyendo esto actualmente. Las guías internas que enseñan cómo personalizar, invocar o expandir tu instalación local de LMAgent.

### `7. /scripts` (Herramientas Core)
Mini aplicaciones internas (en JS o Bash) que el marco utiliza para mantenerse ordenado, por ejemplo, scripts de validación (`lmagent validate`) o generadores de nuevos agentes interactivos (`lmagent create-skill`).

### `8. /templates` (Moldes Universales)
Plantillas que los agentes usan para crear documentos (como un Product Requirements Document oficial o un Readme) garantizando un formato estético e idéntico a lo largo del tiempo.

---

## 🔌 ¿Cómo se integra con mi Entorno de Desarrollo (IDE)?

LMAgent es **agnóstico al editor**. Soporta más de 30 IDEs (Cursor, Trae, Roo, Claude Code, Windsurf).
El truco es que durante la instalación (`lmagent init`), el CLI detecta qué IDEs usas y crea un **"Bridge File"** (archivo puente).

Ejemplo:
- Si usas **Cursor**, crea un archivo en tu proyecto `.cursor/rules/00-lmagent.mdc` que le dice a Cursor: *"Tus instrucciones maestras están en la carpeta .agents/"*.
- Si usas **Windsurf**, modifica las rules globales para forzarlo a leer el `AGENTS.md` de la raíz, que a su vez lo mete en el *Loop* de la carpeta `.agents/`.

Con esto se logra "Un cerebro asombrosamente inteligente para dominarlos a todos".

---

## 🛠️ Modificación y "Self-Healing" (Auto-Reparación)

El comportamiento más asombroso de LMAgent es su **bucle de auto-mantenimiento**.
No tienes que abrir la carpeta `/memory` manualmente y redactar los reportes. El propio Skill (ej: el Backend Engineer), usando la "LMAgent Core Rule" de `00-master.md`, está obligado a abrir `02-active-context.md`, tachar las tareas que terminó y actualizar el estado. ¡El proyecto se documenta solo!

Bienvenido a la programación del futuro.
