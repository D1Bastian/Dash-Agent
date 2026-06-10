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
        from backend.config import resolve_config
        self.uri = resolve_config("MONGO_URI") or os.getenv("MONGO_URI")
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
        if self.db is None:
            return {"ok": True, "mode": "dry-run", "collection": collection_name, "document": document}

        result = await self.db[collection_name].insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document

    async def _find(self, collection_name: str, filter_query: dict, projection: dict = None) -> list:
        if self.db is None:
            return [{"ok": True, "mode": "dry-run", "collection": collection_name, "filter": filter_query}]

        cursor = self.db[collection_name].find(filter_query, projection)
        results = []
        for doc in await cursor.to_list(length=100):
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def register_user(self, user_id, profile):
        """Creates or updates the user's Mission Vault profile."""
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
        if self.db is None:
            return {"ok": True, "mode": "dry-run", "collection": "users", "document": document}

        await self.db["users"].update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "profile": profile,
                    "consent": document["consent"],
                    "updated_at": document["updated_at"],
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": document["created_at"],
                },
            },
            upsert=True,
        )
        saved = await self.db["users"].find_one({"user_id": user_id})
        saved["_id"] = str(saved["_id"])
        return saved

    async def store_context_source(self, user_id, source):
        """Stores one consented data source for future missions."""
        document = {
            "user_id": user_id,
            "source": source,
            "raw_secret_material": False,
            "created_at": self._utc_now()
        }
        if self.db is None:
            return {"ok": True, "mode": "dry-run", "collection": "context_sources", "document": document}

        provider = source.get("provider", "manual")
        await self.db["context_sources"].update_one(
            {"user_id": user_id, "source.provider": provider},
            {
                "$set": {
                    "source": source,
                    "raw_secret_material": False,
                    "updated_at": self._utc_now(),
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": document["created_at"],
                },
            },
            upsert=True,
        )
        saved = await self.db["context_sources"].find_one({"user_id": user_id, "source.provider": provider})
        saved["_id"] = str(saved["_id"])
        return saved

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
        sources = await self._find("context_sources", {"user_id": user_id, "source.provider": provider})
        if not sources or sources[0].get("mode") == "dry-run":
            return None
        return sources[0]

    async def load_user_vault(self, user_id: str) -> dict:
        """Loads user memory, consented context sources, account refs, and recent mission state."""
        if self.db is None:
            return {
                "mode": "dry-run",
                "user": {},
                "memory": {
                    "context_sources": [],
                    "account_refs": [],
                    "recent_missions": [],
                },
            }

        user = await self.db["users"].find_one({"user_id": user_id}) or {}
        if user.get("_id"):
            user["_id"] = str(user["_id"])

        context_sources = await self._find(
            "context_sources",
            {"user_id": user_id},
            {"source.refresh_token": 0, "source.token": 0, "source.secret": 0},
        )
        account_refs = await self._find("account_refs", {"user_id": user_id})
        mission_cursor = self.db["mission_vault"].find(
            {"mission_id": {"$regex": f"-{user_id}($|-)"}}).sort("timestamp", -1).limit(10)
        recent_missions = []
        for mission in await mission_cursor.to_list(length=10):
            mission["_id"] = str(mission["_id"])
            recent_missions.append(mission)

        return {
            "user": user.get("profile", {}),
            "memory": {
                "consent": user.get("consent", {}),
                "context_sources": context_sources,
                "account_refs": account_refs,
                "recent_missions": recent_missions,
            },
        }
