"""MongoDB connection and client management."""
from motor.motor_asyncio import AsyncClient, AsyncDatabase
from app.config import settings


class MongoConnection:
    """Async MongoDB connection manager."""

    client: AsyncClient | None = None
    db: AsyncDatabase | None = None

    async def connect(self):
        """Connect to MongoDB replica set."""
        uri = self._build_uri()
        self.client = AsyncClient(uri)
        self.db = self.client[settings.MONGO_DB]
        print(f"Connected to MongoDB: {settings.MONGO_DB}")

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def _build_uri(self) -> str:
        """Build MongoDB connection URI."""
        hosts = settings.MONGO_HOSTS
        user = settings.MONGO_USER
        password = settings.MONGO_PASSWORD
        auth_source = settings.MONGO_AUTH_SOURCE
        replica_set = settings.MONGO_REPLICA_SET

        return (
            f"mongodb+srv://{user}:{password}@{hosts}/"
            f"{settings.MONGO_DB}?authSource={auth_source}&replicaSet={replica_set}&ssl=true"
        )


mongo_db = MongoConnection()
