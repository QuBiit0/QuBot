---
description: Workflow para analizar y arreglar bugs en servicios backend Python/Node
level: 1-2
personas: [backend-engineer, qa-engineer]
version: "3.6.0"
type: workflow
---

# Bugfix Backend Workflow

> **Tiempo estimado**: 30 min - 2 horas | **Level**: 1-2

Este workflow guía el proceso de análisis y corrección de bugs en backends.

## Pre-requisitos

1. Leer [AGENTS.md](../../AGENTS.md)
2. Leer [rules/workflow.md](../rules/01-workflow.md)
3. Leer [personas/backend-engineer.md](../skills/backend-engineer/SKILL.md)

## Información Requerida

Proporciona la siguiente información sobre el bug:

1. **Descripción del bug**: ¿Qué está pasando?
2. **Comportamiento esperado**: ¿Qué debería pasar?
3. **Pasos para reproducir**: ¿Cómo se reproduce?
4. **Ambiente**: ¿Dev, staging, producción?
5. **Logs/Errores**: ¿Hay mensajes de error?
6. **Frecuencia**: ¿Siempre ocurre o es intermitente?
7. **Impacto**: ¿Crítico, alto, medio, bajo?

---

## Paso 1: Reproducir el Bug

### 1.1 Crear Script de Reproducción

```python
# reproduce_bug.py

"""
Script para reproducir el bug descrito en [issue/ticket].

Bug: [Descripción breve]
Comportamiento esperado: [...]
Comportamiento actual: [...]
"""

import asyncio
import httpx

async def reproduce():
    """Intenta reproducir el bug."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Configurar estado inicial si es necesario
        
        # Ejecutar acción que causa el bug
        response = await client.post("/endpoint", json={
            # Datos que causan el bug
        })
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Verificar si el bug ocurrió
        # assert ... 

if __name__ == "__main__":
    asyncio.run(reproduce())
```

### 1.2 Ejecutar y Confirmar

```bash
# Ejecutar script de reproducción
python reproduce_bug.py

# Si el bug no se reproduce, revisar:
# - ¿Datos correctos?
# - ¿Ambiente correcto?
# - ¿Estado previo necesario?
```

---

## Paso 2: Localizar el Problema

### 2.1 Analizar Logs

```bash
# Buscar errores relacionados
grep -r "ERROR" logs/ | grep -i "[keyword del bug]"

# Ver logs recientes
tail -f logs/app.log | grep -i "[keyword]"
```

### 2.2 Trazar el Código

```
1. Identificar endpoint afectado
2. Seguir flujo: Router → Service → Repository
3. Identificar punto exacto de fallo
4. Verificar inputs/outputs en cada paso
```

### 2.3 Buscar Código Relacionado

```bash
# Buscar funciones/clases relacionadas
grep -rn "function_name" app/

# Buscar usos de la entidad afectada
grep -rn "EntityName" app/
```

---

## Paso 3: Analizar Causa Raíz

### Checklist de Causas Comunes

```
[ ] Validación de input faltante
[ ] Manejo de null/None incorrecto
[ ] Error en lógica condicional
[ ] Race condition
[ ] Timeout no manejado
[ ] Excepción no capturada
[ ] Error de tipo/casting
[ ] Query SQL incorrecta
[ ] Estado inconsistente
[ ] Configuración incorrecta
```

### Documentar Análisis

```markdown
## Análisis del Bug

### Síntoma
[Qué se observa]

### Localización
- Archivo: `app/services/xyz.py`
- Función: `process_data()`
- Línea: 42

### Causa Raíz
[Por qué ocurre]

### Impacto
[Qué afecta]

### Solución Propuesta
[Cómo arreglar]
```

---

## Paso 4: Escribir Test que Falla

Antes de arreglar, escribir test que demuestra el bug:

```python
# tests/test_bug_{issue_number}.py

import pytest

class TestBug{IssueNumber}:
    """
    Test para bug #{issue_number}.
    
    Bug: [Descripción]
    Causa: [Causa raíz]
    """
    
    @pytest.mark.asyncio
    async def test_bug_scenario(self, client):
        """El escenario que causa el bug."""
        # Arrange - Configurar estado
        
        # Act - Ejecutar acción que causa bug
        response = await client.post("/endpoint", json={
            # Datos que causan el bug
        })
        
        # Assert - Verificar comportamiento CORRECTO
        # Este test FALLA antes del fix
        assert response.status_code == 200  # o el esperado
        assert response.json()["field"] == "expected_value"
```

