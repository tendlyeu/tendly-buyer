"""Tool-calling framework for Tendly Chat.

Each tool produces a ToolResult which may include an artifact for the canvas panel,
tender cards for inline display, and a summary for the LLM response context.
"""

from tools.registry import Tool, ToolResult, ToolRegistry, tool_registry
