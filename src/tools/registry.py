"""Central registry: register tools, get OpenAI tool list, execute by name."""
from typing import Any

from src.tools.base import ToolDefinition

# List of (openai_tool_definition, callable)
_registry: list[tuple[ToolDefinition, callable]] = []


def register(definition: ToolDefinition, callable_fn: callable) -> None:
    """Register a tool. definition is the OpenAI tool dict; callable_fn(name, **kwargs) -> str."""
    _registry.append((definition, callable_fn))


def get_openai_tools() -> list[dict[str, Any]]:
    """Return the list of tool definitions for the OpenAI API."""
    return [defn for defn, _ in _registry]


def execute(tool_name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool by name with the given arguments. Returns a string result for the LLM."""
    for definition, callable_fn in _registry:
        if definition.get("function", {}).get("name") == tool_name:
            try:
                result = callable_fn(**arguments)
                return result if isinstance(result, str) else str(result)
            except Exception as e:
                return f"Error: {e!s}"
    return f"Unknown tool: {tool_name}"


def get_tool_registry() -> "ToolRegistry":
    """Return the singleton registry instance (for any code that wants a class interface)."""
    return _ToolRegistryInstance


class ToolRegistry:
    """Thin wrapper over module-level registry."""

    def get_openai_tools(self) -> list[dict[str, Any]]:
        return get_openai_tools()

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        return execute(tool_name, arguments)


_ToolRegistryInstance = ToolRegistry()
