---
description: Workflow para crear o mejorar un agente de IA
level: 2-3
personas: [ai-agent-engineer, backend-engineer]
version: "3.6.0"
type: workflow
---

# New AI Agent Workflow

> **Tiempo estimado**: 4-8 horas | **Level**: 2-3

Este workflow guía la creación o mejora de un agente de IA.

## Pre-requisitos

1. Leer [AGENTS.md](../../AGENTS.md)
2. Leer [rules/agents-ia.md](../rules/08-agents-ai.md)
3. Leer [personas/ai-agent-engineer.md](../skills/ai-agent-engineer/SKILL.md)

## Información Requerida

Antes de comenzar, necesito entender:

1. **Propósito del agente**: ¿Qué tarea debe realizar?
2. **Usuario objetivo**: ¿Quién lo usará? (humano, n8n, otro sistema)
3. **Herramientas necesarias**: ¿Qué acciones debe poder ejecutar?
4. **Conocimiento requerido**: ¿Qué contexto/datos necesita?
5. **Límites**: ¿Qué NO debe poder hacer?
6. **Modelo preferido**: ¿GPT-4, Claude, Gemini, etc.?
7. **Presupuesto por ejecución**: ¿Límite de costo?

---

## Paso 1: Diseñar el Agente

### 1.1 Definir Arquitectura

```
¿El agente necesita...?

┌──────────────────┐
│ Usar herramientas│──▶ Tool-based Agent (ReAct)
└──────────────────┘

┌──────────────────┐
│ Múltiples pasos  │──▶ Multi-step Agent
│ de razonamiento  │
└──────────────────┘

┌──────────────────┐
│ Coordinar otros  │──▶ Orchestrator Agent
│ agentes          │
└──────────────────┘

┌──────────────────┐
│ Solo responder   │──▶ Simple LLM Chain
│ preguntas        │
└──────────────────┘
```

### 1.2 Definir Herramientas

| Tool | Propósito | Parámetros |
|------|-----------|------------|
| [tool_name] | [descripción] | [param1, param2, ...] |
| [tool_name] | [descripción] | [param1, param2, ...] |

### 1.3 Definir Prompt del Sistema

```markdown
## Role
[Descripción del rol del agente]

## Available Tools
[Lista de herramientas con descripciones]

## Guidelines
[Instrucciones de cómo debe comportarse]

## Output Format
[Formato esperado de respuestas]

## Constraints
[Límites y restricciones]
```

---

## Paso 2: Plan de Implementación

### Archivos a Crear

```markdown
## Configuración
- [ ] `agents/config/agents.yaml` - Registrar agente

## Prompts
- [ ] `agents/python/prompts/personas/{agent_name}.md` - System prompt

## Herramientas (si son nuevas)
- [ ] `agents/python/tools/{tool_name}_tool.py` - Implementación
- [ ] `agents/config/tools.yaml` - Registrar tool

## Tests
- [ ] `agents/python/tests/test_{agent_name}.py` - Tests del agente

## API (si se expone via HTTP)
- [ ] `app/routers/agents/{agent_name}.py` - Endpoint
```

---

## Paso 3: Implementar Herramientas

### 3.1 Crear Tool (si es nueva)

```python
# agents/python/tools/{tool_name}_tool.py

from lmagent.tools.base import BaseTool, ToolResult
from pydantic import Field
import structlog

logger = structlog.get_logger()

class {ToolName}Tool(BaseTool):
    """
    {Descripción de la herramienta}.
    
    Usa esta herramienta cuando necesites:
    - [caso de uso 1]
    - [caso de uso 2]
    
    NO uses para:
    - [caso donde NO aplica]
    """
    
    name: str = "{tool_name}"
    description: str = "{Descripción corta para el LLM}"
    
    async def execute(
        self,
        param1: str = Field(..., description="Descripción del parámetro"),
        param2: int = Field(10, description="Parámetro opcional con default")
    ) -> ToolResult:
        """Ejecuta la herramienta."""
        logger.info(
            "{tool_name}_execute",
            param1=param1,
            param2=param2
        )
        
        try:
            # Implementar lógica
            result = await self._do_work(param1, param2)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"param1": param1}
            )
            
        except Exception as e:
            logger.error("{tool_name}_error", error=str(e))
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"suggestion": "Sugerencia para el agente"}
            )
```

