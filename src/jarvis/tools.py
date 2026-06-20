"""
Tool definitions and implementations for the LLM.
Built-in tools (web_search via DuckDuckGo) and routing logic.

This module provides:
  1. Tool definitions (OpenAI function calling format)
  2. Tool implementations (what each tool actually does)
  3. A router that dispatches tool calls to the right handler
"""

from __future__ import annotations

from typing import Any


def get_builtin_tool_defs() -> list[dict]:
    """
    Return OpenAI-format tool definitions for all built-in tools.
    These work without any MCP setup — no API keys, no servers.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": (
                    "Search the web for current information. "
                    "Use this for news, weather, prices, facts, "
                    "or anything that may have changed since the model's training data."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The search query. "
                                "Be specific, use the user's original language."
                            ),
                        }
                    },
                    "required": ["query"],
                },
            },
        },
    ]


# ── Tool implementations ───────────────────────────────────────


def search_web(query: str) -> str:
    """
    Search the web via DuckDuckGo (free, no API key required).
    Returns formatted results as a single string.
    """
    if not query:
        return "Error: 'query' parameter is required"

    try:
        from ddgs import DDGS

        print(f"     🔍 Searching: {query}")
        results = []
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=5)):
                title = r.get("title", "").strip()
                body = r.get("body", "").strip()
                href = r.get("href", "")
                results.append(f"{title}\n  URL: {href}\n  {body}")
                if i >= 4:
                    break

        if not results:
            return "No search results found."

        return "\n\n".join(results)

    except ImportError:
        return (
            "Error: duckduckgo-search package not installed. "
            "Run: uv add duckduckgo-search"
        )
    except Exception as e:
        return f"Search error: {e}"


# ── Tool router ────────────────────────────────────────────────

# Map of built-in tool names to their handler functions
_BUILTIN_HANDLERS: dict[str, callable] = {
    "web_search": search_web,
}


def execute_tool(name: str, args: dict[str, Any]) -> str:
    """
    Execute a tool call by dispatching to the right handler.

    Args:
        name: Tool name (e.g. 'web_search').
        args: Tool arguments dict.

    Returns:
        Tool result as a string.
    """
    handler = _BUILTIN_HANDLERS.get(name)
    if handler:
        return handler(**args)

    return f"Error: tool '{name}' is not available"
