from mcp_client import MCPClient

class FivetranPipeline:
    """
    Dash Agent-1: Fivetran Data Pipeline
    Automates the flow of mission-captured data into the user's data warehouse.
    """
    def __init__(self):
        self.client = MCPClient("fivetran")

    async def stream_mission_data(self, mission_id, captured_data):
        """Streams mission results (e.g., flight price trends) for long-term analytics."""
        return await self.client.call_tool("sync_connector", {
            "connector_id": "mission_results_pipeline",
            "data": {
                "mission_id": mission_id,
                "data": captured_data
            }
        })
