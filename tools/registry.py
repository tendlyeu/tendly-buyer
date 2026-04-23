"""Tool registry: base class, result type, and global registry."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """Result returned by a tool execution."""

    # Canvas artifact (None if tool doesn't produce one)
    artifact_type: Optional[str] = None
    artifact_id: Optional[str] = None
    artifact_data: Optional[Dict[str, Any]] = None

    # Tender cards for inline display in chat
    tenders: List[Dict] = field(default_factory=list)

    # Short summary text for the LLM response context
    summary: str = ""

    # Company data (for company search tool)
    companies: List[Dict] = field(default_factory=list)

    # Error message if execution failed
    error: Optional[str] = None


class Tool:
    """Base class for all chat tools."""

    name: str = ""
    description: str = ""
    artifact_type: Optional[str] = None  # None means no canvas artifact

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        """Execute the tool and return a result.

        Args:
            params: Parameters extracted by the LLM (e.g. country_codes, keywords)
            context: Shared context (chat_service instance, conversation, etc.)

        Returns:
            ToolResult with optional artifact, tenders, summary.
        """
        raise NotImplementedError


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool instance."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_descriptions(self) -> str:
        """Get tool descriptions for the LLM system prompt."""
        lines = []
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)


# Global registry singleton
tool_registry = ToolRegistry()
