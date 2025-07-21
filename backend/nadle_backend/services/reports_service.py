"""Reports service layer for handling report submissions."""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from nadle_backend.models.core import User, Post, PostCreate, PostMetadata
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.exceptions.post import PostNotFoundError
from nadle_backend.exceptions.comment import CommentNotFoundError


class ReportsService:
    """Service layer for report-related business logic."""

    def __init__(
        self,
        post_repository: PostRepository = None,
        comment_repository: CommentRepository = None,
    ):
        """Initialize reports service with dependencies.

        Args:
            post_repository: Post repository instance
            comment_repository: Comment repository instance
        """
        self.post_repository = post_repository or PostRepository()
        self.comment_repository = comment_repository or CommentRepository()

    def _generate_guest_reporter_id(self) -> str:
        """비로그인 사용자용 임시 신고자 ID 생성"""
        return f"guest_report_{uuid.uuid4().hex[:12]}"

    async def create_post_report(
        self, 
        post_id: str, 
        content: str, 
        current_user: Optional[User] = None
    ) -> Post:
        """게시글 신고 생성

        Args:
            post_id: 신고할 게시글 ID
            content: 신고 내용
            current_user: 현재 사용자 (없으면 비로그인 사용자)

        Returns:
            생성된 신고 Post 객체

        Raises:
            PostNotFoundError: 신고할 게시글이 존재하지 않는 경우
        """
        # 신고할 게시글이 존재하는지 확인
        target_post = await self.post_repository.get_by_id(post_id)
        if not target_post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        # 신고자 ID 결정 (로그인/비로그인)
        reporter_id = str(current_user.id) if current_user else self._generate_guest_reporter_id()

        # 신고 메타데이터 생성
        metadata = PostMetadata(
            type="report",
            target_type="post",
            target_id=post_id,
            target_title=target_post.title[:100]  # 신고된 게시글 제목 일부 저장
        )

        # 신고 Post 생성
        report_data = PostCreate(
            title=f"게시글 신고 - {target_post.title[:50]}...",
            content=content,
            type="report",
            service="residential_community",
            metadata=metadata
        )

        # 신고 저장
        report_post = await self.post_repository.create(report_data, reporter_id)
        return report_post

    async def create_comment_report(
        self, 
        comment_id: str, 
        content: str, 
        current_user: Optional[User] = None
    ) -> Post:
        """댓글 신고 생성

        Args:
            comment_id: 신고할 댓글 ID
            content: 신고 내용
            current_user: 현재 사용자 (없으면 비로그인 사용자)

        Returns:
            생성된 신고 Post 객체

        Raises:
            CommentNotFoundError: 신고할 댓글이 존재하지 않는 경우
        """
        # 신고할 댓글이 존재하는지 확인
        target_comment = await self.comment_repository.get_by_id(comment_id)
        if not target_comment:
            raise CommentNotFoundError(f"Comment with ID {comment_id} not found")

        # 신고자 ID 결정 (로그인/비로그인)
        reporter_id = str(current_user.id) if current_user else self._generate_guest_reporter_id()

        # 신고 메타데이터 생성
        metadata = PostMetadata(
            type="report",
            target_type="comment",
            target_id=comment_id,
            target_content=target_comment.content[:100]  # 신고된 댓글 내용 일부 저장
        )

        # 신고 Post 생성
        report_data = PostCreate(
            title=f"댓글 신고 - {target_comment.content[:50]}...",
            content=content,
            type="report",
            service="residential_community",
            metadata=metadata
        )

        # 신고 저장
        report_post = await self.post_repository.create(report_data, reporter_id)
        return report_post

    async def get_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        target_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """신고 목록 조회 (관리자용)

        Args:
            page: 페이지 번호
            page_size: 페이지 크기
            status: 상태 필터
            target_type: 신고 대상 타입 필터 (post/comment)

        Returns:
            페이지네이션된 신고 목록
        """
        # 신고 타입 필터 적용 - metadata.type이 "report"인 게시글 조회
        from nadle_backend.models.core import Post, User
        from bson import ObjectId
        
        # 기본 쿼리 조건
        query = {"metadata.type": "report"}
        
        # 상태 필터 추가
        if status:
            query["status"] = status
            
        # 페이지네이션 계산
        skip = (page - 1) * page_size
        
        # 신고 게시글 조회
        posts_raw = await Post.find(query).sort(-Post.created_at).skip(skip).limit(page_size).to_list()
        total = await Post.find(query).count()
        
        # 사용자 정보를 포함한 신고 목록 생성
        posts = []
        for post in posts_raw:
            try:
                print(f"🔍 Processing post: {post.id}, author_id: {post.author_id}, type: {type(post.author_id)}")
                
                # Post 모델을 dict로 안전하게 변환
                post_dict = {
                    "id": str(post.id),
                    "title": getattr(post, 'title', ''),
                    "content": getattr(post, 'content', ''),
                    "author_id": str(post.author_id),
                    "status": getattr(post, 'status', 'pending'),
                    "created_at": getattr(post, 'created_at', None),
                    "updated_at": getattr(post, 'updated_at', None),
                    "metadata": None
                }
                
                # metadata 안전하게 처리
                if hasattr(post, 'metadata') and post.metadata:
                    try:
                        if hasattr(post.metadata, 'model_dump'):
                            post_dict["metadata"] = post.metadata.model_dump()
                        else:
                            # metadata가 이미 dict인 경우
                            post_dict["metadata"] = post.metadata
                    except Exception as e:
                        print(f"Metadata 처리 오류: {e}")
                        post_dict["metadata"] = None
                
                # author 정보 조회 (guest_report_가 아닌 경우만)
                author_id_str = str(post.author_id)
                print(f"🔍 Checking author_id: {author_id_str}, starts with guest_report_: {author_id_str.startswith('guest_report_')}")
                
                if not author_id_str.startswith('guest_report_'):
                    try:
                        print(f"🔍 Attempting to fetch author for ID: {post.author_id}")
                        
                        # author_id가 이미 ObjectId인지 확인
                        from bson import ObjectId
                        if hasattr(post.author_id, '__class__') and post.author_id.__class__.__name__ == 'PydanticObjectId':
                            # 이미 ObjectId 타입
                            author = await User.get(post.author_id)
                        else:
                            # 문자열인 경우 ObjectId로 변환
                            author = await User.get(ObjectId(author_id_str))
                        
                        if author:
                            post_dict["author"] = {
                                "id": str(author.id),
                                "email": author.email,
                                "user_handle": author.user_handle,
                                "display_name": getattr(author, 'display_name', None),
                                "name": getattr(author, 'name', None)
                            }
                            print(f"✅ Author found: {author.user_handle}")
                        else:
                            print(f"❌ Author not found for ID: {post.author_id}")
                            post_dict["author"] = None
                    except Exception as e:
                        print(f"❌ Author 조회 실패 for {post.author_id}: {e}")
                        import traceback
                        traceback.print_exc()
                        post_dict["author"] = None
                else:
                    print(f"🔍 Guest user detected: {author_id_str}")
                    post_dict["author"] = None
                
                posts.append(post_dict)
            except Exception as e:
                print(f"Post 처리 중 오류: {e}, post_id: {getattr(post, 'id', 'unknown')}")
                # 오류가 있는 post는 건너뛰고 계속 진행
                continue

        # target_type으로 추가 필터링 (dict 객체에서 안전하게 접근)
        if target_type:
            filtered_posts = []
            for p in posts:
                # metadata가 존재하는지 확인
                metadata = p.get("metadata")
                if metadata:
                    try:
                        # dict에서 metadata.target_type 확인
                        if isinstance(metadata, dict):
                            post_target_type = metadata.get("target_type")
                        else:
                            post_target_type = getattr(metadata, "target_type", None)
                        
                        if post_target_type == target_type:
                            filtered_posts.append(p)
                    except (AttributeError, KeyError) as e:
                        print(f"metadata 접근 오류: {e}, post: {p.get('id', 'unknown')}")
                        # metadata 오류가 있어도 계속 진행
                        continue
            posts = filtered_posts
            total = len(posts)

        return {
            "items": posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def update_report_status(
        self, 
        report_id: str, 
        new_status: str
    ) -> Post:
        """신고 상태 업데이트

        Args:
            report_id: 신고 ID
            new_status: 새로운 상태

        Returns:
            업데이트된 신고 Post 객체

        Raises:
            PostNotFoundError: 신고가 존재하지 않는 경우
        """
        # 신고 존재 확인
        report = await self.post_repository.get_by_id(report_id)
        if not report:
            raise PostNotFoundError(f"Report with ID {report_id} not found")

        # 상태 업데이트
        resolved_at = datetime.utcnow() if new_status in ["resolved", "rejected"] else None
        updated_report = await self.post_repository.update_status(
            post_id=report_id,
            new_status=new_status,
            resolved_at=resolved_at
        )

        return updated_report