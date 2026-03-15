# MCP Server Guide

## Arquitectura Básica
Un servidor MCP expone:
- **Resources**: Datos leídos (archivos, DBs).
- **Tools**: Funciones ejecutables (API calls).
- **Prompts**: Plantillas predefinidas.

## Ejemplo TypeScript
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({
  name: "example-server",
  version: "3.6.0",
}, {
  capabilities: {
    resources: {},
    tools: {},
  },
});
```
