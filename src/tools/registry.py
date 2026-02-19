"""Central registry: register tools, get OpenAI tool list, execute by name."""
from typing import Any, Literal

from src.tools.base import ToolDefinition

ToolKind = Literal["generic", "skill"]

# List of (openai_tool_definition, callable, kind)
_registry: list[tuple[ToolDefinition, callable, ToolKind]] = []


def register(
    definition: ToolDefinition,
    callable_fn: callable,
    *,
    kind: ToolKind = "generic",
) -> None:
    """Register a tool. definition is the OpenAI tool dict; callable_fn(**kwargs) -> str.
    kind: 'generic' (always included) or 'skill' (only when a matched skill lists it).
    """
    _registry.append((definition, callable_fn, kind))


def get_openai_tools(
    include_skill_tool_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return tool definitions for this run: all generic tools plus skill tools whose name is in include_skill_tool_names."""
    include = set(include_skill_tool_names or [])
    result: list[dict[str, Any]] = []
    for defn, _, kind in _registry:
        if kind == "generic":
            result.append(defn)
        elif kind == "skill":
            name = defn.get("function", {}).get("name")
            if name and name in include:
                result.append(defn)
    return result


def execute(tool_name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool by name with the given arguments. Returns a string result for the LLM."""
    for definition, callable_fn, _ in _registry:
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

    def get_openai_tools(
        self,
        include_skill_tool_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        return get_openai_tools(include_skill_tool_names=include_skill_tool_names)

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        return execute(tool_name, arguments)


_ToolRegistryInstance = ToolRegistry()
