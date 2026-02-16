"""Tool protocol: name, description, JSON schema for parameters, and callable."""
from typing import Any, Callable

# OpenAI tool definition shape: we use "function" type with name, description, parameters (JSON Schema)
# The callable receives the parsed arguments and returns a string result for the LLM.
ToolDefinition = dict[str, Any]  # {"type": "function", "function": {"name", "description", "parameters"}}


def make_tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    callable_fn: Callable[..., str],
) -> tuple[ToolDefinition, Callable[..., str]]:
    """Build an OpenAI tool definition and the callable that executes it.
    parameters: JSON Schema for the function (e.g. {"type": "object", "properties": {...}, "required": [...]}).
    callable_fn: receives kwargs matching the schema, returns a string (for the LLM).
    """
    definition: ToolDefinition = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }
    return definition, callable_fn
