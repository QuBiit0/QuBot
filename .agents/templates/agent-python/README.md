# LMAgent Python Agent Template

Este template proporciona la estructura base para crear agentes de IA con LMAgent.

## Estructura

```
agent_name/
├── __init__.py
├── config.yaml           # Configuración del agente
├── agent.py              # Clase principal del agente
├── prompts/
│   └── system.md         # System prompt del agente
├── tools/
│   ├── __init__.py
│   └── custom_tool.py    # Herramientas específicas
└── tests/
    └── test_agent.py     # Tests del agente
```

## Uso

## Uso

1. Copiar este directorio:
   ```bash
   cp -r templates/agent-python agents/my-new-agent
   cd agents/my-new-agent
   ```

2. Crear entorno virtual e instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # o venv\Scripts\activate en Windows
   pip install -r requirements.txt
   ```

3. Configurar:
   - Renombrar `config.yaml` y ajustar parámetros
   - Personalizar `prompts/system.md`
   - Crear `.env` con tus API Keys (ver `config.yaml` para referencias)

4. Ejecutar:
   ```bash
   python agent.py
   ```

## Archivos

### config.yaml

Define la configuración del agente:
- Modelo LLM a usar
- Herramientas disponibles
- Límites de costo/iteraciones
- Guardrails

### agent.py

Clase principal que implementa:
- Inicialización con configuración
- Método `run()` para ejecutar el agente
- Integración con tools y prompts

### prompts/system.md

System prompt que define:
- Rol y responsabilidades
- Herramientas disponibles
- Formato de respuestas
- Restricciones
