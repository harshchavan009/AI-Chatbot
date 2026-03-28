from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logging import logger
from types import SimpleNamespace
import asyncio

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {} # Simple in-memory storage: id -> document

    async def find_one(self, query):
        id_val = query.get("id")
        if id_val and id_val in self.data:
            return self.data.get(id_val)
        
        # General search fallback
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
        # 1. Try to find existing doc
        found_id = query.get("id")
        if found_id and found_id not in self.data:
            found_id = None # Reset if id in query doesn't exist yet
            
        if not found_id:
            for d_id, d_val in self.data.items():
                match = True
                for k, v in query.items():
                    if d_val.get(k) != v:
                        match = False
                        break
                if match:
                    found_id = d_id
                    break
        
        # 2. If not found and upsert, create new with random ID (or use ID from query if provided)
        if not found_id:
            if upsert:
                # Use query ID if provided, otherwise random uuid
                target_id = query.get("id") or str(uuid.uuid4()) if 'uuid' in locals() else query.get("id") or str(__import__('uuid').uuid4())
                self.data[target_id] = {"id": target_id}
                found_id = target_id
                if "$setOnInsert" in update:
                    self.data[found_id].update(update["$setOnInsert"])
            else:
                return SimpleNamespace(modified_count=0, upserted_id=None)
        
        doc = self.data[found_id]
        
        # 3. Apply updates
        if "$push" in update:
            for field, value in update["$push"].items():
                if field not in doc or not isinstance(doc[field], list):
                    doc[field] = []
                # Ensure it's a list before appending
                doc[field].append(value)
        
        if "$set" in update:
            doc.update(update["$set"])
            
        return SimpleNamespace(modified_count=1, upserted_id=found_id)

    async def insert_one(self, document):
        if "_id" not in document:
            import uuid
            document["_id"] = str(uuid.uuid4())
        
        # Keep internal 'id' for backward compat with MockCollection find logic
        if "id" not in document:
            document["id"] = document["_id"]
            
        self.data[document["id"]] = document
        return SimpleNamespace(inserted_id=document["_id"])

    def find(self, query=None):
        if not query:
            results = list(self.data.values())
        else:
            username = query.get("username")
            results = [doc for doc in self.data.values() if not username or doc.get("username") == username]
        
        class MockCursor:
            def __init__(self, data):
                self.data = data
                self.index = 0
            def sort(self, field, direction):
                # Simple sort by field if needed, but not implemented for mock
                return self
            def limit(self, n):
                self.data = self.data[:n]
                return self
            def __aiter__(self):
                return self
            async def __anext__(self):
                if self.index >= len(self.data):
                    raise StopAsyncIteration
                val = self.data[self.index]
                self.index += 1
                return val
        
        return MockCursor(results)

    async def delete_many(self, query):
        id_val = query.get("id")
        username = query.get("username")
        if id_val in self.data and self.data[id_val].get("username") == username:
            del self.data[id_val]
            return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    async def count_documents(self, filter=None):
        if not filter:
            return len(self.data)
        # Simple filter support for username
        username = filter.get("username")
        if username:
            return len([doc for doc in self.data.values() if doc.get("username") == username])
        return len(self.data)

class MockDB:
    def __init__(self):
        self.users = MockCollection("users")
        self.conversations = MockCollection("conversations")
        self.messages = MockCollection("messages")
        self.searches = MockCollection("searches")

class Database:
    client: AsyncIOMotorClient = None
    db = None
    is_mock: bool = False
    users = None
    conversations = None
    messages = None
    searches = None

    async def connect_to_storage(self):
        """
        Create database connection on startup with fallback.
        """
        try:
            MONGODB_URL = settings.MONGODB_URL
            logger.info(f"Attempting to connect to MongoDB at {MONGODB_URL}...")
            self.client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=2000)
            # Verify connection
            await self.client.admin.command('ping')
            self.db = self.client.get_database("ai_chatbot")
            self.users = self.db.users
            self.conversations = self.db.conversations
            self.messages = self.db.messages
            self.searches = self.db.searches
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {str(e)}. Falling back to in-memory storage.")
            self.db = MockDB()
            self.is_mock = True
            self.users = self.db.users
            self.conversations = self.db.conversations
            self.messages = self.db.messages
            self.searches = self.db.searches

    async def close_storage_connection(self):
        """
        Close database connection on shutdown.
        """
        if self.client and not self.is_mock:
            self.client.close()
            logger.info("Closed MongoDB connection")

db = Database()