---

## Paso 5: Implementar Fix

### 5.1 Aplicar Corrección

```python
# Antes (código con bug)
def process_data(data):
    result = data["field"]  # Falla si field no existe
    return result

# Después (código corregido)
def process_data(data):
    result = data.get("field")
    if result is None:
        raise ValidationError("field is required")
    return result
```

### 5.2 Verificar que Test Pasa

```bash
# Ejecutar test específico
pytest tests/test_bug_{issue_number}.py -v

# Debería pasar ahora
```

### 5.3 Verificar que Otros Tests No Fallan

```bash
# Ejecutar todos los tests
pytest --cov=app --cov-fail-under=80

# Verificar que no hay regresiones
```

> [!IMPORTANT]
> **🔄 REGLA DE SELF-HEALING (Rule 01)**: Si la ejecución de `pytest` o el linting (`ruff`) arrojan errores, el LLM **DEBE iterar localmente** leyendo los tracebacks y corrigiendo el código fuente de forma proactiva. No debe detener la ejecución ni pedir asistencia humana inmediatamente producto del primer traceback. Debe intentar arreglar los errores colaterales hasta lograr el *Green State*.

---

## Paso 6: Verificar Fix

### 6.1 Re-ejecutar Script de Reproducción

```bash
python reproduce_bug.py

# Debería mostrar comportamiento correcto ahora
```

### 6.2 Test Manual (si aplica)

1. Probar escenario del bug
2. Probar casos edge relacionados
3. Verificar que funcionalidad general sigue bien

---

## Paso 7: Documentar y Commit

### 7.1 Commit Message

```
fix(module): descripción corta del fix

Fixes #{issue_number}

- [Cambio 1]
- [Cambio 2]

Root cause: [Explicación breve de la causa]
```

### 7.2 Actualizar Documentación (si aplica)

- [ ] README si hay cambios de comportamiento
- [ ] Docstrings si hay nuevos parámetros
- [ ] Changelog si es fix significativo

---

## Paso 8: Code Review

### Checklist para Reviewer

- [ ] Test reproduce el bug original
- [ ] Fix es minimal y enfocado
- [ ] No hay regresiones
- [ ] Código sigue estándares
- [ ] Documentación actualizada

---

## Templates

### Bug Report Template

```markdown
## Bug Report

### Descripción
[Qué está pasando]

### Pasos para Reproducir
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

### Comportamiento Esperado
[Qué debería pasar]

### Comportamiento Actual
[Qué pasa actualmente]

### Ambiente
- OS: [...]
- Python/Node: [versión]
- Branch: [...]

### Logs/Screenshots
```
[Logs de error]
```

### Impacto
- [ ] Crítico - Sistema caído
- [ ] Alto - Feature principal afectado
- [ ] Medio - Feature secundario afectado
- [ ] Bajo - Edge case, workaround existe
```

### Fix PR Template

```markdown
## Fix: [Título del Bug]

Fixes #{issue_number}

### Causa Raíz
[Explicación de por qué ocurría el bug]

### Solución
[Qué se cambió y por qué]

### Testing
- [x] Test que reproduce el bug
- [x] Test pasa después del fix
- [x] Sin regresiones en otros tests

### Checklist
- [ ] Código sigue estándares
- [ ] Tests completos
- [ ] Documentación actualizada
```

---

## Checklist Final

- [ ] Bug reproducido localmente
- [ ] Causa raíz identificada
- [ ] Test escrito que falla antes del fix
- [ ] Fix implementado
- [ ] Test pasa después del fix
- [ ] Sin regresiones
- [ ] Commit con mensaje descriptivo
- [ ] PR creado para review

---

## 🛠️ Herramientas Sugeridas

| Fase | Herramienta |
|------|-------------|
| Reproducción | `run_command` (scripts), `grep_search` |
| Análisis | `view_file`, `grep_search`, logs |
| Fix | `replace_file_content`, `write_to_file` |
| Validación | `run_command` (pytest) |

## ⚠️ Errores Comunes

| Error | Solución |
|-------|----------|
| Arreglar sin reproducir primero | SIEMPRE reproducir antes de tocar código |
| No escribir test de regresión | El test debe fallar ANTES del fix |
| Fix muy amplio | Cambiar solo lo necesario, mínima intervención |
