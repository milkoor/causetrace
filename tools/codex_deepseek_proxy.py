"""Minimal Responses API → Chat Completions proxy for Codex CLI + DeepSeek.

Codex v0.130.0 uses the Responses API (HTTP POST /v1/responses).
DeepSeek only supports Chat Completions API. This proxy translates
between the two protocols.

Usage:
    # Start the proxy
    python3 tools/codex_deepseek_proxy.py

    # In another terminal, configure Codex:
    #   ~/.codex/config.toml:
    #     model_provider = "deepseek-proxy"
    #     [model_providers.deepseek-proxy]
    #     name = "DeepSeek Proxy"
    #     base_url = "http://127.0.0.1:4446"
    #     env_key = "DEEPSEEK_AUTH_TOKEN"
    #     supports_websockets = false
    #
    # Then run:
    #   DEEPSEEK_AUTH_TOKEN="sk-..." codex --profile deepseek-proxy exec "hello"
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

import httpx  # pip install httpx

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_AUTH_TOKEN", "")
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
# Use the standard Chat Completions endpoint, not the Anthropic-compatible one
if "anthropic" in DEEPSEEK_BASE:
    DEEPSEEK_BASE = "https://api.deepseek.com/v1"
PROXY_HOST = os.environ.get("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.environ.get("PROXY_PORT", "4446"))

# Map Roles API role to Chat Completions role
# The first user message should be "developer" or "system" in Responses API
ROLE_MAP = {
    "developer": "system",
    "system": "system",
    "user": "user",
    "assistant": "assistant",
}


def _translate_input(input_data: Any) -> list[dict]:
    """Translate Responses API input to Chat Completions messages."""
    if isinstance(input_data, str):
        return [{"role": "user", "content": input_data}]
    if isinstance(input_data, list):
        messages = []
        for item in input_data:
            if isinstance(item, dict):
                role = ROLE_MAP.get(item.get("role", "user"), "user")
                content = item.get("content", "")
                if isinstance(content, list):
                    text_parts = []
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "input_text":
                            text_parts.append(c.get("text", ""))
                    content = "\n".join(text_parts)
                if content:
                    messages.append({"role": role, "content": content})
        return messages
    return [{"role": "user", "content": str(input_data)}]


def _translate_tools(tools: list) -> list:
    """Translate Responses API tool format to Chat Completions tool format.

    Responses API: {"name": "bash", "description": "...", "parameters": {...}, "type": "bash"}
    Chat Completions: {"type": "function", "function": {"name": "bash", "description": "...", "parameters": {...}}}
    """
    translated = []
    for i, tool in enumerate(tools):
        if not isinstance(tool, dict):
            continue
        if "function" in tool:
            translated.append(tool)
            continue

        name = tool.get("name", "") or tool.get("type", f"tool_{i}")
        params = tool.get("parameters") or {}
        if not isinstance(params, dict) or params.get("type") != "object":
            params = {"type": "object", "properties": {}}

        translated.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool.get("description", ""),
                "parameters": params,
            }
        })
    return translated


def _translate_response_events(model: str, response_id: str, reply: dict) -> list[dict]:
    """Translate Chat Completions response to Responses API event stream.

    Returns a list of event dicts matching the Responses API SSE format.
    """
    events = []
    choice = (reply.get("choices") or [{}])[0]
    msg = choice.get("message", {})
    finish_reason = choice.get("finish_reason", "stop")
    usage = reply.get("usage", {})

    reasoning_content = msg.get("reasoning_content", "")
    output_items = []

    # response.created
    events.append({
        "type": "response.created",
        "response": {
            "id": response_id,
            "model": model,
            "status": "in_progress",
            "usage": None,
        }
    })

    # Reasoning
    if reasoning_content:
        reasoning_id = f"reason_{uuid.uuid4().hex[:12]}"
        item = {
            "id": reasoning_id,
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": reasoning_content[:500]}],
        }
        output_items.append(item)
        events.append({"type": "response.output_item.added", "item": item})
        events.append({"type": "response.output_item.done", "item": item})

    # Tool calls
    tool_calls = msg.get("tool_calls") or []
    for tc in tool_calls:
        tc_id = tc.get("id", f"call_{uuid.uuid4().hex[:12]}")
        func = tc.get("function", {})
        item = {
            "id": tc_id,
            "type": "function_call",
            "name": func.get("name", ""),
            "arguments": func.get("arguments", "{}"),
            "status": "in_progress",
            "call_id": tc_id,
        }
        output_items.append(item)
        events.append({"type": "response.output_item.added", "item": item})
        events.append({"type": "response.output_item.done", "item": item})

    # Text content
    text_content = msg.get("content", "")
    if text_content:
        item_id = f"msg_{uuid.uuid4().hex[:12]}"
        item = {
            "id": item_id,
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": text_content}],
        }
        output_items.append(item)
        events.append({"type": "response.output_item.added", "item": item})
        events.append({"type": "response.output_item.done", "item": item})

    # response.completed with output array
    final_status = "completed" if finish_reason != "tool_calls" else "in_progress"
    events.append({
        "type": "response.completed",
        "response": {
            "id": response_id,
            "model": model,
            "status": final_status,
            "output": output_items,
            "usage": {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        },
    })

    return events


class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if len(args) >= 3:
            sys.stderr.write(f"[codex-deepseek-proxy] {args[1]} {args[2]} {args[3] if len(args) > 3 else ''}\n")

    def do_POST(self):
        if self.path not in ("/v1/responses", "/responses"):
            self.send_error(404)
            return

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else self.rfile.read()
        try:
            req = json.loads(body)
        except json.JSONDecodeError as e:
            self.send_error(400, f"Invalid JSON: {e}")
            return

        auth_header = self.headers.get("Authorization", "")
        # Check if the env key matches or use the key from Authorization header
        api_key = DEEPSEEK_API_KEY
        if not api_key and auth_header.startswith("Bearer "):
            api_key = auth_header[7:]

        if not api_key:
            self._send_json(401, {"error": "No API key configured"})
            return

        model = req.get("model", "deepseek-chat")
        input_data = req.get("input", "")
        stream = req.get("stream", False)
        tools = req.get("tools", [])


        messages = _translate_input(input_data)

        # Build Chat Completions request (always non-streaming — we translate to Responses API events)
        cc_req = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            cc_req["tools"] = _translate_tools(tools)

        # If the first message comes from a developer/system role we already
        # translated, we may be missing the user's actual prompt. In that case,
        # add a minimal user message so the API doesn't reject the request.
        has_user_msg = any(m["role"] == "user" for m in messages)
        if not has_user_msg:
            messages.append({"role": "user", "content": "Continue."})

        response_id = f"resp_{uuid.uuid4().hex[:12]}"

        try:
            with httpx.Client(timeout=300.0) as client:
                resp = client.post(
                    f"{DEEPSEEK_BASE}/chat/completions",
                    json=cc_req,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )

                if resp.status_code != 200:
                    self._send_json(resp.status_code, {
                        "error": f"DeepSeek API error: {resp.text[:500]}"
                    })
                    return

                try:
                    reply = resp.json()
                except Exception:
                    self._send_json(502, {
                        "error": f"Empty/non-JSON response from DeepSeek (status {resp.status_code}): {resp.text[:500]}"
                    })
                    return
                events = _translate_response_events(model, response_id, reply)

                if stream:
                    self._send_stream(events)
                else:
                    # Build full Responses API response body with output array
                    resp_body = {
                        "id": response_id,
                        "model": model,
                        "status": "completed",
                        "output": [],
                        "usage": {},
                    }
                    for ev in events:
                        if ev["type"] == "response.completed":
                            resp_body["status"] = ev["response"].get("status", "completed")
                            resp_body["usage"] = ev["response"].get("usage", {})
                        elif ev["type"] == "response.output_item.added":
                            resp_body["output"].append(ev["item"])
                    self._send_json(200, resp_body)

        except Exception as e:
            self._send_json(502, {"error": f"Proxy error: {e}"})

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_stream(self, events: list[dict]):
        body = b""
        for ev in events:
            line = f"data: {json.dumps(ev)}\n\n"
            body += line.encode()
        body += b"data: [DONE]\n\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    if not DEEPSEEK_API_KEY:
        print("WARNING: DEEPSEEK_AUTH_TOKEN is not set.", file=sys.stderr)
        print("  The proxy will start but API calls will fail.", file=sys.stderr)
        print("  Set it with: export DEEPSEEK_AUTH_TOKEN='sk-...'", file=sys.stderr)

    server = HTTPServer((PROXY_HOST, PROXY_PORT), ProxyHandler)
    print(f"[codex-deepseek-proxy] Listening on http://{PROXY_HOST}:{PROXY_PORT}", file=sys.stderr)
    print(f"[codex-deepseek-proxy] Upstream: {DEEPSEEK_BASE}", file=sys.stderr)
    print(file=sys.stderr)
    print("  Codex config.toml:", file=sys.stderr)
    print('    model_provider = "deepseek-proxy"', file=sys.stderr)
    print("    [model_providers.deepseek-proxy]", file=sys.stderr)
    print('    name = "DeepSeek Proxy"', file=sys.stderr)
    print(f'    base_url = "http://{PROXY_HOST}:{PROXY_PORT}"', file=sys.stderr)
    print('    env_key = "DEEPSEEK_AUTH_TOKEN"', file=sys.stderr)
    print("    supports_websockets = false", file=sys.stderr)
    print(file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", file=sys.stderr)
        server.server_close()


if __name__ == "__main__":
    main()
