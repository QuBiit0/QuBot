# Prompt Patterns Library — Prompt Engineer

> Biblioteca de patrones de prompts reutilizables con ejemplos.

## Meta-Prompts (Generating Prompts)

### Pattern: Prompt Generator

```
Eres un experto en ingeniería de prompts. Tu tarea es crear un prompt
optimizado para {OBJETIVO}.

Requisitos del prompt resultante:
- Debe ser claro y sin ambigüedad
- Incluir role, contexto, tarea y formato de output
- Usar ejemplos (few-shot) si mejora la precisión
- Definir restricciones explícitas

Output: Solo el prompt optimizado, listo para usar.
```

## Structural Patterns

### 1. Persona Pattern

```
Eres un {ROL} senior con {N} años de experiencia en {DOMINIO}.
Tu especialidad es {ESPECIALIDAD}.
Siempre {REGLA_1}.
Nunca {RESTRICCIÓN_1}.
```

### 2. Chain of Thought (CoT)

```
Resuelve este problema paso a paso:

Problema: {PROBLEMA}

Piensa en voz alta antes de dar la respuesta final.
Muestra tu razonamiento completo.
```

### 3. Few-Shot with Examples

```
Clasifica el sentimiento del texto como positivo, negativo o neutral.

Texto: "Me encanta este producto, funciona perfecto"
Sentimiento: positivo

Texto: "Pésima calidad, se rompió al segundo uso"
Sentimiento: negativo

Texto: "El paquete llegó a tiempo"
Sentimiento: neutral

Texto: "{INPUT_DEL_USUARIO}"
Sentimiento:
```

### 4. Template Fill Pattern

```
Genera un {TIPO_DE_CONTENIDO} con las siguientes características:
- Tono: {TONO}
- Audiencia: {AUDIENCIA}
- Largo: {LARGO}
- Formato: {FORMATO}
- Debe incluir: {REQUISITOS}
- NO debe incluir: {RESTRICCIONES}
```

### 5. Output Format Pattern

```
Responde ÚNICAMENTE en el siguiente formato JSON:

```json
{
  "analysis": "string - tu análisis detallado",
  "recommendation": "string - tu recomendación",
  "confidence": "number - 0 a 1",
  "reasoning": ["string - paso 1", "string - paso 2"]
}
```

No incluyas texto fuera del JSON.
```

## Advanced Patterns

### Tree of Thought (ToT)

```
Para resolver este problema, genera 3 enfoques diferentes.
Para cada enfoque, evalúa pros y contras.
Luego selecciona el mejor enfoque y desarróllalo.

Problema: {PROBLEMA}

Enfoque 1:
- Idea: ...
- Pros: ...
- Cons: ...

Enfoque 2:
- Idea: ...
- Pros: ...
- Cons: ...

Enfoque 3:
- Idea: ...
- Pros: ...
- Cons: ...

Mejor enfoque: ...
Desarrollo: ...
```

### Self-Consistency

```
Resuelve este problema 3 veces de forma independiente.
Luego compara las 3 respuestas y da la respuesta final
basándote en la mayoría (2 de 3 coinciden).
```

### Reflexion Pattern

```
1. Genera una primera respuesta
2. Critica tu propia respuesta: ¿qué errores tiene?
3. Mejora la respuesta basándote en tu autocrítica
4. Presenta la versión mejorada como respuesta final
```

## System Prompt Best Practices

| ✅ Hacer | ❌ No Hacer |
|---------|------------|
| Ser específico sobre el rol | "Sé útil" (vago) |
| Usar ejemplos concretos | Asumir que entiende |
| Definir formato de output | Dejar output libre |
| Poner restricciones explícitas | Esperar que infiera límites |
| Separar instrucciones con sections | Párrafo largo sin estructura |
| Usar XML tags para separar contexto | Mezclar datos y instrucciones |

## Evaluation Metrics

| Métrica | Método | Target |
|---------|--------|--------|
| **Accuracy** | Eval automático vs ground truth | > 90% |
| **Relevance** | Human eval (1-5) | ≥ 4 |
| **Format compliance** | Regex/schema validation | 100% |
| **Consistency** | Same input → similar output (3x) | > 80% |
| **Hallucination rate** | Fact-check vs sources | < 5% |
| **Token efficiency** | Output quality / tokens used | Maximizar |
