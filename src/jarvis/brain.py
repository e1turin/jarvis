"""
Conversation manager — orchestrates the LLM + tools + history.

This module ties together:
  - LLMClient  (pure API calls from llm.py)
  - tools      (tool definitions + implementations from tools.py)
  - history    (conversation state management)

The flow per user message:
  1. Append user input to conversation copy
  2. Call LLM with optional tool definitions
  3. If LLM returns tool_calls → execute tools → loop back to step 2
  4. If LLM returns text → return ChatResult
  5. If interrupted → discard the turn (caller must NOT commit)
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from jarvis.config import settings
from jarvis.llm import LLMClient, LLMAPIError, LLMConnectionError, LLMTimeoutError
from jarvis.tools import get_builtin_tool_defs, execute_tool

# Maximum tool call iterations per user message (prevents infinite loops)
MAX_TOOL_ITERATIONS = 5


class ChatResult(BaseModel):
    text: str
    action: str = "continue"  # "continue" or "end"


class ConversationManager:
    """
    Manages a single conversation with the LLM.

    Usage:
        brain = ConversationManager(mcp_tool_call=mcp_call_fn)
        result = brain.send_message("Hello")
        brain.commit_turn("Hello", result)  # only if not interrupted
    """

    def __init__(self):
        self.llm = LLMClient()

        system_prompt = settings.load_system_prompt()
        # Immutable history — caller must call commit_turn() to append
        self.history: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    # ── Tool definitions ───────────────────────────────────────

    def get_tools(self) -> list[dict]:
        """Return all available tool definitions (built-in only)."""
        return get_builtin_tool_defs()

    # ── Main message send ──────────────────────────────────────

    def send_message(self, user_input: str) -> ChatResult:
        """
        Send user input and get a response.
        Runs the tool-calling loop automatically.
        Does NOT modify self.history — caller must call commit_turn().
        """
        messages = list(self.history)
        messages.append({"role": "user", "content": user_input})

        tools = self.get_tools()
        tools_disabled = False  # Flag: retry without tools on Gemini errors

        for iteration in range(MAX_TOOL_ITERATIONS):
            print(
                "🧠 Thinking..."
                if iteration == 0
                else f"🔄 Tool result round {iteration + 1}..."
            )

            # ── Call LLM (with fallback for Gemini thought_signature) ──
            try:
                response = self.llm.send(
                    messages,
                    tools=tools if not tools_disabled else None,
                )
            except LLMAPIError as e:
                error_str = str(e).lower()
                if (
                    "thought_signature" in error_str
                    and not tools_disabled
                ):
                    print(
                        "  ⚠️ Model doesn't support function calling via this API,"
                        " retrying without tools"
                    )
                    tools_disabled = True
                    response = self.llm.send(messages, tools=None)
                else:
                    return ChatResult(text=f"LLM Error: {e}", action="end")
            except LLMConnectionError as e:
                return ChatResult(text=str(e), action="end")
            except LLMTimeoutError as e:
                return ChatResult(text=str(e), action="end")

            choice = response.choices[0]
            message = choice.message

            # ── No tool call: return text ──────────────────────
            if not message.tool_calls:
                reply = message.content or ""
                if reply.rstrip().endswith("[END]"):
                    text = reply.rstrip()[: -len("[END]")].strip()
                    return ChatResult(text=text, action="end")
                return ChatResult(text=reply, action="continue")

            # Tools disabled but LLM still returned tool_calls — unlikely but handle
            if tools_disabled:
                return ChatResult(text=message.content or "", action="continue")

            # ── Tool call(s) received ──────────────────────────
            # Add assistant message with tool_calls to context
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            }
            messages.append(assistant_msg)

            # Execute each tool and add results
            for tc in message.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                print(f"   🔧 Calling tool: {tool_name}({tool_args})")

                result_text = execute_tool(
                    tool_name,
                    tool_args,
                )

                # Truncate very long results
                if len(result_text) > 2000:
                    result_text = result_text[:2000] + "\n... (truncated)"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })

        # Maximum iterations reached
        print("  ⚠️ Tool call limit reached, returning last response")
        final = messages[-1].get("content", "I'm still working on that.")
        return ChatResult(text=final, action="continue")

    # ── History management ─────────────────────────────────────

    def commit_turn(self, user_input: str, result: ChatResult):
        """
        Commit a completed (non-interrupted) turn to history.
        """
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": result.text})

    def chat(self, user_input: str) -> ChatResult:
        """
        Convenience: send_message + commit_turn in one call.
        """
        result = self.send_message(user_input)
        self.commit_turn(user_input, result)
        return result


# ── Aliases for backward compatibility ─────────────────────────
# Old code imported JarvisBrain. It's now ConversationManager.
JarvisBrain = ConversationManager
