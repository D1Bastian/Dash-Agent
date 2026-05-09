import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class MCPClient:
    """Small MCP JSON-RPC bridge with a safe dry-run default.

    Set DASH_MCP_MODE=live and DASH_MCP_<PARTNER>_HTTP_URL to call an MCP
    gateway that accepts tools/call JSON-RPC payloads.
    """

    def __init__(self, partner: str):
        self.partner = partner
        self.partner_key = partner.upper().replace("-", "_")
        self.mode = os.getenv("DASH_MCP_MODE", "dry-run").lower()
        self.http_url = os.getenv(f"DASH_MCP_{self.partner_key}_HTTP_URL")
        self.token = os.getenv(f"DASH_MCP_{self.partner_key}_TOKEN")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.mode != "live" or not self.http_url:
            return {
                "ok": True,
                "mode": "dry-run",
                "partner": self.partner,
                "tool": tool_name,
                "arguments": self._redact(arguments),
            }

        return await asyncio.to_thread(self._post_tool_call, tool_name, arguments)

    def _post_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": f"dash-{int(time.time() * 1000)}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib.request.Request(self.http_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return {"ok": False, "status": exc.code, "error": body}

    def _redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._redact_field(key, item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        return value

    def _redact_field(self, key: str, value: Any) -> Any:
        lowered = key.lower()
        if any(term in lowered for term in ["password", "token", "secret", "credential", "email"]):
            return "***"
        return self._redact(value)
