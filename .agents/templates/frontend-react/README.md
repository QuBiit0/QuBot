# LMAgent Frontend React/Next.js Template

Template de proyecto frontend moderno con React/Next.js siguiendo las mejores prácticas de UI/UX.

## 🎨 Inspiración de Diseño

Este template sigue principios de diseño modernos inspirados en:
- **[Dribbble](https://dribbble.com/)** - Para tendencias visuales
- **[Awwwards](https://www.awwwards.com/)** - Para sitios premiados
- **Material Design 3** - Sistema de diseño de Google
- **Shadcn/UI** - Componentes accesibles

## Estructura del Proyecto

```
frontend/
├── app/                       # App Router (Next.js 14+)
│   ├── (auth)/               # Grupo de rutas auth
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/          # Grupo dashboard
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── globals.css           # Estilos globales
│   ├── layout.tsx            # Layout raíz
│   └── page.tsx              # Home
│
├── components/               # Componentes reutilizables
│   ├── ui/                   # Primitivos UI (shadcn style)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── modal.tsx
│   │   └── ...
│   ├── layout/               # Componentes de layout
│   │   ├── header.tsx
│   │   ├── sidebar.tsx
│   │   └── footer.tsx
│   ├── features/             # Componentes por feature
│   │   ├── auth/
│   │   └── dashboard/
│   └── shared/               # Componentes compartidos
│
├── lib/                      # Utilidades
│   ├── api.ts                # Cliente API
│   ├── auth.ts               # Utilidades auth
│   ├── utils.ts              # Helpers
│   └── cn.ts                 # classnames utility
│
├── hooks/                    # Custom hooks
│   ├── use-auth.ts
│   ├── use-media-query.ts
│   └── use-theme.ts
│
├── styles/                   # Estilos adicionales
│   ├── tokens.css            # Design tokens
│   └── animations.css        # Animaciones
│
├── types/                    # TypeScript types
│   └── index.ts
│
├── public/                   # Assets estáticos
│   ├── fonts/
│   ├── images/
│   └── icons/
│
├── tailwind.config.ts        # Config Tailwind
├── next.config.js            # Config Next.js
├── tsconfig.json             # Config TypeScript
└── package.json
```

## Quick Start

```bash
# Crear proyecto con este template
npx create-next-app@latest my-app --typescript --tailwind --eslint --app

# Instalar dependencias adicionales
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install class-variance-authority clsx tailwind-merge
npm install lucide-react
npm install framer-motion

# Dev dependencies
npm install -D @types/node prettier prettier-plugin-tailwindcss
```

## 🎨 Sistema de Diseño

### Design Tokens (CSS Variables)

```css
/* styles/tokens.css */
:root {
  /* Colors - Palette moderna */
  --color-primary: 220 90% 56%;
  --color-primary-foreground: 0 0% 100%;
  
  --color-secondary: 270 60% 50%;
  --color-secondary-foreground: 0 0% 100%;
  
  --color-accent: 340 82% 52%;
  --color-accent-foreground: 0 0% 100%;
  
  --color-background: 0 0% 100%;
  --color-foreground: 222 47% 11%;
  
  --color-muted: 210 40% 96%;
  --color-muted-foreground: 215 16% 47%;
  
  --color-card: 0 0% 100%;
  --color-card-foreground: 222 47% 11%;
  
  --color-border: 214 32% 91%;
  --color-ring: 220 90% 56%;
  
  /* Dark mode */
  --color-background-dark: 222 47% 11%;
  --color-foreground-dark: 210 40% 98%;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-2xl: 3rem;
  
  /* Border radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-full: 9999px;
  
  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
  
  /* Animations */
  --transition-fast: 150ms;
  --transition-base: 200ms;
  --transition-slow: 300ms;
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}

.dark {
  --color-background: var(--color-background-dark);
  --color-foreground: var(--color-foreground-dark);
  /* ... resto de variables dark */
}
```

### Componentes UI Base

```tsx
// components/ui/button.tsx
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md hover:shadow-lg',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        gradient: 'bg-gradient-to-r from-primary to-secondary text-white shadow-lg hover:shadow-xl',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4',
        lg: 'h-12 px-6 text-lg',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}
```

### Animaciones Modernas

```css
/* styles/animations.css */

/* Fade in up - para entradas de contenido */
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Slide in from right - para modales */
@keyframes slide-in-right {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

/* Scale up - para hover effects */
@keyframes scale-up {
  from {
    transform: scale(0.95);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

/* Shimmer - para loading states */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* Utility classes */
.animate-fade-in-up {
  animation: fade-in-up 0.5s var(--ease-out) forwards;
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s var(--ease-out) forwards;
}

.animate-scale-up {
  animation: scale-up 0.2s var(--ease-out) forwards;
}

.skeleton {
  background: linear-gradient(
    90deg,
    hsl(var(--color-muted)) 25%,
    hsl(var(--color-muted-foreground) / 0.1) 50%,
    hsl(var(--color-muted)) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

/* Hover effects */
.hover-lift {
  transition: transform var(--transition-base) var(--ease-out),
              box-shadow var(--transition-base) var(--ease-out);
}

.hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
}

/* Glassmorphism */
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Gradient text */
.gradient-text {
  background: linear-gradient(135deg, hsl(var(--color-primary)), hsl(var(--color-secondary)));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

## 🎯 Patrones de Diseño (Dribbble-Inspired)

### 1. Hero Section Moderna

```tsx
// components/features/landing/hero.tsx
export function Hero() {
  return (
    <section className="relative min-h-screen overflow-hidden bg-gradient-to-br from-background via-background to-primary/5">
      {/* Decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-1/2 -right-1/4 h-[800px] w-[800px] rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-1/2 -left-1/4 h-[600px] w-[600px] rounded-full bg-secondary/10 blur-3xl" />
      </div>
      
      <div className="container relative z-10 mx-auto px-4 py-20 lg:py-32">
        <div className="mx-auto max-w-4xl text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm text-primary animate-fade-in-up">
            ✨ Nuevo lanzamiento v2.0
          </div>
          
          {/* Heading */}
          <h1 className="mb-6 text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl animate-fade-in-up [animation-delay:100ms]">
            Build products with{' '}
            <span className="gradient-text">AI-powered</span>{' '}
            automation
          </h1>
          
          {/* Subtitle */}
          <p className="mb-10 text-xl text-muted-foreground animate-fade-in-up [animation-delay:200ms]">
            The complete framework for developing intelligent agents
            and automated workflows
          </p>
          
          {/* CTAs */}
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center animate-fade-in-up [animation-delay:300ms]">
            <Button size="lg" variant="gradient" className="w-full sm:w-auto">
              Get Started Free
            </Button>
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              View Demo
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
```

### 2. Cards con Hover Effect

```tsx
// components/ui/feature-card.tsx
export function FeatureCard({ icon, title, description }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border bg-card p-6 hover-lift">
      {/* Gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 opacity-0 transition-opacity group-hover:opacity-100" />
      
      {/* Content */}
      <div className="relative z-10">
        <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
          {icon}
        </div>
        <h3 className="mb-2 text-xl font-semibold">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
```

### 3. Dashboard Layout

```tsx
// app/(dashboard)/layout.tsx
export default function DashboardLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-muted/30">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-border bg-card">
        <Sidebar />
      </aside>
      
      {/* Main content */}
      <div className="ml-64 flex-1">
        <Header />
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

## 📱 Responsive Design

```tsx
// Breakpoints en Tailwind config
const breakpoints = {
  sm: '640px',   // Mobile landscape
  md: '768px',   // Tablet
  lg: '1024px',  // Desktop
  xl: '1280px',  // Large desktop
  '2xl': '1536px', // Extra large
};

// Ejemplo de grid responsive
<div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  {items.map(item => <Card key={item.id} {...item} />)}
</div>
```

## 📚 Recursos de Diseño

- [Dribbble](https://dribbble.com/) - Inspiración visual
- [Mobbin](https://mobbin.com/) - Patrones UI reales
- [Refero](https://refero.design/) - Referencias de SaaS
- [Shadcn/UI](https://ui.shadcn.com/) - Componentes accesibles
- [Radix UI](https://www.radix-ui.com/) - Primitivos headless

## Checklist de UX/UI

- [ ] Sistema de tokens de diseño definido
- [ ] Dark mode implementado
- [ ] Componentes accesibles (WCAG 2.1)
- [ ] Animaciones suaves y con propósito
- [ ] Estados de loading (skeletons)
- [ ] Estados de error claros
- [ ] Feedback visual en interacciones
- [ ] Responsive en todos los breakpoints
- [ ] Tipografía legible
- [ ] Contraste adecuado
- [ ] Focus states visibles
