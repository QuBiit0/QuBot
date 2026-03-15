# Mobile Platform Guidelines — Mobile Engineer

> Referencia rápida de guidelines HIG (Apple) y Material Design (Google).

## iOS (Human Interface Guidelines)

### Principios Core
1. **Clarity** — Texto legible, iconos claros, interacciones intuitivas
2. **Deference** — El contenido es la estrella, la UI asiste
3. **Depth** — Capas visuales con transiciones significativas

### Componentes Obligatorios

| Componente | Requisito |
|-----------|-----------|
| Safe Area | Respetar notch/Dynamic Island |
| Navigation Bar | 44pt mínimo de altura |
| Tab Bar | Máximo 5 tabs |
| Touch Target | Mínimo 44x44pt |
| Status Bar | No ocultar sin motivo |

### Tamaños de Tipografía

| Estilo | Tamaño | Peso |
|--------|--------|------|
| Large Title | 34pt | Bold |
| Title 1 | 28pt | Bold |
| Title 2 | 22pt | Bold |
| Title 3 | 20pt | Semibold |
| Headline | 17pt | Semibold |
| Body | 17pt | Regular |
| Callout | 16pt | Regular |
| Subhead | 15pt | Regular |
| Footnote | 13pt | Regular |
| Caption 1 | 12pt | Regular |
| Caption 2 | 11pt | Regular |

### Colores del Sistema

```swift
// Usar siempre colores del sistema para dark mode automático
Color.primary
Color.secondary
Color.accentColor
Color(.systemBackground)
Color(.secondarySystemBackground)
Color(.systemRed)    // Destructivo
Color(.systemGreen)  // Éxito
Color(.systemBlue)   // Acción primaria
```

---

## Android (Material Design 3)

### Principios Core
1. **Adaptive** — Se adapta a todos los tamaños de pantalla
2. **Personal** — Colores dinámicos (Material You)
3. **Expressive** — Tipografía y formas significativas

### Componentes Obligatorios

| Componente | Requisito |
|-----------|-----------|
| Top App Bar | 64dp estándar, 152dp large |
| Navigation Bar | Bottom nav: 3-5 destinos |
| Navigation Rail | Tablet/Desktop: sidebar |
| FAB | Floating Action Button: 56dp |
| Touch Target | Mínimo 48x48dp |

### Tipografía (Material 3)

| Rol | Tamaño | Tracking |
|-----|--------|----------|
| Display Large | 57sp | -0.25 |
| Display Medium | 45sp | 0 |
| Display Small | 36sp | 0 |
| Headline Large | 32sp | 0 |
| Headline Medium | 28sp | 0 |
| Headline Small | 24sp | 0 |
| Title Large | 22sp | 0 |
| Title Medium | 16sp | 0.15 |
| Title Small | 14sp | 0.1 |
| Body Large | 16sp | 0.5 |
| Body Medium | 14sp | 0.25 |
| Body Small | 12sp | 0.4 |
| Label Large | 14sp | 0.1 |
| Label Medium | 12sp | 0.5 |
| Label Small | 11sp | 0.5 |

---

## React Native / Expo — Cross-Platform

### Safe Area

```tsx
import { SafeAreaView } from 'react-native-safe-area-context';

function Screen({ children }) {
  return (
    <SafeAreaView style={{ flex: 1 }} edges={['top', 'bottom']}>
      {children}
    </SafeAreaView>
  );
}
```

### Keyboard Handling

```tsx
import { KeyboardAvoidingView, Platform } from 'react-native';

function FormScreen() {
  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1 }}
    >
      {/* Form content */}
    </KeyboardAvoidingView>
  );
}
```

### Platform-Specific Code

```tsx
import { Platform, StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  shadow: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
    },
    android: {
      elevation: 4,
    },
  }),
});
```

## Checklist Pre-Release

### iOS
- [ ] Funciona en iPhone SE (pantalla más pequeña)
- [ ] Funciona en iPhone 16 Pro Max
- [ ] Dark mode verificado
- [ ] Dynamic Type respetado
- [ ] App Store screenshots (6.7", 6.1", 5.5")

### Android
- [ ] Funciona en pantalla 320dp (ancho mínimo)
- [ ] Funciona en tablets
- [ ] Dark theme verificado
- [ ] Back button handling correcto
- [ ] Permisos solicitados en contexto
