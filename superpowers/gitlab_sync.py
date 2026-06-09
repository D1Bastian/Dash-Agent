import httpx
import logging

class GitLabSync:
    """
    Dash-1: GitLab API Sync Integration
    Automates repository and CI/CD setup via the GitLab API.
    """
    def __init__(self):
        self.api_url = "https://gitlab.com/api/v4"

    async def create_repository(self, token: str, name: str, description: str = "Dash Agent Mission Vault", visibility: str = "public") -> dict:
        """Creates a new repository on GitLab."""
        url = f"{self.api_url}/projects"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "name": name,
            "description": description,
            "visibility": visibility
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                return {
                    "ok": True,
                    "project_id": data.get("id"),
                    "repo_url": data.get("web_url")
                }
        except httpx.HTTPStatusError as e:
            logging.error(f"GitLab API Error: {e.response.text}")
            return {"ok": False, "error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logging.error(f"GitLabSync error: {str(e)}")
            return {"ok": False, "error": str(e)}