### 3.2 Registrar en tools.yaml

```yaml
# agents/config/tools.yaml

tools:
  {tool_name}:
    name: "{Tool Name}"
    module: "agents.python.tools.{tool_name}_tool"
    class: "{ToolName}Tool"
    description: "{Descripción}"
    category: "{category}"
    parameters:
      - name: param1
        type: string
        required: true
        description: "Descripción"
      - name: param2
        type: integer
        default: 10
        description: "Descripción"
```

---

## Paso 4: Crear el Prompt
> 💡 **Tip**: Pídele al `/prompt` engineer que redacte esto por ti.

### 4.1 Escribir System Prompt
El path estándar es `agents/python/prompts/personas/{agent_name}.md`.

```markdown
# agents/python/prompts/personas/{agent_name}.md

You are {Agent Name}, an AI assistant specialized in {domain}.

## Your Role
{Descripción detallada del rol}

## Available Tools

You have access to the following tools:

### {tool_1_name}
{Descripción de cuándo y cómo usar}

### {tool_2_name}
{Descripción de cuándo y cómo usar}

## How to Use Tools

When you need to take an action:
1. Think about which tool is most appropriate
2. Call the tool with the required parameters
3. Wait for the result
4. Use the result to inform your next step or response

## Response Guidelines

- Be concise and direct
- When using data from tools, cite the source
- If a tool fails, explain what happened and try an alternative
- If you cannot complete a task, explain why

## Constraints

- Maximum cost per session: ${max_cost}
- Maximum iterations: {max_iterations}
- Do not {restriction_1}
- Do not {restriction_2}

## Examples

### Example 1: {scenario}

User: "{user_input}"

Thinking: {thought_process}
Action: {tool_name}({params})
Observation: {result}
Response: "{final_response}"
```

---

## Paso 5: Configurar el Agente

### 5.1 Registrar en agents.yaml

```yaml
# agents/config/agents.yaml

agents:
  {agent_name}:
    name: "{Agent Display Name}"
    description: "{Descripción corta}"
    
    # LLM Configuration
    model: "gpt-4o"  # o claude-sonnet-4, gemini-2.5-pro
    temperature: 0.7
    max_tokens: 4096
    
    # Agent Configuration
    max_iterations: 10
    max_cost: 2.00
    
    # System Prompt
    system_prompt: "prompts/personas/{agent_name}.md"
    
    # Tools
    tools:
      - http_request
      - database_query
      - {custom_tool}
    
    # Guardrails
    guardrails:
      require_confirmation: ["database_write", "send_email"]
      blocked_actions: ["delete_production"]
```

---

## Paso 6: Exponer via API (Opcional)

```python
# app/routers/agents/{agent_name}.py

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/agents/{agent-name}", tags=["agents"])

class AgentRequest(BaseModel):
    input: str
    context: dict = {}
    max_cost: float = 2.00

class AgentResponse(BaseModel):
    success: bool
    output: str
    cost: float
    iterations: int
    trajectory_id: str | None = None

@router.post("/run")
async def run_agent(request: AgentRequest) -> AgentResponse:
    """
    Ejecuta el agente {agent_name}.
    
    ## Uso en n8n
    
    1. HTTP Request node
    2. POST {{$env.BACKEND_URL}}/agents/{agent-name}/run
    3. Body: {"input": "tu pregunta o tarea"}
    """
    agent = await load_agent("{agent_name}")
    agent.cost_tracker.max_cost = request.max_cost
    
    result = await agent.run(
        user_input=request.input,
        context=request.context
    )
    
    return AgentResponse(
        success=True,
        output=result,
        cost=agent.cost_tracker.total,
        iterations=agent.iteration_count,
        trajectory_id=agent.trajectory_id
    )
```

