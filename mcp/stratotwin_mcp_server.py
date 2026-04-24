"""
StratoTwin MCP stdio server.

This tiny bridge exposes the existing StratoTwin HTTP API as MCP tools for
Copilot/Superset Agent Builder style workspaces. It deliberately uses only the
Python standard library so it can run in the current project environment.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_BASE = os.environ.get("STRATOTWIN_API_BASE", "http://127.0.0.1:8080").rstrip("/")
DEFAULT_TIMEOUT = float(os.environ.get("STRATOTWIN_MCP_TIMEOUT", "10"))


TOOLS: list[dict[str, Any]] = [
    {
        "name": "stratotwin_query",
        "description": "Ask StratoTwin a natural-language question about topology, blast radius, or alerts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Example: What's the blast radius if L6-CHN-RACK-01 fails?",
                }
            },
            "required": ["question"],
        },
    },
    {
        "name": "stratotwin_blast_radius",
        "description": "Run deterministic blast-radius lookup for a StratoTwin node id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "Example: L1-CHN-FW-01 or L6-CHN-RACK-01",
                }
            },
            "required": ["node_id"],
        },
    },
    {
        "name": "stratotwin_topology_graph",
        "description": "Fetch the current StratoTwin topology graph with nodes, WAN links, and dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit_nodes": {
                    "type": "integer",
                    "description": "Optional maximum number of graph nodes to return.",
                    "minimum": 1,
                    "maximum": 500,
                }
            },
        },
    },
    {
        "name": "stratotwin_alerts_recent",
        "description": "Fetch recent non-positive StratoTwin process executions and alerts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of alerts to return.",
                    "minimum": 1,
                    "maximum": 100,
                }
            },
        },
    },
]


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}

    while True:
        line = sys.stdin.buffer.readline()
        if line == b"":
            return None
        line_text = line.decode("ascii", errors="replace").strip()
        if not line_text:
            break
        if ":" in line_text:
            key, value = line_text.split(":", 1)
            headers[key.lower()] = value.strip()

    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        return None

    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def result_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def http_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    url = f"{API_BASE}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            if not raw:
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def tool_text(payload: Any, is_error: bool = False) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, ensure_ascii=True)
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["isError"] = True
    return result


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "stratotwin_query":
        question = str(arguments.get("question", "")).strip()
        if not question:
            return tool_text("Missing required argument: question", is_error=True)
        return tool_text(http_json("POST", "/query", {"question": question}))

    if name == "stratotwin_blast_radius":
        node_id = str(arguments.get("node_id", "")).strip()
        if not node_id:
            return tool_text("Missing required argument: node_id", is_error=True)
        encoded = urllib.parse.quote(node_id, safe="")
        return tool_text(http_json("GET", f"/blast-radius/{encoded}"))

    if name == "stratotwin_topology_graph":
        limit = arguments.get("limit_nodes")
        query = ""
        if limit is not None:
            query = "?" + urllib.parse.urlencode({"limit_nodes": int(limit)})
        return tool_text(http_json("GET", f"/topology/graph{query}"))

    if name == "stratotwin_alerts_recent":
        limit = int(arguments.get("limit", 20))
        query = "?" + urllib.parse.urlencode({"limit": limit})
        return tool_text(http_json("GET", f"/alerts/recent{query}"))

    return tool_text(f"Unknown tool: {name}", is_error=True)


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}
    log(f"MCP request received: {method}")

    if method == "initialize":
        protocol_version = params.get("protocolVersion", "2024-11-05")
        return result_response(
            request_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "stratotwin", "version": "1.0.0"},
            },
        )

    if method in ("notifications/initialized", "notifications/cancelled"):
        return None

    if method == "ping":
        return result_response(request_id, {})

    if method == "tools/list":
        return result_response(request_id, {"tools": TOOLS})

    if method == "tools/call":
        name = str(params.get("name", ""))
        arguments = params.get("arguments") or {}
        try:
            return result_response(request_id, call_tool(name, arguments))
        except Exception as exc:  # Keep server alive; surface API failures as tool errors.
            log(traceback.format_exc())
            return result_response(request_id, tool_text(str(exc), is_error=True))

    if method in ("resources/list", "prompts/list"):
        key = "resources" if method == "resources/list" else "prompts"
        return result_response(request_id, {key: []})

    return error_response(request_id, -32601, f"Method not found: {method}")


def main() -> int:
    log(f"StratoTwin MCP server started. API_BASE={API_BASE}")
    while True:
        try:
            message = read_message()
            if message is None:
                return 0
            response = handle_request(message)
            if response is not None:
                write_message(response)
        except Exception:
            log(traceback.format_exc())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
