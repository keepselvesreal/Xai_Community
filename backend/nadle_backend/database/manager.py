from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from typing import List, Dict, Any
import logging

# Import settings for dynamic collection names
from ..config import settings

logger = logging.getLogger(__name__)


class IndexManager:
    """Manages MongoDB collection indexes for performance optimization."""
    
    @staticmethod
    def get_user_indexes() -> List[IndexModel]:
        """
        Get index definitions for users collection.
        
        Returns:
            List of IndexModel instances for users collection
        """
        return [
            # Unique email index
            IndexModel(
                [("email", ASCENDING)],
                unique=True,
                name="email_unique_idx"
            ),
            # Index for user handle (username)
            IndexModel(
                [("handle", ASCENDING)],
                unique=True,
                sparse=True,
                name="handle_unique_idx"
            ),
            # Compound index for status and created_at (for queries)
            IndexModel(
                [("status", ASCENDING), ("created_at", DESCENDING)],
                name="status_created_idx"
            ),
            # Text search index for user search
            IndexModel(
                [("name", TEXT), ("bio", TEXT)],
                name="user_text_search_idx",
                weights={"name": 10, "bio": 5}
            )
        ]
    
    @staticmethod
    def get_post_indexes() -> List[IndexModel]:
        """
        Get index definitions for posts collection.
        
        Returns:
            List of IndexModel instances for posts collection
        """
        return [
            # Unique slug index
            IndexModel(
                [("slug", ASCENDING)],
                unique=True,
                name="slug_unique_idx"
            ),
            # Author and created date compound index
            IndexModel(
                [("author_id", ASCENDING), ("created_at", DESCENDING)],
                name="author_created_idx"
            ),
            # Service and status compound index
            IndexModel(
                [("service", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="service_status_created_idx"
            ),
            # Text search index for content
            IndexModel(
                [("title", TEXT), ("content", TEXT), ("tags", TEXT)],
                name="post_text_search_idx",
                weights={"title": 10, "tags": 5, "content": 3}
            ),
            # Index for published posts
            IndexModel(
                [("status", ASCENDING), ("published_at", DESCENDING)],
                name="published_posts_idx",
                partialFilterExpression={"status": "published"}
            ),
            
            # 🚀 SSR 페이지 최적화를 위한 메타데이터 타입별 인덱스
            # 정보/서비스/팁 페이지용 (metadata.type + status + created_at)
            IndexModel(
                [("metadata.type", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="metadata_type_status_created_idx"
            ),
            
            # 메타데이터 타입별 빠른 조회용 (metadata.type + created_at)
            IndexModel(
                [("metadata.type", ASCENDING), ("created_at", DESCENDING)],
                name="metadata_type_created_idx"
            ),
            
            # 메타데이터 타입별 view_count 정렬용 (인기순 정렬 지원)
            IndexModel(
                [("metadata.type", ASCENDING), ("status", ASCENDING), ("view_count", DESCENDING)],
                name="metadata_type_status_views_idx"
            ),
            
            # 메타데이터 타입별 like_count 정렬용 (추천순 정렬 지원)
            IndexModel(
                [("metadata.type", ASCENDING), ("status", ASCENDING), ("like_count", DESCENDING)],
                name="metadata_type_status_likes_idx"
            )
        ]
    
    @staticmethod
    def get_comment_indexes() -> List[IndexModel]:
        """
        Get index definitions for comments collection.
        
        Returns:
            List of IndexModel instances for comments collection
        """
        return [
            # Parent ID index for fetching comments
            IndexModel(
                [("parent_id", ASCENDING), ("created_at", ASCENDING)],
                name="parent_comments_idx"
            ),
            # Author index
            IndexModel(
                [("author_id", ASCENDING), ("created_at", DESCENDING)],
                name="author_comments_idx"
            ),
            # Parent comment index for threaded comments
            IndexModel(
                [("parent_id", ASCENDING)],
                sparse=True,
                name="parent_comment_idx"
            ),
            # Text search for comment content
            IndexModel(
                [("content", TEXT)],
                name="comment_text_search_idx"
            )
        ]
    
    @staticmethod
    def get_reaction_indexes() -> List[IndexModel]:
        """
        Get index definitions for reactions collection.
        
        Returns:
            List of IndexModel instances for reactions collection
        """
        return [
            # Unique constraint: one reaction per user per target
            IndexModel(
                [("user_id", ASCENDING), ("target_id", ASCENDING), ("target_type", ASCENDING)],
                unique=True,
                name="user_target_unique_idx"
            ),
            # Target queries (get all reactions for a post/comment)
            IndexModel(
                [("target_id", ASCENDING), ("target_type", ASCENDING), ("reaction_type", ASCENDING)],
                name="target_reactions_idx"
            ),
            # User reactions query
            IndexModel(
                [("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="user_reactions_idx"
            )
        ]
    
    @staticmethod
    def get_stats_indexes() -> List[IndexModel]:
        """
        Get index definitions for stats collection.
        
        Returns:
            List of IndexModel instances for stats collection
        """
        return [
            # Unique constraint: one stat document per entity
            IndexModel(
                [("entity_id", ASCENDING), ("entity_type", ASCENDING)],
                unique=True,
                name="entity_stats_unique_idx"
            ),
            # Query by type and metrics
            IndexModel(
                [("entity_type", ASCENDING), ("view_count", DESCENDING)],
                name="type_views_idx"
            ),
            # Last updated index for cache management
            IndexModel(
                [("last_updated", DESCENDING)],
                name="stats_updated_idx"
            )
        ]
    
    @staticmethod
    async def create_all_indexes(db: AsyncIOMotorDatabase) -> Dict[str, List[str]]:
        """
        Create all indexes for all collections.
        
        Args:
            db: MongoDB database instance
            
        Returns:
            Dictionary mapping collection names to list of created index names
        """
        index_definitions = {
            settings.users_collection: IndexManager.get_user_indexes(),
            settings.posts_collection: IndexManager.get_post_indexes(),
            settings.comments_collection: IndexManager.get_comment_indexes(),
            settings.user_reactions_collection: IndexManager.get_reaction_indexes(),
            settings.stats_collection: IndexManager.get_stats_indexes()
        }
        
        created_indexes = {}
        
        for collection_name, indexes in index_definitions.items():
            if not indexes:
                continue
                
            collection = db[collection_name]
            
            try:
                # Create indexes
                created = await collection.create_indexes(indexes)
                created_indexes[collection_name] = created
                
                logger.info(f"Created {len(created)} indexes for {collection_name} collection")
                
            except Exception as e:
                logger.error(f"Failed to create indexes for {collection_name}: {str(e)}")
                raise
        
        return created_indexes
    
    @staticmethod
    async def drop_all_indexes(db: AsyncIOMotorDatabase) -> None:
        """
        Drop all indexes except _id index.
        
        Args:
            db: MongoDB database instance
        """
        collections = [
            settings.users_collection, 
            settings.posts_collection, 
            settings.comments_collection, 
            settings.user_reactions_collection, 
            settings.stats_collection
        ]
        
        for collection_name in collections:
            collection = db[collection_name]
            
            try:
                # Drop all indexes except the default _id index
                await collection.drop_indexes()
                logger.info(f"Dropped indexes for {collection_name} collection")
                
            except Exception as e:
                logger.error(f"Failed to drop indexes for {collection_name}: {str(e)}")
                raise
    
    @staticmethod
    async def get_index_info(db: AsyncIOMotorDatabase, collection_name: str) -> List[Dict[str, Any]]:
        """
        Get information about existing indexes for a collection.
        
        Args:
            db: MongoDB database instance
            collection_name: Name of the collection
            
        Returns:
            List of index information dictionaries
        """
        collection = db[collection_name]
        indexes = await collection.list_indexes().to_list(None)
        return indexes
    
    @staticmethod
    async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
        """
        Ensure all required indexes exist, creating them if necessary.
        This is safe to call multiple times.
        
        Args:
            db: MongoDB database instance
        """
        await IndexManager.create_all_indexes(db)
        logger.info("All database indexes have been ensured")