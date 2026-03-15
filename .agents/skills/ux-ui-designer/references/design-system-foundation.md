# Design System Foundation — UX/UI Designer

> Fundamentos de un design system: tokens, espaciado, tipografía, colores y componentes base.

## Design Tokens

### Spacing Scale (8px grid)

```css
:root {
  --space-0: 0;
  --space-1: 4px;     /* 0.25rem */
  --space-2: 8px;     /* 0.5rem  */
  --space-3: 12px;    /* 0.75rem */
  --space-4: 16px;    /* 1rem    */
  --space-5: 20px;    /* 1.25rem */
  --space-6: 24px;    /* 1.5rem  */
  --space-8: 32px;    /* 2rem    */
  --space-10: 40px;   /* 2.5rem  */
  --space-12: 48px;   /* 3rem    */
  --space-16: 64px;   /* 4rem    */
  --space-20: 80px;   /* 5rem    */
  --space-24: 96px;   /* 6rem    */
}
```

### Typography Scale

```css
:root {
  /* Font Family */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Font size */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */

  /* Line height */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;

  /* Font weight */
  --font-regular: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
}
```

### Color Palette (Dark Mode First)

```css
:root {
  /* Neutral */
  --gray-50: #fafafa;
  --gray-100: #f4f4f5;
  --gray-200: #e4e4e7;
  --gray-300: #d4d4d8;
  --gray-400: #a1a1aa;
  --gray-500: #71717a;
  --gray-600: #52525b;
  --gray-700: #3f3f46;
  --gray-800: #27272a;
  --gray-900: #18181b;
  --gray-950: #09090b;

  /* Primary (Customizable) */
  --primary-50: #eff6ff;
  --primary-100: #dbeafe;
  --primary-500: #3b82f6;
  --primary-600: #2563eb;
  --primary-700: #1d4ed8;

  /* Semantic */
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;
}

/* Dark theme */
[data-theme="dark"] {
  --bg-primary: var(--gray-950);
  --bg-secondary: var(--gray-900);
  --bg-tertiary: var(--gray-800);
  --text-primary: var(--gray-50);
  --text-secondary: var(--gray-400);
  --border: var(--gray-700);
}

/* Light theme */
[data-theme="light"] {
  --bg-primary: white;
  --bg-secondary: var(--gray-50);
  --bg-tertiary: var(--gray-100);
  --text-primary: var(--gray-900);
  --text-secondary: var(--gray-500);
  --border: var(--gray-200);
}
```

### Border Radius

```css
:root {
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 24px;
  --radius-full: 9999px;
}
```

### Shadows

```css
:root {
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
}
```

## Breakpoints

| Breakpoint | Width | Target |
|-----------|-------|--------|
| `xs` | < 640px | Mobile portrait |
| `sm` | ≥ 640px | Mobile landscape |
| `md` | ≥ 768px | Tablet |
| `lg` | ≥ 1024px | Desktop |
| `xl` | ≥ 1280px | Large desktop |
| `2xl` | ≥ 1536px | Ultra-wide |

## Contrast Check (WCAG AA)

| Combo | Ratio | Pass AA? |
|-------|-------|----------|
| `--gray-50` on `--gray-900` | 15.1:1 | ✅ |
| `--gray-400` on `--gray-900` | 4.6:1 | ✅ (large text) |
| `--gray-500` on `--gray-950` | 5.0:1 | ✅ |
| `--primary-500` on `white` | 3.1:1 | ❌ (usar 600+) |
| `--primary-600` on `white` | 4.5:1 | ✅ |

## Component States

Todo componente interactivo debe tener estos estados:

| Estado | Descripción | Ejemplo Visual |
|--------|------------|----------------|
| **Default** | Estado normal | — |
| **Hover** | Mouse encima | Lighten 10% |
| **Active** | Click/press | Darken 10% |
| **Focus** | Keyboard focus | Ring 2px primary |
| **Disabled** | No interactivo | Opacity 50% |
| **Loading** | En progreso | Spinner/skeleton |
| **Error** | Estado inválido | Border red |
| **Empty** | Sin datos | Ilustración + CTA |
