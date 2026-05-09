import os

from .mcp_client import MCPClient


class GitLabSync:
    """
    GitLab Mission Sync.

    The first hackathon video uses GitLab as the partner track: after the
    browser registration checkpoint succeeds, Dash provisions a mission
    repository and writes the mission script through GitLab MCP tools.
    """

    def __init__(self):
        self.client = MCPClient("gitlab")

    async def create_mission_repository(self, username: str):
        """Creates the repo used as the mission audit trail."""
        safe_username = username.replace(" ", "-").lower() or "demo-user"
        return await self.client.call_tool("create_repository", {
            "name": f"dash-mission-log-{safe_username}",
            "description": "Dash Agent GitLab registration mission audit trail.",
            "initialize_with_readme": True,
            "visibility": "private"
        })

    async def push_mission_script(self, project_id, script_content, branch: str = "main"):
        """Versions the latest deconstructed DOM mission script to GitLab."""
        mission_id = os.getenv("MISSION_ID", "gitlab-registration")
        return await self.client.call_tool("create_or_update_file", {
            "project_id": project_id,
            "file_path": f"missions/{mission_id}.py",
            "content": script_content,
            "commit_message": "Dash Agent: sync GitLab registration mission",
            "branch": branch
        })
