from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logging import logger
from types import SimpleNamespace
import asyncio
import json
import os
import uuid
from datetime import datetime

class MockCollection:
    def __init__(self, name, db_instance):
        self.name = name
        self.db = db_instance
        # data is stored in the parent MockDB instance to facilitate global persistence
        if self.name not in self.db.all_data:
            self.db.all_data[self.name] = {}
        self.data = self.db.all_data[self.name]

    def _save(self):
        """Trigger a save in the parent database."""
        self.db.save_to_disk()

    async def find_one(self, query):
        # Handle simple ID lookups
        id_val = query.get("id") or query.get("_id")
        if id_val and id_val in self.data:
            return self.data.get(id_val)
        
        # General search
        for doc in self.data.values():
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    async def update_one(self, query, update, upsert=False):
        doc = await self.find_one(query)
        
        if not doc:
            if upsert:
                # Basic upsert logic
                new_id = query.get("id") or query.get("_id") or str(uuid.uuid4())
                doc = {"id": new_id, "_id": new_id}
                if "$setOnInsert" in update:
                    doc.update(update["$setOnInsert"])
                self.data[new_id] = doc
            else:
                return SimpleNamespace(modified_count=0, matched_count=0, upserted_id=None)
        
        matched_count = 1
        
        # Apply updates
        if "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
        
        if "$push" in update:
            for field, value in update["$push"].items():
                if field not in doc or not isinstance(doc[field], list):
                    doc[field] = []
                doc[field].append(value)
        
        self._save()
        return SimpleNamespace(modified_count=1, matched_count=matched_count, upserted_id=doc.get("id"))

    async def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        if "id" not in document:
            document["id"] = document["_id"]
            
        self.data[document["_id"]] = document
        self._save()
        return SimpleNamespace(inserted_id=document["_id"])

    def find(self, query=None):
        if not query:
            results = list(self.data.values())
        else:
            results = []
            for doc in self.data.values():
                match = True
                for k, v in query.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    results.append(doc)
        
        return MockCursor(results)

    async def delete_many(self, query):
        to_delete = []
        for doc_id, doc in self.data.items():
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                to_delete.append(doc_id)
        
        deleted_count = 0
        for doc_id in to_delete:
            del self.data[doc_id]
            deleted_count += 1
            
        if deleted_count > 0:
            self._save()
        return SimpleNamespace(deleted_count=deleted_count)

    async def count_documents(self, filter=None):
        if not filter:
            return len(self.data)
        
        count = 0
        for doc in self.data.values():
            match = True
            for k, v in filter.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count

class MockCursor:
    def __init__(self, data):
        self._data = data
        self._index = 0

    def sort(self, field, direction=-1):
        def sort_key(doc):
            val = doc.get(field)
            if isinstance(val, datetime):
                return val.timestamp()
            if isinstance(val, str):
                try:
                    # Try to parse ISO format strings
                    return datetime.fromisoformat(val).timestamp()
                except:
                    return val
            return val or 0

        self._data.sort(key=sort_key, reverse=(direction == -1))
        return self

    def limit(self, n):
        self._data = self._data[:n]
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._data):
            raise StopAsyncIteration
        val = self._data[self._index]
        self._index += 1
        return val

class MockDB:
    def __init__(self, storage_path="mock_db.json"):
        self.storage_path = storage_path
        self.all_data = {}
        self.load_from_disk()
        
        self.users = MockCollection("users", self)
        self.conversations = MockCollection("conversations", self)
        self.messages = MockCollection("messages", self)
        self.searches = MockCollection("searches", self)
        self.fast_cache = MockCollection("fast_cache", self)

    def load_from_disk(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.all_data = json.load(f)
                logger.info(f"Loaded MockDB from {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to load MockDB: {e}")
                self.all_data = {}
        else:
            self.all_data = {}

    def save_to_disk(self):
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.all_data, f, default=str)
        except Exception as e:
            logger.error(f"Failed to save MockDB: {e}")

class Database:
    client: AsyncIOMotorClient = None
    db = None
    is_mock: bool = False
    users = None
    conversations = None
    messages = None
    searches = None
    fast_cache = None

    def _switch_to_mock(self, reason: str):
        """Helper to switch to persistent mock storage with clean logging."""
        logger.info(f"System: {reason}. Switching to Adaptive Local Storage (Persistent).")
        self.db = MockDB(storage_path="data/mock_db.json")
        self.is_mock = True
        self.users = self.db.users
        self.conversations = self.db.conversations
        self.messages = self.db.messages
        self.searches = self.db.searches
        self.fast_cache = self.db.fast_cache

    async def connect_to_storage(self):
        """
        Create database connection on startup with adaptive fallback.
        """
        # 1. Check for explicit mock override
        if settings.USE_MOCK_STORAGE:
            self._switch_to_mock("USE_MOCK_STORAGE enabled")
            return

        try:
            MONGODB_URL = settings.MONGODB_URL
            
            # 2. Adaptive timeout for local environments
            is_local = "localhost" in MONGODB_URL or "127.0.0.1" in MONGODB_URL
            timeout = 500 if is_local else 5000 # 500ms for local, 5s for Cloud
            
            if is_local:
                logger.info("Detecting local environment... (Fast Check)")
            else:
                logger.info(f"Connecting to Cloud MongoDB at {MONGODB_URL[:20]}...")

            self.client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=timeout)
            
            # 3. Fast verification ping
            await self.client.admin.command('ping')
            
            self.db = self.client.get_database(settings.DATABASE_NAME)
            self.users = self.db.users
            self.conversations = self.db.conversations
            self.messages = self.db.messages
            self.searches = self.db.searches
            self.fast_cache = self.db.fast_cache
            self.is_mock = False
            logger.info("Successfully connected to MongoDB.")
            
        except Exception as e:
            reason = "Local MongoDB not found" if "localhost" in settings.MONGODB_URL else f"Cloud connection failed: {str(e)}"
            self._switch_to_mock(reason)

    async def close_storage_connection(self):
        if self.client and not self.is_mock:
            self.client.close()
            logger.info("Closed MongoDB connection")

db = Database()
