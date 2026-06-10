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
        from backend.config import resolve_config
        self.cloud_id = resolve_config("ELASTIC_CLOUD_ID") or os.getenv("ELASTIC_CLOUD_ID")
        self.api_key = resolve_config("ELASTIC_API_KEY") or os.getenv("ELASTIC_API_KEY")
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

    async def get_solved_actions(self, url: str):
        """Retrieves previously solved DOM mapping actions for a given URL."""
        if not self.client:
            return None
            
        try:
            response = await self.client.search(
                index="solved_missions",
                query={
                    "term": {
                        "url.keyword": url
                    }
                }
            )
            hits = response.get("hits", {}).get("hits", [])
            if hits:
                return hits[0].get("_source", {}).get("actions", [])
            return None
        except Exception as e:
            logging.error(f"ElasticSearch get_solved_actions error: {e}")
            return None

    async def save_solved_actions(self, url: str, actions: list):
        """Saves a successfully executed JSON action mapping to Elastic Search."""
        if not self.client:
            return
            
        try:
            await self.client.index(
                index="solved_missions",
                document={
                    "url": url,
                    "actions": actions
                }
            )
        except Exception as e:
            logging.error(f"ElasticSearch save_solved_actions error: {e}")
