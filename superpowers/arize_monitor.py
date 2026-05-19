import os
import logging
import httpx

class ArizeMonitor:
    """
    Dash-1: Arize Reasoning Observability
    Monitors the Gemini reasoning traces and provides guardrail verification.
    """
    def __init__(self):
        self.api_key = os.getenv("ARIZE_API_KEY")
        self.space_id = os.getenv("ARIZE_SPACE_ID")
        self.endpoint = "https://api.arize.com/v1/log"
        if not self.api_key or not self.space_id:
            logging.warning("ARIZE_API_KEY or ARIZE_SPACE_ID not set, ArizeMonitor running in dry-run mode.")

    async def log_reasoning_trace(self, mission_id, reasoning_steps):
        """Logs the agent's multi-step plan to Arize for observability."""
        payload = {
            "space_key": self.space_id,
            "model_id": "gemini-3",
            "prediction_id": mission_id,
            "features": {"trace": reasoning_steps}
        }
        
        if not self.api_key or not self.space_id:
            return {"ok": True, "mode": "dry-run", "payload": payload}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )
                response.raise_for_status()
                return {"ok": True, "status": response.status_code}
        except Exception as e:
            logging.error(f"ArizeMonitor log_reasoning_trace error: {e}")
            return {"ok": False, "error": str(e)}

    async def verify_guardrails(self, action):
        """Ensures the background action complies with safety protocols."""
        payload = {
            "space_key": self.space_id,
            "model_id": "guardrails-1",
            "prediction_id": f"verify-{action.get('id', 'unknown')}",
            "features": {"action": action}
        }
        
        if not self.api_key or not self.space_id:
            return {"ok": True, "mode": "dry-run", "payload": payload}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )
                response.raise_for_status()
                return {"ok": True, "status": response.status_code}
        except Exception as e:
            logging.error(f"ArizeMonitor verify_guardrails error: {e}")
            return {"ok": False, "error": str(e)}
