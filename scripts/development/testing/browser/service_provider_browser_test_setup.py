#!/usr/bin/env python3
"""
입주 서비스 업체 페이지 브라우저 테스트 데이터 생성기
- 작업 시간: 2025-07-22 12:04 (KST) (date 명령어로 직접 확인한 현재 한국 시간 기준)
- 주요 컴포넌트들:
  - ServiceProviderTestDataGenerator: 브라우저 테스트용 데이터 생성 (lines 23-350)
  - 권한 사용자 계정 생성 (lines 80-110)
  - 일반 사용자 계정 생성 (lines 112-140)
  - 문의/후기 댓글 생성 (lines 200-280)
  - 비공개 문의 및 별점 후기 생성 (lines 282-330)
- 관련 파일: service_provider_browser_test_guide.html (브라우저 확인 가이드)
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
import sys
import os

# 백엔드 패키지 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../backend'))

from nadle_backend.models.core import User, Post, Comment, PostMetadata
from nadle_backend.config import settings
from nadle_backend.database import database


class ServiceProviderTestDataGenerator:
    """입주 서비스 업체 페이지 브라우저 테스트용 데이터 생성기"""
    
    def __init__(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = uuid.uuid4().hex[:4].upper()
        self.session_id = f"BROWSER_TEST_{timestamp}_{random_suffix}"
        
        # 생성할 데이터 통계
        self.data_stats = {
            "created_users": 0,
            "created_posts": 0,
            "created_comments": 0,
            "inquiry_comments": 0,
            "review_comments": 0,
            "private_inquiries": 0,
            "rated_reviews": 0
        }
        
        # 테스트 사용자 정보
        self.test_users = {}
        self.service_posts = []
    
    async def generate_all_test_data(self):
        """모든 브라우저 테스트 데이터 생성"""
        print("🌐 입주 서비스 업체 페이지 브라우저 테스트 데이터 생성 시작!")
        print(f"🆔 세션 ID: {self.session_id}")
        print("=" * 80)
        
        try:
            # 데이터베이스 연결
            await database.connect()
            
            # Beanie 모델 초기화
            await database.init_beanie_models([User, Post, Comment])
            print("✅ 데이터베이스 연결 완료")
            
            # 1. 테스트 사용자 계정 생성
            await self._create_test_users()
            
            # 2. 기존 서비스 업체 게시글 확인 및 추가 생성
            await self._setup_service_posts()
            
            # 3. 문의/후기 댓글 생성
            await self._create_inquiry_review_comments()
            
            # 4. 비공개 문의 및 별점 후기 생성
            await self._create_special_comments()
            
            # 5. 샘플 반응 데이터 생성
            await self._create_sample_reactions()
            
            # 6. 생성 결과 보고
            await self._generate_creation_report()
            
            print("\n🎉 브라우저 테스트 데이터 생성 완료!")
            return True
            
        except Exception as e:
            print(f"\n❌ 데이터 생성 중 오류 발생: {str(e)}")
            return False
    
    async def _create_test_users(self):
        """테스트 사용자 계정 생성"""
        print("\n👥 테스트 사용자 계정 생성...")
        
        # 1. 권한 사용자 계정 (글쓰기 권한 보유)
        writer_user = User(
            email=f"writer_user_{self.session_id.lower()}@example.com",
            user_handle=f"writer_{random.randint(1000, 9999)}",
            display_name="서비스 업체 관리자",
            password_hash="$2b$12$test_hash_for_browser_testing",
            is_active=True,
            status="active",
            metadata={
                "session_id": self.session_id,
                "test_type": "browser_test",
                "user_role": "service_writer",
                "permissions": ["write_service_posts", "manage_comments"],
                "created_for": "입주 서비스 업체 페이지 브라우저 테스트"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await writer_user.save()
        self.test_users['writer'] = writer_user
        self.data_stats['created_users'] += 1
        print(f"   ✅ 권한 사용자 생성: {writer_user.email}")
        
        # 2. 일반 사용자 계정 (권한 없음)
        normal_user = User(
            email=f"normal_user_{self.session_id.lower()}@example.com",
            user_handle=f"normal_{random.randint(1000, 9999)}",
            display_name="일반 사용자",
            password_hash="$2b$12$test_hash_for_browser_testing",
            is_active=True,
            status="active",
            metadata={
                "session_id": self.session_id,
                "test_type": "browser_test",
                "user_role": "normal_user",
                "permissions": ["read_posts", "write_comments"],
                "created_for": "입주 서비스 업체 페이지 브라우저 테스트"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await normal_user.save()
        self.test_users['normal'] = normal_user
        self.data_stats['created_users'] += 1
        print(f"   ✅ 일반 사용자 생성: {normal_user.email}")
        
        # 3. 댓글 작성용 추가 사용자들
        for i in range(3):
            comment_user = User(
                email=f"commenter_{i}_{self.session_id.lower()}@example.com",
                user_handle=f"commenter_{i}_{random.randint(1000, 9999)}",
                display_name=f"댓글 작성자 {i+1}",
                password_hash="$2b$12$test_hash_for_browser_testing",
                is_active=True,
                status="active",
                metadata={
                    "session_id": self.session_id,
                    "test_type": "browser_test",
                    "user_role": "commenter",
                    "created_for": "댓글 작성 테스트"
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await comment_user.save()
            self.test_users[f'commenter_{i}'] = comment_user
            self.data_stats['created_users'] += 1
            print(f"   ✅ 댓글 사용자 {i+1} 생성: {comment_user.email}")
    
    async def _setup_service_posts(self):
        """서비스 업체 게시글 설정"""
        print("\n🏢 서비스 업체 게시글 확인 및 생성...")
        
        # 기존 서비스 업체 게시글 조회
        existing_posts = await Post.find(
            Post.metadata.type == "moving services",
            Post.status == "published"
        ).limit(5).to_list()
        
        if existing_posts:
            self.service_posts = existing_posts
            print(f"   ✅ 기존 서비스 업체 게시글 {len(existing_posts)}개 확인")
        else:
            # 기존 게시글이 없으면 테스트용 생성
            await self._create_sample_service_posts()
    
    async def _create_sample_service_posts(self):
        """샘플 서비스 업체 게시글 생성"""
        writer_user = self.test_users['writer']
        
        sample_services = [
            {
                "title": "브라우저 테스트용 청소 서비스",
                "content": "전문적인 입주 청소 서비스를 제공합니다. 브라우저 테스트를 위한 샘플 데이터입니다.",
                "category": "청소",
                "slug": f"browser-test-cleaning-{self.session_id.lower()}"
            },
            {
                "title": "브라우저 테스트용 이사 서비스", 
                "content": "안전하고 빠른 이사 서비스입니다. 브라우저 테스트를 위한 샘플 데이터입니다.",
                "category": "이사",
                "slug": f"browser-test-moving-{self.session_id.lower()}"
            }
        ]
        
        for service_data in sample_services:
            service_post = Post(
                title=service_data["title"],
                content=service_data["content"],
                service="residential_community",
                author_id=str(writer_user.id),
                metadata=PostMetadata(
                    type="moving services",
                    category=service_data["category"],
                    session_id=self.session_id,
                    test_type="browser_test"
                ),
                slug=service_data["slug"],
                status="published",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                view_count=random.randint(50, 200),
                like_count=random.randint(5, 25),
                dislike_count=random.randint(0, 5),
                comment_count=0,  # 댓글 생성 후 업데이트 예정
                bookmark_count=random.randint(2, 15)
            )
            await service_post.save()
            self.service_posts.append(service_post)
            self.data_stats['created_posts'] += 1
            print(f"   ✅ 서비스 게시글 생성: {service_data['title']}")
    
    async def _create_inquiry_review_comments(self):
        """문의/후기 댓글 생성"""
        print("\n💬 문의/후기 댓글 생성...")
        
        # 각 서비스 업체 게시글에 대해 댓글 생성
        for post in self.service_posts:
            # 공개 문의 댓글 5개
            await self._create_inquiry_comments(post, count=5, private=False)
            
            # 비공개 문의 댓글 2개
            await self._create_inquiry_comments(post, count=2, private=True)
            
            # 별점 포함 후기 댓글 8개
            await self._create_review_comments(post, count=8)
            
            # 댓글 수 업데이트
            total_comments = await Comment.find(
                Comment.parent_id == str(post.id),
                Comment.status == "active"
            ).count()
            
            post.comment_count = total_comments
            await post.save()
    
    async def _create_inquiry_comments(self, post: Post, count: int, private: bool = False):
        """문의 댓글 생성"""
        inquiry_templates = [
            "가격이 어떻게 되나요?",
            "예약은 어떻게 하나요?", 
            "주말 서비스도 가능한가요?",
            "소요 시간은 얼마나 되나요?",
            "추가 서비스는 어떤 것들이 있나요?",
            "취소 정책은 어떻게 되나요?",
            "연락처는 어디로 하면 되나요? 010-1234-5678",
            "견적을 받아보고 싶습니다.",
            "다른 지역도 서비스 가능한가요?",
            "예약 가능한 날짜를 알려주세요."
        ]
        
        for i in range(count):
            user = random.choice([
                self.test_users['normal'],
                self.test_users['commenter_0'],
                self.test_users['commenter_1'],
                self.test_users['commenter_2']
            ])
            
            content = random.choice(inquiry_templates)
            
            comment = Comment(
                content=content,
                parent_id=str(post.id),
                author_id=str(user.id),
                metadata={
                    "subtype": "service_inquiry",
                    "session_id": self.session_id,
                    "test_type": "browser_test",
                    "is_private": private
                },
                status="active",
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                updated_at=datetime.utcnow(),
                like_count=random.randint(0, 5),
                reply_count=0
            )
            await comment.save()
            self.data_stats['created_comments'] += 1
            self.data_stats['inquiry_comments'] += 1
            
            if private:
                self.data_stats['private_inquiries'] += 1
                print(f"   ✅ 비공개 문의 댓글 생성: {content[:20]}...")
            else:
                print(f"   ✅ 공개 문의 댓글 생성: {content[:20]}...")
    
    async def _create_review_comments(self, post: Post, count: int):
        """후기 댓글 생성 (별점 포함)"""
        review_templates = [
            "정말 만족스러운 서비스였습니다!",
            "친절하고 꼼꼼하게 잘해주셨어요.",
            "다음에도 이용하고 싶습니다.",
            "가격 대비 정말 좋은 서비스입니다.",
            "시간 약속도 잘 지키시고 전문적이에요.",
            "추천합니다! 다른 분들도 이용해보세요.",
            "기대 이상으로 깔끔하게 해주셨습니다.",
            "직원분들이 모두 친절하셨어요.",
            "완벽한 서비스! 별 다섯개 드립니다.",
            "조금 아쉬운 부분이 있었지만 전반적으로 좋았습니다."
        ]
        
        for i in range(count):
            user = random.choice([
                self.test_users['normal'],
                self.test_users['commenter_0'], 
                self.test_users['commenter_1'],
                self.test_users['commenter_2']
            ])
            
            content = random.choice(review_templates)
            rating = random.randint(3, 5)  # 3-5점 위주로 생성
            
            comment = Comment(
                content=content,
                parent_id=str(post.id),
                author_id=str(user.id),
                metadata={
                    "subtype": "service_review",
                    "rating": rating,
                    "session_id": self.session_id,
                    "test_type": "browser_test"
                },
                status="active",
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 14)),
                updated_at=datetime.utcnow(),
                like_count=random.randint(0, 8),
                reply_count=0
            )
            await comment.save()
            self.data_stats['created_comments'] += 1
            self.data_stats['review_comments'] += 1
            self.data_stats['rated_reviews'] += 1
            print(f"   ✅ 후기 댓글 생성 (별점 {rating}점): {content[:20]}...")
    
    async def _create_special_comments(self):
        """특별한 댓글들 생성 (답글, 마스킹 테스트용 등)"""
        print("\n🔒 특별 기능 댓글 생성...")
        
        # 마스킹 테스트용 개인정보 포함 비공개 문의
        if self.service_posts:
            post = self.service_posts[0]
            user = self.test_users['normal']
            
            privacy_content = "연락처 010-9876-5432로 전화 주시고, 이메일은 test@privacy.com입니다."
            
            privacy_comment = Comment(
                content=privacy_content,
                parent_id=str(post.id),
                author_id=str(user.id),
                metadata={
                    "subtype": "service_inquiry",
                    "is_private": True,
                    "session_id": self.session_id,
                    "test_type": "browser_test_privacy"
                },
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await privacy_comment.save()
            self.data_stats['created_comments'] += 1
            self.data_stats['private_inquiries'] += 1
            print(f"   ✅ 마스킹 테스트용 비공개 문의 생성")
    
    async def _create_sample_reactions(self):
        """샘플 반응 데이터 생성"""
        print("\n👍 샘플 반응 데이터 생성...")
        # 실제 반응 시스템이 구현되면 여기서 샘플 반응 생성
        print("   ✅ 반응 데이터는 게시글 생성 시 기본값으로 설정됨")
    
    async def _generate_creation_report(self):
        """데이터 생성 결과 보고"""
        print("\n📊 브라우저 테스트 데이터 생성 결과")
        print("=" * 60)
        print(f"🆔 세션 ID: {self.session_id}")
        print(f"👥 생성된 사용자: {self.data_stats['created_users']}명")
        print(f"   - 권한 사용자: {self.test_users['writer'].email}")
        print(f"   - 일반 사용자: {self.test_users['normal'].email}")
        print(f"🏢 서비스 게시글: {len(self.service_posts)}개")
        print(f"💬 생성된 댓글: {self.data_stats['created_comments']}개")
        print(f"   - 문의 댓글: {self.data_stats['inquiry_comments']}개")
        print(f"   - 후기 댓글: {self.data_stats['review_comments']}개")
        print(f"   - 비공개 문의: {self.data_stats['private_inquiries']}개")
        print(f"   - 별점 후기: {self.data_stats['rated_reviews']}개")
        print()
        print("🌐 브라우저 테스트 준비 완료!")
        print("   다음 단계: service_provider_browser_test_guide.html 열어서 테스트 진행")


async def main():
    """메인 실행 함수"""
    print("🎯 입주 서비스 업체 페이지 브라우저 테스트 데이터 생성기")
    print("권한 사용자, 문의/후기 댓글, 비공개 마스킹, 별점 평가 데이터 생성")
    print()
    
    generator = ServiceProviderTestDataGenerator()
    success = await generator.generate_all_test_data()
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))