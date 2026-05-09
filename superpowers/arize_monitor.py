from .mcp_client import MCPClient

class ArizeMonitor:
    """
    Dash-1: Arize Reasoning Observability
    Monitors the Gemini reasoning traces and provides guardrail verification.
    """
    def __init__(self):
        self.client = MCPClient("arize")

    async def log_reasoning_trace(self, mission_id, reasoning_steps):
        """Logs the agent's multi-step plan to Arize for observability."""
        return await self.client.call_tool("log_trace", {
            "model_id": "gemini-3",
            "mission_id": mission_id,
            "trace": reasoning_steps
        })

    async def verify_guardrails(self, action):
        """Ensures the background action complies with safety protocols."""
        return await self.client.call_tool("check_guardrail", {
            "action": action
        })
