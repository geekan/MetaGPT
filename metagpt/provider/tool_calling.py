#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tool calling — shared OpenAI-style tool schema + registry (MEO toolCalling.js twin).

Shared contract:
  to_openai_tool(name, description, parameters) -> { type: "function", function: {...} }
  to_openai_tools(list) -> tools[]
  parse_tool_calls(response) -> [{ id, name, arguments(dict), raw_arguments }]
  ToolRegistry: register / get / list_schemas / execute / run_turn
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from metagpt.logs import logger

ToolFn = Union[Callable[..., Any], Callable[..., Awaitable[Any]]]


def to_openai_tool(name: str, description: str = "", parameters: Optional[dict] = None) -> dict:
    """Build one OpenAI function-calling tool schema."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description or "",
            "parameters": parameters or {"type": "object", "properties": {}, "required": []},
        },
    }


def to_openai_tools(tools: List[dict]) -> List[dict]:
    """Accept already-built tools or {name, description, parameters} dicts."""
    out = []
    for t in tools:
        if isinstance(t, dict) and t.get("type") == "function" and "function" in t:
            out.append(t)
        elif isinstance(t, dict) and "name" in t:
            out.append(to_openai_tool(t["name"], t.get("description", ""), t.get("parameters")))
        elif isinstance(t, tuple) and len(t) >= 2:
            out.append(to_openai_tool(t[0], t[1], t[2] if len(t) > 2 else None))
    return out


def _parse_args(raw: Any) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw) or {}
        except json.JSONDecodeError:
            logger.warning(f"[toolCalling] failed to parse arguments: {raw[:200]}")
            return {"_raw": raw}
    return {"_raw": raw}


def parse_tool_calls(response: Any) -> List[dict]:
    """Extract tool_calls from OpenAI chat completion (dict or SDK object)."""
    calls: List[dict] = []

    # dict OpenAI shape
    if isinstance(response, dict):
        choices = response.get("choices") or []
        message = choices[0].get("message") if choices else {}
        raw_calls = (message or {}).get("tool_calls") or []
        for c in raw_calls:
            fn = c.get("function") or {}
            calls.append(
                {
                    "id": c.get("id") or "",
                    "name": fn.get("name") or "",
                    "arguments": _parse_args(fn.get("arguments")),
                    "raw_arguments": fn.get("arguments"),
                    "type": c.get("type") or "function",
                }
            )
        return calls

    # SDK object
    try:
        message = response.choices[0].message
        raw_calls = getattr(message, "tool_calls", None) or []
        for c in raw_calls:
            fn = getattr(c, "function", None)
            name = getattr(fn, "name", "") if fn else ""
            raw_args = getattr(fn, "arguments", None) if fn else None
            calls.append(
                {
                    "id": getattr(c, "id", "") or "",
                    "name": name or "",
                    "arguments": _parse_args(raw_args),
                    "raw_arguments": raw_args,
                    "type": getattr(c, "type", "function") or "function",
                }
            )
    except Exception as e:
        logger.debug(f"[toolCalling] parse_tool_calls non-OpenAI shape: {e}")
    return calls


@dataclass
class ToolSpec:
    name: str
    description: str = ""
    parameters: dict = field(default_factory=lambda: {"type": "object", "properties": {}, "required": []})
    fn: Optional[ToolFn] = None

    def schema(self) -> dict:
        return to_openai_tool(self.name, self.description, self.parameters)


class ToolRegistry:
    """Register tools and execute model tool_calls (shared interface)."""

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}

    def register(
        self,
        name: Optional[str] = None,
        description: str = "",
        parameters: Optional[dict] = None,
        fn: Optional[ToolFn] = None,
    ) -> ToolSpec:
        """register(fn) decorator or register(name=..., fn=...)."""
        if fn is not None and name is None and callable(fn):
            # used as decorator: register()(fn)
            fn_name = getattr(fn, "__name__", "tool")
            spec = ToolSpec(name=fn_name, description=description or (fn.__doc__ or ""), parameters=parameters, fn=fn)
            self._tools[spec.name] = spec
            return spec
        if callable(name) and fn is None:
            # @registry.register
            target = name
            fn_name = getattr(target, "__name__", "tool")
            spec = ToolSpec(name=fn_name, description=target.__doc__ or "", fn=target)
            self._tools[spec.name] = spec
            return spec
        spec = ToolSpec(name=name or "tool", description=description, parameters=parameters, fn=fn)
        self._tools[spec.name] = spec
        return spec

    def tool(self, name: Optional[str] = None, description: str = "", parameters: Optional[dict] = None):
        """Decorator form: @registry.tool() or @registry.tool('name')."""

        def deco(fn: ToolFn):
            tool_name = name or getattr(fn, "__name__", "tool")
            self.register(tool_name, description or (fn.__doc__ or ""), parameters, fn)
            return fn

        if callable(name):
            fn = name
            name = None
            return deco(fn)
        return deco

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def list_schemas(self) -> List[dict]:
        return [t.schema() for t in self._tools.values()]

    def names(self) -> List[str]:
        return list(self._tools.keys())

    async def execute(self, name: str, arguments: Optional[dict] = None) -> dict:
        """Run tool by name; returns { success, name, result | error }."""
        spec = self._tools.get(name)
        if not spec or spec.fn is None:
            return {"success": False, "name": name, "error": f"Unknown tool: {name}"}
        args = arguments or {}
        try:
            result = spec.fn(**args)
            if hasattr(result, "__await__"):
                result = await result
            return {"success": True, "name": name, "result": result}
        except Exception as e:
            logger.warning(f"[toolCalling] tool {name} failed: {e}")
            return {"success": False, "name": name, "error": str(e)}

    async def run_tool_calls(self, calls: List[dict]) -> List[dict]:
        """Execute a batch of parsed tool_calls."""
        out = []
        for c in calls:
            out.append(await self.execute(c.get("name", ""), c.get("arguments") or {}))
        return out

    async def run_turn(
        self,
        llm: Any,
        messages: List[dict],
        use_tools: bool = True,
        tool_choice: Any = None,
        timeout: Optional[int] = None,
        **ask_kwargs: Any,
    ) -> dict:
        """One agent turn: call LLM with tools, execute calls if any.

        Requires llm.aask_messages(messages, tools=..., ...) or fallback aask.
        Returns { text, tool_calls, tool_results, messages }.
        """
        tools = self.list_schemas() if use_tools else []
        rsp = None
        text = ""
        if hasattr(llm, "aask_messages"):
            kwargs = dict(ask_kwargs)
            if tools:
                kwargs["tools"] = tools
                if tool_choice is not None:
                    kwargs["tool_choice"] = tool_choice
            if timeout is not None:
                kwargs["timeout"] = timeout
            rsp = await llm.aask_messages(messages, **kwargs)
        elif hasattr(llm, "aask"):
            # best-effort: append tool instructions
            msg = messages[-1]["content"] if messages else ""
            if tools:
                names = ", ".join(t["function"]["name"] for t in tools)
                msg = f"{msg}\n\nAvailable tools: {names}"
            text = await llm.aask(msg, timeout=timeout) if timeout else await llm.aask(msg)
            rsp = text
        else:
            raise TypeError("llm must provide aask_messages or aask")

        tool_calls = parse_tool_calls(rsp) if not isinstance(rsp, str) else []
        if isinstance(rsp, str):
            text = rsp
        elif isinstance(rsp, dict):
            try:
                text = (rsp.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            except Exception:
                text = ""
        tool_results: List[dict] = []
        if tool_calls:
            tool_results = await self.run_tool_calls(tool_calls)
            # append tool results for next turn
            messages = list(messages)
            messages.append({"role": "assistant", "content": text or "", "tool_calls": tool_calls})
            for call, res in zip(tool_calls, tool_results):
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "content": json.dumps(res, ensure_ascii=False, default=str),
                    }
                )
        return {
            "text": text,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "messages": messages,
            "response": rsp,
        }


# camelCase aliases
toOpenaiTool = to_openai_tool
toOpenaiTools = to_openai_tools
parseToolCalls = parse_tool_calls
