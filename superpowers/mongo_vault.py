from .mcp_client import MCPClient

class MongoVault:
    """
    Dash-1: MongoDB Mission Vault Integration
    Powers the secure storage of deconstructed DOM paths and user preferences.
    """
    def __init__(self):
        self.client = MCPClient("mongodb")

    async def register_user(self, user_id, profile):
        """Creates the user's Mission Vault profile."""
        return await self.client.call_tool("insert_document", {
            "collection": "users",
            "document": {
                "user_id": user_id,
                "profile": profile,
                "consent": {
                    "raw_passwords_stored": False,
                    "credential_storage": "authorized_reference_only",
                    "context_sources": profile.get("authorized_sources", []),
                },
                "created_at": "ISO8601",
                "updated_at": "ISO8601"
            }
        })

    async def store_context_source(self, user_id, source):
        """Stores one consented data source for future missions."""
        return await self.client.call_tool("insert_document", {
            "collection": "context_sources",
            "document": {
                "user_id": user_id,
                "source": source,
                "raw_secret_material": False,
                "created_at": "ISO8601"
            }
        })

    async def store_authorized_account_ref(self, user_id, service_name, reference):
        """Stores a non-secret account/session reference for a connected service."""
        return await self.client.call_tool("insert_document", {
            "collection": "account_refs",
            "document": {
                "user_id": user_id,
                "service_name": service_name,
                "reference": reference,
                "raw_secret_material": False,
                "created_at": "ISO8601"
            }
        })
        
    async def store_mission_state(self, mission_id, state):
        """Syncs the current background execution state to the vault."""
        return await self.client.call_tool("insert_document", {
            "collection": "mission_vault",
            "document": {
                "mission_id": mission_id,
                "state": state,
                "timestamp": "ISO8601"
            }
        })

    async def get_user_creds(self, user_id):
        """Retrieves encrypted credentials for autonomous form filling."""
        return await self.client.call_tool("find_document", {
            "collection": "secure_creds",
            "filter": {"user_id": user_id}
        })

    async def get_registration_profile(self, user_id):
        """Retrieves non-printed profile fields for the GitLab registration demo."""
        return await self.client.call_tool("find_document", {
            "collection": "registration_profiles",
            "filter": {"user_id": user_id},
            "projection": {
                "first_name": 1,
                "last_name": 1,
                "username": 1,
                "email": 1
            }
        })

    async def get_context_source(self, user_id: str, provider: str) -> dict:
        """Retrieves a stored context source (e.g. Google OAuth refresh token) for a user."""
        return await self.client.call_tool("find_document", {
            "collection": "context_sources",
            "filter": {"user_id": user_id, "source.provider": provider},
        })

