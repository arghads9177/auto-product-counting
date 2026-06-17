"""MongoDB connection and client management."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings


class MongoConnection:
    """Async MongoDB connection manager."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        uri = self._build_uri()
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[settings.MONGO_DB]
        await self.ensure_indexes()
        await self.db.command("ping")
        print(f"Connected to MongoDB: {settings.MONGO_DB}")

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("Disconnected from MongoDB")

    async def ensure_indexes(self) -> None:
        db = self.db
        await db["count_events"].create_index(
            [("camera_id", 1), ("timestamp", -1)]
        )
        await db["count_events"].create_index(
            [("session_id", 1), ("track_id", 1)],
            unique=True,
        )
        await db["sessions"].create_index(
            [("camera_id", 1), ("status", 1)]
        )
        await db["sessions"].create_index("session_id", unique=True)
        await db["activity_events"].create_index(
            [("camera_id", 1), ("timestamp", -1)]
        )
        await db["system_logs"].create_index(
            [("timestamp", -1), ("category", 1)]
        )
        await db["cameras"].create_index("camera_id", unique=True)
        await db["camera_configurations"].create_index("camera_id", unique=True)
        print("MongoDB indexes ensured")

    def _build_uri(self) -> str:
        hosts = settings.MONGO_HOSTS
        user = settings.MONGO_USER
        password = settings.MONGO_PASSWORD
        auth_source = settings.MONGO_AUTH_SOURCE
        replica_set = settings.MONGO_REPLICA_SET

        return (
            f"mongodb://{user}:{password}@{hosts}/"
            f"{settings.MONGO_DB}"
            f"?authSource={auth_source}"
            f"&replicaSet={replica_set}"
            f"&ssl=true"
            f"&tlsAllowInvalidCertificates=true"
        )


mongo_connection = MongoConnection()
