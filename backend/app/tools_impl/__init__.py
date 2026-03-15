from .registry import tool_registry
from .filesystem import FilesystemTool

# Instanciar y registrar todas las herramientas
filesystem_tool = FilesystemTool()

tool_registry.register(filesystem_tool)
