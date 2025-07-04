#!/usr/bin/env python3
"""
자동 테스트 데이터 설정 스크립트

이 스크립트는 다음 작업을 자동으로 수행합니다:
1. 테스트 계정 2개 생성
2. 모든 페이지(정보 페이지 제외)에 게시글 작성
3. 상대방 게시글에 댓글 달기
4. 입주 업체 서비스에 문의/후기 작성
5. 게시글과 댓글에 추천/비추천/저장 반응
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys
import os
from bson import ObjectId

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nadle_backend.config import settings
from nadle_backend.database.connection import database
from nadle_backend.models.core import (
    User, UserCreate, Post, PostCreate, Comment, CommentCreate, UserReaction
)
from nadle_backend.services.auth_service import AuthService
from nadle_backend.services.posts_service import PostsService
from nadle_backend.services.comments_service import CommentsService
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.user_reaction_repository import UserReactionRepository

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'auto_setup_test_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class AutoTestDataSetup:
    """자동 테스트 데이터 설정 클래스"""
    
    def __init__(self):
        self.auth_service = None
        self.posts_service = None
        self.comments_service = None
        self.user_reaction_repository = None
        self.test_users = []
        self.created_posts = []
        self.created_comments = []
        
        # 게시글 타입별 카테고리 매핑 (실제 프론트엔드 구조에 맞춤)
        self.post_types = {
            "board": [
                {"category": "입주 정보", "sample_data": [
                    {"title": "새로 입주한 주민입니다!", "content": "안녕하세요! 이번에 새로 입주하게 되었습니다. 잘 부탁드립니다."},
                    {"title": "입주민 카드 발급 안내", "content": "입주민 카드 발급 절차와 필요 서류에 대해 안내드립니다."}
                ]},
                {"category": "생활 정보", "sample_data": [
                    {"title": "오늘 날씨가 정말 좋네요", "content": "산책하기 좋은 날씨입니다. 다들 좋은 하루 보내세요!"},
                    {"title": "근처 맛집 추천", "content": "아파트 근처에 새로 생긴 맛집 정보를 공유합니다."}
                ]},
                {"category": "이야기", "sample_data": [
                    {"title": "추천 카페 있나요?", "content": "근처에 분위기 좋은 카페 있으면 추천해주세요."},
                    {"title": "이웃과의 따뜻한 만남", "content": "엘리베이터에서 만난 이웃과의 즐거운 대화 이야기입니다."}
                ]}
            ],
            "moving services": [
                {"category": "이사", "sample_data": [
                    {"title": "전문 이사 서비스", "content": "경험 많은 전문가들이 안전하고 빠른 이사를 도와드립니다."},
                    {"title": "포장 이사 전문", "content": "소중한 물건을 안전하게 포장하여 이사해드립니다."}
                ]},
                {"category": "청소", "sample_data": [
                    {"title": "청소 서비스 문의", "content": "정기 청소 서비스에 대해 문의드립니다."},
                    {"title": "입주 청소 전문", "content": "새 집 입주 전 완벽한 청소 서비스를 제공합니다."}
                ]},
                {"category": "에어컨", "sample_data": [
                    {"title": "에어컨 설치 서비스", "content": "전문 기사가 빠르고 정확하게 에어컨을 설치해드립니다."},
                    {"title": "에어컨 청소 및 점검", "content": "정기적인 에어컨 청소와 점검으로 쾌적한 환경을 만들어드립니다."}
                ]}
            ],
            "expert_tips": [
                {"category": "청소/정리", "sample_data": [
                    {"title": "쉽고 빠른 정리 꿀팁", "content": "전문가가 알려주는 효율적인 정리 방법입니다."},
                    {"title": "얼룩 제거의 모든 것", "content": "다양한 얼룩 종류별 제거 방법을 알려드립니다."}
                ]},
                {"category": "생활", "sample_data": [
                    {"title": "전기요금 절약 노하우", "content": "일상에서 실천할 수 있는 전기요금 절약 방법들입니다."},
                    {"title": "실내 공기 관리법", "content": "건강한 실내 환경을 위한 공기 관리 팁을 공유합니다."}
                ]}
            ]
        }
        
        # 댓글 샘플 데이터
        self.sample_comments = [
            "좋은 정보 감사합니다!",
            "저도 궁금했던 내용이네요.",
            "도움이 많이 되었습니다.",
            "동감합니다!",
            "저도 비슷한 경험이 있어요.",
            "유용한 정보 공유해주셔서 감사해요.",
            "이런 정보가 필요했는데 정말 고맙습니다.",
            "다음에도 좋은 정보 부탁드려요!"
        ]
        
        # 문의/후기 샘플 데이터
        self.inquiry_comments = [
            "서비스 이용료는 어떻게 되나요?",
            "예약은 어떻게 하나요?",
            "주말에도 서비스가 가능한가요?",
            "취소 정책은 어떻게 되나요?"
        ]
        
        self.review_comments = [
            "서비스 정말 만족합니다! 추천해요.",
            "직원분들이 친절하시고 서비스 품질이 좋아요.",
            "가격 대비 만족스러운 서비스입니다.",
            "다시 이용하고 싶어요. 좋은 서비스 감사합니다."
        ]
    
    async def initialize_services(self):
        """서비스 초기화"""
        await database.connect()
        
        # Beanie 모델 초기화
        from nadle_backend.models.core import User, Post, Comment, UserReaction, PostStats, Stats
        await database.init_beanie_models([User, Post, Comment, UserReaction, PostStats, Stats])
        
        # Repository 초기화
        post_repo = PostRepository()
        comment_repo = CommentRepository()
        self.user_reaction_repository = UserReactionRepository()
        
        # Service 초기화
        self.auth_service = AuthService()
        self.posts_service = PostsService(post_repo, comment_repo)
        self.comments_service = CommentsService(comment_repo, post_repo)
        
        logger.info("✅ 서비스 초기화 완료")
    
    async def create_test_users(self):
        """테스트 계정 2개 생성"""
        try:
            logger.info("👥 테스트 계정 생성 중...")
            
            test_users_data = [
                {
                    "name": "테스트 사용자 1",
                    "email": "testuser1@example.com",
                    "user_handle": "testuser1",
                    "display_name": "테스트유저1",
                    "password": "TestPassword123",
                    "bio": "테스트용 계정입니다."
                },
                {
                    "name": "테스트 사용자 2",
                    "email": "testuser2@example.com",
                    "user_handle": "testuser2",
                    "display_name": "테스트유저2",
                    "password": "TestPassword123",
                    "bio": "테스트용 계정입니다."
                }
            ]
            
            for user_data in test_users_data:
                user_create = UserCreate(**user_data)
                user_result = await self.auth_service.register_user(user_create)
                
                # 실제 User 객체를 가져오기
                from nadle_backend.repositories.user_repository import UserRepository
                user_repo = UserRepository()
                user = await user_repo.get_by_user_handle(user_result["user_handle"])
                
                self.test_users.append(user)
                logger.info(f"  ✅ 계정 생성: {user.user_handle} ({user.name})")
            
            logger.info(f"✅ 테스트 계정 생성 완료 ({len(self.test_users)}개)")
            
        except Exception as e:
            import traceback
            logger.error(f"❌ 테스트 계정 생성 실패: {str(e)}")
            logger.error(f"📋 상세 에러: {traceback.format_exc()}")
            raise
    
    async def create_sample_posts(self):
        """모든 페이지(정보 페이지 제외)에 게시글 작성"""
        try:
            logger.info("📝 샘플 게시글 작성 중...")
            
            post_count = 0
            
            for post_type, categories in self.post_types.items():
                logger.info(f"  📂 {post_type} 타입 게시글 작성 중...")
                
                for category_data in categories:
                    category = category_data["category"]
                    posts_data = category_data["sample_data"]
                    
                    for i, post_data in enumerate(posts_data):
                        # 사용자 번갈아가며 게시글 작성
                        user = self.test_users[i % len(self.test_users)]
                        
                        post_create = PostCreate(
                            title=post_data["title"],
                            content=post_data["content"],
                            service="residential_community",
                            metadata={
                                "type": post_type,
                                "category": category,
                                "tags": []
                            }
                        )
                        
                        post = await self.posts_service.create_post(post_create, user)
                        self.created_posts.append(post)
                        post_count += 1
                        logger.info(f"    ✅ 게시글 작성: {post.title} ({post_type}/{category}) - {user.user_handle}")
            
            logger.info(f"✅ 샘플 게시글 작성 완료 ({post_count}개)")
            
        except Exception as e:
            import traceback
            logger.error(f"❌ 샘플 게시글 작성 실패: {str(e)}")
            logger.error(f"📋 상세 에러: {traceback.format_exc()}")
            raise
    
    async def create_comments_on_posts(self):
        """상대방 게시글에 댓글 달기"""
        try:
            logger.info("💬 게시글에 댓글 작성 중...")
            
            for post in self.created_posts:
                # 게시글 작성자가 아닌 다른 사용자들이 댓글 달기
                for user in self.test_users:
                    if user.id != post.author_id:
                        comment_content = random.choice(self.sample_comments)
                        
                        comment_create = CommentCreate(
                            content=comment_content
                        )
                        
                        comment = await self.comments_service.create_comment(post.slug, comment_create, user)
                        self.created_comments.append(comment)
                        logger.info(f"  ✅ 댓글 작성: {comment.content[:20]}... - {user.user_handle}")
            
            logger.info(f"✅ 댓글 작성 완료 ({len(self.created_comments)}개)")
            
        except Exception as e:
            logger.error(f"❌ 댓글 작성 실패: {str(e)}")
            raise
    
    async def create_tenant_service_inquiries_reviews(self):
        """입주 업체 서비스에 문의/후기 작성"""
        try:
            logger.info("🏢 입주 업체 서비스 문의/후기 작성 중...")
            
            # 입주 업체 서비스 게시글 찾기
            tenant_service_posts = [
                post for post in self.created_posts 
                if hasattr(post.metadata, 'type') and post.metadata.type == "moving services"
            ]
            
            for post in tenant_service_posts:
                for user in self.test_users:
                    if user.id != post.author_id:
                        # 문의 댓글 작성
                        inquiry_content = random.choice(self.inquiry_comments)
                        inquiry_create = CommentCreate(
                            content=inquiry_content
                        )
                        
                        inquiry_comment = await self.comments_service.create_comment(post.slug, inquiry_create, user)
                        self.created_comments.append(inquiry_comment)
                        logger.info(f"  ✅ 문의 작성: {inquiry_comment.content[:20]}... - {user.user_handle}")
                        
                        # 후기 댓글 작성
                        review_content = random.choice(self.review_comments)
                        review_create = CommentCreate(
                            content=review_content
                        )
                        
                        review_comment = await self.comments_service.create_comment(post.slug, review_create, user)
                        self.created_comments.append(review_comment)
                        logger.info(f"  ✅ 후기 작성: {review_comment.content[:20]}... - {user.user_handle}")
            
            logger.info("✅ 입주 업체 서비스 문의/후기 작성 완료")
            
        except Exception as e:
            logger.error(f"❌ 입주 업체 서비스 문의/후기 작성 실패: {str(e)}")
            raise
    
    async def create_reactions(self):
        """게시글과 댓글에 추천/비추천/저장 반응"""
        try:
            logger.info("👍 게시글/댓글에 반응 추가 중...")
            
            reaction_types = ["like", "dislike", "save"]
            
            # 게시글에 반응 추가
            for post in self.created_posts:
                for user in self.test_users:
                    if user.id != post.author_id:
                        # 랜덤하게 반응 선택 (일부는 반응 안 함)
                        if random.random() < 0.7:  # 70% 확률로 반응
                            reaction_type = random.choice(reaction_types)
                            
                            try:
                                # UserReaction 직접 생성
                                reaction = UserReaction(
                                    user_id=str(user.id),
                                    target_id=str(post.id),
                                    target_type="post",
                                    reaction_type=reaction_type,
                                    created_at=datetime.utcnow()
                                )
                                await reaction.insert()
                                logger.info(f"  ✅ 게시글 반응: {reaction_type} - {user.user_handle}")
                            except Exception as e:
                                logger.warning(f"  ⚠️ 게시글 반응 실패: {str(e)}")
            
            # 댓글에 반응 추가
            for comment in self.created_comments:
                for user in self.test_users:
                    if user.id != comment.author_id:
                        # 랜덤하게 반응 선택 (일부는 반응 안 함)
                        if random.random() < 0.5:  # 50% 확률로 반응
                            reaction_type = random.choice(["like", "dislike"])  # 댓글은 저장 제외
                            
                            try:
                                # UserReaction 직접 생성
                                reaction = UserReaction(
                                    user_id=str(user.id),
                                    target_id=str(comment.id),
                                    target_type="comment",
                                    reaction_type=reaction_type,
                                    created_at=datetime.utcnow()
                                )
                                await reaction.insert()
                                logger.info(f"  ✅ 댓글 반응: {reaction_type} - {user.user_handle}")
                            except Exception as e:
                                logger.warning(f"  ⚠️ 댓글 반응 실패: {str(e)}")
            
            logger.info("✅ 반응 추가 완료")
            
        except Exception as e:
            logger.error(f"❌ 반응 추가 실패: {str(e)}")
            raise
    
    async def run(self):
        """전체 프로세스 실행"""
        try:
            logger.info("🚀 자동 테스트 데이터 설정 시작")
            logger.info("=" * 50)
            
            # 1. 서비스 초기화
            await self.initialize_services()
            
            # 2. 테스트 계정 생성
            await self.create_test_users()
            
            # 3. 샘플 게시글 작성
            await self.create_sample_posts()
            
            # 4. 댓글 작성
            await self.create_comments_on_posts()
            
            # 5. 입주 업체 서비스 문의/후기 작성
            await self.create_tenant_service_inquiries_reviews()
            
            # 6. 반응 추가
            await self.create_reactions()
            
            logger.info("=" * 50)
            logger.info("🎉 자동 테스트 데이터 설정 완료!")
            logger.info(f"📊 생성된 데이터:")
            logger.info(f"  👥 사용자: {len(self.test_users)}명")
            logger.info(f"  📝 게시글: {len(self.created_posts)}개")
            logger.info(f"  💬 댓글: {len(self.created_comments)}개")
            
        except Exception as e:
            logger.error(f"❌ 자동 테스트 데이터 설정 실패: {str(e)}")
            raise
        finally:
            if database.is_connected:
                await database.disconnect()
                logger.info("✅ 데이터베이스 연결 종료")


async def main():
    """메인 실행 함수"""
    setup = AutoTestDataSetup()
    await setup.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🚫 사용자가 프로그램을 중단했습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 프로그램 실행 중 오류: {str(e)}")
        sys.exit(1)