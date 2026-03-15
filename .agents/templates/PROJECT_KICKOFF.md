# 🚀 PROJECT KICKOFF
## LMAgent Framework v3.0 (SPEC+LM)

> **🤖 AGENTE DE IA**: Si detectas este archivo, activa el **AUTO-START PROTOCOL** (ver final del documento).
> 
> Si las secciones están vacías `[...]`, activa el **MODO INTERACTIVO** y haz las preguntas al usuario.

---

# INFORMACIÓN DEL PROYECTO

## 1. Visión del Producto 🔭

### Nombre del Proyecto
<!-- Nombre clave o final del proyecto -->
```
[Escribe el nombre aquí]
```
> *Ejemplo: "AgentFlow 2026" o "NutriTrack AI"*

### Elevator Pitch
<!-- En UNA frase: ¿Qué es y para quién? Máximo 280 caracteres -->
```
[Describe tu producto aquí]
```
> *Ejemplo: "Un asistente de IA que organiza automáticamente la agenda de médicos conectándose a WhatsApp y Google Calendar, reduciendo el ausentismo de pacientes en un 40%."*

### Tipo de Proyecto
<!-- Marca UNA opción con [x] -->
- [ ] **MVP (Speed)** - Validar idea rápido, priorizar velocidad sobre perfección
- [ ] **Producto Escalable (Quality)** - Arquitectura limpia, TDD, para producción
- [ ] **Prototipo/Demo** - Visualmente impactante, puede tener mocks
- [ ] **Herramienta Interna** - Utilidad sobre estética

---

## 2. Usuarios y Problema 👥

### Usuario Principal
<!-- ¿Quién usará esto principalmente? -->
```
Rol: [ej: Contador, Médico, Developer]
Edad/Perfil: [ej: 40+ años, poco tecnológico]
Contexto: [ej: Usa principalmente celular, prefiere WhatsApp]
```
> *Ejemplo: "Médico Cardiólogo: 50+ años, poco tecnológico, usa voz para notas."*

### Usuario Secundario (opcional)
```
Rol: [ej: Cliente del usuario principal]
Contexto: [ej: Quiere confirmar turno sin instalar apps]
```
> *Ejemplo: "Paciente: Quiere confirmar turno por WhatsApp sin instalar apps."*

### Problema Principal a Resolver
<!-- ¿Qué dolor específico resuelves? Sé concreto con números si es posible. -->
```
[Describe el problema aquí]
```
> *Ejemplo: "El médico pierde 2 horas diarias confirmando turnos manualmente por teléfono."*

### ¿Por qué ahora?
<!-- ¿Por qué este problema es urgente? -->
```
[Explica la urgencia]
```

---

## 3. Funcionalidades Clave ✨

### 🟢 MUST HAVE (MVP)
<!-- Sin esto, el producto NO funciona. Máximo 5 items. -->
1. [Feature 1]
   > *Ej: "Chatbot en WhatsApp que entienda lenguaje natural."*
2. [Feature 2]
   > *Ej: "Sincronización bi-direccional con Google Calendar."*
3. [Feature 3]
4. [Feature 4]
5. [Feature 5]

### 🟡 SHOULD HAVE (v1.1)
<!-- Importante pero puede esperar a la siguiente versión -->
1. [Feature extra 1]
   > *Ej: "Recordatorios automáticos 24hs antes."*
2. [Feature extra 2]

### 🔴 OUT OF SCOPE (NO hacer ahora)
<!-- Explícitamente excluido para evitar scope creep -->
1. [Lo que NO haremos]
   > *Ej: "Pagos online (se hará en Q3)."*
2. [Otra cosa que NO haremos]

---

## 4. Stack Tecnológico 🛠️

> **Instrucción**: Marca con [x] lo que prefieras. Si no sabes, deja TODO vacío y el Architect decidirá lo mejor para tu caso.

### Frontend
- [ ] **Next.js 15+ / React 19** *(Recomendado para web apps)*
- [ ] **React Native / Expo** *(Apps móviles)*
- [ ] **Vue 3 / Nuxt 4** *(Alternativa a React)*
- [ ] **Sin Frontend** *(Solo backend/API)*
- [ ] **Otro**: _________

### Backend
- [ ] **Python 3.12+ (FastAPI)** *(Recomendado para IA/Agents)*
- [ ] **Node.js 22+ (NestJS)** *(TypeScript estricto)*
- [ ] **Go** *(Alto rendimiento)*
- [ ] **Otro**: _________

### Base de Datos
- [ ] **PostgreSQL 16+** *(Recomendado - relacional + vectores)*
- [ ] **Supabase** *(BaaS rápido con auth incluido)*
- [ ] **MongoDB** *(Documentos)*
- [ ] **Otro**: _________

### Infraestructura
- [ ] **Docker Compose** *(Desarrollo local standard)*
- [ ] **Vercel** *(Fácil deploy para frontend)*
- [ ] **Railway** *(Fácil con base de datos)*
- [ ] **AWS/GCP** *(Enterprise)*

### IA & Agents
- [ ] **OpenAI (GPT-4o)** *(Más popular)*
- [ ] **Anthropic (Claude)** *(Mejor para código)*
- [ ] **Gemini (Google)** *(Multi-modal)*
- [ ] **Local (Ollama)** *(Sin costo de API)*

