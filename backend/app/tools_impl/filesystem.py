import os

from .base import BaseTool, ToolResult


class FilesystemTool(BaseTool):
    name = "filesystem"
    description = (
        "Permite leer y escribir archivos en el sistema local de forma segura."
    )
    parameters = {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["read", "write", "list"]},
            "path": {"type": "string"},
            "content": {
                "type": "string",
                "description": "Contenido para la operación de escritura",
            },
        },
        "required": ["operation", "path"],
    }

    async def execute(
        self, operation: str, path: str, content: str = None
    ) -> ToolResult:
        try:
            # Validación simple de seguridad (Sandbox)
            safe_base = "/app/storage"
            full_path = os.path.abspath(os.path.join(safe_base, path))

            if not full_path.startswith(os.path.abspath(safe_base)):
                return ToolResult(
                    success=False,
                    output=None,
                    error="Acceso denegado: Path fuera del sandbox.",
                )

            if operation == "read":
                with open(full_path) as f:
                    return ToolResult(success=True, output=f.read())

            elif operation == "write":
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content)
                return ToolResult(success=True, output="Archivo escrito correctamente.")

            elif operation == "list":
                files = os.listdir(full_path)
                return ToolResult(success=True, output=files)

            return ToolResult(
                success=False, output=None, error="Operación no soportada."
            )

        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
