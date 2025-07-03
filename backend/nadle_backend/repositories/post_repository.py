"""Post repository for data access layer."""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import re
import uuid
from beanie import PydanticObjectId
from nadle_backend.models.core import Post, PostCreate, PostUpdate, PaginationParams, User
from nadle_backend.exceptions.post import PostNotFoundError, PostSlugAlreadyExistsError


class PostRepository:
    """Repository for post data access operations."""
    
    async def create(self, post_data: PostCreate, author_id: str) -> Post:
        """Create a new post.
        
        Args:
            post_data: Post creation data
            author_id: ID of the post author
            
        Returns:
            Created post instance
            
        Raises:
            PostSlugAlreadyExistsError: If slug already exists
        """
        # Create post document first with temporary slug
        temp_slug = "temp-" + str(uuid.uuid4())[:8]
        
        post = Post(
            title=post_data.title,
            content=post_data.content,
            service=post_data.service,
            metadata=post_data.metadata,
            slug=temp_slug,  # Temporary slug
            author_id=author_id,
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            published_at=datetime.utcnow(),
            view_count=0,
            like_count=0,
            dislike_count=0,
            comment_count=0
        )
        
        # Save to database to get the ID
        await post.save()
        
        # Now generate final slug with post ID + Korean title
        title_slug = self._generate_slug(post_data.title)
        final_slug = f"{str(post.id)}-{title_slug}"
        
        # Update the post with the final slug
        post.slug = final_slug
        await post.save()
        
        return post
    
    async def get_by_id(self, post_id: str, include_deleted: bool = False) -> Post:
        """Get post by ID.
        
        Args:
            post_id: Post ID
            include_deleted: Whether to include deleted posts (for admin operations)
            
        Returns:
            Post instance
            
        Raises:
            PostNotFoundError: If post not found
        """
        try:
            if include_deleted:
                post = await Post.get(PydanticObjectId(post_id))
            else:
                post = await Post.find_one({"_id": PydanticObjectId(post_id), "status": {"$ne": "deleted"}})
            
            if post is None:
                raise PostNotFoundError(post_id=post_id)
            return post
        except Exception:
            raise PostNotFoundError(post_id=post_id)
    
    async def get_by_slug(self, slug: str) -> Post:
        """Get post by slug.
        
        Args:
            slug: Post slug
            
        Returns:
            Post instance
            
        Raises:
            PostNotFoundError: If post not found
        """
        post = await Post.find_one({"slug": slug, "status": {"$ne": "deleted"}})
        if post is None:
            raise PostNotFoundError(slug=slug)
        return post
    
    async def update(self, post_id: str, update_data: PostUpdate) -> Post:
        """Update post.
        
        Args:
            post_id: Post ID
            update_data: Update data
            
        Returns:
            Updated post instance
            
        Raises:
            PostNotFoundError: If post not found
        """
        post = await self.get_by_id(post_id)
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            
            # If title is updated, update slug as well
            if "title" in update_dict:
                title_slug = self._generate_slug(update_dict["title"])
                new_slug = f"{str(post.id)}-{title_slug}"
                if new_slug != post.slug:
                    update_dict["slug"] = new_slug
            
            # Update post
            await post.update({"$set": update_dict})
            
            # Refresh post data
            updated_post = await self.get_by_id(post_id)
            return updated_post
        
        return post
    
    async def delete(self, post_id: str) -> bool:
        """Soft delete post (mark as deleted instead of physical deletion).
        
        Args:
            post_id: Post ID
            
        Returns:
            True if deletion successful
            
        Raises:
            PostNotFoundError: If post not found
        """
        from datetime import datetime
        
        # Include deleted posts in case we need to re-delete or handle edge cases
        post = await self.get_by_id(post_id, include_deleted=True)
        
        # Soft delete: update status to 'deleted' instead of physical deletion
        post.status = "deleted"
        post.updated_at = datetime.utcnow()
        await post.save()
        
        return True
    
    async def list_posts(
        self, 
        page: int = 1, 
        page_size: int = 20,
        service_type: Optional[str] = None,
        metadata_type: Optional[str] = None,
        author_id: Optional[str] = None,
        status: str = "published",
        sort_by: str = "created_at"
    ) -> Tuple[List[Post], int]:
        """List posts with pagination and filters.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            service_type: Filter by service type
            metadata_type: Filter by metadata type
            author_id: Filter by author ID
            status: Filter by status
            sort_by: Sort field
            
        Returns:
            Tuple of (posts list, total count)
        """
        # Build query - exclude deleted posts
        query = {"status": {"$ne": "deleted"}}
        if status != "all":
            query["status"] = status
        if service_type:
            query["service"] = service_type
        if metadata_type == "board":
            # 게시판: metadata.type이 없거나 null이거나 "board"인 경우
            query["$or"] = [
                {"metadata.type": {"$exists": False}},
                {"metadata.type": None},
                {"metadata.type": "board"}
            ]
        elif metadata_type:
            query["metadata.type"] = metadata_type
        if author_id:
            query["author_id"] = author_id
        
        # Count total
        total = await Post.find(query).count()
        
        # Get posts with pagination
        skip = (page - 1) * page_size
        sort_field = f"-{sort_by}" if sort_by in ["created_at", "updated_at", "view_count", "like_count"] else sort_by
        
        posts = await Post.find(query).sort(sort_field).skip(skip).limit(page_size).to_list()
        
        return posts, total
    
    async def search_posts(
        self,
        query: str,
        service_type: Optional[str] = None,
        metadata_type: Optional[str] = None,
        sort_by: str = "created_at",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Post], int]:
        """Search posts by text query.
        
        Args:
            query: Search query string
            service_type: Filter by service type
            sort_by: Sort field
            page: Page number
            page_size: Number of items per page
            
        Returns:
            Tuple of (posts list, total count)
        """
        # Build search query - exclude deleted posts
        search_filter = {
            "status": {"$ne": "deleted"},
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"metadata.tags": {"$in": [re.compile(query, re.IGNORECASE)]}}
            ]
        }
        
        if service_type:
            search_filter["service"] = service_type
        
        if metadata_type == "board":
            # 게시판: metadata.type이 없거나 null이거나 "board"인 경우
            # 기존 검색 조건($or)을 보존하고 새로운 조건 추가
            existing_or = search_filter.get("$or", [])
            search_filter = {
                "status": {"$ne": "deleted"},
                "$and": [
                    {"$or": existing_or},  # 기존 제목/내용/태그 검색 조건
                    {
                        "$or": [
                            {"metadata.type": {"$exists": False}},
                            {"metadata.type": None},
                            {"metadata.type": "board"}
                        ]
                    }
                ]
            }
        elif metadata_type:
            search_filter["metadata.type"] = metadata_type
        
        # Count total
        total = await Post.find(search_filter).count()
        
        # Get posts with pagination
        skip = (page - 1) * page_size
        sort_field = f"-{sort_by}" if sort_by in ["created_at", "updated_at", "view_count", "like_count"] else sort_by
        
        posts = await Post.find(search_filter).sort(sort_field).skip(skip).limit(page_size).to_list()
        
        return posts, total
    
    async def increment_view_count(self, post_id: str) -> bool:
        """Increment post view count.
        
        Args:
            post_id: Post ID
            
        Returns:
            True if successful
        """
        try:
            result = await Post.find({"_id": PydanticObjectId(post_id)}).update({"$inc": {"view_count": 1}})
            return True
        except Exception as e:
            print(f"Error incrementing view count for post {post_id}: {e}")
            return False
    
    async def increment_bookmark_count(self, post_id: str) -> bool:
        """Increment post bookmark count.
        
        Args:
            post_id: Post ID
            
        Returns:
            True if successful
        """
        try:
            result = await Post.find({"_id": PydanticObjectId(post_id)}).update({"$inc": {"bookmark_count": 1}})
            return True
        except Exception as e:
            print(f"Error incrementing bookmark count for post {post_id}: {e}")
            return False
    
    async def decrement_bookmark_count(self, post_id: str) -> bool:
        """Decrement post bookmark count.
        
        Args:
            post_id: Post ID
            
        Returns:
            True if successful
        """
        try:
            result = await Post.find({"_id": PydanticObjectId(post_id)}).update({"$inc": {"bookmark_count": -1}})
            return True
        except Exception as e:
            print(f"Error decrementing bookmark count for post {post_id}: {e}")
            return False
    
    async def update_post_counts(self, post_id: str, update_fields: Dict[str, int]) -> bool:
        """Update post count fields using increment operations.
        
        Args:
            post_id: Post ID
            update_fields: Dictionary of field names and increment values (can be negative)
            
        Returns:
            True if successful
        """
        try:
            result = await Post.find({"_id": PydanticObjectId(post_id)}).update({"$inc": update_fields})
            return True
        except Exception as e:
            print(f"Error updating post counts for post {post_id}: {e}")
            return False
    
    async def get_user_reactions(self, user_id: str, post_ids: List[str]) -> Dict[str, str]:
        """Get user reactions for posts.
        
        Args:
            user_id: User ID
            post_ids: List of post IDs
            
        Returns:
            Dictionary mapping post_id to reaction_type
        """
        # This would typically query the Reaction collection
        # For now, return empty dict as placeholder
        return {}
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title.
        
        Args:
            title: Post title
            
        Returns:
            URL-friendly slug
        """
        import uuid
        
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        # Remove special characters except hyphens, alphanumeric, and Korean characters
        slug = re.sub(r"[^a-z0-9\s\-가-힣]", "", slug)
        # Replace multiple spaces/hyphens with single hyphen
        slug = re.sub(r"[\s-]+", "-", slug)
        # Remove leading/trailing hyphens
        slug = slug.strip("-")
        
        # If slug is empty or only contains Korean characters that might cause URL issues,
        # generate a unique identifier based on title hash and random string
        if not slug or len(slug) < 3:
            # Create a short hash from title + random component for uniqueness
            import hashlib
            title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
            random_part = str(uuid.uuid4())[:8]
            slug = f"post-{title_hash}-{random_part}"
        
        return slug
    
    async def _ensure_unique_slug(self, base_slug: str) -> str:
        """Ensure slug is unique by appending number if necessary.
        
        Args:
            base_slug: Base slug to make unique
            
        Returns:
            Unique slug
        """
        slug = base_slug
        counter = 1
        
        while await Post.find_one(Post.slug == slug) is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    async def get_authors_by_ids(self, author_ids: List[str]) -> List[User]:
        """Get authors by their IDs.
        
        Args:
            author_ids: List of author IDs
            
        Returns:
            List of User instances
        """
        if not author_ids:
            return []
        
        try:
            # Convert string IDs to ObjectIds
            object_ids = [PydanticObjectId(author_id) for author_id in author_ids]
            
            # Query users collection
            authors = await User.find({"_id": {"$in": object_ids}}).to_list()
            return authors
        except Exception as e:
            print(f"Error fetching authors: {e}")
            return []
    
    async def find_by_author(self, author_id: str) -> List[Post]:
        """Find all posts by author ID.
        
        Args:
            author_id: Author ID
            
        Returns:
            List of posts by the author (excluding deleted posts)
        """
        try:
            posts = await Post.find({
                "author_id": author_id,
                "status": {"$ne": "deleted"}
            }).sort("-created_at").to_list()
            return posts
        except Exception:
            return []
    
    async def find_by_author_paginated(self, author_id: str, limit: int = 10, skip: int = 0) -> List[Post]:
        """Find posts by author ID with pagination.
        
        Args:
            author_id: Author ID
            limit: Maximum number of posts to return (default: 10)
            skip: Number of posts to skip (default: 0)
            
        Returns:
            List of posts by the author with pagination (excluding deleted posts)
        """
        try:
            posts = await Post.find({
                "author_id": author_id,
                "status": {"$ne": "deleted"}
            }).sort("-created_at").skip(skip).limit(limit).to_list()
            return posts
        except Exception:
            return []
    
    async def count_by_author(self, author_id: str) -> int:
        """Count total posts by author ID.
        
        Args:
            author_id: Author ID
            
        Returns:
            Total number of posts by the author (excluding deleted posts)
        """
        try:
            count = await Post.find({
                "author_id": author_id,
                "status": {"$ne": "deleted"}
            }).count()
            return count
        except Exception:
            return 0
    
    async def list_posts_optimized(
        self, 
        page: int = 1,
        page_size: int = 20,
        metadata_type: Optional[str] = None,
        sort_by: str = "created_at"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """MongoDB aggregation을 사용한 최적화된 게시글 조회.
        
        기존 list_posts + get_authors_by_ids + _calculate_post_stats를 
        단일 aggregation 쿼리로 최적화.
        
        Args:
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수
            metadata_type: 메타데이터 타입 필터 (property_information, moving services, expert_tips, board)
            sort_by: 정렬 필드
            
        Returns:
            Tuple of (게시글 리스트, 총 개수)
        """
        # 기본 매치 조건
        match_stage = {"status": {"$ne": "deleted"}}
        if metadata_type == "board":
            # 게시판: metadata.type이 없거나 null이거나 "board"인 경우
            match_stage["$or"] = [
                {"metadata.type": {"$exists": False}},
                {"metadata.type": None},
                {"metadata.type": "board"}
            ]
        elif metadata_type:
            match_stage["metadata.type"] = metadata_type
            
        print(f"🔍 Repository match_stage: {match_stage}")
        print(f"📊 Searching for metadata_type: '{metadata_type}'")
        
        # 정렬 필드 설정 (내림차순)
        sort_field = sort_by
        sort_direction = -1  # 내림차순
        
        # Aggregation 파이프라인 구성
        pipeline = [
            # 1. 매치 조건으로 필터링
            {"$match": match_stage},
            
            # 2. 정렬 (작성자 정보는 나중에 별도로 조회)
            {"$sort": {sort_field: sort_direction}},
            
            # 5. 페이지네이션과 총 개수를 동시에 처리 ($facet)
            {"$facet": {
                "posts": [
                    {"$skip": (page - 1) * page_size},
                    {"$limit": page_size}
                ],
                "total": [
                    {"$count": "count"}
                ]
            }}
        ]
        
        try:
            # 디버깅을 위한 매치 스테이지 로깅
            print(f"🔍 Aggregation match_stage: {match_stage}")
            
            # Aggregation 실행
            result = await Post.aggregate(pipeline).to_list()
            
            if not result:
                return [], 0
            
            # 결과 추출
            posts = result[0].get("posts", [])
            total_result = result[0].get("total", [])
            total = total_result[0]["count"] if total_result else 0
            
            print(f"✅ Repository query result - total: {total}, posts: {len(posts)}")
            if posts:
                print(f"📝 First post sample: {posts[0].get('title', 'No title')}")
            
            return posts, total
            
        except Exception as e:
            print(f"Error in list_posts_optimized: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return [], 0
    
    async def update_post_counts(self, post_id: str, count_updates: Dict[str, int]) -> bool:
        """Post 모델의 카운트 필드들을 업데이트.
        
        Args:
            post_id: 업데이트할 게시글 ID
            count_updates: 업데이트할 카운트 딕셔너리
                예: {"like_count": 1, "dislike_count": -1, "bookmark_count": 1}
                
        Returns:
            업데이트 성공 여부
        """
        try:
            from beanie import PydanticObjectId
            
            # 증감 연산자 구성
            inc_updates = {}
            for field, value in count_updates.items():
                if value != 0:  # 0이 아닌 경우만 업데이트
                    inc_updates[field] = value
            
            if not inc_updates:
                return True  # 업데이트할 내용이 없으면 성공으로 간주
            
            # MongoDB $inc 연산자를 사용해 카운트 업데이트
            result = await Post.get_motor_collection().update_one(
                {"_id": PydanticObjectId(post_id)},
                {"$inc": inc_updates}
            )
            
            # 카운트가 음수가 되지 않도록 보장
            # 각 필드가 0보다 작으면 0으로 설정
            for field in inc_updates.keys():
                await Post.get_motor_collection().update_one(
                    {
                        "_id": PydanticObjectId(post_id),
                        field: {"$lt": 0}
                    },
                    {"$set": {field: 0}}
                )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating post counts for {post_id}: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False