# Accessibility Guide — Frontend Engineer

> Guía de accesibilidad WCAG 2.1 AA para aplicaciones React/Next.js.

## Principios POUR

| Principio | Significado | Ejemplo |
|-----------|------------|---------|
| **P**erceptible | El usuario puede percibir el contenido | Alt text en imágenes |
| **O**perable | El usuario puede interactuar | Navegación por teclado |
| **U**nderstandable | El usuario entiende | Labels descriptivos |
| **R**obust | Funciona en distintos contextos | HTML semántico |

## Checklist Rápido

### Imágenes y Media
- [ ] `alt` text en todas las imágenes (`""` si es decorativa)
- [ ] Videos con subtítulos
- [ ] Animaciones respetan `prefers-reduced-motion`

### Color y Contraste
- [ ] Contraste texto ≥ 4.5:1 (AA)
- [ ] Contraste texto grande ≥ 3:1
- [ ] Contraste elementos UI ≥ 3:1
- [ ] No depender solo del color para información

### Navegación por Teclado
- [ ] Todo accesible con Tab/Shift+Tab
- [ ] Focus visible y claro
- [ ] No focus traps
- [ ] Skip links al inicio de la página
- [ ] Orden de Tab lógico

### Formularios
- [ ] Labels asociados a inputs (`htmlFor`)
- [ ] Errores de validación claros y descriptivos
- [ ] Campos requeridos indicados
- [ ] Autocompletado habilitado donde aplique

### Semántica HTML
- [ ] Un solo `<h1>` por página
- [ ] Jerarquía de headings correcta (h1→h2→h3)
- [ ] `<nav>`, `<main>`, `<footer>` usados
- [ ] Listas con `<ul>`/`<ol>`, no `<div>`
- [ ] Botones con `<button>`, no `<div onClick>`

## Patrones React Accesibles

### Botón vs Link

```tsx
// ✅ Botón: ejecuta una acción
<button onClick={handleSave}>Guardar</button>

// ✅ Link: navega a otra página
<a href="/settings">Configuración</a>

// ❌ NUNCA: div como botón
<div onClick={handleSave}>Guardar</div>
```

### Focus Management

```tsx
import { useRef, useEffect } from 'react';

function Modal({ isOpen, onClose, children }) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      closeRef.current?.focus();  // Focus en el modal al abrir
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <h2 id="modal-title">Título del Modal</h2>
      {children}
      <button ref={closeRef} onClick={onClose}>Cerrar</button>
    </div>
  );
}
```

### Reduced Motion

```css
/* Respetar preferencias de usuario */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Live Regions

```tsx
// Para anuncios dinámicos a screen readers
function Notification({ message }) {
  return (
    <div role="status" aria-live="polite" aria-atomic="true">
      {message}
    </div>
  );
}

// Para errores urgentes
function ErrorAlert({ error }) {
  return (
    <div role="alert" aria-live="assertive">
      {error}
    </div>
  );
}
```

## Herramientas de Testing

| Herramienta | Tipo | Uso |
|-------------|------|-----|
| **axe DevTools** | Browser extension | Auditoría automática inline |
| **Lighthouse** | Built-in Chrome | Score de accesibilidad |
| **jest-axe** | Unit test | Tests automáticos de a11y |
| **Pa11y** | CLI | CI/CD pipeline check |
| **Screen reader** (NVDA/VoiceOver) | Manual | Testing real |

```tsx
// jest-axe en tests
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('Button is accessible', async () => {
  const { container } = render(<Button>Click me</Button>);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```
