#!/usr/bin/env python3
"""
테스트 서비스 데이터 생성 스크립트
"""

import asyncio
import json
import os
from datetime import datetime
from nadle_backend.models.core import Post, PostMetadata, User
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

async def create_test_service():
    # 데이터베이스 연결
    try:
        from nadle_backend.core.config import settings
        client = AsyncIOMotorClient(settings.DATABASE_URL)
        await init_beanie(database=client[settings.DATABASE_NAME], document_models=[Post, User])
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # 테스트 사용자 찾기/생성
    test_user = await User.find_one({"email": "test@test.com"})
    if not test_user:
        print("Creating test user...")
        test_user = User(
            email="test@test.com",
            user_handle="testuser",
            name="테스트 사용자",
            password_hash="test_hash"
        )
        await test_user.save()
    
    # 테스트 서비스 데이터
    service_data = {
        "company": {
            "name": "테스트 청소업체",
            "contact": "010-1234-5678",
            "availableHours": "09:00-18:00",
            "description": "아파트 전문 청소 서비스를 제공합니다."
        },
        "services": [
            {
                "name": "일반 청소",
                "price": 50000,
                "description": "기본적인 집안 청소 서비스"
            },
            {
                "name": "입주 청소",
                "price": 80000,
                "specialPrice": 70000,
                "description": "새 입주시 전체 청소 서비스"
            }
        ]
    }
    
    # 서비스 게시글 생성
    test_post = Post(
        title="테스트 청소업체",
        content=json.dumps(service_data, ensure_ascii=False, indent=2),
        slug="test-cleaning-service",
        service="residential_community",
        author_id=test_user.id,
        metadata=PostMetadata(
            type="moving services",
            category="청소",
            tags=["청소", "업체", "서비스"],
            visibility="public"
        ),
        status="published",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        published_at=datetime.utcnow(),
        view_count=0,
        like_count=0,
        dislike_count=0,
        comment_count=0,
        bookmark_count=0
    )
    
    # 기존 같은 슬러그가 있으면 삭제
    existing = await Post.find_one({"slug": "test-cleaning-service"})
    if existing:
        await existing.delete()
        print("Deleted existing test service")
    
    await test_post.save()
    print(f"✅ Created test service: {test_post.title} (id: {test_post.id}, slug: {test_post.slug})")
    
    client.close()
    return test_post.slug

if __name__ == "__main__":
    slug = asyncio.run(create_test_service())
    if slug:
        print(f"\n🔗 Test service URL: http://localhost:5173/moving-services-post/{slug}")
        print(f"🔗 API URL: http://localhost:8000/api/posts/services/{slug}")