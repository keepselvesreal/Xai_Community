#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.core.config import settings

async def check_property_posts():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    # property_information 타입 게시글 조회
    posts = await db.posts.find({
        'type': 'property_information'
    }).to_list(length=None)
    
    print(f'=== property_information 타입 게시글 총 {len(posts)}개 ===')
    
    for i, post in enumerate(posts, 1):
        print(f'\n--- 게시글 {i} ---')
        print(f'ID: {post.get("_id")}')
        print(f'제목: {post.get("title")}')
        print(f'타입: {post.get("type")}')
        print(f'서비스: {post.get("service")}')
        print(f'카테고리: {post.get("category")}')
        print(f'태그: {post.get("tags")}')
        print(f'작성자: {post.get("author")}')
        
        # service 필드가 없는 경우 확인
        if 'service' not in post:
            print('⚠️  service 필드가 없습니다!')
        elif post.get('service') is None:
            print('⚠️  service 필드가 null입니다!')
        elif post.get('service') == '':
            print('⚠️  service 필드가 빈 문자열입니다!')
    
    # 전문가 꿀정보 타입 게시글도 확인
    print('\n\n=== 전문가 꿀정보 타입 게시글 확인 ===')
    expert_posts = await db.posts.find({
        'type': 'expert_tips'
    }).to_list(length=2)  # 샘플 2개만
    
    for i, post in enumerate(expert_posts, 1):
        print(f'\n--- 전문가 꿀정보 게시글 {i} ---')
        print(f'ID: {post.get("_id")}')
        print(f'제목: {post.get("title")}')
        print(f'타입: {post.get("type")}')
        print(f'서비스: {post.get("service")}')
        print(f'카테고리: {post.get("category")}')
        print(f'태그: {post.get("tags")}')
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(check_property_posts())