---

## 5. Diseño y UX 🎨 (opcional)

### Estilo Visual Preferido
- [ ] **Neo-Brutalism** *(Tendencia 2025/26)*
- [ ] **Glassmorphism / Apple Style** *(Elegante)*
- [ ] **Minimal SaaS** *(Inter font, Tailwind)*
- [ ] **Dark Mode First**
- [ ] **Sin preferencia** *(el diseñador decide)*

---

## 6. Integraciones Externas 🔌 (opcional)

<!-- ¿Con qué servicios debe conectarse? -->
- [ ] WhatsApp Business API
- [ ] Stripe / MercadoPago (Pagos)
- [ ] Google Calendar / Outlook
- [ ] Email (SendGrid, Resend)
- [ ] Auth0 / Clerk (Autenticación)
- [ ] Otro: _________

---

## 7. Restricciones 📅 (opcional)

### Deadline
```
[Si hay fecha límite, escríbela. Ej: "Demo para inversores el 15 de marzo"]
```

### Presupuesto de Infraestructura
```
[Límite mensual. Ej: "$50/mes máximo en cloud"]
```

### Otras Restricciones
```
[Cualquier otra limitación técnica o de negocio]
```

---

## 8. Métricas de Éxito 📊 (recomendado)

<!-- ¿Cómo sabrás que el proyecto fue exitoso? -->
| Métrica | Valor Actual | Meta |
|---------|--------------|------|
| [Ej: Tiempo de categorización] | [3 horas] | [10 minutos] |
| [Ej: Usuarios activos] | [0] | [100 en primer mes] |
| [Ej: NPS] | [N/A] | [> 50] |

---

## 9. Contexto Adicional 💬 (opcional)

<!-- Links, documentos, competidores, diseños existentes -->
```
[Cualquier información extra que ayude a entender el proyecto]
```

---

# ═══════════════════════════════════════════════════════════════════════════════
#                           🤖 SECCIÓN PARA EL AGENTE
# ═══════════════════════════════════════════════════════════════════════════════

## AUTO-START PROTOCOL

**Cuando detectes este archivo en la raíz del proyecto:**

### Caso A: Template Completado (secciones tienen contenido)
```
1. Ejecutar: lmagent init (si no está inicializado)
2. Leer PROJECT_KICKOFF.md completo
3. Clasificar como Level 3-4 (proyecto nuevo)
4. Ejecutar workflow /spec automáticamente:
   - Crear specs/[project-name]/spec.yaml
   - Mostrar al usuario → Pedir aprobación
   - Crear specs/[project-name]/plan.yaml
   - Mostrar al usuario → Pedir aprobación
   - Crear specs/[project-name]/tasks.yaml
   - Implementar tasks en orden
5. Documentar todo en el proceso
```

### Caso B: Template Vacío o Incompleto (secciones tienen [...])
```
ACTIVAR MODO INTERACTIVO:

1. Saludar al usuario:
   "Detecté que este es un proyecto nuevo. Voy a hacerte algunas 
   preguntas para entender qué quieres construir."

2. Hacer preguntas en ESTE ORDEN (una a la vez):

   Q1: "¿Cómo se llama tu proyecto? (nombre clave)"
   
   Q2: "En una frase, ¿qué es y para quién?"
   
   Q3: "¿Es un MVP rápido, un producto escalable, un prototipo/demo, 
        o una herramienta interna?"
   
   Q4: "¿Quién es el usuario principal? Describe su perfil brevemente."
   
   Q5: "¿Qué problema específico resuelve? Sé concreto."
   
   Q6: "Dame 3-5 features que DEBEN estar en el MVP (sin esto no funciona)."
   
   Q7: "¿Hay alguna restricción de tecnología, deadline o presupuesto?"

3. Con las respuestas, llenar el template internamente
4. Continuar con Caso A (workflow /spec)
```

## Estructura de Salida Esperada

```
proyecto/
├── PROJECT_KICKOFF.md    ← Este archivo (input del usuario)
├── AGENTS.md             ← Copiado de LMAgent
├── .lmagent              ← Marker del framework
│
├── specs/
│   └── [project-name]/
│       ├── spec.yaml     ← Generado por /pm
│       ├── plan.yaml     ← Generado por /arch
│       └── tasks.yaml    ← Generado por /dev
│
├── src/                  ← Código implementado
├── tests/                ← Tests
├── docs/                 ← Documentación
│   └── adr/              ← Architecture Decision Records
└── README.md             ← Generado automáticamente
```

## Validación de Completitud

Considerar **COMPLETO** si tiene al menos:
- [ ] Nombre del proyecto
- [ ] Descripción/Pitch
- [ ] Tipo de proyecto seleccionado
- [ ] Usuario principal descrito
- [ ] Problema definido
- [ ] Al menos 2 MUST HAVE features

Si faltan ≥3 de estos → Activar **MODO INTERACTIVO**.

---

**FIN DEL TEMPLATE**

*LMAgent v3.6.0 (SPEC+LM) - Build More, Automate Dreams* 🚀
