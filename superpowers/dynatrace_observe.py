import logging
import os

import httpx


class DynatraceObserve:
    """Dash runtime telemetry adapter with a safe dry-run default."""

    def __init__(self):
        from backend.config import resolve_config
        self.api_url = (resolve_config("DYNATRACE_API_URL") or os.getenv("DYNATRACE_API_URL") or "").rstrip("/")
        self.api_token = resolve_config("DYNATRACE_API_TOKEN") or os.getenv("DYNATRACE_API_TOKEN", "")
        if not self.api_url or not self.api_token:
            logging.warning("DYNATRACE_API_URL or DYNATRACE_API_TOKEN not set, DynatraceObserve running in dry-run mode.")

    async def emit_event(self, event: dict) -> dict:
        payload = {
            "event.type": "dash.mission",
            "event.provider": "dash-agent",
            **event,
        }

        if not self.api_url or not self.api_token:
            return {"ok": True, "mode": "dry-run", "payload": payload}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/v2/bizevents/ingest",
                    json=[payload],
                    headers={
                        "Authorization": f"Api-Token {self.api_token}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                return {"ok": True, "status": response.status_code}
        except Exception as exc:
            logging.error("DynatraceObserve emit_event error: %s", exc)
            return {"ok": False, "error": str(exc)}
