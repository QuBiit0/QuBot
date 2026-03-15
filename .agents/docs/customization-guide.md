# 🛠️ Customization Guide

LMAgent es 100% personalizable. Aquí te explicamos cómo adaptarlo a tu equipo.

## 1. Personalizando Skills (Roles)
Los Skills viven en `.agents/skills/`. Cada carpeta es un "cerebro" especializado.

### Estructura de un Skill
- `SKILL.md`: (**Obligatorio**) El prompt maestro. Define la personalidad y capacidades.
- `scripts/`: Scripts ejecutables (Python/Node) que el skill puede usar.
- `references/`: Documentación estática que el skill lee para aprender.

### Cómo crear un Skill nuevo
Basta con crear un archivo `SKILL.md`:
```yaml
---
name: Cloud Architect
description: Experto en AWS y Terraform
triggers: [/cloud, /aws]
---

# Cloud Architect Persona
Eres un experto en infraestructura...
```

## 2. Personalizando Reglas (Governance)
Las reglas en `.agents/rules/` son leídas por **todos** los skills.

- **00-master.md**: El índice maestro. Si agregas una regla, enlázala aquí.
- **Tech Stack**: Edita `02-tech-stack.md` para definir qué librerías permites.

## 3. Personalizando Workflows (SOPs)
Los workflows en `.agents/workflows/` son "recetas" paso a paso.
El Orchestrator los usa para guiar procesos complejos.

## 4. Extendiendo el CLI
Si quieres lógica imperativa (comandos), puedes modificar `install.js` o agregar scripts en `.agents/scripts/` y llamarlos con `lmagent run tu-script`.
