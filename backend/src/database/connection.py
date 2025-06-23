from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
import logging
from typing import Optional, List, Type
from beanie import Document

from ..config import settings

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self._is_connected: bool = False
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected
    
    async def connect(self) -> None:
        """
        Establish connection to MongoDB Atlas.
        Uses connection pooling with optimized settings.
        """
        try:
            # Create Motor client with simple configuration (matching working v4 project)
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000
            )
            
            # Get database instance
            self.database = self.client[settings.database_name]
            
            # Verify connection with ismaster (matching working v4 project)
            await self.client.admin.command('ismaster')
            
            self._is_connected = True
            logger.info(f"Successfully connected to MongoDB Atlas: {settings.database_name}")
            
        except Exception as e:
            # Clean up on failure
            self.client = None
            self.database = None
            self._is_connected = False
            
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self._is_connected = False
            logger.info("MongoDB connection closed")
    
    async def ping(self) -> bool:
        """
        Check if the database connection is alive.
        Returns True if connection is healthy, False otherwise.
        """
        if not self.client:
            return False
        
        try:
            await self.client.admin.command('ismaster')
            return True
        except Exception as e:
            logger.warning(f"Database ping failed: {str(e)}")
            return False
    
    async def init_beanie_models(self, document_models: List[Type[Document]]) -> None:
        """
        Initialize Beanie ODM with document models.
        
        Args:
            document_models: List of Beanie Document classes
        """
        if not self.database:
            raise RuntimeError("Database not connected")
        
        try:
            await init_beanie(
                database=self.database,
                document_models=document_models
            )
            logger.info(f"Initialized Beanie with {len(document_models)} models")
        except Exception as e:
            logger.error(f"Failed to initialize Beanie: {str(e)}")
            raise
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """
        Get the database instance.
        
        Returns:
            AsyncIOMotorDatabase instance
            
        Raises:
            RuntimeError: If database is not connected
        """
        if not self.database:
            raise RuntimeError("Database not connected")
        return self.database
    
    def get_client(self) -> AsyncIOMotorClient:
        """
        Get the MongoDB client instance.
        
        Returns:
            AsyncIOMotorClient instance
            
        Raises:
            RuntimeError: If client is not connected
        """
        if not self.client:
            raise RuntimeError("Database client not connected")
        return self.client
    
    async def check_connection(self) -> bool:
        """
        Check and restore database connection if needed.
        
        Returns:
            True if connection is healthy or restored, False otherwise
        """
        # If not connected, try to connect
        if not self._is_connected:
            try:
                await self.connect()
                return True
            except Exception:
                return False
        
        # If connected, verify with ping
        if await self.ping():
            return True
        
        # Connection lost, try to reconnect
        logger.warning("Database connection lost, attempting to reconnect...")
        try:
            await self.disconnect()
            await self.connect()
            return await self.ping()
        except Exception as e:
            logger.error(f"Failed to restore database connection: {str(e)}")
            return False


# Global database instance
database = Database()


# Dependency functions for FastAPI
async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency to get database instance.
    Ensures connection is established.
    """
    if not database.is_connected:
        await database.connect()
    return database.get_database()


async def get_client() -> AsyncIOMotorClient:
    """
    FastAPI dependency to get MongoDB client.
    Ensures connection is established.
    """
    if not database.is_connected:
        await database.connect()
    return database.get_client()