---

## Paso 7: Testing

### 7.1 Tests del Agente

```python
# agents/python/tests/test_{agent_name}.py

import pytest
from unittest.mock import AsyncMock, patch

class TestAgent{AgentName}:
    """Tests para {agent_name}."""
    
    @pytest.mark.asyncio
    async def test_basic_query(self, agent):
        """Debe responder a query básica."""
        result = await agent.run("Test query")
        assert result is not None
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_uses_correct_tool(self, agent, mock_llm):
        """Debe usar la herramienta correcta."""
        mock_llm.return_value = MockResponse(
            tool_calls=[{"name": "{tool_name}", "args": {...}}]
        )
        
        with patch.object(agent.tools['{tool_name}'], 'execute') as mock_tool:
            mock_tool.return_value = ToolResult(success=True, data={})
            await agent.run("Query that requires {tool_name}")
            mock_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handles_tool_error(self, agent):
        """Debe manejar errores de tools."""
        with patch.object(agent.tools['{tool_name}'], 'execute') as mock_tool:
            mock_tool.return_value = ToolResult(
                success=False,
                error="Simulated error"
            )
            result = await agent.run("Query")
            # Debería manejar el error gracefully
            assert "error" in result.lower() or agent.iteration_count > 1
    
    @pytest.mark.asyncio
    async def test_respects_cost_limit(self, agent):
        """Debe respetar límite de costo."""
        agent.cost_tracker.max_cost = 0.001  # Muy bajo
        
        with pytest.raises(CostLimitExceeded):
            await agent.run("Expensive query")
```

### 7.2 Test Manual

1. Ejecutar agente con queries de ejemplo
2. Verificar que usa tools correctamente
3. Verificar manejo de errores
4. Verificar límites de costo

---

## Paso 8: Documentación

### Documentar en README del agente

```markdown
# {Agent Name}

## Descripción
{Qué hace este agente}

## Uso

### Via Python
```python
from agents.python.runner import load_agent

agent = await load_agent("{agent_name}")
result = await agent.run("Tu pregunta o tarea")
```

### Via API
```bash
curl -X POST {backend_url}/agents/{agent-name}/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Tu pregunta o tarea"}'
```

### Via n8n
[Instrucciones de configuración]

## Herramientas Disponibles
| Tool | Descripción |
|------|-------------|
| {tool_1} | {descripción} |
| {tool_2} | {descripción} |

## Ejemplos
[Ejemplos de uso con inputs y outputs]

## Límites
- Costo máximo: ${max_cost}
- Iteraciones máximas: {max_iterations}
```

---

## Checklist Final

### Implementación
- [ ] Prompt del sistema escrito y probado
- [ ] Herramientas implementadas (si nuevas)
- [ ] Agente registrado en agents.yaml
- [ ] API endpoint creado (si aplica)

### Testing
- [ ] Tests unitarios pasando
- [ ] Test manual con casos de uso reales
- [ ] Verificación de límites de costo

### Documentación
- [ ] README del agente
- [ ] Ejemplos de uso
- [ ] Documentación para n8n (si aplica)

### Seguridad
- [ ] Guardrails configurados
- [ ] Permisos de tools revisados
- [ ] Logging de auditoría habilitado

---

## 🛠️ Herramientas Sugeridas

| Fase | Herramienta |
|------|-------------|
| Diseño | `write_to_file` (prompts, configs) |
| Implementación | `run_command` (tests), `view_file` |
| Testing | `run_command` (evals), `browser_subagent` |
| Docs | `mcp_context7_query-docs` (LangChain, etc.) |

## ⚠️ Errores Comunes

| Error | Solución |
|-------|----------|
| Tools sin schema estricto | SIEMPRE definir con Pydantic/Field |
| Sin limite de costo | Configurar `max_cost` desde el inicio |
| Prompt vago | Ser específico en rol, tools y constraints |
| Sin evals | Implementar tests de Faithfulness y Tool Accuracy |
