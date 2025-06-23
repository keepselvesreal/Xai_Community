from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging
from config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """MongoDB에 연결합니다."""
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_url)
        db.database = db.client[settings.database_name]
        
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """MongoDB 연결을 종료합니다."""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")

async def init_database():
    """데이터베이스와 Beanie ODM을 초기화합니다."""
    try:
        await init_beanie(
            database=db.database,
            document_models=[]  # 모델들을 여기에 추가할 예정
        )
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_database():
    """데이터베이스 인스턴스를 반환합니다."""
    return db.database