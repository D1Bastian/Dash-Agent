import os
import logging

try:
    from elasticsearch import AsyncElasticsearch
except ImportError:
    AsyncElasticsearch = None

class ElasticSearch:
    """
    Dash-1: Elastic Action Search
    Powers the millisecond retrieval of previously solved DOM structures.
    """
    def __init__(self):
        self.cloud_id = os.getenv("ELASTIC_CLOUD_ID")
        self.api_key = os.getenv("ELASTIC_API_KEY")
        if self.cloud_id and self.api_key and AsyncElasticsearch:
            self.client = AsyncElasticsearch(
                cloud_id=self.cloud_id,
                api_key=self.api_key,
            )
        else:
            self.client = None
            logging.warning("ELASTIC_CLOUD_ID not set or elasticsearch not installed, ElasticSearch running in dry-run mode.")

    async def find_dom_pattern(self, url, element_name):
        """Searches the global index for the most resilient selector for a given element."""
        if not self.client:
            return {"ok": True, "mode": "dry-run", "url": url, "element_name": element_name}
        
        try:
            response = await self.client.search(
                index="deconstructed_dom_v2",
                query={
                    "query_string": {
                        "query": f"url:{url} AND name:{element_name}"
                    }
                }
            )
            hits = response.get("hits", {}).get("hits", [])
            if hits:
                return hits[0].get("_source", {})
            return None
        except Exception as e:
            logging.error(f"ElasticSearch error: {e}")
            return {"ok": False, "error": str(e)}
