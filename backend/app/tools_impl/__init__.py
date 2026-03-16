from .filesystem import FilesystemTool
from .registry import tool_registry

# Instanciar y registrar todas las herramientas
filesystem_tool = FilesystemTool()

tool_registry.register(filesystem_tool)
