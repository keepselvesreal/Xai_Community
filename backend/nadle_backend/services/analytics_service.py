"""Analytics service for user analytics and statistics."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pymongo import ASCENDING, DESCENDING
import random
import string
from beanie import PydanticObjectId

from nadle_backend.models.core import User, Post, Comment, UserReaction
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.user_reaction_repository import UserReactionRepository
from nadle_backend.services.session_service import SessionService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Analytics service for collecting and analyzing user data."""

    def __init__(self):
        """Initialize analytics service with repositories."""
        self.user_repo = UserRepository()
        self.post_repo = PostRepository()
        self.comment_repo = CommentRepository()
        self.reaction_repo = UserReactionRepository()
        self.session_service = SessionService()

    async def get_user_statistics(self) -> Dict[str, int]:
        """
        사용자 통계 조회
        - 총 사용자 수
        - 신규 사용자 (오늘, 최근 7일)
        - 일일 활성 사용자 (오늘 로그인한 사용자)
        """
        try:
            # 날짜 범위 설정
            now = datetime.utcnow()
            today_start = datetime(now.year, now.month, now.day)
            week_ago = today_start - timedelta(days=7)

            # 총 사용자 수
            total_users = await User.count()

            # 신규 사용자 (오늘)
            new_users_today = await User.find(
                {"created_at": {"$gte": today_start}}
            ).count()

            # 신규 사용자 (최근 7일)
            new_users_weekly = await User.find(
                {"created_at": {"$gte": week_ago}}
            ).count()

            # 일일 활성 사용자 (오늘 활동한 사용자 수)
            # 임시: 실제 활동 기반 계산이 복잡하므로 간단한 방식 사용
            # 현재 활성 세션 + 오늘 생성된 콘텐츠 작성자 기반 계산
            try:
                active_sessions = await self.session_service.get_active_sessions_count()

                # 오늘 게시글 작성한 사용자 수
                post_authors_today = len(
                    await Post.find({"created_at": {"$gte": today_start}}).distinct(
                        "author_id"
                    )
                )

                # 오늘 댓글 작성한 사용자 수
                comment_authors_today = len(
                    await Comment.find({"created_at": {"$gte": today_start}}).distinct(
                        "author_id"
                    )
                )

                # 최소값 보장: 활성 세션, 게시글 작성자, 댓글 작성자 중 최대값
                daily_active_users = max(
                    active_sessions, post_authors_today, comment_authors_today, 1
                )

            except Exception as e:
                logger.error(f"DAU 계산 간소화 버전 오류: {e}")
                daily_active_users = 1  # 최소 1명 보장

            return {
                "total_users": total_users,
                "new_users_today": new_users_today,
                "new_users_weekly": new_users_weekly,
                "daily_active_users": daily_active_users,
            }

        except Exception as e:
            logger.error(f"사용자 통계 조회 오류: {e}")
            raise

    async def _calculate_daily_active_users(self, today_start: datetime) -> int:
        """
        일일 활성 사용자(DAU) 계산
        오늘 하루 동안 다음 활동 중 하나라도 한 사용자 수:
        1. 게시글 작성
        2. 댓글 작성
        3. 반응(좋아요, 북마크) 활동
        4. 로그인 (last_login 업데이트)
        """
        try:
            active_user_ids = set()

            # 1. 오늘 게시글 작성한 사용자
            post_authors = await Post.find(
                {"created_at": {"$gte": today_start}}
            ).distinct("author_id")
            active_user_ids.update(post_authors)

            # 2. 오늘 댓글 작성한 사용자
            comment_authors = await Comment.find(
                {"created_at": {"$gte": today_start}}
            ).distinct("author_id")
            active_user_ids.update(comment_authors)

            # 3. 오늘 반응(좋아요, 북마크) 활동한 사용자
            reaction_users = await UserReaction.find(
                {"updated_at": {"$gte": today_start}}
            ).distinct("user_id")
            active_user_ids.update(reaction_users)

            # 4. 오늘 로그인한 사용자 (last_login 기반) - null 값 처리
            login_users = await User.find(
                {"last_login": {"$gte": today_start}}
            ).distinct("_id")
            # ObjectId를 문자열로 변환
            login_user_ids = [str(user_id) for user_id in login_users]
            active_user_ids.update(login_user_ids)

            # 5. 임시: 최소 1명의 DAU 보장 (현재 API를 호출한 사용자 포함)
            # 실제로는 로그인 시 last_login을 업데이트해야 함
            if len(active_user_ids) == 0:
                # 오늘 생성된 사용자나 활동이 전혀 없을 때 최소 DAU 보장
                # 실제 운영에서는 제거해야 함
                pass

            # 디버깅용 로그
            logger.info(
                f"DAU 계산 결과: 게시글작성({len(post_authors)}), 댓글작성({len(comment_authors)}), 반응({len(reaction_users)}), 로그인({len(login_user_ids)})"
            )
            logger.info(f"총 활성 사용자 ID: {active_user_ids}")

            # 중복 제거된 활성 사용자 수 반환
            return len(active_user_ids)

        except Exception as e:
            logger.error(f"DAU 계산 오류: {e}")
            # 오류 시 현재 활성 세션 수로 폴백
            try:
                active_sessions = await self.session_service.get_active_sessions_count()
                return active_sessions
            except:
                return 0

    async def get_signup_conversion_rate(self) -> Dict[str, Any]:
        """
        가입 전환율 조회 (방문 → 가입)
        오늘과 어제 기준으로 방문자 수와 가입자 수를 비교
        """
        try:
            # 날짜 범위 설정
            now = datetime.utcnow()
            today_start = datetime(now.year, now.month, now.day)
            yesterday_start = today_start - timedelta(days=1)
            day_before_start = yesterday_start - timedelta(days=1)

            # 오늘 가입자 수
            signups_today = await User.find(
                {"created_at": {"$gte": today_start}}
            ).count()

            # 어제 가입자 수
            signups_yesterday = await User.find(
                {"created_at": {"$gte": yesterday_start, "$lt": today_start}}
            ).count()

            # 그저께 가입자 수 (비교용)
            signups_day_before = await User.find(
                {"created_at": {"$gte": day_before_start, "$lt": yesterday_start}}
            ).count()

            # 방문자 수는 세션 기반으로 추정
            # 현재는 가입자 수의 10-15배로 추정 (실제 환경에서는 GA4나 별도 트래킹 필요)
            visitors_today = max(signups_today * 12, 20)  # 최소 20명
            visitors_yesterday = max(signups_yesterday * 12, 20)  # 최소 20명
            visitors_day_before = max(signups_day_before * 12, 20)

            # 전환율 계산
            conversion_rate_today = (
                (signups_today / visitors_today * 100) if visitors_today > 0 else 0
            )
            conversion_rate_yesterday = (
                (signups_yesterday / visitors_yesterday * 100)
                if visitors_yesterday > 0
                else 0
            )
            conversion_rate_day_before = (
                (signups_day_before / visitors_day_before * 100)
                if visitors_day_before > 0
                else 0
            )

            # 변화율 계산 (오늘 대비 어제 전환율 차이)
            if conversion_rate_yesterday > 0:
                conversion_rate_change = (
                    conversion_rate_today - conversion_rate_yesterday
                )
            else:
                conversion_rate_change = 0

            return {
                "visitors_today": visitors_today,
                "signups_today": signups_today,
                "conversion_rate_today": round(conversion_rate_today, 1),
                "visitors_yesterday": visitors_yesterday,
                "signups_yesterday": signups_yesterday,
                "conversion_rate_yesterday": round(conversion_rate_yesterday, 1),
                "conversion_rate_change": round(conversion_rate_change, 1),
            }

        except Exception as e:
            logger.error(f"가입 전환율 조회 오류: {e}")
            raise

    async def get_event_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        이벤트 통계 조회
        - 게시글 작성, 추천, 저장, 댓글 작성
        - 오늘 건수와 어제 대비 변화
        """
        try:
            # 날짜 범위 설정
            now = datetime.utcnow()
            today_start = datetime(now.year, now.month, now.day)
            yesterday_start = today_start - timedelta(days=1)

            # 게시글 작성
            posts_today = await Post.find({"created_at": {"$gte": today_start}}).count()

            posts_yesterday = await Post.find(
                {"created_at": {"$gte": yesterday_start, "$lt": today_start}}
            ).count()

            # 댓글 작성
            comments_today = await Comment.find(
                {"created_at": {"$gte": today_start}}
            ).count()

            comments_yesterday = await Comment.find(
                {"created_at": {"$gte": yesterday_start, "$lt": today_start}}
            ).count()

            # 게시글 추천 (좋아요)
            likes_today = await UserReaction.find(
                {"liked": True, "created_at": {"$gte": today_start}}
            ).count()

            likes_yesterday = await UserReaction.find(
                {
                    "liked": True,
                    "created_at": {"$gte": yesterday_start, "$lt": today_start},
                }
            ).count()

            # 게시글 저장 (북마크) - 오늘 북마크 상태가 변경되어 현재 저장된 것들
            bookmarks_today = await UserReaction.find(
                {"bookmarked": True, "updated_at": {"$gte": today_start}}
            ).count()

            bookmarks_yesterday = await UserReaction.find(
                {
                    "bookmarked": True,
                    "updated_at": {"$gte": yesterday_start, "$lt": today_start},
                }
            ).count()

            return {
                "post_creation": {
                    "today": posts_today,
                    "yesterday_change": posts_today - posts_yesterday,
                },
                "post_likes": {
                    "today": likes_today,
                    "yesterday_change": likes_today - likes_yesterday,
                },
                "post_bookmarks": {
                    "today": bookmarks_today,
                    "yesterday_change": bookmarks_today - bookmarks_yesterday,
                },
                "comment_creation": {
                    "today": comments_today,
                    "yesterday_change": comments_today - comments_yesterday,
                },
            }

        except Exception as e:
            logger.error(f"이벤트 통계 조회 오류: {e}")
            raise

    async def get_site_bounce_rate(self) -> float:
        """
        전체 사이트 이탈률 조회
        현재는 추정치 반환 (실제로는 GA4나 별도 세션 트래킹 필요)
        """
        try:
            # 세션 기반 이탈률 계산 (임시)
            # 실제 구현에서는 페이지뷰 수와 단일 페이지 세션 비율 계산

            # 최근 7일간 데이터로 추정
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)

            # 게시글 조회수 기반 추정
            recent_posts = await Post.find({"created_at": {"$gte": week_ago}}).to_list()

            if not recent_posts:
                return 35.0  # 기본값

            # 평균 조회수와 댓글 수 비율로 참여도 추정
            total_views = sum(post.view_count or 0 for post in recent_posts)
            total_comments = await Comment.find(
                {"created_at": {"$gte": week_ago}}
            ).count()

            # 참여도가 높을수록 이탈률 낮음
            if total_views > 0:
                engagement_rate = (total_comments / total_views) * 100
                bounce_rate = max(20, 50 - engagement_rate * 5)  # 최소 20%, 최대 50%
            else:
                bounce_rate = 35.0

            return round(bounce_rate, 1)

        except Exception as e:
            logger.error(f"이탈률 조회 오류: {e}")
            return 35.0  # 기본값 반환

    async def get_realtime_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        실시간 활동 피드 조회
        최근 생성된 게시글, 댓글, 반응 등을 시간순으로 반환
        """
        try:
            activities = []
            logger.info(f"실시간 활동 조회 시작, limit: {limit}")

            # 최근 게시글만 먼저 테스트
            try:
                recent_posts = (
                    await Post.find()
                    .sort([("created_at", DESCENDING)])
                    .limit(5)
                    .to_list()
                )
                logger.info(f"최근 게시글 수: {len(recent_posts)}")

                for post in recent_posts:
                    try:
                        user = (
                            await User.get(post.author_id) if post.author_id else None
                        )
                        activities.append(
                            {
                                "timestamp": post.created_at.isoformat(),
                                "activity_type": "post_create",
                                "user_name": (
                                    user.display_name or user.user_handle
                                    if user
                                    else "알 수 없는 사용자"
                                ),
                                "description": f'"{post.title}" 게시글 작성',
                                "target_title": post.title,
                            }
                        )
                    except Exception as post_error:
                        logger.error(f"게시글 활동 처리 오류: {post_error}")
                        continue

            except Exception as posts_error:
                logger.error(f"게시글 조회 오류: {posts_error}")

            # 최근 댓글 추가
            try:
                recent_comments = (
                    await Comment.find()
                    .sort([("created_at", DESCENDING)])
                    .limit(5)
                    .to_list()
                )
                logger.info(f"최근 댓글 수: {len(recent_comments)}")

                for comment in recent_comments:
                    try:
                        user = (
                            await User.get(comment.author_id)
                            if comment.author_id
                            else None
                        )
                        post = (
                            await Post.get(comment.parent_id)
                            if comment.parent_id
                            else None
                        )
                        activities.append(
                            {
                                "timestamp": comment.created_at.isoformat(),
                                "activity_type": "comment_create",
                                "user_name": (
                                    user.display_name or user.user_handle
                                    if user
                                    else "알 수 없는 사용자"
                                ),
                                "description": f'"{post.title if post else "게시글"}" 댓글 작성',
                                "target_title": post.title if post else None,
                            }
                        )
                    except Exception as comment_error:
                        logger.error(f"댓글 활동 처리 오류: {comment_error}")
                        continue

            except Exception as comments_error:
                logger.error(f"댓글 조회 오류: {comments_error}")

            # 최근 가입 사용자 (간단한 버전)
            try:
                recent_users = (
                    await User.find()
                    .sort([("created_at", DESCENDING)])
                    .limit(3)
                    .to_list()
                )
                logger.info(f"최근 가입 사용자 수: {len(recent_users)}")

                for user in recent_users:
                    activities.append(
                        {
                            "timestamp": user.created_at.isoformat(),
                            "activity_type": "signup",
                            "user_name": user.display_name or user.user_handle,
                            "description": "회원가입 완료 🎉",
                            "target_title": None,
                        }
                    )
            except Exception as users_error:
                logger.error(f"사용자 조회 오류: {users_error}")

            # 최근 반응 (좋아요, 북마크) 추가
            try:
                recent_reactions = (
                    await UserReaction.find()
                    .sort([("updated_at", DESCENDING)])
                    .limit(5)
                    .to_list()
                )
                logger.info(f"최근 반응 수: {len(recent_reactions)}")

                for reaction in recent_reactions:
                    try:
                        user = (
                            await User.get(reaction.user_id)
                            if reaction.user_id
                            else None
                        )
                        post = (
                            await Post.get(reaction.target_id)
                            if reaction.target_id
                            else None
                        )

                        # UserReaction 모델의 새로운 필드 구조에 맞게 수정
                        if reaction.liked:
                            reaction_type = "like"
                            reaction_emoji = "👍"
                            reaction_text = "추천"
                        elif reaction.disliked:
                            reaction_type = "dislike"
                            reaction_emoji = "👎"
                            reaction_text = "비추천"
                        elif reaction.bookmarked:
                            reaction_type = "bookmark"
                            reaction_emoji = "💾"
                            reaction_text = "저장"
                        else:
                            continue  # 어떤 반응도 없는 경우 스킵

                        activities.append(
                            {
                                "timestamp": reaction.updated_at.isoformat(),
                                "activity_type": reaction_type,
                                "user_name": (
                                    user.display_name or user.user_handle
                                    if user
                                    else "알 수 없는 사용자"
                                ),
                                "description": f'"{post.title if post else "게시글"}" {reaction_emoji} {reaction_text}',
                                "target_title": post.title if post else None,
                            }
                        )
                    except Exception as reaction_error:
                        logger.error(f"반응 활동 처리 오류: {reaction_error}")
                        continue

            except Exception as reactions_error:
                logger.error(f"반응 조회 오류: {reactions_error}")

            # 시간순 정렬 후 제한
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            logger.info(f"총 활동 수: {len(activities)}")
            return activities[:limit]

        except Exception as e:
            logger.error(f"실시간 활동 조회 오류: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def simulate_user_activity(
        self, activity_type: str, count: int
    ) -> Dict[str, Any]:
        """
        개발환경용 사용자 활동 시뮬레이션
        """
        try:
            created_items = []

            if activity_type == "signup":
                # 가상 사용자 생성
                for i in range(count):
                    user_handle = f"test_user_{''.join(random.choices(string.ascii_lowercase, k=6))}"
                    user = User(
                        email=f"{user_handle}@test.com",
                        user_handle=user_handle,
                        display_name=f"테스트 사용자 {i+1}",
                        name=f"테스트{i+1}",
                        password_hash="$2b$12$test_hashed_password",  # 테스트용 해시된 패스워드
                        is_verified=True,
                        created_at=datetime.utcnow(),
                    )
                    await user.create()
                    created_items.append(user.id)

            elif activity_type == "post_create":
                # 가상 게시글 생성
                users = await User.find().limit(10).to_list()
                if not users:
                    raise ValueError("시뮬레이션할 사용자가 없습니다.")

                for i in range(count):
                    user = random.choice(users)
                    # Generate unique slug
                    slug = f"test-post-{random.randint(1000, 9999)}-{int(datetime.utcnow().timestamp())}"

                    post = Post(
                        title=f"테스트 게시글 {i+1}",
                        slug=slug,
                        content=f"이것은 테스트용 게시글 내용입니다. {i+1}",
                        service="residential_community",
                        author_id=str(user.id),
                        metadata={
                            "type": random.choice(
                                [
                                    "board",
                                    "property_information",
                                    "expert_tips",
                                    "moving_services",
                                ]
                            ),
                            "editor_type": "plain",
                            "visibility": "public",
                        },
                        created_at=datetime.utcnow(),
                    )
                    await post.create()
                    created_items.append(post.id)

            elif activity_type == "like":
                # 가상 좋아요 생성
                users = await User.find().limit(10).to_list()
                posts = await Post.find().limit(20).to_list()

                if not users or not posts:
                    raise ValueError("시뮬레이션할 사용자 또는 게시글이 없습니다.")

                for i in range(count):
                    user = random.choice(users)
                    post = random.choice(posts)

                    # 중복 반응 체크
                    existing = await UserReaction.find_one(
                        {
                            "user_id": str(user.id),
                            "target_id": str(post.id),
                            "target_type": "post",
                        }
                    )

                    if not existing:
                        reaction = UserReaction(
                            user_id=str(user.id),
                            target_id=str(post.id),
                            target_type="post",
                            liked=True,
                            created_at=datetime.utcnow(),
                        )
                        await reaction.create()
                        created_items.append(reaction.id)

            elif activity_type == "bookmark":
                # 가상 북마크 생성
                users = await User.find().limit(10).to_list()
                posts = await Post.find().limit(20).to_list()

                if not users or not posts:
                    raise ValueError("시뮬레이션할 사용자 또는 게시글이 없습니다.")

                for i in range(count):
                    user = random.choice(users)
                    post = random.choice(posts)

                    # 중복 반응 체크
                    existing = await UserReaction.find_one(
                        {
                            "user_id": str(user.id),
                            "target_id": str(post.id),
                            "target_type": "post",
                        }
                    )

                    if not existing:
                        reaction = UserReaction(
                            user_id=str(user.id),
                            target_id=str(post.id),
                            target_type="post",
                            bookmarked=True,
                            created_at=datetime.utcnow(),
                        )
                        await reaction.create()
                        created_items.append(reaction.id)
                    elif not existing.bookmarked:
                        # 기존 반응이 있지만 북마크되지 않은 경우 북마크 추가
                        existing.bookmarked = True
                        existing.updated_at = datetime.utcnow()
                        await existing.save()
                        created_items.append(existing.id)

            elif activity_type == "comment":
                # 가상 댓글 생성
                users = await User.find().limit(10).to_list()
                posts = await Post.find().limit(20).to_list()

                if not users or not posts:
                    raise ValueError("시뮬레이션할 사용자 또는 게시글이 없습니다.")

                for i in range(count):
                    user = random.choice(users)
                    post = random.choice(posts)

                    comment = Comment(
                        parent_type="post",
                        parent_id=str(post.id),
                        author_id=str(user.id),
                        content=f"테스트 댓글입니다. {i+1}번째 댓글",
                        created_at=datetime.utcnow(),
                    )
                    await comment.create()
                    created_items.append(comment.id)

            return {
                "activity_type": activity_type,
                "created_count": len(created_items),
                "created_ids": [str(item_id) for item_id in created_items],
            }

        except Exception as e:
            logger.error(f"활동 시뮬레이션 오류: {e}")
            raise

    async def reset_test_data(self) -> Dict[str, Any]:
        """
        개발환경용 테스트 데이터 초기화
        """
        try:
            # 테스트 사용자 삭제 (이메일에 'test'가 포함된 사용자)
            test_users = await User.find({"email": {"$regex": "test"}}).to_list()
            deleted_users = len(test_users)
            for user in test_users:
                await user.delete()

            # 테스트 게시글 삭제 (제목에 '테스트'가 포함된 게시글)
            test_posts = await Post.find({"title": {"$regex": "테스트"}}).to_list()
            deleted_posts = len(test_posts)
            for post in test_posts:
                await post.delete()

            # 관련 댓글과 반응도 정리
            deleted_comments = 0
            deleted_reactions = 0

            for post in test_posts:
                comments = await Comment.find({"post_id": post.id}).to_list()
                deleted_comments += len(comments)
                for comment in comments:
                    await comment.delete()

                reactions = await UserReaction.find({"target_id": post.id}).to_list()
                deleted_reactions += len(reactions)
                for reaction in reactions:
                    await reaction.delete()

            return {
                "deleted_users": deleted_users,
                "deleted_posts": deleted_posts,
                "deleted_comments": deleted_comments,
                "deleted_reactions": deleted_reactions,
            }

        except Exception as e:
            logger.error(f"테스트 데이터 초기화 오류: {e}")
            raise
