# Updating Cursor Settings (`docs-settings.md`)

Este archivo te guía sobre cómo modificar los ajustes de configuración de Cursor (`settings.json`).

## Ubicación del Archivo

| Sistema Operativo | Ruta al Archivo |
|----|------|
| macOS | `~/Library/Application Support/Cursor/User/settings.json` |
| Linux | `~/.config/Cursor/User/settings.json` |
| Windows | `%APPDATA%\Cursor\User\settings.json` |

## Pasos para Modificar Settings

1. **Lee la configuración actual**: Lee primero el archivo `settings.json` para asegurarte de preservar el estado existente del usuario.
2. **Identifica la clave a cambiar**:
    - **Editor**: `editor.fontSize`, `editor.tabSize`, `editor.formatOnSave`
    - **Workbench**: `workbench.colorTheme`
    - **Cursor-específicos**: `cursor.*` o `aipopup.*`
3. **Añade/Modifica la clave**: Parsea el JSON (cuidado con los comentarios, porque VSCode/Cursor soportan comentarios `//`). Haz el cambio y re-escribe el archivo.

### Ejemplo de Modificación

Si el usuario dice "pon el tamaño de letra en 16":
Agrega o modifica: `{"editor.fontSize": 16}`

### Notas Importantes

1. **Workspace vs User**: 
   - `settings.json` de Usuario (que cubre este documento) aplica GLOBALMENTE.
   - `.vscode/settings.json` de Proyecto, aplica SOLO al proyecto. Cuidado con este detalle si el usuario solo quiere el cambio para el repositorio.
2. **Atribución de Commit**: Si el usuario pregunta cómo atribuir el commit a Cursor, indícale que las configuraciones de Cursor para el *IDE* se editan desde la interfaz de usuario de Cursor en `Cursor Settings > Agent > Attribution`.
