"""Tools available to the agent. Each integration is a tool with name, schema, and callable."""
from src.tools.registry import get_tool_registry

# Import tools so they register themselves
import src.tools.calendar  # noqa: F401

__all__ = ["get_tool_registry"]
