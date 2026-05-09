from mcp_client import MCPClient

class ElasticSearch:
    """
    Dash-1: Elastic Action Search
    Powers the millisecond retrieval of previously solved DOM structures.
    """
    def __init__(self):
        self.client = MCPClient("elastic")

    async def find_dom_pattern(self, url, element_name):
        """Searches the global index for the most resilient selector for a given element."""
        return await self.client.call_tool("search_elements", {
            "query": f"url:{url} AND name:{element_name}",
            "index": "deconstructed_dom_v2"
        })
