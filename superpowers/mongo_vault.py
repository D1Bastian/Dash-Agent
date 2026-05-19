import os
from datetime import datetime, timezone
import logging

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    AsyncIOMotorClient = None

class MongoVault:
    """
    Dash-1: MongoDB Mission Vault Integration
    Powers the secure storage of deconstructed DOM paths and user preferences.
    """
    def __init__(self):
        self.uri = os.getenv("MONGO_URI")
        if self.uri and AsyncIOMotorClient:
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client.get_database("dash_agent")
        else:
            self.client = None
            self.db = None
            logging.warning("MONGO_URI not set or motor not installed, MongoVault running in dry-run mode.")

    def _utc_now(self):
        return datetime.now(timezone.utc).isoformat()

    async def _insert(self, collection_name: str, document: dict) -> dict:
        if not self.db:
            return {"ok": True, "mode": "dry-run", "collection": collection_name, "document": document}
        
        result = await self.db[collection_name].insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document

    async def _find(self, collection_name: str, filter_query: dict, projection: dict = None) -> list:
        if not self.db:
            return [{"ok": True, "mode": "dry-run", "collection": collection_name, "filter": filter_query}]
        
        cursor = self.db[collection_name].find(filter_query, projection)
        results = []
        for doc in await cursor.to_list(length=100):
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def register_user(self, user_id, profile):
        """Creates the user's Mission Vault profile."""
        document = {
            "user_id": user_id,
            "profile": profile,
            "consent": {
                "raw_passwords_stored": False,
                "credential_storage": "authorized_reference_only",
                "context_sources": profile.get("authorized_sources", []),
            },
            "created_at": self._utc_now(),
            "updated_at": self._utc_now()
        }
        return await self._insert("users", document)

    async def store_context_source(self, user_id, source):
        """Stores one consented data source for future missions."""
        document = {
            "user_id": user_id,
            "source": source,
            "raw_secret_material": False,
            "created_at": self._utc_now()
        }
        return await self._insert("context_sources", document)

    async def store_authorized_account_ref(self, user_id, service_name, reference):
        """Stores a non-secret account/session reference for a connected service."""
        document = {
            "user_id": user_id,
            "service_name": service_name,
            "reference": reference,
            "raw_secret_material": False,
            "created_at": self._utc_now()
        }
        return await self._insert("account_refs", document)
        
    async def store_mission_state(self, mission_id, state):
        """Syncs the current background execution state to the vault."""
        document = {
            "mission_id": mission_id,
            "state": state,
            "timestamp": self._utc_now()
        }
        return await self._insert("mission_vault", document)

    async def get_user_creds(self, user_id):
        """Retrieves encrypted credentials for autonomous form filling."""
        return await self._find("secure_creds", {"user_id": user_id})

    async def get_registration_profile(self, user_id):
        """Retrieves non-printed profile fields for the GitLab registration demo."""
        return await self._find("registration_profiles", 
            {"user_id": user_id},
            {"first_name": 1, "last_name": 1, "username": 1, "email": 1}
        )

    async def get_context_source(self, user_id: str, provider: str) -> dict:
        """Retrieves a stored context source (e.g. Google OAuth refresh token) for a user."""
        return await self._find("context_sources", {"user_id": user_id, "source.provider": provider})
